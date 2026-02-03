"""
Persona Service for Archon

This module provides persona management functionality, integrating with Supabase
for persona storage and Agent Zero for agent creation with persona-based behavior.

Service follows Archon's established patterns:
- Async service methods with proper error handling
- Supabase client integration
- Service discovery for Agent Zero URL
- Comprehensive logging via unified config
- Pydantic models for type safety
"""

from typing import Any

import asyncio
import httpx
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger
from ..config.service_discovery import get_agents_url
from ..utils import get_supabase_client

logger = get_logger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class Persona(BaseModel):
    """
    Persona model representing an AI agent persona.

    Attributes:
        id: Unique persona identifier
        name: Display name for the persona
        description: Human-readable description of persona characteristics
        system_prompt: Base system prompt defining core behavior
        behavior_weights: Dict of behavior modifiers (creativity, formality, etc.)
        is_active: Whether persona is available for use
        archon_enhancements: Optional Archon-specific prompt additions
        created_at: Timestamp when persona was created
        updated_at: Timestamp of last update
    """

    id: str
    name: str
    description: str
    system_prompt: str
    behavior_weights: dict[str, float] = Field(default_factory=dict)
    is_active: bool = True
    archon_enhancements: dict[str, str] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PersonaCreateRequest(BaseModel):
    """Request model for creating a new agent with persona."""

    persona_id: str = Field(..., description="ID of persona to use")
    form_name: str | None = Field(None, description="Optional Archon form for behavior overrides")
    overrides: dict[str, Any] | None = Field(None, description="Custom behavior weight overrides")
    agent_name: str | None = Field(None, description="Custom name for the agent (defaults to persona name)")


class AgentCreateResponse(BaseModel):
    """Response model from Agent Zero agent creation."""

    agent_id: str
    status: str
    message: str
    persona_id: str | None = None
    system_prompt: str | None = None


# ============================================================================
# Persona Service
# ============================================================================

