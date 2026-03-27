# BUILD_PLAN_022: Background Agents — Autonomous Long-Running Tasks

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** MUST-CLOSE
**Competitive Gap:** Claude Code and Cursor have background agents that run tasks autonomously. Crux has no background execution.
**Goal:** `crux bg <task>` spawns a background agent that runs a task, saves results to `.crux/agents/`, and reports completion via session state.

**Covers:** background agents

## Architecture

```
$ crux bg "run all tests and fix any failures"
Agent spawned: bg-abc123
Running in background...

[Later]
$ crux bg status
bg-abc123: completed (3 tests fixed, 2 files changed)

$ crux bg results bg-abc123
[shows full log]
```

## Phase 1: Agent Spawning

- [ ] 1.1 `crux bg <task>` CLI — spawn a detached process that runs the task
- [ ] 1.2 Agent runs as a subprocess with its own session state in `.crux/agents/<id>/`
- [ ] 1.3 Agent log written to `.crux/agents/<id>/log.jsonl`
- [ ] 1.4 `crux bg list` — show running and completed agents
- [ ] 1.5 `crux bg status <id>` — show agent status
- [ ] 1.6 `crux bg results <id>` — show full results
- [ ] 1.7 `crux bg cancel <id>` — kill running agent
- [ ] 1.8 Tests

## Phase 2: Agent Execution

- [ ] 2.1 Agent connects to LLM (Ollama/Anthropic/OpenAI) autonomously
- [ ] 2.2 Agent has access to Crux tools (file read/write, bash, git)
- [ ] 2.3 Agent writes progress updates to log
- [ ] 2.4 Agent updates main session state on completion (add_decision, files_touched)
- [ ] 2.5 Tests

## Phase 3: MCP Integration

- [ ] 3.1 MCP tool: `spawn_background_agent(task)` — launch from any connected tool
- [ ] 3.2 MCP tool: `list_agents()` — show running/completed
- [ ] 3.3 MCP tool: `agent_status(id)` — get status
- [ ] 3.4 MCP tool: `agent_results(id)` — get full results
- [ ] 3.5 Tests

## Convergence Criteria
- Background agent spawning and management
- Autonomous LLM-powered task execution
- Results reported to main session
- MCP tools for in-session management
- Two consecutive clean audit passes
