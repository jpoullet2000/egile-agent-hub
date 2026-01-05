"""Plugin loader for Egile Agent Hub.

This module dynamically loads and configures agent plugins based on configuration.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin cannot be loaded."""
    pass


class PluginRegistry:
    """Registry of available agent plugins."""

    _plugins: dict[str, type] = {}
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize the plugin registry by importing available plugins."""
        if cls._initialized:
            return

        logger.info("Initializing plugin registry...")

        # Try to import ProspectFinder plugin
        try:
            from egile_agent_prospectfinder import ProspectFinderPlugin
            cls._plugins["prospectfinder"] = ProspectFinderPlugin
            logger.info("Registered ProspectFinderPlugin")
        except ImportError as e:
            logger.warning(f"ProspectFinderPlugin not available: {e}")

        # Try to import XTwitter plugin
        try:
            from egile_agent_x_twitter import XTwitterPlugin
            cls._plugins["xtwitter"] = XTwitterPlugin
            logger.info("Registered XTwitterPlugin")
        except ImportError as e:
            logger.warning(f"XTwitterPlugin not available: {e}")

        cls._initialized = True
        logger.info(f"Plugin registry initialized with {len(cls._plugins)} plugin(s)")

    @classmethod
    def get_plugin_class(cls, plugin_type: str) -> type:
        """
        Get plugin class by type.

        Args:
            plugin_type: Type of plugin ("prospectfinder", "xtwitter")

        Returns:
            Plugin class

        Raises:
            PluginLoadError: If plugin type is not registered
        """
        if not cls._initialized:
            cls.initialize()

        if plugin_type not in cls._plugins:
            available = ", ".join(cls._plugins.keys()) or "none"
            raise PluginLoadError(
                f"Plugin type '{plugin_type}' not found. Available: {available}"
            )

        return cls._plugins[plugin_type]

    @classmethod
    def create_plugin(cls, plugin_type: str, config: dict[str, Any]) -> Any:
        """
        Create a plugin instance with the given configuration.

        Args:
            plugin_type: Type of plugin to create
            config: Plugin configuration dictionary

        Returns:
            Configured plugin instance

        Raises:
            PluginLoadError: If plugin cannot be created
        """
        plugin_class = cls.get_plugin_class(plugin_type)

        # Extract plugin-specific configuration
        plugin_config = cls._get_plugin_config(plugin_type, config)

        try:
            logger.info(f"Creating {plugin_type} plugin with config: {plugin_config}")
            return plugin_class(**plugin_config)
        except Exception as e:
            raise PluginLoadError(
                f"Failed to create {plugin_type} plugin: {e}"
            )

    @classmethod
    def _get_plugin_config(cls, plugin_type: str, agent_config: dict[str, Any]) -> dict[str, Any]:
        """
        Extract plugin-specific configuration from agent config.

        Args:
            plugin_type: Type of plugin
            agent_config: Full agent configuration

        Returns:
            Plugin-specific configuration dictionary
        """
        # Common parameters
        plugin_config = {
            "mcp_transport": agent_config.get("mcp_transport", "stdio"),
            "mcp_command": agent_config.get("mcp_command"),
            "mcp_host": agent_config.get("mcp_host", os.getenv("MCP_HOST", "localhost")),
            "mcp_port": agent_config.get("mcp_port"),
            "timeout": agent_config.get("timeout", 120.0),
            "use_mcp": agent_config.get("use_mcp", False),  # Default to direct mode for Windows compatibility
        }

        # Plugin-specific defaults
        if plugin_type == "prospectfinder":
            if not plugin_config["mcp_command"]:
                plugin_config["mcp_command"] = "python -m egile_mcp_prospectfinder.server"
            if not plugin_config["mcp_port"]:
                plugin_config["mcp_port"] = int(os.getenv("PROSPECTFINDER_MCP_PORT", "8001"))

        elif plugin_type == "xtwitter":
            if not plugin_config["mcp_command"]:
                plugin_config["mcp_command"] = "python -m egile_mcp_x_post_creator.server"
            if not plugin_config["mcp_port"]:
                plugin_config["mcp_port"] = int(os.getenv("XTWITTER_MCP_PORT", "8002"))

        return plugin_config


def load_plugins_for_agents(agents_config: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Load plugins for all agents in the configuration.

    Args:
        agents_config: List of agent configuration dictionaries

    Returns:
        Dictionary mapping agent name to plugin instance

    Raises:
        PluginLoadError: If any plugin fails to load
    """
    PluginRegistry.initialize()
    
    plugins = {}
    for agent_config in agents_config:
        agent_name = agent_config["name"]
        plugin_type = agent_config.get("plugin_type")

        if not plugin_type:
            logger.info(f"Agent '{agent_name}' has no plugin_type, skipping plugin load")
            continue

        try:
            plugin = PluginRegistry.create_plugin(plugin_type, agent_config)
            plugins[agent_name] = plugin
            logger.info(f"Loaded {plugin_type} plugin for agent '{agent_name}'")
        except PluginLoadError as e:
            logger.error(f"Failed to load plugin for agent '{agent_name}': {e}")
            raise

    return plugins
