# Egile Agent Hub

**Multi-Agent System Manager** - Run multiple Egile agents and teams in a single unified AgentOS instance.

## Overview

Egile Agent Hub eliminates the need for multiple browser tabs and manual copy-pasting between agents. It provides:

- **Single AgentOS Instance** - All agents accessible from one browser tab
- **Agno Team Support** - Group agents into coordinated teams with shared conversation history
- **Flexible Configuration** - YAML-based agent and team definitions
- **Automatic MCP Management** - Starts and manages all required MCP servers
- **Unified Model Selection** - Share the same AI model across agents or override per-agent/team

## Features

✅ **Multi-Agent Coordination**
- Run ProspectFinder, XTwitter, and custom agents simultaneously
- Switch between agents without changing browser tabs
- Shared database for persistent conversation history

✅ **Agno Teams**
- Group agents into teams with a team leader that delegates tasks
- Teams share conversation context and database
- Nested teams supported (teams within teams)

✅ **Simple Configuration**
- YAML-based agent definitions
- Environment variable management
- Hot-swappable configuration (restart to apply changes)

✅ **Automatic MCP Server Management**
- Starts all required MCP servers on unique ports
- Graceful shutdown handling
- Process monitoring and error recovery

## Quick Start

### 1. Installation

```bash
cd egile-agent-hub
./install.sh   # or install.bat on Windows
```

This installs all dependencies:
- egile-agent-core
- egile-mcp-prospectfinder + egile-agent-prospectfinder
- egile-mcp-x-post-creator + egile-agent-x-twitter
- PyYAML, Agno, and other requirements

### 2. Configuration

#### a) Configure Environment Variables

Edit `.env` (created from `.env.example`):

```bash
# At least one AI model API key (priority: Mistral > XAI > OpenAI)
MISTRAL_API_KEY=your_mistral_api_key_here
XAI_API_KEY=your_xai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Google API (for ProspectFinder)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here

# X/Twitter API (for XTwitter)
X_API_KEY=your_x_api_key_here
X_API_SECRET=your_x_api_secret_here
X_ACCESS_TOKEN=your_x_access_token_here
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret_here
```

#### b) Define Your Agents

Edit `agents.yaml` (see `agents.yaml.example` for full documentation):

```yaml
agents:
  - name: prospectfinder
    description: "Find business prospects in specific sectors and countries"
    plugin_type: prospectfinder
    mcp_port: 8001
    instructions:
      - "You are a business development assistant specialized in finding prospects."
      - "Use the find_prospects tool to search for companies by sector and country."
      - "Always provide detailed company information including contact details."

  - name: xtwitter
    description: "Create and publish X/Twitter posts with AI assistance"
    plugin_type: xtwitter
    mcp_port: 8002
    instructions:
      - "You are a social media manager for X/Twitter."
      - "Always draft posts with create_post first and show them to the user."
      - "NEVER publish without explicit user approval."
      - "When publishing, always set confirm=True in publish_post."

  - name: content-writer
    description: "General purpose content writing assistant"
    instructions:
      - "You are a professional content writer."
      - "Create engaging, well-structured content for various purposes."

teams:
  - name: sales-team
    description: "Automated sales team that finds prospects and creates outreach content"
    members:
      - prospectfinder
      - xtwitter
    instructions:
      - "Coordinate between prospectfinder and xtwitter to automate sales outreach."
      - "First use prospectfinder to find relevant companies."
      - "Then use xtwitter to craft personalized outreach posts."
      - "Always get user approval before publishing."
```

### 3. Run the Hub

```bash
./start.sh   # or start.bat on Windows
# Or directly: agent-hub
```

This will:
1. Start MCP servers for ProspectFinder (port 8001) and XTwitter (port 8002)
2. Create all configured agents and teams
3. Start AgentOS API on port 8000

### 4. Open Agent UI

In a separate terminal:

```bash
cd ../agent-ui
pnpm dev
```

Then open http://localhost:3000 in your browser. You'll see all your agents and teams in the dropdown selector!

## Configuration Reference

### Agent Definition

```yaml
agents:
  - name: agent-name              # Required: Unique identifier
    description: "Agent purpose"  # Optional: Human-readable description
    plugin_type: prospectfinder   # Optional: "prospectfinder" or "xtwitter"
    mcp_port: 8001               # Required if plugin_type is set
    mcp_host: localhost          # Optional: Default "localhost"
    instructions:                # Optional: List of instruction strings
      - "Instruction 1"
      - "Instruction 2"
    model_override:              # Optional: Override default model
      provider: xai              # "mistral", "xai", or "openai"
      model: grok-4-1-fast-reasoning
    markdown: true               # Optional: Default true
    debug_mode: false            # Optional: Default false
```

### Team Definition (Agno Team)

