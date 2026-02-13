"""
Persona API endpoints for Archon

This module provides HTTP endpoints for persona management and agent creation,
integrating with Agent Zero's persona-based agent system.

Key features:
- List available personas with filtering
- Retrieve detailed persona information
- Create agents with persona-based behavior
- Reference data for thread types and persona metadata
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger
from ..services.persona_service import (
    AgentCreateResponse,
    Persona,
    get_persona_service,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/personas", tags=["personas"])


# ============================================================================
# Request/Response Models
# ============================================================================

class PersonaListResponse(BaseModel):
    """Response model for persona list endpoint."""

    personas: list[Persona]
    total_count: int


class PersonaDetailResponse(BaseModel):
    """Response model for persona detail endpoint."""

    persona: Persona


class AgentCreateRequest(BaseModel):
    """Request model for creating an agent from a persona."""

    persona_id: str = Field(..., description="ID of persona to use for agent creation")
    form_name: str | None = Field(None, description="Optional Archon form for behavior overrides")
    overrides: dict[str, Any] | None = Field(None, description="Custom behavior weight overrides")
    agent_name: str | None = Field(None, description="Custom name for the agent (defaults to persona name)")


class ThreadTypeResponse(BaseModel):
    """Response model for thread types reference data."""

    thread_types: list[dict[str, Any]]
    description: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=PersonaListResponse)
async def list_personas(
    active_only: bool = Query(
        True,
        description="If True, only return active personas. If False, return all personas including inactive ones."
    )
):
    """
    List all available personas from Supabase.

    Returns a list of personas with their system prompts, behavior weights,
    and Archon-specific enhancements. Personas define AI agent personalities
    and behavioral patterns.

    Args:
        active_only: Filter to only return personas where is_active=True.
                    Defaults to True. Set to False to include inactive personas.

    Returns:
        PersonaListResponse containing:
        - personas: List of Persona objects
        - total_count: Total number of personas returned

    Raises:
        HTTPException 500: If persona retrieval fails

    Example:
        GET /api/personas?active_only=true

        Response:
        {
            "personas": [
                {
                    "id": "code_reviewer",
                    "name": "Code Review Expert",
                    "description": "Expert code reviewer with focus on security...",
                    "system_prompt": "You are an expert code reviewer...",
                    "behavior_weights": {"creativity": 0.3, "formality": 0.9},
                    "is_active": true,
                    "archon_enhancements": {...}
                }
            ],
            "total_count": 1
        }
    """
    try:
        logger.info(f"Listing personas with active_only={active_only}")

        persona_service = get_persona_service()
        success, result = await persona_service.list_personas(active_only=active_only)

        if not success:
            error_msg = result.get("error", "Failed to list personas")
            logger.error(f"Failed to list personas: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        logger.info(f"Successfully retrieved {result['total_count']} personas")
        return PersonaListResponse(
            personas=result["personas"],
            total_count=result["total_count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing personas: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while listing personas: {str(e)}"
        )


@router.get("/thread-types", response_model=ThreadTypeResponse)
async def get_thread_types():
    """
    Get reference data for available thread types.

    Thread types define the execution context and capabilities for agents.
    This endpoint provides metadata about supported thread types for
    agent creation and configuration.

    Returns:
        ThreadTypeResponse containing:
        - thread_types: List of thread type definitions
        - description: Human-readable description of thread types

    Example:
        GET /api/personas/thread-types

        Response:
        {
            "thread_types": [
                {
                    "id": "standard",
                    "name": "Standard Thread",
                    "description": "Default agent execution context",
                    "capabilities": ["chat", "tools", "memory"]
                },
                {
                    "id": "research",
                    "name": "Research Thread",
                    "description": "Enhanced context for research tasks",
                    "capabilities": ["chat", "tools", "memory", "web_search", "knowledge_base"]
                }
            ],
            "description": "Available thread types for agent creation"
        }
    """
    try:
        logger.info("Fetching thread types reference data")

        # TODO: Integrate with Agent Zero's thread type API when available
        # For now, return static reference data
        thread_types = [
            {
                "id": "standard",
                "name": "Standard Thread",
                "description": "Default agent execution context with core capabilities",
                "capabilities": ["chat", "tools", "memory"],
                "max_context_tokens": 8192,
                "supported_models": ["gpt-4", "claude-3", "llama-3"]
            },
            {
                "id": "research",
                "name": "Research Thread",
                "description": "Enhanced context for research and knowledge-intensive tasks",
                "capabilities": ["chat", "tools", "memory", "web_search", "knowledge_base", "citation"],
                "max_context_tokens": 16384,
                "supported_models": ["gpt-4", "claude-3"]
            },
            {
                "id": "creative",
                "name": "Creative Thread",
                "description": "Optimized for creative writing and content generation",
                "capabilities": ["chat", "tools", "memory", "creative_mode"],
                "max_context_tokens": 4096,
                "supported_models": ["gpt-4", "claude-3", "llama-3"]
            }
        ]

        logger.info(f"Returning {len(thread_types)} thread types")
        return ThreadTypeResponse(
            thread_types=thread_types,
            description="Available thread types for agent creation in Agent Zero"
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching thread types: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while fetching thread types: {str(e)}"
        )



@router.get("/{persona_id}", response_model=PersonaDetailResponse)
async def get_persona(persona_id: str):
    """
    Retrieve detailed information about a specific persona.

    Returns the complete persona definition including system prompt,
    behavior weights, Archon enhancements, and metadata.

    Args:
        persona_id: Unique identifier of the persona to retrieve

    Returns:
        PersonaDetailResponse containing the requested Persona object

    Raises:
        HTTPException 404: If persona with specified ID not found
        HTTPException 500: If persona retrieval fails

    Example:
        GET /api/personas/code_reviewer

        Response:
        {
            "persona": {
                "id": "code_reviewer",
                "name": "Code Review Expert",
                "description": "Expert code reviewer...",
                "system_prompt": "You are an expert code reviewer...",
                "behavior_weights": {"creativity": 0.3, "formality": 0.9},
                "is_active": true,
                "archon_enhancements": {...},
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    """
    try:
        logger.info(f"Fetching persona: {persona_id}")

        persona_service = get_persona_service()
        success, result = await persona_service.get_persona(persona_id)

        if not success:
            error_msg = result.get("error", "Persona not found")
            logger.warning(f"Failed to get persona {persona_id}: {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)

        logger.info(f"Successfully retrieved persona: {result['persona'].name}")
        return PersonaDetailResponse(persona=result["persona"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting persona {persona_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while retrieving persona: {str(e)}"
        )


@router.post("/agent/create", response_model=AgentCreateResponse)
async def create_agent_from_persona(request: AgentCreateRequest):
    """
    Create a new agent in Agent Zero using the specified persona.

    This endpoint:
    1. Fetches the persona from Supabase
    2. Enhances the system prompt with Archon-specific additions
    3. Applies form-based behavior weight overrides if specified
    4. Creates a new agent via Agent Zero's /api/persona/agent/create endpoint

    The created agent will exhibit behavior defined by the persona's system
    prompt and behavior weights, with optional Archon form enhancements.

    Args:
        request: AgentCreateRequest containing:
            - persona_id: ID of persona to use (required)
            - form_name: Optional Archon form for behavior overrides
            - overrides: Optional dict of behavior weight overrides
            - agent_name: Optional custom name for the agent

    Returns:
        AgentCreateResponse containing:
        - agent_id: ID of the created agent
        - status: Agent status from Agent Zero
        - message: Status message
        - persona_id: ID of persona used
        - system_prompt: Enhanced system prompt applied to agent

    Raises:
        HTTPException 404: If specified persona not found
        HTTPException 500: If agent creation fails

    Example:
        POST /api/personas/agent/create

        Body:
        {
            "persona_id": "code_reviewer",
            "form_name": "strict_review",
            "overrides": {"creativity": 0.3, "formality": 0.9},
            "agent_name": "My Code Reviewer"
        }

        Response:
        {
            "agent_id": "agent_abc123",
            "status": "created",
            "message": "Agent created successfully",
            "persona_id": "code_reviewer",
            "system_prompt": "You are an expert code reviewer..."
        }
    """
    try:
        logger.info(
            f"Creating agent from persona '{request.persona_id}' "
            f"(form: {request.form_name or 'None'}, agent_name: {request.agent_name or 'None'})"
        )

        persona_service = get_persona_service()
        success, result = await persona_service.create_agent_with_persona(
            persona_id=request.persona_id,
            form_name=request.form_name,
            overrides=request.overrides,
            agent_name=request.agent_name
        )

        if not success:
            error_msg = result.get("error", "Failed to create agent")

            # Detect persona-not-found errors and return 404 instead of 500
            if "not found" in error_msg.lower() or "Persona with ID" in error_msg:
                logger.warning(f"Persona not found: {request.persona_id} - {error_msg}")
                raise HTTPException(status_code=404, detail=error_msg)

            logger.error(f"Failed to create agent from persona {request.persona_id}: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        logger.info(f"Successfully created agent {result['agent_id']} from persona {request.persona_id}")
        return AgentCreateResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error creating agent from persona {request.persona_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while creating agent: {str(e)}"
        )
