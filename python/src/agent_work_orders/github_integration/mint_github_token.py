"""GitHub App Token Minter

Mints short-lived GitHub App installation tokens with caching.
Reusable module for Archon GitHub integration.

Based on: PMOVES-BoTZ/features/github/mint_and_exec.py

Usage:
    token = await get_installation_token()
    # or with force refresh
    token = await get_installation_token(force_refresh=True)
"""

from __future__ import annotations

import os
import time
from typing import Literal

import jwt
import requests

from ..utils.structured_logger import get_logger

logger = get_logger(__name__)

# Token cache with 50-minute expiry (tokens valid for 60 min)
_token_cache: dict[str, dict[str, str | float]] = {}

# Cache key prefix
CACHE_KEY = "github_token"


def _get_credentials() -> tuple[str, str, str]:
    """Get GitHub App credentials from environment.

    Returns:
        Tuple of (app_id, installation_id, pem_key)

    Raises:
        KeyError: If required environment variables are missing
    """
    app_id = os.environ["GH_APP_ID"]
    install_id = os.environ["GH_APP_INSTALLATION_ID"]

    # PEM key is multi-line - handle special cases
    pem = os.environ.get("GH_APP_SEC", "")
    if not pem or pem.startswith("-----BEGIN") and len(pem) < 100:
        # Try reading from env file if env var is incomplete
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "pmoves", "env.tier-agent")
        try:
            with open(env_file) as f:
                in_pem = False
                pem_lines = []
                for line in f:
                    line = line.rstrip("\n")
                    if line.startswith("GH_APP_SEC="):
                        pem_lines.append(line.split("=", 1)[1].strip())
                        in_pem = True
                    elif in_pem:
                        if line.startswith("-----END") or (line and not line.startswith("-----")):
                            break
                        pem_lines.append(line)
                pem = "\n".join(pem_lines)
        except Exception:
            pass

    if not pem or len(pem) < 100:
        raise ValueError(
            "GH_APP_SEC not set or incomplete (must be full PEM private key)"
        )

    return app_id, install_id, pem


async def mint_installation_token() -> str:
    """Mint a short-lived GitHub App installation token.

    Signs a JWT with the App's PEM key, then exchanges it for an
    installation access token via the GitHub API.

    The token expires after 1 hour. This function handles caching.

    Returns:
        str: Installation access token.

    Raises:
        KeyError: If required env vars are missing.
        ValueError: If PEM key is invalid.
        requests.HTTPError: If the GitHub API call fails.
    """
    logger.info("github_token_mint_started")

    app_id, install_id, pem = _get_credentials()

    now = int(time.time())
    payload = {
        "iat": now - 60,   # issued at (60s clock skew tolerance)
        "exp": now + 600,  # expires in 10 minutes
        "iss": app_id,
    }

    jwt_token = jwt.encode(payload, pem, algorithm="RS256")
    logger.debug("github_jwt_created", app_id=app_id)

    resp = requests.post(
        f"https://api.github.com/app/installations/{install_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )
    resp.raise_for_status()

    token = resp.json()["token"]
    logger.info("github_token_minted", token_prefix=token[:10])

    return token


def _is_cache_valid(cache_entry: dict[str, str | float]) -> bool:
    """Check if cached token is still valid."""
    expires_at = cache_entry.get("expires_at", 0)
    return time.time() < expires_at


async def get_installation_token(
    force_refresh: bool = False,
    cache_key: str = CACHE_KEY
) -> str:
    """Get GitHub App installation token with caching.

    Args:
        force_refresh: Force token refresh even if cache is valid
        cache_key: Cache key for storing the token

    Returns:
        str: Installation access token.

    Raises:
        KeyError: If GH_APP_* env vars are missing
        ValueError: If PEM key is invalid
        requests.HTTPError: If the GitHub API call fails
    """
    global _token_cache

    # Check cache first
    if not force_refresh and cache_key in _token_cache:
        cache_entry = _token_cache[cache_key]
        if _is_cache_valid(cache_entry):
            logger.info("github_token_cache_hit", cache_key=cache_key)
            return str(cache_entry["token"])

    logger.info("github_token_cache_miss", force_refresh=force_refresh)

    # Mint new token
    token = await mint_installation_token()

    # Cache with 50-minute expiry (tokens valid for 60 min)
    _token_cache[cache_key] = {
        "token": token,
        "expires_at": time.time() + (50 * 60),  # 50 minutes
    }

    logger.info("github_token_cached", expires_in="50min")
    return token


def clear_token_cache(cache_key: str = CACHE_KEY) -> None:
    """Clear cached token (e.g., after credentials change).

    Args:
        cache_key: Cache key to clear
    """
    global _token_cache
    if cache_key in _token_cache:
        del _token_cache[cache_key]
    logger.info("github_token_cache_cleared", cache_key=cache_key)


__all__ = [
    "mint_installation_token",
    "get_installation_token",
    "clear_token_cache",
]
