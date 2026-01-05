"""Egile Agent Hub - Multi-Agent System Manager.

This package provides a unified hub for running multiple Egile agents and teams
in a single AgentOS instance, eliminating the need for multiple browser tabs.
"""

from egile_agent_hub.config import AgentHubConfig, ConfigError, load_config
from egile_agent_hub.plugin_loader import PluginLoadError, PluginRegistry
from egile_agent_hub.run_server import run_all, run_agentos_only

__version__ = "0.1.0"

__all__ = [
    "AgentHubConfig",
    "ConfigError",
    "PluginLoadError",
    "PluginRegistry",
    "load_config",
    "run_all",
    "run_agentos_only",
]
