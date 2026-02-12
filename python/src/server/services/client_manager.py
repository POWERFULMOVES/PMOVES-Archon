"""
Client Manager Service

Manages database and API client connections.

IMPORTANT: Now returns sync_credential_service to bypass the /rest/v1/
path prefix issue with self-hosted PostgREST v12.
"""

import os
import re
import warnings

from ..config.logfire_config import search_logger
from .credential_service_sync import sync_credential_service


def get_supabase_client():
    """
    DEPRECATED: This function previously returned the old supabase client
    which has /rest/v1/ prefix issues.

    For database operations, use sync_credential_service instead.
    """
    warnings.warn(
        "get_supabase_client() is deprecated. Use sync_credential_service for database operations.",
        DeprecationWarning,
        stacklevel=2
    )

    # Return sync credential service which properly handles PostgREST v12
    return sync_credential_service


# Legacy: Keep old function name for backward compatibility but it now returns sync service
def create_supabase_client():
    """
    Legacy function - kept for backward compatibility.

    Returns sync_credential_service which uses httpx directly.
    """
    # Log deprecation notice once per session
    if not hasattr(create_supabase_client, "_warned"):
        warnings.warn(
            "create_supabase_client() is deprecated. Direct HTTP operations should use sync_credential_service methods.",
            DeprecationWarning,
            stacklevel=2
        )
        create_supabase_client._warned = True

    return sync_credential_service
