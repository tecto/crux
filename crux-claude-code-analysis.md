# Crux → Claude Code: Integration Analysis (MCP-First Architecture)

## Executive Summary

This document has been rewritten to reflect the MCP-first architectural shift: **all Crux logic now lives in a single MCP server.** Claude Code connects to the Crux MCP Server like any other tool — the server is the brain, Claude Code hooks are paper-thin shims that forward events. There is no Claude Code-specific adapter, no sync script, no plugin with embedded logic. One server. Every tool. All intelligence in `.crux/`.

The integration reduces to three things:

1. **MCP server registration** — one entry in Claude Code's MCP config
2. **Hook shims** — 4-5 hooks in `hooks.json`, each ~10 lines, zero logic, forwarding events to the MCP server
3. **One-time mode generation** — `crux init --tool claude-code` generates `.claude/agents/*.md` from `.crux/modes/`

That's the entire integration. Everything else is the MCP server's problem.

---

## The Architectural Shift

### Before: Adapter Model (Deprecated)

```
┌───────────────────┐     ┌──────────────────────┐
│    .crux/          │────▶│  sync_claude_code.sh  │────▶ .claude/agents/*.md
│  (source of truth) │     │  (full adapter)       │────▶ .claude/rules/*.md
│                    │     │  (tool-specific logic) │────▶ .claude/hooks/*.sh
└───────────────────┘     └──────────────────────┘
```

Problems: every tool needed a full adapter with format conversion logic. Adding a tool = writing hundreds of lines. Logic duplicated across adapters. Knowledge queries implemented per-tool. Maintenance nightmare.

### After: MCP-First Model (Current)

```
┌─────────────────────────────────────────────┐
│              Crux MCP Server                 │
│         (ALL logic lives here)               │
│                                              │
│  Knowledge, session, corrections, digest,    │
│  safety, modes, project context              │
│                                              │
│  Reads/writes: ~/.crux/ and .crux/           │
└──────────────┬──────────────────────────────┘
               │ MCP protocol (stdio)
    ┌──────────┼──────────────────┐
    │          │                  │
    ▼          ▼                  ▼
┌────────┐ ┌────────┐    ┌──────────────┐
│ Claude │ │OpenCode│    │Cursor/Cline/ │
│  Code  │ │        │    │Roo Code/etc  │
│        │ │        │    │              │
│ hooks: │ │plugins:│    │  MCP only    │
│ ~10 LOC│ │~10 LOC │    │ (no hooks)   │
│  each  │ │ each   │    │              │
└────────┘ └────────┘    └──────────────┘
```

Benefits: one codebase for all logic. Adding a tool = one MCP config line (+ optional hook shims). Knowledge queries, session state, corrections, safety — all handled by the server. Hooks contain zero logic.

---

## What the MCP Server Provides (Pull — LLM Calls Crux)

The Crux MCP Server exposes these tools to Claude Code via standard MCP protocol. Claude Code's LLM decides when to call them:

| MCP Tool | What It Does | Crux Concept |
|----------|-------------|--------------|
| `crux_lookup_knowledge(query, mode)` | Search knowledge base for relevant entries | Three-tier knowledge (project → user → public) |
| `crux_get_session_state()` | Resume where you left off after tool switch | Session state / tool switching |
| `crux_update_session(working_on, decision, file)` | Track progress, decisions, files touched | Session logging |
| `crux_get_mode_prompt(mode)` | Load canonical mode definition | 21 specialized modes |
| `crux_validate_script(content)` | Safety preflight on scripts/commands | Five-gate safety pipeline |
| `crux_get_digest()` | Daily self-assessment with analytics | Daily digest |
| `crux_write_handoff(context)` | Prepare for mode or tool switch | Mode handoffs |
| `crux_promote_knowledge(entry)` | Promote project knowledge → user level | Knowledge promotion pipeline |
| `crux_get_project_context()` | Auto-generated PROJECT.md | Project context detection |

This covers knowledge, session state, digest, safety validation, mode definitions, project context, and handoff management — roughly **60% of Crux's value**. One server. Every tool. Zero tool-specific logic.

---

## What Hook Shims Provide (Push — Crux Observes Events)

MCP is pull-only — the LLM calls you. But some capabilities require push — Crux needs to intercept events the LLM doesn't control. Claude Code's hook system enables this with paper-thin shims that forward to the MCP server.

### Why Hooks Are Necessary

1. **Correction detection** — Crux needs to see every user message to detect "no, wrong, actually." The LLM won't voluntarily call `crux_log_correction()` on itself.

