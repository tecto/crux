# Crux Ecosystem Integration Analysis (MCP-First Architecture)

## What This Document Covers

A deep technical analysis of how Crux integrates with every major AI coding tool under the MCP-first architecture. The fundamental shift: **all Crux logic lives in one MCP server.** Tool integrations reduce to registering the MCP server (one config line) plus optional paper-thin hook shims for tools that support event interception. This document covers Claude Code, OpenCode, Aider, Continue.dev, Cursor, Cline, Windsurf, Roo Code, Goose, Amp, and Zed.

---

## The Architecture

```
┌─────────────────────────────────────────────┐
│              Crux MCP Server                 │
│         (ALL logic lives here)               │
│                                              │
│  Knowledge, session, corrections, digest,    │
│  safety, modes, project context, handoffs    │
│                                              │
│  Reads/writes: ~/.crux/ and .crux/           │
│                                              │
│  MCP Tools:                                  │
│  ├─ crux_lookup_knowledge(query, mode)       │
│  ├─ crux_get_session_state()                 │
│  ├─ crux_update_session(working_on, ...)     │
│  ├─ crux_detect_correction(input)            │
│  ├─ crux_get_mode_prompt(mode_name)          │
│  ├─ crux_validate_script(content)            │
│  ├─ crux_validate_bash_command(command)      │
│  ├─ crux_get_digest()                        │
│  ├─ crux_write_handoff(context)              │
│  ├─ crux_promote_knowledge(entry)            │
│  ├─ crux_get_project_context()               │
│  └─ crux_log_interaction(tool, result)       │
│                                              │
│  MCP Resources:                              │
│  ├─ crux://modes/{mode_name}                 │
│  ├─ crux://knowledge/{scope}/{topic}         │
│  ├─ crux://digest/today                      │
│  └─ crux://project-context                   │
│                                              │
│  MCP Prompts:                                │
│  ├─ crux_mode_system_prompt                  │
│  ├─ crux_safety_audit                        │
│  └─ crux_correction_analysis                 │
└──────────────┬──────────────────────────────┘
               │ MCP protocol (stdio/HTTP)
    ┌──────────┼──────────┼──────────┐
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│ Claude │ │OpenCode│ │  Roo   │ │ Cursor/  │
│  Code  │ │        │ │  Code  │ │ Cline/   │
│        │ │        │ │        │ │ Continue/│
│hooks + │ │plugins+│ │ MCP +  │ │ Windsurf/│
│  MCP   │ │  MCP   │ │ modes  │ │ Goose/   │
│        │ │        │ │        │ │ Zed/Aider│
│ FULL   │ │ FULL   │ │ FULL   │ │          │
│FEATURE │ │FEATURE │ │FEATURE │ │ MCP-ONLY │
└────────┘ └────────┘ └────────┘ └──────────┘
```

### Three Integration Tiers

| Tier | What It Means | Crux Value | Tools |
|------|--------------|------------|-------|
| **Full (MCP + hooks)** | MCP server + paper-thin hook shims for event interception | 100% — all Crux capabilities including push-based correction detection, safety interception, session logging, compaction injection | Claude Code, OpenCode |
| **Enhanced (MCP + native modes)** | MCP server + tool's own mode system | ~85% — knowledge, safety, learning, digest, plus native mode integration. Correction detection is pull-based (LLM calls it) rather than push-based (hook fires automatically) | Roo Code |
| **Standard (MCP only)** | MCP server registration only | ~60% — knowledge, session state, modes, safety validation, digest, project context. No automatic correction detection or safety interception (LLM must choose to call these) | Cursor, Cline, Continue, Windsurf, Goose, Zed, Aider (when MCP ships) |

The key insight: **even Standard tier (MCP-only) gives 60%+ of Crux's value with one config line.** The remaining 40% (push-based correction detection, automatic safety interception, session logging, compaction injection) requires hooks — but most tools will get hooks eventually, and the MCP server is ready when they do.

---

## The Landscape (Updated)

