# Command: restore

Restore session context after a restart or crash.

## Behavior

When the user types `/restore`, immediately call the `restore_context` MCP tool and present the returned context. Then confirm you're ready to continue from where the previous session left off.

## Steps

1. Call the `restore_context` tool (no arguments needed)
2. Read the returned context carefully
3. Present a brief summary: mode, what was being worked on, key decisions, pending tasks
4. Ask if the user wants to continue with the pending work

## Usage
```
/restore
```