2. **Safety interception** — The preflight validator needs to fire *before* a Bash command runs and block it if it fails. MCP can validate scripts when asked, but can't prevent execution.

3. **Session logging** — Every tool call and response needs to be captured for analytics. The LLM won't call `crux_log_interaction()` after every action.

4. **Compaction injection** — When context compresses, critical state (active work, mode, decisions) needs to survive. The LLM doesn't know compaction is happening.

5. **Auto-mode detection** — Detecting that a debugging conversation should trigger debug mode requires watching the conversation flow, not waiting to be called.

### The Hook Shims (Complete Claude Code Integration)

All hooks forward to the MCP server. Zero logic in the hooks themselves.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "crux mcp call crux_detect_correction --input \"$USER_PROMPT\"",
            "timeout": 5,
            "statusMessage": "Crux: checking for corrections..."
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "crux mcp call crux_validate_bash_command --input \"$TOOL_INPUT\"",
            "timeout": 10,
            "statusMessage": "Crux: safety preflight..."
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "crux mcp call crux_log_interaction --tool \"$TOOL_NAME\" --result \"$TOOL_RESULT\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "crux mcp call crux_inject_compaction_state",
            "timeout": 10,
            "statusMessage": "Crux: preserving state for compaction..."
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "crux mcp call crux_session_startup",
            "timeout": 15,
            "statusMessage": "Crux: loading session context..."
          }
        ]
      }
    ]
  }
}
```

That's it. Five hook entries. Each one is a single `crux mcp call` command. The MCP server handles all the intelligence — correction pattern matching, safety validation, session state management, compaction context generation, and startup digest.

---

## One-Time Mode Generation

The one thing MCP can't do is create native agent definitions in Claude Code's format. Claude Code expects subagent files at `.claude/agents/*.md` with specific frontmatter. This is handled once:

```bash
crux init --tool claude-code
```

This reads canonical mode definitions from `~/.crux/modes/` and generates:

```
.claude/agents/
├── build-py.md              # Python specialist
├── build-ex.md              # Elixir specialist
├── debug.md                 # Debugger
├── plan.md                  # Architect (read-only)
├── review.md                # Code reviewer (read-only)
├── test.md                  # TDD enforcement
├── security.md              # Security auditor
├── design-ui.md             # UI design
├── design-review.md         # Design review
├── design-system.md         # Design system
├── design-responsive.md     # Responsive design
├── design-accessibility.md  # Accessibility audit
├── writer.md                # Technical writer
├── analyst.md               # Data analyst
├── psych.md                 # Psychological support
├── legal.md                 # Legal reasoning
├── strategist.md            # Strategic planning
├── explain.md               # Teaching/explanation
├── infra-architect.md       # Infrastructure planning
├── ai-infra.md              # AI infrastructure
├── mac.md                   # macOS operations
└── docker.md                # Container operations
```

Each generated file maps Crux mode definitions to Claude Code subagent format:

```yaml
---
name: build-ex
description: Elixir/Phoenix/Ash development. Use when writing Elixir code, working with Phoenix controllers, Ash resources, or Ecto queries.
tools: Read, Write, Edit, Bash, Grep, Glob
disallowedTools: WebFetch
model: sonnet
permissionMode: default
maxTurns: 50
---

You are an Elixir specialist. Follow these principles:
[content from ~/.crux/modes/build-ex.md]

## Crux Integration
- Use crux_lookup_knowledge("elixir", "build-ex") for relevant patterns
- Session state is tracked via crux_update_session() — called automatically by hooks
- Corrections are detected automatically — no manual logging needed
- For mode handoffs, call crux_write_handoff() before switching
```

**This is a one-time generation.** If modes change in `~/.crux/modes/`, re-run `crux init --tool claude-code`. But the day-to-day intelligence — knowledge, corrections, session state, safety — all flows through the MCP server, not through these files.

---

## Concept-by-Concept Mapping (Updated for MCP-First)

### 1. MODES (21 specialized personas)

**Before**: Required full adapter to generate `.claude/agents/*.md` from `.crux/modes/`. Sync script ran on every mode change.

**After**: One-time generation via `crux init --tool claude-code`. Mode definitions are mostly static. The dynamic part — mode switching, handoff context, knowledge injection — happens through MCP tools (`crux_get_mode_prompt`, `crux_write_handoff`, `crux_lookup_knowledge`).

**What maps to Claude Code subagents:**
- System prompts → subagent markdown body
- Tool access constraints → `tools` / `disallowedTools` fields
- Model selection → `model` field (sonnet/opus/haiku)
- Read-only modes → `permissionMode: plan`

**What the MCP server handles that subagents can't:**
- Mode handoffs with context preservation (`crux_write_handoff`)
- Knowledge injection per-mode (`crux_lookup_knowledge` with mode filter)
- Mode usage tracking for analytics (`crux_log_interaction`)
- Auto-mode detection from conversation flow (SessionStart hook)

**Sampling parameters** (temperature, top_p): Claude Code still offers no per-subagent temperature control. This is a known limitation. Claude Code's effort level (low/medium/high) partially compensates.

**Verdict**: One-time setup + MCP handles the dynamic parts. Clean separation.

---

### 2. SCRIPTS-FIRST ARCHITECTURE

**Before**: Required PreToolUse hooks with embedded validation logic.

**After**: PreToolUse hook forwards to `crux_validate_bash_command`. The MCP server decides whether to block, warn, or allow. All validation logic lives server-side.

**Recommendation (unchanged)**: Make scripts-first optional and configurable. Claude's models are trustworthy enough for direct file edits. Use the safety pipeline for high-risk operations (deployment, database changes, multi-file refactoring), not for adding a comment.

**Verdict**: The hook is simpler now (one line, no logic). The MCP server makes the decision. Good architecture.

---

### 3. SAFETY PIPELINE (Seven-Stage)

**Before**: Implemented as a chain of Claude Code hooks — preflight, prompt audit, human approval, DRY_RUN — with logic spread across multiple shell scripts.

**After**: The PreToolUse hook calls `crux_validate_bash_command`. The MCP server runs the full pipeline internally:
1. Preflight validation
2. Test-spec check (TDD gate)
3. Security audit loop
4. Second opinion (if configured)
5. Human approval decision
6. DRY_RUN flag
7. Design validation (if applicable)

The hook just forwards the command. The MCP server returns `{allow: true}` or `{block: true, reason: "..."}`. All seven stages are the server's problem.

**Key advantage of MCP-first**: The adversarial audit can use a different model. The MCP server can call Ollama locally for a second opinion from a different model family — true architectural diversity. This was hard to do in the old hook-only approach.

**Verdict**: Dramatically simplified on the Claude Code side. All complexity lives where it belongs — in the server.

---

### 4. SESSION LOGGING

**Before**: Needed custom logging logic in hooks, writing to supplementary JSONL files.

**After**: PostToolUse hook calls `crux_log_interaction` on every tool call. SessionStart hook calls `crux_session_startup` which returns digest + injects prior state. The MCP server manages all logging in `.crux/sessions/` and `.crux/corrections/`.

**Claude Code's native logging** (transcript.jsonl) still exists and is still useful. Crux's logging is additive — it extracts structured correction patterns, tracks mode usage, and generates analytics that Claude Code doesn't.

**Verdict**: Clean complement to Claude Code's native logging. No conflict.

---

### 5. CORRECTION DETECTION

**Before**: Required a complex hook script that analyzed user messages for negation patterns, maintained sliding windows, and wrote structured reflections.

**After**: UserPromptSubmit hook calls `crux_detect_correction` with the user's message. The MCP server handles all pattern matching, context analysis, and reflection generation. Writes to `.crux/corrections/corrections.jsonl`. If a correction triggers knowledge generation, the server handles that too.

**This is still Crux's most unique contribution.** No other tool in the Claude Code ecosystem does correction detection. The MCP-first approach makes it cleaner — the detection logic is centralized and benefits every tool, not just Claude Code.

**Verdict**: ✅ Same high value. Simpler implementation.

---

### 6. KNOWLEDGE BASE (Organic, Three-Tier)

**Before**: Knowledge entries stored as `.claude/rules/` files. Promotion script moved entries between scopes. SessionStart hook injected relevant entries.

**After**: All knowledge operations are MCP tools:
- `crux_lookup_knowledge(query, mode)` — search with mode context
- `crux_promote_knowledge(entry)` — project → user → public promotion
- Knowledge generation happens server-side when corrections are detected

The LLM calls `crux_lookup_knowledge` when it needs project context, coding patterns, or prior corrections. The MCP server searches `.crux/knowledge/` (project-level) and `~/.crux/knowledge/` (user-level) and returns relevant entries.

**Cross-project learning**: Because knowledge lives in `~/.crux/knowledge/shared/`, corrections from a Python project can inform an Elixir project. This happens automatically — the MCP server searches all knowledge, not just project-scoped.

**Versus Claude Code's native memory**: Claude Code has `MEMORY.md` (manual, "remember to use Bun") and `CLAUDE.md` (static). Crux's knowledge is organic (generated from corrections), hierarchical (project → user → public), and cross-project. Completely different approach. Complementary.

**Verdict**: ✅ Still the highest-value Crux contribution. Now cleaner through MCP.

---

### 7. COMPACTION INJECTION

**Before**: Required a hook script that read state files and output critical context.

**After**: PreCompact hook calls `crux_inject_compaction_state`. The MCP server generates a context summary from `.crux/sessions/state.json` — active work, key decisions, files touched, pending tasks, mode context. This gets injected into the compacted context.

**Verdict**: Same value, simpler implementation. One MCP call replaces a custom script.

---

### 8. DAILY DIGEST / ANALYTICS

**Before**: SessionStart hook ran `daily-digest.sh` which parsed logs and generated reports.

**After**: SessionStart hook calls `crux_session_startup`. The MCP server generates the digest from `.crux/corrections/`, `.crux/sessions/`, and `~/.crux/analytics/`. Returns: correction rates, mode usage, knowledge promotion candidates, tool switching history, actionable recommendations.

**New capability**: Because the MCP server tracks sessions across ALL tools, the digest now includes cross-tool analytics. "You switched between Claude Code and OpenCode 3 times today. Most corrections happened in Claude Code during Elixir work. Consider reviewing build-ex mode definition."

**Verdict**: ✅ Higher value than before because of cross-tool visibility.

---

### 9. MODE HANDOFFS

**Before**: Required a `/handoff` skill that wrote context to a file, and a target subagent that read it.

**After**: The LLM calls `crux_write_handoff(context)` before switching modes/subagents. The MCP server writes the handoff to `.crux/sessions/handoff.md`. The target subagent's instructions tell it to call `crux_get_session_state()` on startup, which includes the handoff context.

**Tool-to-tool handoffs**: The same mechanism handles switching from Claude Code to OpenCode. `crux switch opencode` updates `.crux/sessions/state.json` with the handoff, and OpenCode's MCP connection reads it on startup. Mode handoffs and tool handoffs use the same MCP tools.

**Verdict**: ✅ Unified handoff mechanism for both mode switching and tool switching.

---

### 10. PROJECT CONTEXT (PROJECT.md)

**Before**: Required a `/init-project` skill with detection scripts.

**After**: The LLM calls `crux_get_project_context()`. The MCP server generates/returns the project context from `.crux/context/PROJECT.md`, including detected tech stack, hot files, recent changes, and directory structure.

**Verdict**: Same value, cleaner access. The project context is an MCP resource, not a generated file.

---

### 11. TOOL HIERARCHY

**Before**: Complex hook logic to enforce "try MCP first, fall back to Bash."

**After**: Documented in the generated CLAUDE.md as guidance. Claude's instruction-following is strong enough that prompt-based guidance works. The MCP server's `crux_validate_bash_command` can suggest alternatives ("Consider using the MCP tool instead of raw bash for this").

**Verdict**: Prompt-based guidance + MCP suggestion. No enforcement hooks needed.

---

### 12. TOKEN BUDGETS / THINK ROUTING / MODEL MANAGEMENT

**Still not applicable.** Token budgets aren't enforceable in Claude Code. Think/no-think routing is a Qwen-specific optimization. Model management is API-only in Claude Code.

**What IS relevant from the model management concept**: The MCP server could suggest model switches. "This task is complex — consider using opus for this subagent." But this is guidance, not enforcement.

**Verdict**: ❌ Skip. Same as before.

---

## Complete Claude Code Integration (What to Build)

### Step 1: Register MCP Server

Add to Claude Code's MCP config (`.claude/mcp.json` or equivalent):

```json
{
  "mcpServers": {
    "crux": {
      "command": "crux",
      "args": ["mcp", "serve"],
      "env": {
        "CRUX_PROJECT": ".",
        "CRUX_USER": "~/.crux"
      }
    }
  }
}
```

One entry. This gives Claude Code access to all 10+ MCP tools.

### Step 2: Generate Hook Shims

```bash
crux init --tool claude-code
```

This generates:
- `.claude/hooks.json` — the 5 hook entries shown above (UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, SessionStart)
- `.claude/agents/*.md` — 21 subagent mode definitions from `~/.crux/modes/`

### Step 3: There Is No Step 3

That's the entire integration. The MCP server handles everything else.

---

## What Gets Deleted (vs. the Old Approach)

| Old Approach | Replaced By | Status |
|---|---|---|
| `sync_claude_code.sh` adapter | `crux init --tool claude-code` (one-time) | **Deleted** |
| Claude Code-specific plugin logic | Crux MCP Server | **Deleted** |
| Hook scripts with embedded validation logic | Hook shims → MCP server calls | **Deleted** |
| `.claude/rules/` knowledge files | MCP `crux_lookup_knowledge` | **Deleted** |
| Supplementary JSONL logging scripts | MCP `crux_log_interaction` | **Deleted** |
| Daily digest shell script | MCP `crux_session_startup` | **Deleted** |
| Correction detection shell script | MCP `crux_detect_correction` | **Deleted** |
| Handoff context file management | MCP `crux_write_handoff` / `crux_get_session_state` | **Deleted** |

Everything that was a shell script or adapter is now an MCP server function. The only Claude Code-specific artifacts that remain are:
1. `.claude/hooks.json` (5 shim entries)
2. `.claude/agents/*.md` (21 mode definitions, one-time generated)
3. `.claude/mcp.json` (MCP server registration)

---

## Value Assessment (Updated)

### What Crux Adds to Claude Code (Through MCP)

1. **Correction detection + organic knowledge** — Still the #1 unique contribution. No other tool in the Claude Code ecosystem does this. Now cleaner through MCP.

2. **Cross-tool session continuity** — NEW. You can switch between Claude Code and OpenCode mid-project. The MCP server maintains the bridge. This was impossible in the old adapter model.

3. **Self-assessment / daily digest** — Now with cross-tool analytics. The MCP server sees all tools, not just Claude Code.

4. **21 specialized modes with handoffs** — Richer than before (expanded from 15). Handoffs now use the same MCP mechanism as tool switching.

5. **Seven-stage safety pipeline** — Fully server-side. Can use different model families for adversarial audit (Ollama locally for diversity). The hook just forwards; the server decides.

6. **Cross-project learning** — Knowledge promoted to `~/.crux/knowledge/shared/` is available in every project, across every tool. Compound learning.

### What Crux Doesn't Add (Same as Before)

1. Sampling parameter control (Claude Code limitation)
2. Token budget enforcement (not feasible)
3. Model registry (API-only in Claude Code)
4. Tool hierarchy enforcement (prompt guidance sufficient)

### What's NEW in MCP-First That Didn't Exist Before

1. **One-line tool onboarding** — adding Crux to any new tool = registering the MCP server
2. **Cross-tool correction learning** — correction in Cursor improves Claude Code
3. **Unified handoff protocol** — mode switches and tool switches use the same mechanism
4. **Cross-tool analytics** — digest shows how you work across all tools
5. **Adversarial diversity** — MCP server can call Ollama for second opinion from different model family

---

## Migration Priority (Updated)

### Phase 1: MCP Foundation (Immediate)

1. Build Crux MCP Server (Python, stdlib + MCP SDK)
2. Implement core MCP tools: `crux_lookup_knowledge`, `crux_get_session_state`, `crux_update_session`, `crux_get_mode_prompt`, `crux_get_project_context`
3. `crux init --tool claude-code` generates hooks.json + agents/*.md
4. Test: Claude Code connects, can query knowledge, can load modes

### Phase 2: Correction Detection + Learning (Unique Value)

5. Implement `crux_detect_correction` in MCP server
6. Implement correction → knowledge generation pipeline
7. Implement `crux_promote_knowledge` for promotion pipeline
8. Implement `crux_get_digest` for session startup analytics
9. Test: Corrections detected across sessions, knowledge accumulates

### Phase 3: Safety + Handoffs (Graduated Value)

10. Implement `crux_validate_bash_command` (full seven-stage pipeline)
11. Implement `crux_write_handoff` for mode/tool switching
12. Implement `crux_inject_compaction_state` for context preservation
13. Test: Risky commands caught, handoffs preserve context, compaction survives

### Phase 4: Cross-Tool + Cross-Project (Ecosystem Value)

14. Test `crux switch` between Claude Code and OpenCode
15. Cross-project knowledge aggregation
16. Cross-tool analytics in daily digest
17. Community knowledge sharing infrastructure

---

## The Simplicity Argument

The old approach required:
- A full adapter per tool (~200-400 lines each)
- Tool-specific hook scripts with embedded logic
- Format conversion for knowledge, modes, and state
- Maintenance when any tool changed their format

The MCP-first approach requires:
- One MCP server (shared across all tools)
- One config line per tool (MCP registration)
- ~50 lines of hook shims per tool with hook support
- One-time mode generation per tool

Adding Cursor support goes from "write a full adapter" to "add Crux to `.cursor/mcp.json`." Adding Windsurf support? Same thing. Adding whatever AI coding tool launches next month? Same thing.

The MCP server is the product. The integrations are trivial.
