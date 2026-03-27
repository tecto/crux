# BUILD_PLAN_019: Terminal Agent — Interactive CLI Agent Mode

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** SHOULD-CLOSE
**Competitive Gap:** Codex CLI and Gemini CLI are terminal-native agents. Crux's `crux` CLI is a management tool, not an interactive agent. CruxCLI is the agent but it's a separate binary.
**Goal:** `crux agent` launches an interactive terminal session where the Crux binary acts as a coding agent — reads prompts, plans actions, executes tools, reports results. Uses any configured LLM provider (Ollama, Anthropic, OpenAI).

**Covers:** Terminal agent, Cascade agent

## Architecture

```
$ crux agent
Crux Agent (qwen3.5:27b via Ollama)
Project: /Users/user/personal/crux (Rust)
Mode: build-py

> add a health check endpoint

Planning...
1. Create src/health.rs with /health route
2. Add to router
3. Write test
4. Verify build

Executing step 1...
[creates file]

Executing step 2...
[edits router]

...
Done. 3 files changed, all tests pass.

>
```

## Phase 1: REPL Loop

- [ ] 1.1 `crux agent` CLI subcommand — interactive REPL with prompt
- [ ] 1.2 Read user input, send to LLM (Ollama first, then Anthropic/OpenAI)
- [ ] 1.3 Display LLM response with formatting
- [ ] 1.4 Session state: auto-restore on start, auto-save on each interaction
- [ ] 1.5 Tests

## Phase 2: Tool Execution

- [ ] 2.1 LLM can request tool calls (file read, file write, bash execute, git operations)
- [ ] 2.2 Tool call format: JSON function calls from LLM → execute → return result
- [ ] 2.3 Permission system: ask before destructive operations (file write, bash)
- [ ] 2.4 Tests

## Phase 3: Multi-Provider Support

- [ ] 3.1 Provider selection: `crux agent --provider ollama --model qwen3.5:27b`
- [ ] 3.2 Anthropic provider: `crux agent --provider anthropic --model claude-sonnet`
- [ ] 3.3 OpenAI provider: `crux agent --provider openai --model gpt-5`
- [ ] 3.4 Auto-detect: try Ollama first, then check API keys
- [ ] 3.5 Tests

## Phase 4: Flow Mode

- [ ] 4.1 Multi-step workflows: agent plans → user approves → agent executes all steps
- [ ] 4.2 Checkpoint between steps: save state so agent can resume if interrupted
- [ ] 4.3 Tests

## Convergence Criteria
- Interactive terminal agent with REPL
- Tool execution (file read/write, bash, git)
- Multi-provider LLM support
- Two consecutive clean audit passes
