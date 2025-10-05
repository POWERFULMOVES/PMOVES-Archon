#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BUNDLE_ROOT=$(cd "${SCRIPT_DIR}" && pwd)
TAILSCALE_HELPER="${BUNDLE_ROOT}/../tailscale/tailscale_up.sh"
TAILSCALE_AUTH_FILE="${BUNDLE_ROOT}/../tailscale/tailscale_authkey.txt"

log() {
  echo "[jetson-postinstall] $*"
}

apt update && apt -y upgrade
apt -y install docker.io docker-compose-plugin curl gnupg git

# Enable NVIDIA runtime (JetPack already ships it)
cat >/etc/docker/daemon.json <<'JSON'
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": { "path": "nvidia-container-runtime", "runtimeArgs": [] }
  }
}
JSON
systemctl enable --now docker
usermod -aG docker "${SUDO_USER:-$USER}"
systemctl restart docker

# Tailscale setup and Tailnet join
curl -fsSL https://tailscale.com/install.sh | sh
systemctl enable tailscaled
systemctl start tailscaled

join_tailnet() {
  local helper_path="$1"
  local auth_file="$2"
  local auth_value="${TAILSCALE_AUTHKEY:-}"

  if [[ -z "${auth_value}" && -f "${auth_file}" ]]; then
    auth_value=$(head -n1 "${auth_file}" | tr -d '\r')
    if [[ -n "${auth_value}" ]]; then
      log "Using Tailnet auth key from ${auth_file}."
    else
      log "Tailnet auth key file ${auth_file} is empty; continuing without auth key."
    fi
  fi

  if [[ -n "${auth_value}" ]]; then
    export TAILSCALE_AUTHKEY="${auth_value}"
  fi

  if ( # subshell keeps helper's shell options local
    if [[ -n "${auth_value}" ]]; then
      export TAILSCALE_AUTHKEY
    fi
    # shellcheck disable=SC1090
    source "${helper_path}"
  ); then
    log "Tailnet join completed successfully."
  else
    local status=$?
    log "Tailnet join failed via helper (${helper_path}) with exit code ${status}."
  fi
}

if [[ -f "${TAILSCALE_HELPER}" ]]; then
  if [[ -x "${TAILSCALE_HELPER}" ]]; then
    log "Attempting Tailnet join using ${TAILSCALE_HELPER}."
    join_tailnet "${TAILSCALE_HELPER}" "${TAILSCALE_AUTH_FILE}"
  else
    log "Tailnet helper found at ${TAILSCALE_HELPER} but is not executable; attempting to source anyway."
    join_tailnet "${TAILSCALE_HELPER}" "${TAILSCALE_AUTH_FILE}"
  fi
else
  log "Tailnet helper not found at ${TAILSCALE_HELPER}; skipping automatic tailscale up."
fi

# jetson-containers install
git clone https://github.com/dusty-nv/jetson-containers.git /opt/jetson-containers || true
bash /opt/jetson-containers/install.sh || true

echo "Jetson bootstrap complete."
