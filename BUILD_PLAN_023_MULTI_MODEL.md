# BUILD_PLAN_023: Multi-Model Native — Seamless Provider Switching

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** MUST-CLOSE
**Competitive Gap:** Aider, Roo Code, and Codex CLI natively support multiple models. Crux has model routing (tiers) but the actual binary only calls Ollama directly. No native Anthropic/OpenAI chat completion.
**Goal:** Crux binary can directly call any LLM provider — Ollama, Anthropic, OpenAI, OpenRouter — for agent mode, auditing, and tool execution. Provider selection is automatic based on available credentials.

**Covers:** multi-model

## Architecture

```
Provider chain (checked in order):
1. Ollama (local, free) — if running
2. Anthropic (if ANTHROPIC_API_KEY set)
3. OpenAI (if OPENAI_API_KEY set)
4. OpenRouter (if OPENROUTER_API_KEY set)
5. Disabled (error: no provider available)
```

## Phase 1: Provider Abstraction

- [ ] 1.1 Create `src/llm/mod.rs` with `LlmProvider` trait: `generate(prompt, model) -> Result<String>`
- [ ] 1.2 `src/llm/ollama.rs` — existing Ollama client wrapped as provider
- [ ] 1.3 `src/llm/anthropic.rs` — Anthropic Messages API via reqwest
- [ ] 1.4 `src/llm/openai.rs` — OpenAI Chat Completions API via reqwest
- [ ] 1.5 `src/llm/openrouter.rs` — OpenRouter API (OpenAI-compatible) via reqwest
- [ ] 1.6 `auto_select_provider()` — pick best available provider
- [ ] 1.7 Tests for each provider (mock HTTP responses)

## Phase 2: Chat Completion

- [ ] 2.1 `chat(messages, model, provider)` — full chat completion with message history
- [ ] 2.2 Streaming support (optional — for agent REPL)
- [ ] 2.3 Tool calling support (for agent tool execution)
- [ ] 2.4 Tests

## Phase 3: Integration

- [ ] 3.1 Audit scripts (gates 4-5) use provider abstraction instead of direct Ollama
- [ ] 3.2 Agent mode (PLAN-019) uses provider abstraction
- [ ] 3.3 `get_available_tiers` MCP tool queries all providers
- [ ] 3.4 Tests

## Convergence Criteria
- 4 LLM providers (Ollama, Anthropic, OpenAI, OpenRouter)
- Auto-selection based on available credentials
- Chat completion with message history
- Two consecutive clean audit passes
