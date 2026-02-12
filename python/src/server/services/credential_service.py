"""
Credential management service for Archon backend

Handles loading, storing, and accessing credentials with encryption for sensitive values.
Credentials include API keys, service credentials, and application configuration.

Uses the sync credential service which directly accesses PostgREST v12 without
the /rest/v1/ path prefix that supabase-py library adds.
"""

import os
import time
from dataclasses import dataclass
from typing import Any

# Import the sync credential service that bypasses /rest/v1/ prefix
from .credential_service_sync import (
    sync_credential_service,
    get_credential as sync_get_credential,
    set_credential as sync_set_credential,
    delete_credential as sync_delete_credential,
    list_all_credentials as sync_list_all_credentials,
    get_credentials_by_category as sync_get_credentials_by_category,
    CredentialItem,
)

from ..config.logfire_config import get_logger

logger = get_logger(__name__)


# Re-export CredentialItem from sync service for backwards compatibility
__all__ = [
    "CredentialService",
    "credential_service",
    "get_credential",
    "set_credential",
    "initialize_credentials",
]


class CredentialService:
    """
    Service for managing application credentials and configuration.

    This is a compatibility wrapper around the sync credential service
    which uses httpx directly to avoid the /rest/v1/ prefix issue
    with self-hosted PostgREST v12.
    """

    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._cache_initialized = False
        self._rag_settings_cache: dict[str, Any] | None = None
        self._rag_cache_timestamp: float | None = None
        self._rag_cache_ttl = 300  # 5 minutes TTL for RAG settings cache

    async def load_all_credentials(self) -> dict[str, Any]:
        """Load all credentials from database and cache them."""
        return await sync_credential_service.load_all_credentials()

    async def get_credential(self, key: str, default: Any = None, decrypt: bool = True) -> Any:
        """Get a credential value by key."""
        return await sync_get_credential(key, default)

    async def get_encrypted_credential_raw(self, key: str) -> str | None:
        """Get raw encrypted value for a credential (without decryption)."""
        # For encrypted raw, we need to get from cache without decryption
        if not self._cache_initialized:
            await self.load_all_credentials()
        value = self._cache.get(key)
        if isinstance(value, dict) and value.get("is_encrypted"):
            return value.get("encrypted_value")
        return None

    async def set_credential(
        self,
        key: str,
        value: str,
        is_encrypted: bool = False,
        category: str = None,
        description: str = None,
    ) -> bool:
        """Set a credential value."""
        result = await sync_set_credential(key, value, is_encrypted, category, description)

        # Handle cache invalidation for RAG settings
        if result and category == "rag_strategy":
            self._rag_settings_cache = None
            self._rag_cache_timestamp = None
            logger.debug(f"Invalidated RAG settings cache due to update of {key}")

            # Invalidate provider service cache
            try:
                from .llm_provider_service import clear_provider_cache
                clear_provider_cache()
                logger.debug("Also cleared LLM provider service cache")
            except Exception as e:
                logger.warning(f"Failed to clear provider service cache: {e}")

            # Invalidate LLM provider service cache for provider config
            try:
                from . import llm_provider_service
                cache_keys_to_clear = ["provider_config_llm", "provider_config_embedding", "rag_strategy_settings"]
                for cache_key in cache_keys_to_clear:
                    if cache_key in llm_provider_service._settings_cache:
                        del llm_provider_service._settings_cache[cache_key]
                        logger.debug(f"Invalidated LLM provider service cache key: {cache_key}")
            except ImportError:
                logger.warning("Could not import llm_provider_service to invalidate cache")
            except Exception as e:
                logger.error(f"Error invalidating LLM provider service cache: {e}")

        return result

    async def delete_credential(self, key: str) -> bool:
        """Delete a credential."""
        result = await sync_delete_credential(key)

        # Handle cache invalidation for RAG settings
        if result:
            if self._rag_settings_cache is not None and key in self._rag_settings_cache:
                self._rag_settings_cache = None
                self._rag_cache_timestamp = None
                logger.debug(f"Invalidated RAG settings cache due to deletion of {key}")

                # Invalidate provider service cache
                try:
                    from .llm_provider_service import clear_provider_cache
                    clear_provider_cache()
                    logger.debug("Also cleared LLM provider service cache")
                except Exception as e:
                    logger.warning(f"Failed to clear provider service cache: {e}")

                # Invalidate LLM provider service cache
                try:
                    from . import llm_provider_service
                    cache_keys_to_clear = ["provider_config_llm", "provider_config_embedding", "rag_strategy_settings"]
                    for cache_key in cache_keys_to_clear:
                        if cache_key in llm_provider_service._settings_cache:
                            del llm_provider_service._settings_cache[cache_key]
                            logger.debug(f"Invalidated LLM provider service cache key: {cache_key}")
                except ImportError:
                    logger.warning("Could not import llm_provider_service to invalidate cache")
                except Exception as e:
                    logger.error(f"Error invalidating LLM provider service cache: {e}")

        return result

    async def get_credentials_by_category(self, category: str) -> dict[str, Any]:
        """Get all credentials for a specific category."""
        # Special caching for rag_strategy category
        if category == "rag_strategy":
            current_time = time.time()

            if (
                self._rag_settings_cache is not None
                and self._rag_cache_timestamp is not None
                and current_time - self._rag_cache_timestamp < self._rag_cache_ttl
            ):
                logger.debug("Using cached RAG settings")
                return self._rag_settings_cache

        result = await sync_get_credentials_by_category(category)

        # Cache rag_strategy results
        if category == "rag_strategy":
            self._rag_settings_cache = result
            self._rag_cache_timestamp = time.time()
            logger.debug(f"Cached RAG settings with {len(result)} items")

        return result

    async def list_all_credentials(self) -> list[CredentialItem]:
        """Get all credentials as a list of CredentialItem objects."""
        return await sync_list_all_credentials()

    # Provider Management Methods

    async def get_active_provider(self, service_type: str = "llm") -> dict[str, Any]:
        """
        Get currently active provider configuration.

        Args:
            service_type: Either 'llm' or 'embedding'

        Returns:
            Dict with provider, api_key, base_url, and models
        """
        try:
            # Get RAG strategy settings (where UI saves provider selection)
            rag_settings = await self.get_credentials_by_category("rag_strategy")

            # Get selected provider based on service type
            if service_type == "embedding":
                # First check for explicit EMBEDDING_PROVIDER setting (new split provider approach)
                explicit_embedding_provider = rag_settings.get("EMBEDDING_PROVIDER")

                # Validate that embedding provider actually supports embeddings
                embedding_capable_providers = {"openai", "google", "openrouter", "ollama"}

                if (explicit_embedding_provider and
                    explicit_embedding_provider != "" and
                    explicit_embedding_provider in embedding_capable_providers):
                    # Use explicitly set embedding provider
                    provider = explicit_embedding_provider
                    logger.debug(f"Using explicit embedding provider: '{provider}'")
                else:
                    # Fall back to OpenAI as default embedding provider for backward compatibility
                    if explicit_embedding_provider and explicit_embedding_provider not in embedding_capable_providers:
                        logger.warning(f"Invalid embedding provider '{explicit_embedding_provider}' doesn't support embeddings, defaulting to OpenAI")
                    provider = "openai"
                    logger.debug(f"No explicit embedding provider set, defaulting to OpenAI for backward compatibility")
            else:
                provider = rag_settings.get("LLM_PROVIDER", "openai")
                # Ensure provider is a valid string, not a boolean or other type
                if not isinstance(provider, str) or provider.lower() in ("true", "false", "none", "null"):
                    provider = "openai"

            # Get API key for this provider
            api_key = await self._get_provider_api_key(provider)

            # Get base URL if needed
            base_url = self._get_provider_base_url(provider, rag_settings)

            # Get models with provider-specific fallback logic
            chat_model = rag_settings.get("MODEL_CHOICE", "")

            # If MODEL_CHOICE is empty, try provider-specific model settings
            if not chat_model and provider == "ollama":
                chat_model = rag_settings.get("OLLAMA_CHAT_MODEL", "")
                if chat_model:
                    logger.debug(f"Using OLLAMA_CHAT_MODEL: {chat_model}")

            embedding_model = rag_settings.get("EMBEDDING_MODEL", "")

            return {
                "provider": provider,
                "api_key": api_key,
                "base_url": base_url,
                "chat_model": chat_model,
                "embedding_model": embedding_model,
            }

        except Exception as e:
            logger.error(f"Error getting active provider for {service_type}: {e}")
            # Fallback to environment variable
            provider = os.getenv("LLM_PROVIDER", "openai")
            return {
                "provider": provider,
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": None,
                "chat_model": "",
                "embedding_model": "",
            }

    async def _get_provider_api_key(self, provider: str) -> str | None:
        """Get API key for a specific provider."""
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "grok": "GROK_API_KEY",
            "ollama": None,  # No API key needed
        }

        key_name = key_mapping.get(provider)
        if key_name:
            return await self.get_credential(key_name)
        return "ollama" if provider == "ollama" else None

    def _get_provider_base_url(self, provider: str, rag_settings: dict) -> str | None:
        """Get base URL for provider."""
        if provider == "ollama":
            return rag_settings.get("LLM_BASE_URL", "http://host.docker.internal:11434/v1")
        elif provider == "google":
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        elif provider == "openrouter":
            return "https://openrouter.ai/api/v1"
        elif provider == "anthropic":
            return "https://api.anthropic.com/v1"
        elif provider == "grok":
            return "https://api.x.ai/v1"
        return None  # Use default for OpenAI

    async def set_active_provider(self, provider: str, service_type: str = "llm") -> bool:
        """Set active provider for a service type."""
        try:
            # For now, we'll update RAG strategy settings
            return await self.set_credential(
                "LLM_PROVIDER",
                provider,
                category="rag_strategy",
                description=f"Active {service_type} provider",
            )
        except Exception as e:
            logger.error(f"Error setting active provider {provider} for {service_type}: {e}")
            return False


