"""
Claude Code MCP Adapter for Archon

Integrates Claude Code CLI slash commands into Archon's prompt/form system
via Agent Zero's MCP interface.

This adapter enables Archon to:
- Execute TAC slash commands through Agent Zero
- Route knowledge queries to appropriate services
- Access PMOVES infrastructure programmatically
"""

import httpx
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result from a Claude Code command execution."""
    success: bool
    output: Any
    stderr: Optional[str] = None
    error: Optional[str] = None
    command: Optional[str] = None


class ClaudeCodeMCPAdapter:
    """MCP adapter exposing Claude Code commands to Archon via Agent Zero."""

    def __init__(
        self,
        agent_zero_url: str = "http://agent-zero:8080",
        timeout: float = 30.0
    ):
        self.agent_zero_url = agent_zero_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy initialization of async client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def execute_slash_command(
        self,
        command: str,
        prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> CommandResult:
        """
        Execute a Claude Code slash command via Agent Zero's MCP interface.

        Args:
            command: Slash command (e.g., "/search:hirag", "/health:check-all")
            prompt: Optional prompt/query for the command
            context: Additional context for execution

        Returns:
            CommandResult with output or error
        """
        payload = {
            "instrument": "claude_code",
            "action": "execute_command",
            "params": {
                "command": command,
                "prompt": prompt,
                "context": context or {}
            }
        }

        try:
            response = await self.client.post(
                f"{self.agent_zero_url}/mcp/execute",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return CommandResult(
                success=data.get("success", False),
                output=data.get("output") or data.get("stdout"),
                stderr=data.get("stderr"),
                command=data.get("command")
            )
        except httpx.HTTPStatusError as e:
            return CommandResult(
                success=False,
                output=None,
                error=f"HTTP error: {e.response.status_code}"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def list_available_commands(self) -> List[str]:
        """List all available Claude Code slash commands."""
        payload = {
            "instrument": "claude_code",
            "action": "list_commands"
        }

        try:
            response = await self.client.post(
                f"{self.agent_zero_url}/mcp/execute",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("commands", [])
        except Exception:
            return []

    async def get_command_help(self, command: str) -> Optional[str]:
        """Get help text for a specific command."""
        payload = {
            "instrument": "claude_code",
            "action": "get_command_help",
            "params": {"command": command}
        }

        try:
            response = await self.client.post(
                f"{self.agent_zero_url}/mcp/execute",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("help")
        except Exception:
            return None

    # Convenience methods for common operations

    async def search_knowledge(self, query: str) -> CommandResult:
        """Search Hi-RAG v2 knowledge base."""
        return await self.execute_slash_command("/search:hirag", query)

    async def deep_research(self, topic: str) -> CommandResult:
        """Initiate DeepResearch for complex queries."""
        return await self.execute_slash_command("/search:deepresearch", topic)

    async def check_health(self) -> CommandResult:
        """Check health of all PMOVES services."""
        return await self.execute_slash_command("/health:check-all")

    async def get_metrics(self, promql: str = "up") -> CommandResult:
        """Query Prometheus metrics."""
        return await self.execute_slash_command("/health:metrics", promql)

    async def agent_status(self) -> CommandResult:
        """Check Agent Zero health status."""
        return await self.execute_slash_command("/agents:status")

    async def mcp_query(self, query: str) -> CommandResult:
        """Query Agent Zero's MCP API directly."""
        return await self.execute_slash_command("/agents:mcp-query", query)


# Archon MCP tool registration
# These definitions tell Archon how to expose Claude Code commands as MCP tools

ARCHON_MCP_TOOLS = [
    {
        "name": "claude_code_search",
        "description": "Search PMOVES knowledge base using Claude Code CLI",
        "adapter": "ClaudeCodeMCPAdapter",
        "method": "execute_slash_command",
        "params": {
            "command": {
                "type": "string",
                "enum": ["/search:hirag", "/search:supaserch", "/search:deepresearch"],
                "description": "Search command to execute"
            },
            "prompt": {
                "type": "string",
                "description": "Search query"
            }
        }
    },
    {
        "name": "claude_code_health",
        "description": "Check PMOVES service health using Claude Code CLI",
        "adapter": "ClaudeCodeMCPAdapter",
        "method": "execute_slash_command",
        "params": {
            "command": {
                "type": "string",
                "enum": ["/health:check-all", "/health:metrics"],
                "description": "Health command to execute"
            }
        }
    },
    {
        "name": "claude_code_agents",
        "description": "Interact with Agent Zero using Claude Code CLI",
        "adapter": "ClaudeCodeMCPAdapter",
        "method": "execute_slash_command",
        "params": {
            "command": {
                "type": "string",
                "enum": ["/agents:status", "/agents:mcp-query"],
                "description": "Agent command to execute"
            },
            "prompt": {
                "type": "string",
                "description": "Query for MCP operations (optional)",
                "optional": True
            }
        }
    },
    {
        "name": "claude_code_deploy",
        "description": "Execute deployment operations using Claude Code CLI",
        "adapter": "ClaudeCodeMCPAdapter",
        "method": "execute_slash_command",
        "params": {
            "command": {
                "type": "string",
                "enum": ["/deploy:smoke-test", "/deploy:services", "/deploy:up"],
                "description": "Deploy command to execute"
            }
        }
    },
    {
        "name": "claude_code_botz",
        "description": "Manage PMOVES environment using BoTZ commands",
        "adapter": "ClaudeCodeMCPAdapter",
        "method": "execute_slash_command",
        "params": {
            "command": {
                "type": "string",
                "enum": ["/botz:init", "/botz:profile", "/botz:mcp", "/botz:secrets"],
                "description": "BoTZ command to execute"
            },
            "prompt": {
                "type": "string",
                "description": "Arguments for the command",
                "optional": True
            }
        }
    }
]


# Factory function for Archon integration
def create_adapter(config: Optional[Dict[str, Any]] = None) -> ClaudeCodeMCPAdapter:
    """Create a configured ClaudeCodeMCPAdapter instance."""
    config = config or {}
    return ClaudeCodeMCPAdapter(
        agent_zero_url=config.get("agent_zero_url", "http://agent-zero:8080"),
        timeout=config.get("timeout", 30.0)
    )