| Tool | Open Source | Local Models | Hook System | MCP Support | Crux Tier | Integration Effort |
|------|-----------|-------------|-------------|-------------|-----------|-------------------|
| **Claude Code** | No | No (API) | 20 hook events | Yes | **Full** | 1 MCP config + 5 hook shims |
| **OpenCode** | Yes | Yes (Ollama) | Event plugins | Yes | **Full** | 1 MCP config + thin plugins |
| **Roo Code** | Yes | Yes | MCP-based | Yes | **Enhanced** | 1 MCP config + mode mapping |
| **Cursor** | No | Workaround | Cursor Hooks | Yes | **Standard** | 1 MCP config |
| **Cline** | Yes | Yes (Ollama) | User approval | Yes | **Standard** | 1 MCP config |
| **Continue.dev** | Yes | Yes (Ollama) | MCP-based | Yes | **Standard** | 1 MCP config |
| **Windsurf** | No | No | Cascade Hooks | Yes | **Standard+** | 1 MCP config (Cascade hooks could enable Full) |
| **Goose** | Yes | Yes | MCP-first | Yes | **Standard** | 1 MCP config |
| **Zed** | Yes | Via agents | Slash commands | Yes | **Standard** | 1 MCP config |
| **Aider** | Yes | Yes (Ollama) | None | Pending (#4506) | **Standard (future)** | 1 MCP config (when available) |
| **Amp** | No | No | Subagent API | Limited | **Blocked** | Watch for MCP support |

**The standout finding remains unchanged**: No tool in the ecosystem has correction detection, organic knowledge generation, or continuous self-improvement. This is Crux's unique value proposition across every integration target.

---

## What MCP Handles vs. What Hooks Handle

### MCP (Pull — LLM Calls Crux) — Available to ALL Tools

| Capability | MCP Tool | Value |
|-----------|---------|-------|
| Knowledge search | `crux_lookup_knowledge(query, mode)` | LLM queries for relevant patterns, corrections, project knowledge |
| Session resumption | `crux_get_session_state()` | Resume after tool switch — decisions, files, pending tasks |
| Session tracking | `crux_update_session(working_on, decision, file)` | Track progress across interactions |
| Mode definitions | `crux_get_mode_prompt(mode)` | Load specialized persona for current task |
| Safety validation | `crux_validate_script(content)` | Run seven-stage pipeline on a script/command |
| Daily digest | `crux_get_digest()` | Self-assessment with analytics |
| Handoff context | `crux_write_handoff(context)` | Prepare for mode or tool switch |
| Knowledge promotion | `crux_promote_knowledge(entry)` | Promote project knowledge → user level |
| Project context | `crux_get_project_context()` | Auto-detected tech stack, hot files, structure |

### Hooks (Push — Crux Observes Events) — Only Full-Tier Tools

| Capability | Why Hooks Needed | What It Does |
|-----------|-----------------|-------------|
| Correction detection | LLM won't call `crux_detect_correction()` on itself | Hook fires on every user message, detects negation/redirection patterns |
| Safety interception | MCP can validate but can't *prevent* execution | Hook fires before Bash/Edit, blocks if pipeline fails |
| Session logging | LLM won't log every interaction automatically | Hook fires after every tool call, captures for analytics |
| Compaction injection | LLM doesn't know compaction is happening | Hook fires before context compression, preserves critical state |
| Auto-mode detection | Requires watching conversation flow | Hook detects debugging conversation → suggests debug mode |

**The hooks are paper-thin shims** — 5-10 lines each, zero logic. They forward events to the MCP server, which does all the work. Example (Claude Code):

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "crux mcp call crux_detect_correction --input \"$USER_PROMPT\""
      }]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "crux mcp call crux_validate_bash_command --input \"$TOOL_INPUT\""
      }]
    }]
  }
}
```

---

## Tool-by-Tool Analysis (Updated for MCP-First)

### Claude Code — Full Tier

**Integration**: 1 MCP config entry + 5 hook shims (UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, SessionStart). One-time mode generation via `crux init --tool claude-code` produces `.claude/agents/*.md`.

**What's changed from adapter model**: Everything that was a shell script with embedded logic is now a one-line `crux mcp call`. The hook scripts with validation logic, the sync adapters, the format converters — all deleted. The MCP server handles it.

**What Crux adds**: Correction detection, organic knowledge, daily digest, seven-stage safety pipeline, 21 modes with handoffs, cross-project learning, cross-tool session continuity.

**What Claude Code already does well**: Session persistence, subagent architecture, permission system, auto-compaction. Don't replicate these.

**Unique advantage of Claude Code integration**: 20 hook events is the richest hook system in the ecosystem. This means Full tier with complete push-based capabilities. Correction detection is automatic, not dependent on the LLM choosing to call it.

See `crux-claude-code-analysis.md` for the detailed concept-by-concept mapping.

---

### OpenCode — Full Tier

**Integration**: 1 MCP config entry + thin event plugins (correction detection, safety gate, session logging). The existing OpenCode plugins are refactored from containing Crux logic to being thin shims that forward to the MCP server.

**What's changed**: The current OpenCode plugins (JS tools with embedded knowledge lookup, correction detection, safety validation) are being rewritten. All logic moves to the MCP server. The plugins become ~10-line event forwarders.

**What Crux adds**: Same as Claude Code — correction detection, organic knowledge, safety pipeline, modes, handoffs, cross-project learning.

**What OpenCode already does well**: Local model support via Ollama, custom modes, MCP integration. OpenCode is the primary development environment for Crux itself.

**Unique advantage**: OpenCode is open source and Crux's home environment. The integration can go deeper than any other tool because both sides are modifiable.

---

### Roo Code — Enhanced Tier (Highest Synergy)

**Integration**: 1 MCP config entry. No hook shims needed (Roo Code doesn't have a hook system that maps cleanly). But Roo Code has something better: **a full custom modes system that is architecturally almost identical to Crux's.**

```yaml
# .roo/modes/build-ex.yaml
name: Elixir Builder
slug: build-ex
roleDefinition: |
  You are an Elixir specialist...
groups:
  - read
  - edit
  - command
customInstructions: |
  Always use pattern matching. Prefer Ash resources over raw Ecto.
```

**What this means for integration**: Crux's 21 mode definitions in `~/.crux/modes/` can be converted to Roo Code's YAML format via `crux init --tool roo-code`. But the dynamic intelligence — knowledge lookup, correction detection, session state, safety validation — all flows through the MCP server.

**What Crux adds**: Safety pipeline (Roo Code has basic approval only), correction detection, organic knowledge base, daily digest, cross-project learning, cross-tool session continuity (switch between Roo Code and Claude Code seamlessly).

**What Roo Code already does well**: Custom modes with tool access control, mode switching, subtask spawning in alternate modes, per-mode model selection. Roo Code has the best native modes system of any tool.

**Why Enhanced tier, not Standard**: Roo Code's modes system means Crux modes are natively rendered, not just injected via MCP prompts. The LLM operates in a properly scoped mode context. This is better than Standard tier tools where modes are just MCP-provided context.

**Correction detection limitation**: Without hooks, correction detection is pull-based. The LLM can call `crux_detect_correction`, but won't do so automatically when the user corrects it. This could be partially mitigated by instructing Roo Code modes to call `crux_detect_correction` when they detect user frustration — but it's not as reliable as a push-based hook.

**Recommendation**: Roo Code is the second-highest-priority integration after Claude Code. The native modes alignment plus Crux's unique capabilities (learning, safety, knowledge) creates the most complete AI operating system in the open-source ecosystem.

---

### Aider — Standard Tier (When MCP Ships)

**What's changed from adapter model**: The entire wrapper/fork approach is **deprecated**. No more `CruxAiderWrapper` class wrapping Aider's unsupported Python API. No more process-level interception. When Aider ships MCP support (open issue #4506), Crux becomes an MCP server that Aider calls. One config line. Done.

**What Crux adds via MCP**: Knowledge lookup (Aider starts every session fresh — Crux carries knowledge forward), mode-specific system prompts (Aider only has 3 modes vs Crux's 21), project context beyond repo map, safety validation, daily digest.

**What Aider already does well (don't replicate)**:
- **Git integration** — Auto-commit, undo, diff. Best in class.
- **Repo map** — Tree-sitter AST analysis. Superior to file listing.
- **Lint/test loops** — Auto-lint, auto-test, fix-retry cycles. Already tight.
- **Multi-model routing** — LiteLLM handles 75+ providers.
- **Edit formats** — Search/replace blocks with fuzzy matching.

**Correction detection limitation**: MCP-only (Standard tier). No hooks. The LLM would need to voluntarily call `crux_detect_correction`, which it won't do reliably. Correction learning for Aider will be less effective than for Claude Code or OpenCode.

**Workaround**: Document Crux modes and knowledge as Aider's `--read` files. Aider can read `.crux/knowledge/` entries as context files. Not as clean as MCP, but works today without waiting for MCP support.

**Recommendation**: Wait for MCP support (#4506). In the meantime, publish a "Crux + Aider" workflow guide showing how to use `.crux/knowledge/` files with Aider's `--read` flag for knowledge injection.

---

### Cursor — Standard Tier

**Integration**: 1 MCP config entry in `.cursor/mcp.json`. Crux modes can also be mapped to `.cursor/rules/*.mdc` files via `crux init --tool cursor` for one-time generation.

**What Crux adds via MCP**: Organic knowledge (Cursor has no memory system), correction detection (pull-based), daily digest, cross-project knowledge, session state for tool switching.

**What Cursor already does well**: Agent mode with multi-step planning, rules-based behavior, large MCP ecosystem (1800+ servers).

**Limitation**: Closed-source. Can't go deeper than MCP + rules. But MCP is sufficient for 60%+ of Crux's value.

**Unique opportunity**: Cursor has the largest user base of any AI coding tool. Even Standard tier integration reaches millions of developers. The marketing angle: "Add Crux intelligence to Cursor in 30 seconds — one line in your MCP config."

---

### Continue.dev — Standard Tier

**Integration**: 1 MCP config entry. Continue already has full MCP support with three transport types (stdio, HTTP, SSE).

**What Crux adds**: Modes (Continue has none), correction learning (Continue has basic memory MCP only), safety pipeline.

**What Continue already does**: Model routing, context providers, slash commands, .prompt file sharing.

**Integration effort**: Minimal. MCP is native and well-documented in Continue.

---

### Cline — Standard Tier

**Integration**: 1 MCP config entry. Cline has full MCP support and can even auto-create MCP servers.

**What Crux adds**: Modes, organic learning, safety pipeline beyond binary approve/deny.

**What Cline already does**: User-in-the-loop approval for every action, MCP marketplace, gRPC protocol buffers.

**Integration effort**: Minimal. Cline's MCP system is actively maintained.

---

### Windsurf — Standard+ Tier

**Integration**: 1 MCP config entry. But Windsurf has an interesting advantage: **Cascade Hooks** (pre-prompt, post-response, transcript logging) could potentially enable Full tier integration if they expose the right event interception points.

**What Crux adds**: Organic learning (Windsurf has no correction detection), cross-project knowledge, mode system.

**What Windsurf already does**: SOC 2 compliant audit logging, pre-prompt filtering, full transcript collection, team rules.

**Unique angle**: Windsurf's enterprise focus means Crux's safety pipeline and audit trail would resonate with its user base. The seven-stage safety pipeline + Windsurf's compliance logging = strong enterprise story.

**Recommendation**: Investigate Cascade Hooks for Full tier capability. If they support user-message interception and pre-execution blocking, Windsurf could get push-based correction detection and safety interception.

---

### Goose — Standard Tier

**Integration**: 1 MCP config entry. Goose is MCP-first by design — every extension is an MCP server. Crux is a natural Goose extension.

**What Crux adds**: Modes, safety pipeline (Goose uses Docker isolation instead of script validation), correction learning, knowledge base.

**What Goose already does**: Docker containerization for safety, MCP-first extensibility, AAIF compliance.

**Integration effort**: Very low. Goose expects MCP servers.

**Interesting comparison**: Goose's Docker isolation vs. Crux's seven-stage pipeline are complementary approaches to safety. Docker isolates the execution environment. Crux validates the intent before execution. Both together = defense in depth.

---

### Zed — Standard Tier

**Integration**: 1 MCP config entry. Zed supports MCP servers and custom slash commands via extensions.

**What Crux adds**: Modes, safety pipeline, correction learning, knowledge base.

**What Zed already does**: Agent Communication Protocol (ACP), slash commands, growing MCP support.

**Integration effort**: Low via MCP path. Extensions require Rust + Wasm compilation (higher effort, more capability).

---

### Amp — Blocked

**Integration**: Not feasible today. Amp is closed-source with a proprietary subagent system and limited MCP support.

**Recommendation**: Watch for MCP support. When it ships, Crux connects with one config line like any other tool.

---

## What's Genuinely Unique About Crux (Unchanged — No Tool Has These)

### 1. Automatic Correction Detection
No tool tracks when users correct it. No tool extracts structured reflections. No tool builds knowledge from mistakes. **Still Crux's #1 differentiator.**

### 2. Organic Knowledge Generation
Every tool's "memory" is manual. Crux generates knowledge automatically from correction clusters, promotes across projects, and surfaces in digests. **No equivalent anywhere.**

### 3. Daily Self-Assessment Digest
No tool generates analytics about its own performance. Now enhanced: cross-tool analytics show how you work across Claude Code, OpenCode, Cursor, etc.

### 4. Cross-Project Learning
Tools are project-siloed. Crux's three-tier knowledge (project → user → public) with automated promotion is unique. Under MCP-first, this is a single server operation — knowledge generated in any tool, in any project, is accessible everywhere.

### 5. Seven-Stage Safety Pipeline
Most tools have binary safety. Crux's graduated pipeline (preflight → test-spec → security-audit → second-opinion → human-approval → DRY_RUN → design-validation) is the most sophisticated in the ecosystem. Now fully server-side with adversarial diversity (MCP server can call different model families via Ollama).

### 6. Cross-Tool Session Continuity
**NEW — only possible under MCP-first.** No tool lets you switch between coding tools mid-project without losing context. `crux switch <tool>` captures session state and the next tool picks up where the last left off. This capability doesn't exist anywhere else because nobody else has a tool-agnostic intelligence layer.

### 7. Mode Handoffs with Context
Even Roo Code (excellent modes) loses context on mode switch. Crux's handoff mechanism preserves continuity across both mode transitions and tool transitions. Under MCP-first, mode handoffs and tool handoffs use the same MCP tools.

---

## Strategic Recommendations (Updated)

### Priority 1: Build the Crux MCP Server
One Python server (stdlib + MCP SDK) that exposes all `.crux/` operations as MCP tools, resources, and prompts. This is the product. Everything else is configuration.

### Priority 2: Claude Code Integration (Full Tier)
Claude Code's 20 hook events enable complete push-based capabilities. Five hook shims + MCP registration = 100% of Crux's value. This is where you dogfood the full experience.

### Priority 3: OpenCode Integration (Full Tier)
Refactor existing plugins from embedded logic to thin MCP forwarders. OpenCode is Crux's home environment and the primary local development tool.

### Priority 4: Roo Code Integration (Enhanced Tier)
Highest synergy in the ecosystem. Native modes alignment + Crux's unique capabilities = the most complete open-source AI operating system. `crux init --tool roo-code` generates YAML mode files.

### Priority 5: Cursor/Continue/Cline (Standard Tier)
These tools have large user bases and native MCP support. The generic MCP server works with zero tool-specific adaptation. One config line each. Publish "Add Crux to [tool] in 30 seconds" tutorials for each one.

### Priority 6: Aider (Standard Tier — When MCP Ships)
Wait for #4506. In the meantime, publish workflow guide using `.crux/knowledge/` with Aider's `--read` flag.

### What NOT to Build
- ~~Tool-specific adapters~~ — **Deleted.** One MCP server replaces all of them.
- ~~Wrapper classes around tools~~ — **Deleted.** No more `CruxAiderWrapper`.
- ~~Format conversion sync scripts~~ — **Deleted.** Only `crux init --tool X` for one-time mode generation.
- Don't replicate git integration (Aider does it best)
- Don't replicate repo map / AST analysis (Aider's tree-sitter is excellent)
- Don't replicate model routing (LiteLLM handles this)
- Don't replicate lint/test loops (Aider and Claude Code handle these)
- Don't build IDE-specific extensions when MCP works

---

## Onboarding: `crux adopt` (Mid-Session Capture)

A critical practical concern: most developers won't discover Crux at the start of a fresh project. They'll find it mid-session, hours or days into a codebase. The cold-start problem kills adoption if you have to "start over" to get value.

`crux adopt` solves this with a two-phase capture:

**Phase 1: Mechanical capture** (the script does this automatically):
- Init `.crux/` structure
- Parse git log → files touched, commit messages as decisions
- Detect project tech stack → generate PROJECT.md
- Import existing CLAUDE.md / `.cursor/rules/` / `.opencode/` configs into `.crux/`
- Set up `.claude/mcp.json` (or equivalent) for next session
- Sync agents from `~/.crux/modes/`

**Phase 2: LLM brain dump** (the current session's LLM writes its own context):
- Handoff context: what it was working on, what decisions were made and why
- Session state: pending tasks, files touched, key architectural choices
- Knowledge entries: patterns discovered, corrections that happened, conventions established
- The LLM knows things git log doesn't — this is the richest possible context capture

After `crux adopt`, the current session exits cleanly. The next session starts with the Crux MCP server + hooks active, seeded with rich context from the adopt capture. No cold start. No lost context.

This is the adoption path for every tool in the ecosystem: you don't have to start a new project. You adopt Crux into wherever you already are.

---

## The Vision (Updated)

Crux isn't an alternative to any of these tools. It's the **intelligence layer** that sits underneath all of them.

You code with Claude Code, OpenCode, Cursor, Roo Code, or Aider depending on the task. The Crux MCP Server runs in the background, accumulating knowledge from your corrections, validating your commands against the safety pipeline, tracking your session state, and generating daily self-assessments.

When you switch tools — `crux switch opencode` after a morning in Claude Code, or `crux switch cursor` for a quick UI tweak — your intelligence follows you. Same knowledge. Same corrections. Same context. Different tool.

When you discover Crux mid-project — `crux adopt` captures everything the current session knows, and the next session starts with full Crux intelligence from day one.

The MCP server is the brain. The tools are interchangeable hands.

One server. Every tool. All your intelligence in `.crux/`.