# Global instance
credential_service = CredentialService()


async def get_credential(key: str, default: Any = None) -> Any:
    """Convenience function to get a credential."""
    return await credential_service.get_credential(key, default)


async def set_credential(
    key: str, value: str, is_encrypted: bool = False, category: str = None, description: str = None
) -> bool:
    """Convenience function to set a credential."""
    return await credential_service.set_credential(key, value, is_encrypted, category, description)


async def initialize_credentials() -> None:
    """Initialize credential service by loading all credentials and setting environment variables."""
    await credential_service.load_all_credentials()

    # Only set infrastructure/startup credentials as environment variables
    # RAG settings will be looked up on-demand from credential service
    infrastructure_credentials = [
        "OPENAI_API_KEY",  # Required for API client initialization
        "HOST",  # Server binding configuration
        "PORT",  # Server binding configuration
        "MCP_TRANSPORT",  # Server transport mode
        "LOGFIRE_ENABLED",  # Logging infrastructure setup
        "PROJECTS_ENABLED",  # Feature flag for module loading
    ]

    # LLM provider credentials (for sync client support)
    provider_credentials = [
        "GOOGLE_API_KEY",  # Google Gemini API key
        "LLM_PROVIDER",  # Selected provider
        "LLM_BASE_URL",  # Ollama base URL
        "EMBEDDING_MODEL",  # Custom embedding model
        "MODEL_CHOICE",  # Chat model for sync contexts
    ]

    # RAG settings that should NOT be set as env vars (will be looked up on demand):
    # - USE_CONTEXTUAL_EMBEDDINGS
    # - CONTEXTUAL_EMBEDDINGS_MAX_WORKERS
    # - USE_HYBRID_SEARCH
    # - USE_AGENTIC_RAG
    # - USE_RERANKING

    # Code extraction settings (loaded on demand, not set as env vars):
    # - MIN_CODE_BLOCK_LENGTH
    # - MAX_CODE_BLOCK_LENGTH
    # - ENABLE_COMPLETE_BLOCK_DETECTION
    # - ENABLE_LANGUAGE_SPECIFIC_PATTERNS
    # - ENABLE_PROSE_FILTERING
    # - MAX_PROSE_RATIO
    # - MIN_CODE_INDICATORS
    # - ENABLE_DIAGRAM_FILTERING
    # - ENABLE_CONTEXTUAL_LENGTH
    # - CODE_EXTRACTION_MAX_WORKERS
    # - CONTEXT_WINDOW_SIZE
    # - ENABLE_CODE_SUMMARIES

    # Set infrastructure credentials
    for key in infrastructure_credentials:
        try:
            value = await credential_service.get_credential(key, decrypt=True)
            if value:
                os.environ[key] = str(value)
                logger.info(f"Set environment variable: {key}")
        except Exception as e:
            logger.warning(f"Failed to set environment variable {key}: {e}")

    # Set provider credentials with proper environment variable names
    for key in provider_credentials:
        try:
            value = await credential_service.get_credential(key, decrypt=True)
            if value:
                # Map credential keys to environment variable names
                env_key = key.upper()  # Convert to uppercase for env vars
                os.environ[env_key] = str(value)
                logger.info(f"Set environment variable: {env_key}")
        except Exception:
            # This is expected for optional credentials
            logger.debug(f"Optional credential not set: {key}")

    logger.info("Credentials loaded and environment variables set")
