# Plugin Discovery System

## Overview

The Egile Agent Hub now features a **dynamic plugin discovery system** that automatically detects installed egile agent plugins and loads only those that are actually needed.

## Key Features

### 1. **Automatic Discovery**
- Scans installed Python packages for `egile-agent-*` packages
- No need to manually register plugins in code
- Excludes framework packages (core, hub)

### 2. **Lazy Loading**
- Plugins are only imported when actually used
- Faster startup time
- Lower memory footprint

### 3. **Easy Plugin Listing**
Run this command to see all available plugins:
```bash
python -m egile_agent_hub.plugin_loader
```

Example output:
```
Found 2 egile plugin(s):

  - prospectfinder       (package: egile_agent_prospectfinder)
  - x-twitter            (package: egile_agent_x_twitter)

Use these plugin types in your agents.yaml configuration.
```

## How It Works

### Plugin Naming Convention

The system automatically converts package names to plugin types:
- `egile-agent-prospectfinder` → `prospectfinder`
- `egile-agent-x-twitter` → `x-twitter`
- `egile-agent-my-plugin` → `my-plugin`

Hyphens are preserved to follow YAML naming conventions.

### Plugin Class Discovery

When a plugin is loaded, the system looks for the plugin class using these naming patterns:
1. **CamelCase with "Plugin" suffix**: `ProspectFinderPlugin`, `XTwitterPlugin`
2. **Capitalized with "Plugin" suffix**: `ProspectfinderPlugin`
3. **Generic**: `Plugin`

The class must be importable from the package root (e.g., `from egile_agent_prospectfinder import ProspectFinderPlugin`).

## Usage in agents.yaml

Use the plugin type names discovered by the system:

```yaml
agents:
  - name: prospectfinder
    description: "Find business prospects"
    plugin_type: prospectfinder  # Use the plugin type from discovery
    mcp_port: 8001
    
  - name: xtwitter
    description: "X/Twitter posting"
    plugin_type: x-twitter  # Hyphens match YAML conventions
    mcp_port: 8002
```

## Benefits

### Before (Hardcoded)
```python
# Had to manually import and register each plugin
from egile_agent_prospectfinder import ProspectFinderPlugin
from egile_agent_x_twitter import XTwitterPlugin

_plugins = {
    "prospectfinder": ProspectFinderPlugin,
    "xtwitter": XTwitterPlugin,
}
```

**Problems:**
- Required code changes for each new plugin
- Imported all plugins even if not used
- Manual maintenance of plugin registry

### After (Dynamic Discovery)
```python
# Automatic discovery - no manual registration needed!
PluginRegistry.discover_plugins()
available = PluginRegistry.list_available_plugins()
# Returns: ["prospectfinder", "x_twitter"]

# Plugins are loaded only when needed
plugin = PluginRegistry.create_plugin("prospectfinder", config)
```

**Benefits:**
- ✅ Zero code changes for new plugins
- ✅ Only loads plugins that are actually used
- ✅ Automatic plugin listing
- ✅ Easy to add new plugins via pip install

## Creating New Plugins

To create a plugin that works with the discovery system:

1. **Package Name**: Use pattern `egile-agent-<plugin-name>`
   ```toml
   [project]
   name = "egile-agent-myplugin"
   ```

2. **Plugin Class**: Export it from package root
   ```python
   # src/egile_agent_myplugin/__init__.py
   from .plugin import MyPluginPlugin
   
   __all__ = ["MyPluginPlugin"]
   ```

3. **Install**: The plugin will be auto-discovered
   ```bash
   pip install egile-agent-myplugin
   python -m egile_agent_hub.plugin_loader  # Verify it appears
   ```

4. **Configure**: Add to agents.yaml
   ```yaml
   agents:
     - name: myplugin_agent
       plugin_type: myplugin
       mcp_port: 8003
   ```

## Programmatic Access

```python
from egile_agent_hub.plugin_loader import PluginRegistry

# Discover all available plugins
PluginRegistry.discover_plugins()

# List available plugin types
plugins = PluginRegistry.list_available_plugins()
print(plugins)  # ["prospectfinder", "x-twitter"]

# Load a specific plugin class
PluginClass = PluginRegistry.get_plugin_class("prospectfinder")

# Create a plugin instance
config = {"mcp_port": 8001, "use_mcp": False}
plugin = PluginRegistry.create_plugin("prospectfinder", config)
```

## Troubleshooting

### Plugin Not Detected

1. **Check package name**:
   ```bash
   pip list | grep egile-agent
   ```
   Package should start with `egile-agent-`

2. **Run discovery**:
   ```bash
   python -m egile_agent_hub.plugin_loader
   ```

3. **Check logs**: Enable INFO logging to see discovery details

### Plugin Class Not Found

Error: `Could not find plugin class in <package>`

**Solution**: Ensure plugin class is exported from package `__init__.py`:
```python
from .plugin import MyPluginPlugin
__all__ = ["MyPluginPlugin"]
```

### Import Error

Error: `Failed to import plugin package`

**Solution**: Verify the package is installed in the current environment:
```bash
pip show egile-agent-<plugin-name>
```