```yaml
teams:
  - name: team-name                  # Required: Unique identifier
    description: "Team purpose"      # Optional: Team description
    members:                         # Required: List of agent names
      - agent1
      - agent2
    instructions:                    # Optional: Instructions for team leader
      - "Team coordination instruction"
    model_override:                  # Optional: Override for team leader
      provider: mistral
      model: mistral-large-2512
```

## How Agno Teams Work

An **Agno Team** consists of:

1. **Team Leader** - An AI that coordinates the team, delegates tasks to members based on their roles
2. **Team Members** - Individual agents (or sub-teams) that handle specific tasks
3. **Shared Database** - All team members share conversation history and session state

**Example workflow with a sales team:**

```
User: "Find 5 SaaS companies in France and draft a Twitter post about them"

Team Leader (sales-team):
  ↓ Delegates to prospectfinder: "Find 5 SaaS companies in France"
  ↓ Receives results
  ↓ Delegates to xtwitter: "Draft a Twitter post about these companies: [results]"
  ↓ Receives draft
  ↓ Returns to user: "Here are 5 SaaS companies and a draft post..."

User: "Publish the post"
  ↓ Team leader delegates to xtwitter: "Publish with confirm=True"
```

All of this happens in **one conversation** with **shared context**.

## Usage Examples

### Example 1: Individual Agents

With this `agents.yaml`:

```yaml
agents:
  - name: prospectfinder
    plugin_type: prospectfinder
    mcp_port: 8001
  - name: xtwitter
    plugin_type: xtwitter
    mcp_port: 8002
```

Users can:
- Select "prospectfinder" to search for companies
- Switch to "xtwitter" to create posts
- **Limitation**: No shared context between agents (separate conversations)

### Example 2: Coordinated Team

With this `agents.yaml`:

```yaml
agents:
  - name: prospectfinder
    plugin_type: prospectfinder
    mcp_port: 8001
  - name: xtwitter
    plugin_type: xtwitter
    mcp_port: 8002

teams:
  - name: sales-team
    members:
      - prospectfinder
      - xtwitter
```

Users can:
- Select "sales-team" in the UI
- Ask: "Find 10 AI startups in Germany and create a Twitter thread about them"
- The team leader automatically:
  1. Delegates prospect search to prospectfinder
  2. Delegates Twitter content creation to xtwitter
  3. Coordinates the workflow
- **Benefit**: One request, full automation with shared context

### Example 3: Mixed Setup

```yaml
agents:
  - name: prospectfinder
    plugin_type: prospectfinder
    mcp_port: 8001
  - name: xtwitter
    plugin_type: xtwitter
    mcp_port: 8002
  - name: content-writer
    # No plugin - general purpose
  - name: researcher
    # No plugin - general purpose

teams:
  - name: sales-team
    members: [prospectfinder, xtwitter]
  - name: content-team
    members: [content-writer, xtwitter]
```

Users can select:
- `sales-team` - For automated sales workflows
- `content-team` - For content creation + social posting
- `prospectfinder` - For prospect search only
- `researcher` - For general research

## Ports

| Service | Default Port |
|---------|-------------|
| AgentOS API | 8000 |
| ProspectFinder MCP | 8001 |
| XTwitter MCP | 8002 |
| Agent UI | 3000 (separate) |

Configure in `.env`:

```bash
AGENTOS_PORT=8000
PROSPECTFINDER_MCP_PORT=8001
XTWITTER_MCP_PORT=8002
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `MISTRAL_API_KEY` | One of three | Mistral AI API key |
| `XAI_API_KEY` | One of three | X.AI (Grok) API key |
| `OPENAI_API_KEY` | One of three | OpenAI API key |
| `MISTRAL_MODEL` | No | Default: `mistral-large-2512` |
| `XAI_MODEL` | No | Default: `grok-4-1-fast-reasoning` |
| `OPENAI_MODEL` | No | Default: `gpt-4o-mini` |
| `AGENTS_CONFIG_FILE` | No | Default: `agents.yaml` |
| `AGENTOS_PORT` | No | Default: `8000` |
| `AGENTOS_HOST` | No | Default: `0.0.0.0` |
| `DB_FILE` | No | Default: `agent_hub.db` |
| `PROSPECTFINDER_MCP_PORT` | If using ProspectFinder | Default: `8001` |
| `XTWITTER_MCP_PORT` | If using XTwitter | Default: `8002` |
| `GOOGLE_API_KEY` | If using ProspectFinder | Google API key |
| `GOOGLE_CSE_ID` | If using ProspectFinder | Google Custom Search Engine ID |
| `X_API_KEY` | If using XTwitter | Twitter API key |
| `X_API_SECRET` | If using XTwitter | Twitter API secret |
| `X_ACCESS_TOKEN` | If using XTwitter | Twitter access token |
| `X_ACCESS_TOKEN_SECRET` | If using XTwitter | Twitter access token secret |

## Commands

After installation, you can use these commands:

```bash
# Run all services (MCP servers + AgentOS)
agent-hub

