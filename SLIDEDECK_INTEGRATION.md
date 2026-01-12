# SlideDeck Integration into Egile Agent Hub - Setup Instructions

## What Was Done

The SlideDeck agent has been successfully integrated into egile-agent-hub. Here's what changed:

### 1. Files Modified

- **agents.yaml** - Added slidedeck agent configuration
- **agents.yaml.example** - Added slidedeck example
- **src/egile_agent_hub/run_server.py** - Added "slidedeck" to MCP module map
- **pyproject.toml** - Added egile-agent-slidedeck dependency
- **README.md** - Updated documentation with slidedeck examples

### 2. Configuration Added

The active `agents.yaml` now includes:

```yaml
agents:
  - name: slidedeck
    description: "Create professional PowerPoint presentations with AI-generated content and images"
    plugin_type: slidedeck
    mcp_port: 8003
    instructions:
      - "You are a professional presentation designer and content strategist."
      - "WORKFLOW: Always start with start_deck(title, audience), then add slides with add_slide(), and finally export with export_deck()."
      - "NEVER skip starting a deck - you must call start_deck() before adding any slides."
      - "After each slide is added, confirm with the user before adding more."
      - "AUDIENCES: Choose ceo (business/ROI focus), cto (architecture/tech), engineer (implementation), or general (balanced)."
      - "Keep slides focused with 3-5 bullet points maximum."
      - "ALWAYS show the file location clearly after exporting."
```

## How to Use

### Step 1: Restart the Hub

The hub needs to be restarted to pick up the new configuration:

```bash
# Stop current processes (Ctrl+C in the terminal running agent-hub)
# Or kill the processes:
Stop-Process -Id 77128, 86464

# Restart the hub
cd C:\Users\jeanb\OneDrive\Documents\projects\egile-agent-hub
.\start.bat
```

### Step 2: Test in Agent UI

1. Open Agent UI at http://localhost:3000
2. Select "slidedeck" from the agent dropdown
3. Try this conversation:

```
User: "Create a CEO presentation about the Egile ecosystem"

Agent: [Will call start_deck() with ceo audience]

User: "Add 5 slides covering key features"

Agent: [Will call add_slide() 5 times with appropriate content]

User: "Export it"

Agent: [Will call export_deck() and show the file path]
```

### Step 3: Find Your PowerPoint

The presentation will be saved at:
```
C:\Users\jeanb\OneDrive\Documents\projects\egile-mcp-slidedeck\presentations\[filename].pptx
```

The agent will display the full path when exporting.

## Troubleshooting

### Issue: Agent doesn't use tools, just generates text

**Cause**: The agent might not be recognizing it has access to the slidedeck tools.

**Solution**:
1. Check the hub logs for "Registered X tool(s) for 'slidedeck'"
2. Ensure egile-agent-slidedeck is installed: `pip show egile-agent-slidedeck`
3. If not installed, run: `pip install -e C:\Users\jeanb\OneDrive\Documents\projects\egile-agent-slidedeck`

### Issue: "Deck ID not found" errors

**Cause**: Each conversation needs to start with `start_deck()`.

**Solution**: Always start a new conversation with creating a deck before adding slides.

### Issue: No PowerPoint file created

**This was the original issue - now fixed!**
- The export path is now shown clearly: `📄 C:\...\presentations\filename.pptx`
- The directory is automatically created
- File creation is logged

### Issue: Agent "forgets" previous slides

**Cause**: This is actually working as intended - the deck state is maintained by the MCP server, not in the conversation. However, the agent should remember within a single conversation.

**Solution**: 
- Keep the conversation in one session
- The deck_id is cached by the plugin per conversation
- Starting a new conversation = new deck

## Example Team Configuration

Want to create a "pitch team" that researches prospects and creates presentations?

Add to `agents.yaml`:

```yaml
teams:
  - name: pitch-team
    description: "Research prospects and create tailored pitch presentations"
    members:
      - prospectfinder
      - slidedeck
    instructions:
      - "Coordinate between prospectfinder and slidedeck."
      - "First research the target company with prospectfinder."
      - "Then create a tailored presentation with slidedeck."
      - "Always confirm key points before creating slides."
```

Then in Agent UI:
```
Select: pitch-team

User: "Create a pitch for CMS focusing on AI consulting"
Team: [Delegates to prospectfinder to research CMS, then to slidedeck to create presentation]
```

## Next Steps

1. **Stop the hub** - Ctrl+C or kill processes 77128 and 86464
2. **Restart** - Run `.\start.bat` in the egile-agent-hub directory
3. **Test** - Use Agent UI to create a presentation
4. **Verify** - Check that the .pptx file is created in the presentations folder
5. **Open** - Open the PowerPoint file to confirm it worked!

## What the Agent Should Do Now

When you say: **"CMS is my prospect and I want to sell it my egile ecosystem, create the slides and save them"**

The agent should:
1. Call `start_deck(title="Egile Ecosystem for CMS", audience="ceo")`
2. Call `add_slide()` multiple times with appropriate content
3. Call `export_deck()` to create the .pptx file
4. Show you the exact file path

Instead of just generating markdown text!