class PersonaService:
    """
    Service for managing AI agent personas and creating persona-based agents.

    This service integrates with:
    - Supabase for persona storage and retrieval
    - Agent Zero's /api/persona/agent/create endpoint for agent instantiation
    - Archon's prompt templates for persona enhancement
    """

    def __init__(self, supabase_client=None):
        """
        Initialize the PersonaService.

        Args:
            supabase_client: Optional Supabase client instance. If not provided,
                           uses the global client from utils.
        """
        self.supabase_client = supabase_client or get_supabase_client()
        self.agent_zero_url = get_agents_url()
        self.timeout = httpx.Timeout(
            connect=5.0,
            read=30.0,
            write=10.0,
            pool=5.0,
        )

    async def get_persona(self, persona_id: str) -> tuple[bool, dict[str, Any]]:
        """
        Retrieve a specific persona by ID from Supabase.

        Args:
            persona_id: Unique identifier of the persona to retrieve

        Returns:
            Tuple of (success, result_dict) where result_dict contains:
            - persona: Persona object on success
            - error: Error message string on failure

        Example:
            success, result = await persona_service.get_persona("dev_assistant")
            if success:
                persona = result["persona"]
                print(f"Found persona: {persona.name}")
        """
        try:
            logger.info(f"Fetching persona: {persona_id}")

            # Run blocking Supabase call in thread pool to avoid blocking event loop
            response = await asyncio.to_thread(
                lambda: (
                    self.supabase_client.table("archon_personas")
                    .select("*")
                    .eq("id", persona_id)
                    .execute()
                )
            )

            if not response.data:
                logger.warning(f"Persona not found: {persona_id}")
                return False, {"error": f"Persona with ID '{persona_id}' not found"}

            persona_data = response.data[0]
            persona = Persona(**persona_data)

            logger.info(f"Successfully retrieved persona: {persona.name}")
            return True, {"persona": persona}

        except Exception as e:
            logger.error(f"Error fetching persona {persona_id}: {e}", exc_info=True)
            return False, {"error": f"Failed to retrieve persona: {str(e)}"}

    async def list_personas(self, active_only: bool = True) -> tuple[bool, dict[str, Any]]:
        """
        List all available personas from Supabase.

        Args:
            active_only: If True, only return personas where is_active=True.
                        If False, return all personas including inactive ones.

        Returns:
            Tuple of (success, result_dict) where result_dict contains:
            - personas: List of Persona objects
            - total_count: Total number of personas returned
            - error: Error message string on failure

        Example:
            success, result = await persona_service.list_personas(active_only=True)
            if success:
                for persona in result["personas"]:
                    print(f"{persona.name}: {persona.description}")
        """
        try:
            logger.info(f"Listing personas (active_only={active_only})")

            # Build query function to run in thread pool
            def build_and_execute_query():
                query = self.supabase_client.table("archon_personas").select("*")
                if active_only:
                    query = query.eq("is_active", True)
                return query.order("name").execute()

            # Run blocking Supabase call in thread pool to avoid blocking event loop
            response = await asyncio.to_thread(build_and_execute_query)

            personas = [Persona(**p) for p in response.data]

            logger.info(f"Retrieved {len(personas)} personas")
            return True, {
                "personas": personas,
                "total_count": len(personas)
            }

        except Exception as e:
            logger.error(f"Error listing personas: {e}", exc_info=True)
            return False, {"error": f"Failed to list personas: {str(e)}"}

    async def create_agent_with_persona(
        self,
        persona_id: str,
        form_name: str | None = None,
        overrides: dict[str, Any] | None = None,
        agent_name: str | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        Create a new agent in Agent Zero using the specified persona.

        This method:
        1. Fetches the persona from Supabase
        2. Enhances the system prompt with Archon-specific additions
        3. Applies form-based behavior weight overrides if specified
        4. Calls Agent Zero's /api/persona/agent/create endpoint

        Args:
            persona_id: ID of persona to use for agent creation
            form_name: Optional Archon form name for behavior overrides
            overrides: Optional dict of behavior weight overrides (e.g., {"creativity": 0.8})
            agent_name: Optional custom name for the agent (defaults to persona name)

        Returns:
            Tuple of (success, result_dict) where result_dict contains:
            - agent_id: ID of created agent (on success)
            - status: Agent status from Agent Zero
            - message: Status message
            - persona_id: ID of persona used
            - system_prompt: Enhanced system prompt applied to agent
            - error: Error message string on failure

        Example:
            success, result = await persona_service.create_agent_with_persona(
                persona_id="code_reviewer",
                form_name="strict_review",
                overrides={"creativity": 0.3, "formality": 0.9}
            )
            if success:
                print(f"Agent created: {result['agent_id']}")
        """
        try:
            # Step 1: Fetch persona from Supabase
            persona_success, persona_result = await self.get_persona(persona_id)
            if not persona_success:
                return False, {"error": f"Failed to fetch persona: {persona_result.get('error')}"}

            persona: Persona = persona_result["persona"]

            # Step 2: Build enhanced system prompt
            system_prompt = await self.build_system_prompt(persona, form_name)

            # Step 3: Apply behavior weight overrides
            behavior_weights = persona.behavior_weights.copy() if persona.behavior_weights else {}
            if overrides:
                behavior_weights.update(overrides)

            # Step 4: Prepare agent creation request
            request_data = {
                "name": agent_name or persona.name,
                "system_prompt": system_prompt,
                "behavior_weights": behavior_weights,
                "persona_id": persona_id,
                "metadata": {
                    "form_name": form_name,
                    "archon_enhanced": True
                }
            }

            logger.info(f"Creating agent with persona '{persona.name}' at Agent Zero")

            # Step 5: Call Agent Zero API
            endpoint = f"{self.agent_zero_url}/api/persona/agent/create"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                agent_response = response.json()

            logger.info(f"Agent created successfully: {agent_response.get('agent_id')}")

            return True, {
                "agent_id": agent_response.get("agent_id"),
                "status": agent_response.get("status", "created"),
                "message": agent_response.get("message", "Agent created successfully"),
                "persona_id": persona_id,
                "system_prompt": system_prompt
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating agent: {e.response.status_code} - {e.response.text}")
            return False, {
                "error": f"Agent Zero returned error: {e.response.status_code}",
                "details": e.response.text
            }
        except httpx.TimeoutException:
            logger.error("Timeout creating agent in Agent Zero")
            return False, {"error": "Request to Agent Zero timed out"}
        except Exception as e:
            logger.error(f"Error creating agent with persona: {e}", exc_info=True)
            return False, {"error": f"Failed to create agent: {str(e)}"}

    async def build_system_prompt(self, persona: Persona, form_name: str | None = None) -> str:
        """
        Build an enhanced system prompt from persona and optional Archon form.

        This method combines:
        1. Base persona system prompt
        2. Archon-specific prompt enhancements (if form_name provided)
        3. Behavior-based prompt adjustments

        Args:
            persona: Persona object containing base system prompt
            form_name: Optional Archon form name for additional enhancements

        Returns:
            Enhanced system prompt string

        Example:
            prompt = await persona_service.build_system_prompt(dev_persona, "code_review")
            # Returns: "You are an expert developer... [base prompt]
            #          ### Archon Code Review Mode
            #          Focus on security, performance... [enhancements]"
        """
        try:
            # Start with base persona prompt
            prompt_parts = [persona.system_prompt]

            # Add Archon-specific enhancements if form provided
            if form_name:
                archon_additions = await self.get_archon_prompt_enhancements(form_name)
                if archon_additions:
                    prompt_parts.append(f"\n### Archon Enhancements ({form_name})")
                    prompt_parts.append(archon_additions)

            # Add behavior-based prompt adjustments
            if persona.behavior_weights:
                adjustments = self._build_behavior_adjustments(persona.behavior_weights)
                if adjustments:
                    prompt_parts.append("\n### Behavioral Guidelines")
                    prompt_parts.append(adjustments)

            # Combine all parts
            enhanced_prompt = "\n\n".join(prompt_parts)

            logger.debug(f"Built enhanced system prompt for persona '{persona.name}' "
                        f"(form: {form_name or 'None'})")
            return enhanced_prompt

        except Exception as e:
            logger.error(f"Error building system prompt: {e}", exc_info=True)
            # Fallback to base prompt if enhancement fails
            return persona.system_prompt

    async def get_archon_prompt_enhancements(self, form_name: str) -> str | None:
        """
        Retrieve Archon-specific prompt enhancements for a given form.

        This method looks up form-specific prompt additions from the archon_prompts
        table, allowing Archon to layer domain-specific behavior on top of base personas.

        Args:
            form_name: Name of the Archon form to retrieve enhancements for

        Returns:
            String of prompt enhancements or None if not found

        Example:
            enhancements = await persona_service.get_archon_prompt_enhancements("code_review")
            # Returns: "Focus on: security vulnerabilities, performance issues,
            #          code maintainability, and adherence to project standards."
        """
        try:
            if not form_name:
                return None

            # Query archon_prompts table for form enhancements
            # Run blocking Supabase call in thread pool to avoid blocking event loop
            response = await asyncio.to_thread(
                lambda: (
                    self.supabase_client.table("archon_prompts")
                    .select("prompt")
                    .eq("prompt_name", f"form_{form_name}_enhancements")
                    .execute()
                )
            )

            if response.data:
                enhancements = response.data[0].get("prompt", "")
                logger.debug(f"Retrieved Archon enhancements for form: {form_name}")
                return enhancements
            else:
                logger.debug(f"No Archon enhancements found for form: {form_name}")
                return None

        except Exception as e:
            logger.warning(f"Error retrieving Archon prompt enhancements for '{form_name}': {e}")
            return None

    def _build_behavior_adjustments(self, behavior_weights: dict[str, float]) -> str:
        """
        Build behavioral guideline text from behavior weight dict.

        Args:
            behavior_weights: Dict of behavior names to weight values (0.0-1.0)

        Returns:
            Formatted behavioral guideline string
        """
        adjustments = []

        for behavior, weight in behavior_weights.items():
            if weight >= 0.8:
                level = "very high"
            elif weight >= 0.6:
                level = "high"
            elif weight >= 0.4:
                level = "moderate"
            elif weight >= 0.2:
                level = "low"
            else:
                level = "very low"

            behavior_human = behavior.replace("_", " ").title()
            adjustments.append(f"- {behavior_human}: {level} priority")

        return "\n".join(adjustments) if adjustments else ""


# ============================================================================
# Global Service Instance
# ============================================================================

_persona_service = None


def get_persona_service() -> PersonaService:
    """
    Get or create the global PersonaService instance.

    Returns:
        Global PersonaService singleton instance
    """
    global _persona_service
    if _persona_service is None:
        _persona_service = PersonaService()
    return _persona_service


__all__ = [
    "PersonaService",
    "Persona",
    "PersonaCreateRequest",
    "AgentCreateResponse",
    "get_persona_service",
]
