#!/usr/bin/env bash
# PMOVES Environment Preflight Check (Bash)
# Usage:
#   bash scripts/env_check.sh        # full scan
#   bash scripts/env_check.sh -q     # quick

set -euo pipefail
quick=0
[[ "${1:-}" == "-q" ]] && quick=1

have(){ command -v "$1" >/dev/null 2>&1; }
ver(){ ($@ --version 2>/dev/null || true) | head -n1 | tr -s ' '; }

echo
echo "== PMOVES Environment Check =="
echo "CWD: $(pwd)"
echo "OS:  $(uname -a || true)"
echo

echo "Commands:"
for c in rg git python python3 pip uv poetry conda node npm make docker docker-compose; do
  if have "$c"; then
    printf "[OK] %-14s %s\n" "$c" "$(ver "$c")"
  else
    printf "[--] %-14s\n" "$c"
  fi
done
if have docker; then
  if docker compose version >/dev/null 2>&1; then
    printf "[OK] %-14s %s\n" "compose" "$(docker compose version | head -n1 | tr -s ' ')"
  elif have docker-compose; then
    printf "[OK] %-14s %s\n" "compose" "$(docker-compose --version | tr -s ' ')"
  else
    printf "[--] %-14s\n" "compose"
  fi
fi

echo
echo "Repo shape:"
for d in services contracts schemas supabase neo4j n8n comfyui datasets docs; do
  if [[ -d "$d" ]]; then printf "%-14s %s\n" "$d:" "yes"; else printf "%-14s %s\n" "$d:" "no"; fi
done

echo
echo "Contracts:"
if [[ -f contracts/topics.json ]]; then
  if cat contracts/topics.json >/dev/null 2>&1; then
    echo "contracts/topics.json: valid"
    # Ensure summary topics exist and schema files are present
    need_topics=("health.weekly.summary.v1" "finance.monthly.summary.v1")
    for t in "${need_topics[@]}"; do
      if ! jq -e --arg T "$t" '.topics[$T]' contracts/topics.json >/dev/null 2>&1; then
        echo "WARN: missing topic in topics.json: $t"
      fi
    done
  else
    echo "contracts/topics.json: invalid"
  fi
else
  echo "contracts/topics.json: missing"
fi

echo
echo "Ports:"
ports=(6333 7474 8088 8085 3000 8087 8084 7700)
for p in "${ports[@]}"; do
  if command -v lsof >/dev/null 2>&1; then
    if lsof -iTCP:$p -sTCP:LISTEN -P -n >/dev/null 2>&1; then
      printf "%-6s %s\n" "$p" "LISTENING"
    else
      printf "%-6s %s\n" "$p" "free"
    fi
  else
    printf "%-6s %s\n" "$p" "(lsof not installed)"
  fi
done

echo
echo ".env status:"
if [[ -f .env ]]; then echo ".env present:       true"; else echo ".env present:       false"; fi
if [[ -f .env.example ]]; then echo ".env.example:       true"; else echo ".env.example:       false"; fi

echo
echo "Mappers:"
if [[ -f tools/events_to_cgp.py ]]; then echo "events_to_cgp.py:   present"; else echo "events_to_cgp.py:   missing"; fi

echo
echo "Done."