# Run only AgentOS (assumes MCP servers running separately)
agent-hub-agentos

# Or use Python module directly
python -m egile_agent_hub.run_server
```

## Troubleshooting

### Configuration file not found

**Error**: `Configuration file not found: agents.yaml`

**Solution**: Create `agents.yaml` from `agents.yaml.example`:

```bash
cp agents.yaml.example agents.yaml
# Edit agents.yaml to define at least one agent
```

### No AI model API key configured

**Error**: `No AI model API key configured`

**Solution**: Set at least one API key in `.env`:

```bash
MISTRAL_API_KEY=your_key_here
# or XAI_API_KEY or OPENAI_API_KEY
```

### MCP server failed to start

**Error**: `MCP server ... failed to start`

**Possible causes**:
1. Port already in use - Change port in `agents.yaml`
2. Missing dependencies - Run `./install.sh` again
3. Missing API credentials - Check `.env` for required keys

### Plugin not available

**Error**: `ProspectFinderPlugin not available`

**Solution**: Install the plugin package:

```bash
cd ../egile-agent-prospectfinder
pip install -e .
```

### Team references unknown agent

**Error**: `Team 'sales-team' references unknown agent: prospectfinder`

**Solution**: Make sure all team members are defined in the `agents` section:

```yaml
agents:
  - name: prospectfinder  # Must be defined
    plugin_type: prospectfinder
    mcp_port: 8001

teams:
  - name: sales-team
    members:
      - prospectfinder  # References the agent above
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Agent UI (Port 3000)                │
│              http://localhost:3000                  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
                       ↓
┌─────────────────────────────────────────────────────┐
│            AgentOS API (Port 8000)                  │
│  • Manages all agents and teams                     │
│  • Routes requests to appropriate agent/team        │
│  • Handles conversation history in SQLite           │
└──────────┬─────────────────────┬────────────────────┘
           │                     │
           ↓                     ↓
  ┌────────────────┐    ┌────────────────┐
  │ ProspectFinder │    │    XTwitter    │
  │     Agent      │    │     Agent      │
  │   (with MCP)   │    │   (with MCP)   │
  └───────┬────────┘    └───────┬────────┘
          │                     │
          ↓ SSE                 ↓ SSE
  ┌────────────────┐    ┌────────────────┐
  │ ProspectFinder │    │   XTwitter     │
  │  MCP Server    │    │  MCP Server    │
  │  (Port 8001)   │    │  (Port 8002)   │
  └────────────────┘    └────────────────┘
```

## Best Practices

1. **Start Simple** - Begin with 1-2 agents, then add more as needed
2. **Use Teams for Workflows** - Group agents that need to collaborate
3. **Clear Instructions** - Provide detailed, specific instructions for each agent
4. **Unique Ports** - Ensure each MCP server has a unique port
5. **Test Individual Agents First** - Verify each agent works before creating teams
6. **Version Control** - Keep `agents.yaml` and `.env.example` in version control (but not `.env`!)

## Extending the Hub

### Adding a New Agent Plugin

1. Install the plugin package:
   ```bash
   pip install -e ../your-new-agent
   ```

2. Register in `plugin_loader.py`:
   ```python
   # In PluginRegistry.initialize()
   try:
       from your_new_agent import YourPlugin
       cls._plugins["your_plugin_type"] = YourPlugin
   except ImportError as e:
       logger.warning(f"YourPlugin not available: {e}")
   ```

3. Add to `agents.yaml`:
   ```yaml
   agents:
     - name: your-agent
       plugin_type: your_plugin_type
       mcp_port: 8003
   ```

### Creating Custom Agents (No Plugin)

You can create agents without plugins for general-purpose tasks:

```yaml
agents:
  - name: researcher
    description: "Research assistant"
    instructions:
      - "You are a research assistant."
      - "Help users find and analyze information."
      - "Provide sources for your claims."
    model_override:
      provider: xai
      model: grok-4-1-fast-reasoning
```

These agents don't need MCP servers and can use the base model's capabilities.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests if applicable
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Related Projects

- [egile-agent-core](../egile-agent-core) - Core agent framework
- [egile-agent-prospectfinder](../egile-agent-prospectfinder) - ProspectFinder agent
- [egile-agent-x-twitter](../egile-agent-x-twitter) - XTwitter agent
- [agent-ui](../agent-ui) - Web interface for AgentOS
- [Agno](https://github.com/agno-agi/agno) - Multi-agent framework

## Support

For issues, questions, or feature requests:
- GitHub Issues: [Create an issue](#)
- Documentation: See `agents.yaml.example` for detailed configuration examples

---

**Made with ❤️ for the Egile Agent ecosystem**
