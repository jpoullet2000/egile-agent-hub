"""Plugin loader for Egile Agent Hub.

This module dynamically loads and configures agent plugins based on configuration.
Automatically discovers installed egile plugins and loads only those that are needed.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin cannot be loaded."""
    pass


class PluginRegistry:
    """Registry of available agent plugins with dynamic discovery."""

    _available_plugins: dict[str, str] = {}  # Maps plugin_type -> package_name
    _loaded_plugins: dict[str, type] = {}  # Maps plugin_type -> plugin class
    _discovered: bool = False

    @classmethod
    def discover_plugins(cls) -> None:
        """Discover all installed egile agent plugins."""
        if cls._discovered:
            return

        logger.info("Discovering installed egile plugins...")
        
        # Packages to exclude (not actual agent plugins)
        excluded_packages = {"egile-agent-core", "egile_agent_core", "egile-agent-hub", "egile_agent_hub"}
        
        # Find all installed packages that match egile agent patterns
        for dist in importlib.metadata.distributions():
            package_name = dist.metadata.get("Name", "")
            
            # Check if it's an egile agent plugin package
            if package_name.startswith("egile-agent-") or package_name.startswith("egile_agent_"):
                # Skip non-plugin packages
                if package_name in excluded_packages:
                    continue
                
                # Convert package name to plugin type (e.g., "egile-agent-prospectfinder" -> "prospectfinder")
                plugin_type = package_name.replace("egile-agent-", "").replace("egile_agent_", "")
                
                # Keep hyphens for consistency with YAML naming conventions (e.g., "x-twitter")
                # No normalization needed - preserve the original format
                
                # Convert to import name (hyphens to underscores)
                import_name = package_name.replace("-", "_")
                
                cls._available_plugins[plugin_type] = import_name
                logger.info(f"Discovered plugin: {plugin_type} (package: {package_name})")
        
        cls._discovered = True
        logger.info(f"Plugin discovery complete. Found {len(cls._available_plugins)} plugin(s)")

    @classmethod
    def list_available_plugins(cls) -> list[str]:
        """
        List all available plugin types that can be loaded.
        
        Returns:
            List of plugin type names
        """
        if not cls._discovered:
            cls.discover_plugins()
        
        return list(cls._available_plugins.keys())

    @classmethod
    def get_mcp_server_module(cls, plugin_type: str) -> str | None:
        """
        Get the MCP server module name for a plugin type.
        
        Args:
            plugin_type: Type of plugin
            
        Returns:
            MCP server module path or None if not available
        """
        try:
            plugin_class = cls._load_plugin_class(plugin_type)
            # Create a temporary instance to check for mcp_server_module property
            # Most plugins have __init__ that can be called without args or with defaults
            if hasattr(plugin_class, 'mcp_server_module'):
                # Try to access as class property first
                try:
                    module = plugin_class.mcp_server_module
                    if module and not callable(module):
                        return module
                except (AttributeError, TypeError):
                    pass
                
                # Try creating instance with default args
                try:
                    temp_instance = plugin_class()
                    return temp_instance.mcp_server_module
                except (TypeError, AttributeError):
                    pass
            
            return None
        except Exception as e:
            logger.debug(f"Could not get MCP server module for {plugin_type}: {e}")
            return None

    @classmethod
    def _load_plugin_class(cls, plugin_type: str) -> type:
        """
        Dynamically load a plugin class by type.
        
        Args:
            plugin_type: Type of plugin to load
            
        Returns:
            Plugin class
            
        Raises:
            PluginLoadError: If plugin cannot be loaded
        """
        if plugin_type in cls._loaded_plugins:
            return cls._loaded_plugins[plugin_type]
        
        if not cls._discovered:
            cls.discover_plugins()
        
        if plugin_type not in cls._available_plugins:
            available = ", ".join(cls._available_plugins.keys()) or "none"
            raise PluginLoadError(
                f"Plugin type '{plugin_type}' not found. Available plugins: {available}"
            )
        
        package_name = cls._available_plugins[plugin_type]
        
        try:
            # Try to import the plugin class
            # Convention: plugin classes should be importable from the package root
            # and named like ProspectFinderPlugin, XTwitterPlugin, etc.
            module = importlib.import_module(package_name)
            
            # Try common naming conventions for plugin classes
            # Handle both hyphenated (x-twitter) and single-word (prospectfinder) plugin types
            
            # Normalize to underscore-separated for consistent word splitting
            normalized = plugin_type.replace("-", "_")
            
            # Try to get the class name from __all__ first
            plugin_class = None
            if hasattr(module, "__all__"):
                for name in module.__all__:
                    if name.endswith("Plugin"):
                        plugin_class = getattr(module, name)
                        break
            
            # If not found in __all__, try common naming patterns
            if plugin_class is None:
                possible_class_names = [
                    # Standard CamelCase: ProspectFinderPlugin, XTwitterPlugin
                    "".join(word.capitalize() for word in normalized.split("_")) + "Plugin",
                ]
                
                # For hyphenated types, also try without separator: XtwitterPlugin
                if "-" in plugin_type:
                    possible_class_names.append(
                        plugin_type.replace("-", "").capitalize() + "Plugin"
                    )
                
                # Add generic fallback
                possible_class_names.append("Plugin")
                
                for class_name in possible_class_names:
                    if hasattr(module, class_name):
                        plugin_class = getattr(module, class_name)
                        break
            
            if plugin_class is None:
                raise PluginLoadError(
                    f"Could not find plugin class in {package_name}. "
                    f"Tried: {', '.join(possible_class_names)}"
                )
            
            cls._loaded_plugins[plugin_type] = plugin_class
            logger.info(f"Loaded plugin class {plugin_class.__name__} from {package_name}")
            return plugin_class
            
        except ImportError as e:
            raise PluginLoadError(
                f"Failed to import plugin package '{package_name}': {e}"
            )
        except Exception as e:
            raise PluginLoadError(
                f"Failed to load plugin class for '{plugin_type}': {e}"
            )

    @classmethod
    def get_plugin_class(cls, plugin_type: str) -> type:
        """
        Get plugin class by type, loading it dynamically if needed.

        Args:
            plugin_type: Type of plugin (e.g., "prospectfinder", "xtwitter")

        Returns:
            Plugin class

        Raises:
            PluginLoadError: If plugin type is not found or cannot be loaded
        """
        return cls._load_plugin_class(plugin_type)

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

        elif plugin_type in ("xtwitter", "x-twitter", "x_twitter"):
            if not plugin_config["mcp_command"]:
                plugin_config["mcp_command"] = "python -m egile_mcp_x_post_creator.server"
            if not plugin_config["mcp_port"]:
                plugin_config["mcp_port"] = int(os.getenv("XTWITTER_MCP_PORT", "8002"))

        return plugin_config


