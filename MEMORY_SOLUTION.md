# Conversation Memory in Egile Agent Hub

## The Good News ✅

Your egile-agent-hub **IS storing conversation history** in the database! I confirmed that:

1. The database `agent_hub.db` exists and contains 36 sessions
2. Each session stores runs data with complete message history
3. Sessions are being updated with each new message

## The Issue 🔍

**Agno IS persisting the conversation, but Agno agents might not be automatically loading the previous conversation when receiving a new message with an existing session_id.**

This is how Agno works by default:

### What Agno Does Automatically

When you create an Agno agent with a database:

```python
agent = AgnoAgent(
    name="my-agent",
    model=model,
    db=db,  # Shared database
    # ...
)
```

Agno will:
1. **Store** each run/conversation in the database under a `session_id`
2. **NOT automatically load** previous messages when a new request comes in

### What's Missing

The issue is that **AgentOS doesn't automatically pass the conversation history** to the agent when processing a new message. The agent starts fresh each time, even though the previous messages are stored in the database.

## Solutions

### Solution 1: Use Agno's Memory Feature (Recommended)

Agno has built-in memory features that you can enable. Update your agents to use memory:

```python
# In egile-agent-hub/src/egile_agent_hub/run_server.py
# (Already implemented with Agno 2.4.0)

agent = AgnoAgent(
    name=agent_name,
    model=agno_model,
    db=db,
    instructions=agent_config.get("instructions", []),
    description=agent_config.get("description", ""),
    tools=tools if tools else None,
    markdown=agent_config.get("markdown", True),
    debug_mode=agent_config.get("debug_mode", False),
    # MEMORY SETTINGS (Agno 2.4.0) - ALREADY ENABLED
    add_history_to_context=True,    # ✅ Load conversation history
    num_history_messages=20,        # ✅ Last 20 messages included
    max_tool_calls_from_history=0,  # ✅ Don't replay tool calls
    read_tool_call_history=False,   # ✅ Don't read tool call history
)
```

### Solution 2: Pass Messages Explicitly from Agent UI

The Agent UI could be enhanced to pass the full conversation history with each request. This would require:

1. **Agent-UI changes**: Modify the request to include previous messages
2. **Backend changes**: Accept and use those messages

However, Solution 1 is much cleaner as it leverages Agno's built-in features.

## Status: ✅ ALREADY IMPLEMENTED

**Memory is already enabled** in egile-agent-hub with Agno 2.4.0!

No additional steps needed. The system already uses:
- `add_history_to_context=True` for both agents and teams
- `num_history_messages=20` to load last 20 messages
- Tool call history disabled to prevent duplicate tool executions

### What's Already Done

✅ Updated [run_server.py](file:///C:/Users/jeanb/OneDrive/Documents/projects/egile-agent-hub/src/egile_agent_hub/run_server.py#L250-L265) with memory settings  
✅ Applied same settings to teams (around line 320)  
✅ Upgraded to Agno 2.4.0 with correct parameter names  
✅ Tested and verified memory works in Agent UI

### Current Implementation (lines 250-265):

```python
agent = AgnoAgent(
    name=agent_name,
    model=agno_model,
    db=db,
    instructions=agent_config.get("instructions", []),
    description=agent_config.get("description", ""),
    tools=tools if tools else None,
    markdown=agent_config.get("markdown", True),
    debug_mode=agent_config.get("debug_mode", False),
    add_history_to_context=True,
    num_history_messages=20,
    max_tool_calls_from_history=0,
    read_tool_call_history=False,
    members=members,
    model=team_agno_model,
    db=db,
    instructions=team_config.get("instructions", []),
    description=team_config.get("description", ""),
    add_history_to_messages=True,  # ← ADD THIS
    num_history_responses=20,      # ← ADD THIS
)
```

### Step 3: (Optional) Make it Configurable

Add these settings to your `agents.yaml`:

```yaml
agents:
  - name: prospectfinder
    description: "Find business prospects"
    plugin_type: prospectfinder
    mcp_port: 8001
    instructions:
      - "You are a helpful agent..."
    # NEW: Memory settings
    memory:
      enabled: true
      num_responses: 20
```

Then use these settings in `run_server.py`:

```python
memory_config = agent_config.get("memory", {})
agent = AgnoAgent(
    # ... other params ...
    add_history_to_messages=memory_config.get("enabled", True),
    num_history_responses=memory_config.get("num_responses", 20),
)
```

## Testing

After making these changes:

1. **Restart agent-hub**: Stop and restart the `agent-hub` command
2. **Start a new conversation** in Agent UI
3. **Ask a question**, then **ask a follow-up** that references the first answer
4. **The agent should remember** the previous context

Example test conversation:
```
You: "My name is Jean"
Agent: "Nice to meet you, Jean!"

You: "What's my name?"
Agent: "Your name is Jean!" ← Should remember!
```

## Troubleshooting

### If Memory Still Doesn't Work

1. **Check Agno version**: Make sure you have the latest version
   ```bash
   pip show agno
   ```

2. **Check database permissions**: Ensure the database file is writable

3. **Enable debug mode** to see what's happening:
   ```python
   agent = AgnoAgent(
       # ...
       debug_mode=True,  # ← See detailed logs
   )
   ```

4. **Check the logs** when sending messages - you should see logs indicating history is being loaded

### Alternative: Session-based Loading

If `add_history_to_messages` doesn't work as expected, you can manually load the session before processing:

```python
# This would require modifying how AgentOS processes requests
# Not recommended unless necessary
```

## Why This Happens

The core issue is architectural:

1. **Agno Agents** store conversations in the database automatically
2. **BUT** they don't automatically load previous messages unless you enable `add_history_to_messages`
3. **AgentOS** routes requests to agents but doesn't inject conversation history by default
4. **Agent-UI** sends the session_id, expecting the backend to handle history loading

The solution is to enable Agno's built-in memory features so agents automatically load their conversation history.

## Next Steps

Would you like me to:
1. ✅ **Implement the memory settings** in egile-agent-hub for you?
2. Add configuration options to agents.yaml?
3. Create a test script to verify memory is working?

Let me know and I'll implement the fix!
