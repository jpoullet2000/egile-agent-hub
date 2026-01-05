"""Configuration loader for Egile Agent Hub.

This module loads and validates agent and team configurations from YAML files.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


class AgentHubConfig:
    """Container for agent hub configuration."""

    def __init__(
        self,
        agents: list[dict[str, Any]],
        teams: list[dict[str, Any]] | None = None,
    ):
        """
        Initialize agent hub configuration.

        Args:
            agents: List of agent configuration dictionaries
            teams: Optional list of team configuration dictionaries
        """
        self.agents = agents
        self.teams = teams or []
        self._validate()

    def _validate(self) -> None:
        """Validate the configuration."""
        if not self.agents and not self.teams:
            raise ConfigError("At least one agent or team must be defined")

        # Validate agents
        agent_names = set()
        for agent in self.agents:
            if "name" not in agent:
                raise ConfigError("All agents must have a 'name' field")
            
            name = agent["name"]
            if name in agent_names:
                raise ConfigError(f"Duplicate agent name: {name}")
            agent_names.add(name)

            # Validate plugin configuration
            if "plugin_type" in agent:
                plugin_type = agent["plugin_type"]
                if plugin_type not in ["prospectfinder", "xtwitter"]:
                    raise ConfigError(
                        f"Invalid plugin_type '{plugin_type}' for agent '{name}'. "
                        f"Must be 'prospectfinder' or 'xtwitter'"
                    )
                
                # For stdio transport, mcp_command is required instead of mcp_port
                transport = agent.get("mcp_transport", "stdio")
                if transport == "sse" and "mcp_port" not in agent:
                    raise ConfigError(
                        f"Agent '{name}' uses SSE transport but missing 'mcp_port'"
                    )
                elif transport == "stdio" and "mcp_command" not in agent:
                    # mcp_command is optional - has defaults in plugin_loader
                    pass

        # Validate teams
        team_names = set()
        for team in self.teams:
            if "name" not in team:
                raise ConfigError("All teams must have a 'name' field")
            
            name = team["name"]
            if name in team_names:
                raise ConfigError(f"Duplicate team name: {name}")
            team_names.add(name)

            if "members" not in team or not team["members"]:
                raise ConfigError(f"Team '{name}' must have at least one member")

            # Verify all team members exist as agents
            for member in team["members"]:
                if member not in agent_names:
                    raise ConfigError(
                        f"Team '{name}' references unknown agent: {member}"
                    )

    def get_agents_by_team(self, team_name: str) -> list[dict[str, Any]]:
        """
        Get all agents that belong to a specific team.

        Args:
            team_name: Name of the team

        Returns:
            List of agent configurations for the team
        """
        # Find team definition
        team = None
        for t in self.teams:
            if t["name"] == team_name:
                team = t
                break

        if not team:
            return []

        # Get member agents
        member_names = team["members"]
        return [agent for agent in self.agents if agent["name"] in member_names]

    def get_mcp_servers(self) -> dict[str, dict[str, Any]]:
        """
        Get all MCP server configurations.

        Returns:
            Dictionary mapping agent name to MCP server config
        """
        mcp_servers = {}
        for agent in self.agents:
            if "plugin_type" in agent and "mcp_port" in agent:
                mcp_servers[agent["name"]] = {
                    "plugin_type": agent["plugin_type"],
                    "port": agent["mcp_port"],
                    "host": agent.get("mcp_host", "localhost"),
                }
        return mcp_servers


def load_config(config_file: str | Path | None = None) -> AgentHubConfig:
    """
    Load agent hub configuration from YAML file.

    Args:
        config_file: Path to YAML configuration file.
                    If None, tries AGENTS_CONFIG_FILE env var, then agents.yaml

    Returns:
        Validated AgentHubConfig instance

    Raises:
        ConfigError: If configuration is invalid or file not found
    """
    # Determine config file path
    if config_file is None:
        config_file = os.getenv("AGENTS_CONFIG_FILE", "agents.yaml")
    
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise ConfigError(
            f"Configuration file not found: {config_path}\n"
            f"Create {config_path} based on agents.yaml.example"
        )

    # Load YAML
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load {config_path}: {e}")

    if not data:
        raise ConfigError(f"Configuration file is empty: {config_path}")

    # Extract agents and teams
    agents = data.get("agents", [])
    teams = data.get("teams", [])

    if not isinstance(agents, list):
        raise ConfigError("'agents' must be a list")
    if not isinstance(teams, list):
        raise ConfigError("'teams' must be a list")

    logger.info(f"Loaded configuration from {config_path}")
    logger.info(f"Found {len(agents)} agent(s) and {len(teams)} team(s)")

    return AgentHubConfig(agents=agents, teams=teams)


def get_default_model_config() -> dict[str, str]:
    """
    Get default model configuration from environment variables.

    Returns:
        Dictionary with 'provider' and 'model' keys

    Raises:
        ConfigError: If no model API key is configured
    """
    # Priority: Mistral > XAI > OpenAI
    if os.getenv("MISTRAL_API_KEY"):
        return {
            "provider": "mistral",
            "model": os.getenv("MISTRAL_MODEL", "mistral-large-2512"),
        }
    elif os.getenv("XAI_API_KEY"):
        return {
            "provider": "xai",
            "model": os.getenv("XAI_MODEL", "grok-4-1-fast-reasoning"),
        }
    elif os.getenv("OPENAI_API_KEY"):
        return {
            "provider": "openai",
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        }
    else:
        raise ConfigError(
            "No AI model API key configured. "
            "Set one of: MISTRAL_API_KEY, XAI_API_KEY, or OPENAI_API_KEY"
        )
