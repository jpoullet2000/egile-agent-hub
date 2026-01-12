"""Main server runner for Egile Agent Hub.

This module orchestrates:
- Loading configuration from YAML
- Starting MCP servers for each agent plugin
- Creating Agno Agents and Teams
- Starting the unified AgentOS instance
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

import uvicorn
from agno.agent import Agent as AgnoAgent
from agno.db.sqlite import AsyncSqliteDb
from agno.os import AgentOS
from agno.team import Team as AgnoTeam
from dotenv import load_dotenv

from egile_agent_core.models import Mistral, OpenAI, XAI
from egile_agent_core.models.agno_adapter import AgnoModelAdapter
from egile_agent_hub.config import ConfigError, get_default_model_config, load_config
from egile_agent_hub.plugin_loader import PluginLoadError, load_plugins_for_agents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global process tracking
mcp_processes: list[subprocess.Popen] = []


async def start_mcp_server(
    module_name: str,
    port: int,
    host: str = "0.0.0.0",
) -> subprocess.Popen | None:
    """
    Start a single MCP server as a subprocess.

    Args:
        module_name: Python module to run (e.g., "egile_mcp_prospectfinder.server")
        port: Port number for the MCP server
        host: Host to bind to

    Returns:
        Subprocess instance or None if failed
    """
    logger.info(f"Starting MCP server: {module_name} on {host}:{port}")

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    try:
        # Start with inherited stdout/stderr so we can see MCP server logs
        # Use -u for unbuffered output
        process = subprocess.Popen(
            [
                sys.executable,
                "-u",  # Unbuffered output
                "-m",
                module_name,
                "--transport",
                "sse",
                "--host",
                host,
                "--port",
                str(port),
            ],
            stdout=None,  # Inherit stdout to see logs
            stderr=None,  # Inherit stderr to see errors
            text=True,
            env=env,
            bufsize=0,  # No buffering
        )

        # Wait for startup
        await asyncio.sleep(2)

        # Check if process is still running
        if process.poll() is not None:
            logger.error(f"MCP server {module_name} failed to start (check output above)")
            return None

        logger.info(f"MCP server {module_name} started successfully on port {port}")
        return process

    except Exception as e:
        logger.error(f"Failed to start MCP server {module_name}: {e}")
        return None


async def start_all_mcp_servers(hub_config) -> list[subprocess.Popen]:
    """
    Start all MCP servers required by the agent configuration (SSE transport only).
    
    For stdio transport, servers are spawned on-demand by the MCP clients.

    Args:
        hub_config: AgentHubConfig instance

    Returns:
        List of subprocess instances
    """
    processes = []
    mcp_servers = hub_config.get_mcp_servers()

    if not mcp_servers:
        logger.info("No MCP servers to start (no agents with plugins)")
        return processes
    
    # Filter for SSE transport only - stdio servers are spawned by clients
    sse_servers = {
        name: config for name, config in mcp_servers.items()
        if config.get("transport", "sse") == "sse"
    }
    
    if not sse_servers:
        logger.info("No SSE MCP servers to pre-start (using stdio transport)")
        return processes

    logger.info(f"Starting {len(sse_servers)} SSE MCP server(s)...")

    # Map plugin types to module names
    module_map = {
        "prospectfinder": "egile_mcp_prospectfinder.server",
        "xtwitter": "egile_mcp_x_post_creator.server",
        "slidedeck": "egile_mcp_slidedeck.server",
    }

    # Start each unique MCP server
    started_ports = set()
    for agent_name, server_config in sse_servers.items():
        plugin_type = server_config["plugin_type"]
        port = server_config["port"]
        host = server_config["host"]

        # Skip if already started on this port
        if port in started_ports:
            logger.info(f"MCP server for {agent_name} already started on port {port}")
            continue

        module_name = module_map.get(plugin_type)
        if not module_name:
            logger.warning(f"Unknown plugin type '{plugin_type}' for agent '{agent_name}'")
            continue

        process = await start_mcp_server(module_name, port, host)
        if process:
            processes.append(process)
            started_ports.add(port)

    logger.info(f"Successfully started {len(processes)} MCP server(s)")
    return processes


def create_model_instance(model_config: dict[str, str]):
    """
    Create a model instance from configuration.

    Args:
        model_config: Dictionary with 'provider' and 'model' keys

    Returns:
        BaseLLM instance
    """
    provider = model_config["provider"]
    model_name = model_config["model"]

    if provider == "mistral":
        return Mistral(model=model_name)
    elif provider == "xai":
        return XAI(model=model_name)
    elif provider == "openai":
        return OpenAI(model=model_name)
    else:
        raise ValueError(f"Unknown model provider: {provider}")


async def create_multi_agent_os(hub_config, plugins: dict[str, Any]) -> AgentOS:
    """
    Create a unified AgentOS with all configured agents and teams.

    Args:
        hub_config: AgentHubConfig instance
        plugins: Dictionary mapping agent name to plugin instance

    Returns:
        Configured AgentOS instance
    """
    logger.info("Creating multi-agent AgentOS...")

    # Get default model configuration
    default_model_config = get_default_model_config()
    logger.info(f"Default model: {default_model_config['provider']} - {default_model_config['model']}")

    # Create shared database
    db_file = os.getenv("DB_FILE", "agent_hub.db")
    db = AsyncSqliteDb(db_file=db_file)
    logger.info(f"Using database: {db_file}")

    # Create agents
    agno_agents = {}
    for agent_config in hub_config.agents:
        agent_name = agent_config["name"]
        logger.info(f"Creating agent: {agent_name}")

        # Determine model for this agent
        if "model_override" in agent_config:
            model_config = agent_config["model_override"]
            if isinstance(model_config, str):
                # Simple model name override
                model_config = {
                    "provider": default_model_config["provider"],
                    "model": model_config,
                }
        else:
            model_config = default_model_config

        model = create_model_instance(model_config)

        # Get plugin if configured
        plugin = plugins.get(agent_name)
        tools = []
        if plugin:
            if hasattr(plugin, "get_tool_functions"):
                tool_functions = plugin.get_tool_functions()
                tools = list(tool_functions.values())
                logger.info(f"  Registered {len(tools)} tool(s) for '{agent_name}'")

        # Create adapter with tools
        # Tools must be registered with the adapter so it can execute them
        agno_model = AgnoModelAdapter(model, tools=tools if tools else None)
        logger.info(f"Successfully created AgnoModelAdapter with {len(tools) if tools else 0} tools")

        # Create Agno agent
        agent = AgnoAgent(
            name=agent_name,
            model=agno_model,
            db=db,
            instructions=agent_config.get("instructions", []),
            description=agent_config.get("description", ""),
            tools=tools if tools else None,
            markdown=agent_config.get("markdown", True),
            debug_mode=agent_config.get("debug_mode", False),
        )
        agno_agents[agent_name] = agent
        logger.info(f"  Created agent '{agent_name}'")
    
    # Initialize all plugins by calling on_agent_start
    # This is critical for plugins that need to connect to MCP servers
    # Normally Agno would call this, but for team members it doesn't happen
    logger.info("Initializing agent plugins...")
    for agent_name, agent in agno_agents.items():
        plugin = plugins.get(agent_name)
        if plugin and hasattr(plugin, 'on_agent_start'):
            try:
                # Create a dummy Agent-like object with the name for the plugin
                class AgentProxy:
                    def __init__(self, name):
                        self.name = name
                
                await plugin.on_agent_start(AgentProxy(agent_name))
                logger.info(f"  Initialized plugin for '{agent_name}'")
            except Exception as e:
                logger.error(f"  Failed to initialize plugin for '{agent_name}': {e}")
                raise

    # Create teams (if configured)
    agno_teams = []
    if hub_config.teams:
        logger.info(f"Creating {len(hub_config.teams)} team(s)...")
        
        for team_config in hub_config.teams:
            team_name = team_config["name"]
            logger.info(f"Creating team: {team_name}")

            # Get team members
            member_names = team_config["members"]
            members = [agno_agents[name] for name in member_names if name in agno_agents]
            
            if not members:
                logger.warning(f"Team '{team_name}' has no valid members, skipping")
                continue

            # Determine team leader model
            if "model_override" in team_config:
                model_config = team_config["model_override"]
                if isinstance(model_config, str):
                    model_config = {
                        "provider": default_model_config["provider"],
                        "model": model_config,
                    }
                team_model = create_model_instance(model_config)
            else:
                team_model = create_model_instance(default_model_config)

            # Wrap team model in AgnoModelAdapter (teams also need wrapped models)
            try:
                team_agno_model = AgnoModelAdapter(team_model)
            except TypeError:
                logger.warning(f"AgnoModelAdapter doesn't support tools parameter - using older version")
                team_agno_model = AgnoModelAdapter(team_model)

            # Create Agno team
            team = AgnoTeam(
                name=team_name,
                members=members,
                model=team_agno_model,
                db=db,
                instructions=team_config.get("instructions", []),
                description=team_config.get("description", ""),
            )
            agno_teams.append(team)
            logger.info(f"  Created team '{team_name}' with {len(members)} member(s)")

    # AgentOS requires Agent instances in agents parameter
    # And Team instances in teams parameter (separate!)
    os_agents = list(agno_agents.values())
    
    if agno_teams:
        logger.info(f"Created {len(agno_teams)} team(s) with {len(os_agents)} total agent(s)")
        logger.info(f"AgentOS will expose {len(os_agents)} agent(s) and {len(agno_teams)} team(s)")
    else:
        logger.info(f"AgentOS will expose {len(os_agents)} individual agent(s)")

    # Create AgentOS with both agents and teams
    agent_os = AgentOS(
        id=os.getenv("AGENTOS_ID", "egile-agent-hub"),
        description="Multi-Agent Hub powered by Egile Agent Core",
        agents=os_agents,
        teams=agno_teams if agno_teams else None,
    )

    logger.info("Multi-agent AgentOS created successfully!")
    return agent_os


def print_startup_info():
    """Print startup information and instructions."""
    print("\n" + "=" * 70)
    print("🚀 EGILE AGENT HUB - Multi-Agent System")
    print("=" * 70)
    print("\n📡 Services Running:")
    print(f"  • AgentOS API:     http://localhost:{os.getenv('AGENTOS_PORT', '8000')}")
    
    # Print MCP servers
    config = load_config()
    mcp_servers = config.get_mcp_servers()
    if mcp_servers:
        print("\n  • MCP Servers:")
        for agent_name, server_config in mcp_servers.items():
            plugin_type = server_config["plugin_type"]
            port = server_config["port"]
            print(f"    - {plugin_type.capitalize()}: http://localhost:{port}")
    
    print("\n💡 Next Steps:")
    print("  1. (Optional) Start Agent UI in ../agent-ui:")
    print("     cd ../agent-ui && pnpm dev")
    print("  2. Open http://localhost:3000 in your browser")
    print("  3. Select an agent/team from the dropdown and start chatting!")
    
    print("\n⚙️  Configuration:")
    print(f"  • Config file: {os.getenv('AGENTS_CONFIG_FILE', 'agents.yaml')}")
    print(f"  • Database:    {os.getenv('DB_FILE', 'agent_hub.db')}")
    
    print("\n" + "=" * 70)
    print("Press Ctrl+C to stop all services")
    print("=" * 70 + "\n")


def cleanup_processes():
    """Terminate all MCP server processes."""
    global mcp_processes
    if mcp_processes:
        logger.info("Shutting down MCP servers...")
        for process in mcp_processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
                try:
                    process.kill()
                except:
                    pass
        mcp_processes = []
        logger.info("All MCP servers stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("\nReceived shutdown signal, cleaning up...")
    cleanup_processes()
    sys.exit(0)


def run_all():
    """Run all services: MCP servers + AgentOS."""
    global mcp_processes
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Load configuration
        logger.info("Loading agent hub configuration...")
        hub_config = load_config()

        # Load plugins
        logger.info("Loading agent plugins...")
        plugins = load_plugins_for_agents(hub_config.agents)

        # Start MCP servers (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        mcp_processes = loop.run_until_complete(start_all_mcp_servers(hub_config))

        # Create AgentOS (async - needs plugin initialization)
        agent_os = loop.run_until_complete(create_multi_agent_os(hub_config, plugins))
        app = agent_os.get_app()

        # Print startup info
        print_startup_info()

        # Run AgentOS
        agentos_port = int(os.getenv("AGENTOS_PORT", "8000"))
        agentos_host = os.getenv("AGENTOS_HOST", "0.0.0.0")
        
        uvicorn.run(app, host=agentos_host, port=agentos_port)

    except (ConfigError, PluginLoadError) as e:
        logger.error(f"Configuration error: {e}")
        cleanup_processes()
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        cleanup_processes()
        sys.exit(1)
    finally:
        cleanup_processes()


def run_agentos_only():
    """Run only AgentOS (assumes MCP servers are already running)."""
    try:
        # Load configuration
        logger.info("Loading agent hub configuration...")
        hub_config = load_config()

        # Load plugins
        logger.info("Loading agent plugins...")
        plugins = load_plugins_for_agents(hub_config.agents)

        # Create AgentOS (async - needs plugin initialization)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agent_os = loop.run_until_complete(create_multi_agent_os(hub_config, plugins))
        app = agent_os.get_app()

        # Print info
        print("\n" + "=" * 70)
        print("🚀 EGILE AGENT HUB - AgentOS Only")
        print("=" * 70)
        print("\n⚠️  Note: MCP servers must be started separately!")
        print(f"\n📡 AgentOS API: http://localhost:{os.getenv('AGENTOS_PORT', '8000')}")
        print("=" * 70 + "\n")

        # Run AgentOS
        agentos_port = int(os.getenv("AGENTOS_PORT", "8000"))
        agentos_host = os.getenv("AGENTOS_HOST", "0.0.0.0")
        
        uvicorn.run(app, host=agentos_host, port=agentos_port)

    except (ConfigError, PluginLoadError) as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


def main():
    """Main entry point - runs all services."""
    run_all()


if __name__ == "__main__":
    main()