def load_plugins_for_agents(agents_config: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Load plugins for all agents in the configuration.
    Only loads plugins that are actually referenced in the configuration.

    Args:
        agents_config: List of agent configuration dictionaries

    Returns:
        Dictionary mapping agent name to plugin instance

    Raises:
        PluginLoadError: If any plugin fails to load
    """
    # Discover available plugins first (this is fast and only happens once)
    PluginRegistry.discover_plugins()
    available = PluginRegistry.list_available_plugins()
    logger.info(f"Available plugins: {', '.join(available) if available else 'none'}")
    
    plugins = {}
    for agent_config in agents_config:
        agent_name = agent_config["name"]
        plugin_type = agent_config.get("plugin_type")

        if not plugin_type:
            logger.info(f"Agent '{agent_name}' has no plugin_type, skipping plugin load")
            continue

        try:
            # Plugin class is loaded lazily only when needed
            plugin = PluginRegistry.create_plugin(plugin_type, agent_config)
            plugins[agent_name] = plugin
            logger.info(f"Loaded {plugin_type} plugin for agent '{agent_name}'")
        except PluginLoadError as e:
            logger.error(f"Failed to load plugin for agent '{agent_name}': {e}")
            raise

    return plugins


def print_available_plugins() -> None:
    """
    Utility function to print all available plugins.
    Useful for debugging and configuration.
    """
    PluginRegistry.discover_plugins()
    available = PluginRegistry.list_available_plugins()
    
    if not available:
        print("No egile plugins found.")
        print("\nTo install plugins, run:")
        print("  pip install egile-agent-prospectfinder")
        print("  pip install egile-agent-x-twitter")
        return
    
    print(f"Found {len(available)} egile plugin(s):\n")
    for plugin_type in sorted(available):
        package_name = PluginRegistry._available_plugins[plugin_type]
        print(f"  - {plugin_type:20s} (package: {package_name})")
    
    print("\nUse these plugin types in your agents.yaml configuration.")


if __name__ == "__main__":
    # Allow running as: python -m egile_agent_hub.plugin_loader
    logging.basicConfig(level=logging.INFO)
    print_available_plugins()
