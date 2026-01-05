# Egile Agent Hub - Quick Reference

## Installation

```bash
cd egile-agent-hub
./install.sh   # or install.bat on Windows
```

## Configuration

### 1. Edit `.env`
```bash
# Set at least one API key
MISTRAL_API_KEY=your_key
# or XAI_API_KEY or OPENAI_API_KEY

# Google API (for ProspectFinder)
GOOGLE_API_KEY=your_key
GOOGLE_CSE_ID=your_id

# X/Twitter API (for XTwitter)
X_API_KEY=your_key
X_API_SECRET=your_secret
X_ACCESS_TOKEN=your_token
X_ACCESS_TOKEN_SECRET=your_token_secret
```

### 2. Edit `agents.yaml`

**Simple agents:**
```yaml
agents:
  - name: prospectfinder
    plugin_type: prospectfinder
    mcp_port: 8001
  - name: xtwitter
    plugin_type: xtwitter
    mcp_port: 8002
```

**With a team:**
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
    members: [prospectfinder, xtwitter]
    instructions:
      - "Coordinate prospect finding and social media posting"
```

## Running

```bash
# Start hub (all services)
./start.sh   # or start.bat or: agent-hub

# Start Agent UI (separate terminal)
cd ../agent-ui
pnpm dev

# Open browser
http://localhost:3000
```

## Ports

| Service | Port |
|---------|------|
| AgentOS | 8000 |
| ProspectFinder MCP | 8001 |
| XTwitter MCP | 8002 |
| Agent UI | 3000 |

## Commands

```bash
agent-hub              # Run all services
agent-hub-agentos      # Run only AgentOS
python -m egile_agent_hub.run_server  # Direct Python
```

## Agent Types

| Type | Description | Requires |
|------|-------------|----------|
| `prospectfinder` | Find business prospects | Google API, port 8001 |
| `xtwitter` | Create/publish X posts | X API, port 8002 |
| Custom (no plugin_type) | General purpose | Nothing |

## Team Coordination

Teams share conversation history and coordinate between agents:

```yaml
teams:
  - name: team-name
    members: [agent1, agent2]
    instructions:
      - "Team coordination instructions"
```

When user selects a team, the team leader delegates tasks to members automatically.

## Troubleshooting

| Error | Solution |
|-------|----------|
| Config file not found | `cp agents.yaml.example agents.yaml` |
| No API key | Set one in `.env` (MISTRAL/XAI/OPENAI) |
| MCP server failed | Check port not in use, credentials in `.env` |
| Plugin not available | `pip install -e ../plugin-package` |

## File Structure

```
egile-agent-hub/
├── agents.yaml          # Your agent/team definitions
├── .env                 # Your API keys (create from .env.example)
├── agents.yaml.example  # Configuration template
├── .env.example         # Environment template
├── install.sh/.bat      # Installation script
├── start.sh/.bat        # Start script
├── README.md            # Full documentation
└── src/
    └── egile_agent_hub/
        ├── config.py           # YAML loader
        ├── plugin_loader.py    # Plugin registry
        ├── run_server.py       # Main server
        └── __init__.py
```

## Next Steps

1. ✅ Install: `./install.sh`
2. ✅ Configure: Edit `.env` and `agents.yaml`
3. ✅ Run: `./start.sh`
4. ✅ UI: `cd ../agent-ui && pnpm dev`
5. ✅ Browse: http://localhost:3000

See [README.md](README.md) for complete documentation.
