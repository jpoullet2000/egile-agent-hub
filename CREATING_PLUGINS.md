# Creating a New Agent Plugin

This guide explains how to create a new agent plugin that integrates with the Egile Agent Hub.

## Overview

Agent plugins are automatically discovered by the hub via Python entry points. No manual registration in the hub code is required!

## Quick Start

1. **Create your plugin package structure:**
   ```
   egile-agent-yourplugin/
   ├── pyproject.toml
   ├── src/
   │   └── egile_agent_yourplugin/
   │       ├── __init__.py
   │       └── plugin.py
   ```

2. **Create your plugin class:**
   ```python
   # src/egile_agent_yourplugin/plugin.py
   from egile_agent_core.plugins import Plugin
   
   class YourPlugin(Plugin):
       @property
       def name(self) -> str:
           return "yourplugin"
       
       @property
       def description(self) -> str:
           return "Description of what your plugin does"
       
       @property
       def version(self) -> str:
           return "0.1.0"
       
       @property
       def mcp_server_module(self) -> str:
           """Return the Python module path for your MCP server."""
           return "egile_mcp_yourplugin.server"
       
       def get_tool_functions(self) -> dict:
           """Return tools your agent provides."""
           return {
               "your_tool": self._your_tool,
           }
       
       async def _your_tool(self, param: str):
           """Your tool implementation."""
           return f"Result: {param}"
   ```

3. **Configure entry point in pyproject.toml:**
   ```toml
   [project.entry-points."egile_agent_core.plugins"]
   yourplugin = "egile_agent_yourplugin:YourPlugin"
   ```

4. **Install your plugin:**
   ```bash
   pip install -e .
   ```

5. **Add to agents.yaml:**
   ```yaml
   agents:
     - name: yourplugin
       description: "Your plugin description"
       plugin_type: yourplugin  # Must match your plugin name
       mcp_port: 8005           # Choose an available port
       instructions:
         - "Custom instructions for your agent"
   ```

6. **Start the hub:**
   ```bash
   cd egile-agent-hub
   agent-hub
   ```

The hub will automatically:
- Discover your installed plugin
- Load the plugin class
- Get the MCP server module from `mcp_server_module` property
- Start the MCP server on the configured port
- Create the agent with your tools

## Key Components

### 1. Plugin Class

Must inherit from `egile_agent_core.plugins.Plugin` and implement:

**Required Properties:**
- `name`: Unique identifier for your plugin
- `description`: Human-readable description
- `version`: Plugin version

**Optional Properties:**
- `mcp_server_module`: Python module path for MCP server (if using MCP)

**Optional Methods:**
- `get_tool_functions()`: Return dict of tool name -> function
- `on_agent_start(agent)`: Called when agent starts
- `on_agent_stop(agent)`: Called when agent stops

### 2. MCP Server (Optional)

If your plugin provides tools via MCP:

```python
# egile-mcp-yourplugin/src/egile_mcp_yourplugin/server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("egile-mcp-yourplugin")

@app.list_tools()
async def list_tools():
    return [...]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    return [...]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
```

### 3. Entry Point

Must be registered in `pyproject.toml`:

```toml
[project.entry-points."egile_agent_core.plugins"]
yourplugin = "egile_agent_yourplugin:YourPlugin"
```

The entry point group **must** be `"egile_agent_core.plugins"`.

## Auto-Discovery

The hub automatically discovers plugins through:

1. **Package Discovery**: Scans installed packages starting with `egile-agent-*`
2. **Entry Point Loading**: Loads plugin class from entry point
3. **MCP Module Discovery**: Gets MCP server module from `mcp_server_module` property

**No need to modify hub code!**

## Examples

See existing plugins for reference:
- [egile-agent-investment](../egile-agent-investment) - Stock analysis
- [egile-agent-slidedeck](../egile-agent-slidedeck) - Presentation generation
- [egile-agent-prospectfinder](../egile-agent-prospectfinder) - Prospect finding
- [egile-agent-x-twitter](../egile-agent-x-twitter) - Twitter posting

## Plugin Naming Conventions

- **Package**: `egile-agent-yourname` or `egile-agent-your-name`
- **Module**: `egile_agent_yourname` (underscores)
- **Plugin Type**: Same as package suffix (e.g., `yourname` or `your-name`)
- **Class**: `YourNamePlugin` (CamelCase + "Plugin")

## Tool Registration

### Method 1: Direct (Recommended for Hub)

Return tools from `get_tool_functions()`:

```python
def get_tool_functions(self) -> dict:
    return {
        "tool_name": self._tool_function,
    }

async def _tool_function(self, param: str):
    return "result"
```

### Method 2: MCP Server

Define tools in MCP server and set `mcp_server_module`:

```python
@property
def mcp_server_module(self) -> str:
    return "egile_mcp_yourplugin.server"
```

## Configuration Options

In `agents.yaml`:

```yaml
agents:
  - name: yourplugin           # Agent identifier
    description: "..."          # Agent description
    plugin_type: yourplugin     # Must match plugin name
    
    # MCP Configuration (if using MCP)
    mcp_port: 8005             # Port for MCP server
    mcp_host: localhost        # MCP server host
    
    # Agent Instructions
    instructions:
      - "Instruction 1"
      - "Instruction 2"
    
    # Model Override (optional)
    model_override:
      provider: openai
      model: gpt-4
```

## Testing Your Plugin

1. **Install in development mode:**
   ```bash
   pip install -e .
   ```

2. **Verify discovery:**
   ```python
   from egile_agent_hub.plugin_loader import PluginRegistry
   print(PluginRegistry.list_available_plugins())
   # Should include 'yourplugin'
   ```

3. **Check MCP module:**
   ```python
   module = PluginRegistry.get_mcp_server_module('yourplugin')
   print(module)  # Should print your module path
   ```

4. **Test with hub:**
   ```bash
   cd egile-agent-hub
   agent-hub
   ```

## Troubleshooting

### Plugin Not Discovered

- Check package name starts with `egile-agent-`
- Verify entry point in `pyproject.toml`
- Reinstall: `pip install -e .`
- Check: `pip show egile-agent-yourplugin`

### MCP Server Won't Start

- Verify `mcp_server_module` returns correct path
- Check MCP server can run standalone
- Ensure port is available
- Check MCP package is installed

### Tools Not Available

- Verify `get_tool_functions()` returns dict
- Check tool functions are async
- Ensure plugin is initialized

## Best Practices

1. **Use semantic versioning** for plugin versions
2. **Provide clear descriptions** for tools and agents
3. **Handle errors gracefully** in tool functions
4. **Document your tools** with docstrings
5. **Test standalone** before integrating with hub
6. **Follow naming conventions** for consistency
7. **Use type hints** for better IDE support

## Publishing Your Plugin

1. Build package: `python -m build`
2. Publish to PyPI: `python -m twine upload dist/*`
3. Users can install: `pip install egile-agent-yourplugin`
4. Hub auto-discovers after installation

## Support

- See existing plugins for examples
- Check hub logs for discovery messages
- Use `PluginRegistry` for debugging
- Consult [PLUGIN_DISCOVERY.md](PLUGIN_DISCOVERY.md) for details
