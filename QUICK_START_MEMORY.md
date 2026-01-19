# Quick Start: Conversation Memory

## Status: ✅ Already Working!

Your agents **remember conversations** automatically! 🎉

**Memory is enabled by default** - no configuration required.

## How to Use

Just start chatting in Agent UI:

```
You: My name is John
Agent: Nice to meet you, John!

You: What's my name?
Agent: Your name is John! ✅
```

Memory persists throughout the entire conversation session.

### 2. Test It

Open Agent UI and try:
```
You: Remember that my favorite color is blue
Agent: I'll remember that!

You: What's my favorite color?
Agent: Your favorite color is blue! ✅
```

## Memory Configuration

**Current Settings** (hardcoded in run_server.py):
- ✅ **Enabled**: Yes (all agents and teams)
- ✅ **History Length**: 20 messages per session
- ✅ **Tool Call History**: Disabled (prevents duplicate tool executions)

These settings are optimized for most use cases and cannot currently be customized per-agent via YAML.

### To Customize (requires code change):

Edit `egile-agent-hub/src/egile_agent_hub/run_server.py` line 261:

```python
num_history_messages=20,  # Change this number
```

Then restart agent-hub.

## Technical Details

**Memory Implementation** (Agno 2.4.0):
- `add_history_to_context=True` - Loads conversation history from database
- `num_history_messages=20` - Last 20 messages included in context
- `max_tool_calls_from_history=0` - Tool calls from history are not re-executed
- `read_tool_call_history=False` - Tool call history is not loaded

This prevents issues like duplicate calendar events or emails from being created.

## What Gets Remembered

✅ Previous messages in the **same session**  
✅ Context from earlier in the conversation  
✅ Information the user shared  
✅ Tasks the agent completed

❌ NOT remembered across **different sessions**  
❌ NOT remembered after creating a "New Chat" in Agent UI

## Test Script

Run this to verify memory is working:

```bash
cd egile-agent-hub
python test_memory.py
```

## FAQ

### Do I need to update my agents.yaml?

**No!** Memory is enabled by default. Your existing configuration will work with memory automatically.

### Will this use more tokens?

Yes, slightly. Memory means more context is sent to the LLM. But:
- Default 20 messages ≈ 3,000-14,000 tokens
- Still well within LLM limits (100K+ tokens)
- Worth it for better conversations

### Can I disable memory for specific agents?

Yes! Add this to your agent config:
```yaml
memory:
  enabled: false
```

### Does memory persist after restarting agent-hub?

**Yes!** Sessions are stored in the database (`agent_hub.db`), so conversations persist across restarts.

### How do I clear old sessions?

Sessions accumulate in the database. You can:
1. Delete the database file: `agent_hub.db` (will clear all sessions)
2. Use Agent UI's delete session feature
3. Manually delete from database (advanced)

## Troubleshooting

### Memory not working?

1. **Restart agent-hub** (most common fix)
2. **Check you're in the same session** - creating a new chat starts a new session
3. **Run the test script**: `python test_memory.py`
4. **Check logs** for "with memory enabled"

### Still not working?

See [MEMORY_FIX_SUMMARY.md](file:///C:/Users/jeanb/OneDrive/Documents/projects/egile-agent-hub/MEMORY_FIX_SUMMARY.md) for detailed troubleshooting.

## Summary

**Before**: Agents forgot the conversation immediately  
**Now**: Agents remember the last 20 messages automatically  
**Action Needed**: Just restart agent-hub  

That's it! 🎉
