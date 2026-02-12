"""
Synchronous credential service wrapper for self-hosted Supabase.

Uses httpx directly to make HTTP requests to PostgREST v12 without
the /rest/v1/ path prefix that the standard supabase library adds.
"""
import asyncio
import base64
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config.logfire_config import get_logger

logger = get_logger(__name__)


@dataclass
class CredentialItem:
    """Represents a credential/setting item."""
    key: str
    value: str | None = None
    encrypted_value: str | None = None
    is_encrypted: bool = False
    category: str | None = None
    description: str | None = None


class SyncCredentialService:
    """Async credential service that uses httpx directly to bypass /rest/v1/ prefix."""

    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._cache_initialized = False
        self._rag_settings_cache: dict[str, Any] | None = None
        self._rag_cache_timestamp: float | None = None
        self._rag_cache_ttl = 300
        self._client: httpx.AsyncClient | None = None

        # Get Supabase configuration
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._service_key = os.getenv("SUPABASE_SERVICE_KEY")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _close_client(self):
        """Close the httpx client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _get_encryption_key(self) -> bytes:
        """Generate encryption key from environment variables."""
        service_key = os.getenv("SUPABASE_SERVICE_KEY", "default-key-for-development")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"static_salt_for_credentials",
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(service_key.encode()))
        return key

    def _encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value using Fernet encryption."""
        if not value:
            return ""
        try:
            fernet = Fernet(self._get_encryption_key())
            encrypted_bytes = fernet.encrypt(value.encode("utf-8"))
            return base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Error encrypting value: {e}")
            raise

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value using Fernet encryption."""
        if not encrypted_value:
            return ""
        try:
            fernet = Fernet(self._get_encryption_key())
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode("utf-8"))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Error decrypting value: {e}")
            raise

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make async HTTP request to PostgREST with proper headers."""
        client = await self._get_client()
        url = f"{self._supabase_url}/{endpoint.lstrip('/')}"
        headers = {
            "apikey": self._service_key,
            "Authorization": f"Bearer {self._service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

        # Handle body for POST/PUT
        json_data = kwargs.pop("json", None)
        if json_data:
            return await client.request(method, url, headers=headers, json=json_data)
        else:
            return await client.request(method, url, headers=headers, params=kwargs)

    async def load_all_credentials(self) -> dict[str, Any]:
        """Load all credentials from database and cache them."""
        try:
            response = await self._make_request("GET", "archon_settings", select="*")
            response.raise_for_status()

            credentials = {}
            for item in response.json():
                key = item["key"]
                if item["is_encrypted"] and item["encrypted_value"]:
                    credentials[key] = {
                        "encrypted_value": item["encrypted_value"],
                        "is_encrypted": True,
                        "category": item["category"],
                        "description": item["description"],
                    }
                else:
                    credentials[key] = item["value"]

            self._cache = credentials
            self._cache_initialized = True
            logger.info(f"Loaded {len(credentials)} credentials from database")
            return credentials

        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            raise

    async def get_credential(self, key: str, default: Any = None, decrypt: bool = True) -> Any:
        """Get a credential value by key."""
        if not self._cache_initialized:
            await self.load_all_credentials()

        value = self._cache.get(key, default)

        if isinstance(value, dict) and value.get("is_encrypted") and decrypt:
            encrypted_value = value.get("encrypted_value")
            if encrypted_value:
                try:
                    return self._decrypt_value(encrypted_value)
                except Exception as e:
                    logger.error(f"Failed to decrypt credential {key}: {e}")
                    return default
        return value

    async def set_credential(
        self,
        key: str,
        value: str,
        is_encrypted: bool = False,
        category: str = None,
        description: str = None,
    ) -> bool:
        """Set a credential value."""
        try:
            if is_encrypted:
                encrypted_value = self._encrypt_value(value)
                data = {
                    "key": key,
                    "encrypted_value": encrypted_value,
                    "value": None,
                    "is_encrypted": True,
                    "category": category,
                    "description": description,
                }
            else:
                data = {
                    "key": key,
                    "value": value,
                    "encrypted_value": None,
                    "is_encrypted": False,
                    "category": category,
                    "description": description,
                }

            # Use upsert for insert/update
            response = await self._make_request("POST", "archon_settings", json=data)
            response.raise_for_status()

            self._cache[key] = value
            logger.info(f"Successfully stored credential: {key}")
            return True

        except Exception as e:
            logger.error(f"Error setting credential {key}: {e}")
            return False

    async def delete_credential(self, key: str) -> bool:
        """Delete a credential."""
        try:
            response = await self._make_request("DELETE", f"archon_settings?key=eq.{key}")
            response.raise_for_status()

            if key in self._cache:
                del self._cache[key]

            logger.info(f"Successfully deleted credential: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting credential {key}: {e}")
            return False

    async def get_credentials_by_category(self, category: str) -> dict[str, Any]:
        """Get all credentials for a specific category."""
        if not self._cache_initialized:
            await self.load_all_credentials()

        credentials = {}
        for key, value in self._cache.items():
            if isinstance(value, dict) and value.get("category") == category:
                credentials[key] = value

        return credentials

    async def list_all_credentials(self) -> list[CredentialItem]:
        """Get all credentials as a list of CredentialItem objects."""
        if not self._cache_initialized:
            await self.load_all_credentials()

        credentials = []
        for key, value in self._cache.items():
            if isinstance(value, dict) and value.get("is_encrypted") and value.get("encrypted_value"):
                cred = CredentialItem(
                    key=key,
                    value="[ENCRYPTED]",
                    encrypted_value=None,
                    is_encrypted=value.get("is_encrypted"),
                    category=value.get("category"),
                    description=value.get("description"),
                )
            elif isinstance(value, dict):
                cred = CredentialItem(
                    key=key,
                    value=value,
                    encrypted_value=None,
                    is_encrypted=False,
                    category=value.get("category"),
                    description=value.get("description"),
                )
            else:
                cred = CredentialItem(
                    key=key,
                    value=str(value),
                    encrypted_value=None,
                    is_encrypted=False,
                    category=None,
                    description=None,
                )
            credentials.append(cred)

        return credentials


# Global instance
sync_credential_service = SyncCredentialService()


async def get_credential(key: str, default: Any = None) -> Any:
    """Async get_credential wrapper."""
    return await sync_credential_service.get_credential(key, default)


async def set_credential(
    key: str, value: str, is_encrypted: bool = False, category: str = None, description: str = None
) -> bool:
    """Async set_credential wrapper."""
    return await sync_credential_service.set_credential(key, value, is_encrypted, category, description)


async def delete_credential(key: str) -> bool:
    """Async delete_credential wrapper."""
    return await sync_credential_service.delete_credential(key)


async def list_all_credentials() -> list[CredentialItem]:
    """Async list_all_credentials wrapper."""
    return await sync_credential_service.list_all_credentials()


async def get_credentials_by_category(category: str) -> dict[str, Any]:
    """Async get_credentials_by_category wrapper."""
    return await sync_credential_service.get_credentials_by_category(category)
