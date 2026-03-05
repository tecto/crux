# Crux → Claude Code: Deep Integration Analysis

## Executive Summary

Claude Code already has native equivalents for roughly 60% of what Crux does — but the implementations differ significantly. The remaining 40% represents genuine value that Crux can bring. This document maps every Crux concept to Claude Code's architecture, identifies what's redundant, what's additive, and where the real opportunity lies.

---

## The Fundamental Architectural Difference

**Crux was designed for dumb pipes.** OpenCode + Ollama gives you a capable but unguided LLM. Crux fills the gap with modes, safety gates, knowledge management, and self-improvement — all enforced by code because the model can't be trusted to self-regulate.

**Claude Code is an opinionated product.** It already has a permission system, subagents, skills, hooks, context management, and session persistence. It ships with Anthropic's models (Sonnet, Opus, Haiku) which are instruction-following by design.

This means: some Crux concepts are solving problems Claude Code doesn't have, while others address gaps Claude Code genuinely has.

---

## Concept-by-Concept Mapping

### 1. MODES (15 specialized personas)

**Crux**: 15 mode files, each with a system prompt (~120-155 tokens), tool access constraints, think/no-think routing, and sampling parameters. Switching via `/mode <name>`.

**Claude Code equivalent**: **Subagents** — the closest native concept.

```
.claude/agents/
├── build-py.md      # Python development specialist
├── build-ex.md      # Elixir/Ash specialist
├── debug.md         # Debugging specialist
├── plan.md          # Architecture planning (read-only)
├── review.md        # Code review (read-only)
├── psych.md         # Psychological support
└── ... (15 total)
```

Each subagent `.md` file supports:

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
1. Ash First — always prefer Ash resources over raw Ecto.
2. Pattern matching everywhere — destructure in function heads.
3. Immutability mindset — never mutate state.
4. Use LiveView for interactive features.
5. All file modifications go through scripts in .opencode/scripts/.
```

**What maps well:**
- System prompts → subagent markdown body
- Tool access constraints → `tools` / `disallowedTools` fields
- Model selection → `model` field (sonnet/opus/haiku)
- Read-only modes → `permissionMode: plan`

**What DOESN'T map:**
- **Sampling parameters** (temperature, top_p, top_k): Claude Code offers NO per-subagent temperature control. You get model selection (haiku/sonnet/opus) and effort level (low/medium/high), but not fine-grained sampling. This is a real loss for modes where Crux specifically tuned temp 0.6 vs 0.7.
- **Think/no-think routing**: Claude's models don't have Qwen's `/think` and `/no_think` directives. Extended thinking is controlled by `alwaysThinkingEnabled` globally or effort level, not per-mode. However, Claude's effort level (low/medium/high) on Sonnet/Opus 4.6 serves a similar purpose.
- **Automatic mode switching**: Claude Code delegates to subagents automatically based on task description, but there's no explicit `/mode debug` command. You'd need to create skills that trigger subagent delegation.
- **Mode handoffs with context**: Subagents have isolated context windows. When a subagent finishes, only its summary returns to the main conversation. Crux's handoff-context.md mechanism doesn't have a direct equivalent.

**Verdict**: ⚠️ **Partially redundant, partially additive.** Subagents cover ~70% of modes. The missing 30% (sampling control, think routing, explicit mode switching with context transfer) represents genuine Crux value. The mode handoff mechanism is particularly valuable — Claude Code subagents lose context when they return.

**Recommendation**: Implement modes as subagents, but add a skill (`/mode`) that manages mode state and writes handoff context to a shared file that subagents read on startup.

---

### 2. SCRIPTS-FIRST ARCHITECTURE

**Crux**: All file modifications go through templated scripts in `.opencode/scripts/`. Scripts have headers (risk level, status, description), support DRY_RUN, and go through the five-gate pipeline.

**Claude Code equivalent**: **No direct equivalent.** Claude Code lets the model use Write/Edit tools directly. There's no script-intermediary layer.

**However**, Claude Code has:
- **PreToolUse hooks** that fire before every Edit/Write/Bash call
- **Permission system** that can require approval for file modifications
- **Sandbox filesystem** that restricts where writes can go

**What this means**: You could enforce scripts-first via hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/enforce-scripts-first.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

The hook script would check if the write target is inside `.opencode/scripts/` (allowed) or a project file (blocked with feedback: "Use a script instead").

**Verdict**: ✅ **Genuinely additive.** Scripts-first is a discipline that Claude Code doesn't impose. The PreToolUse hook mechanism makes it enforceable. This is one of Crux's strongest contributions.

**But consider**: Is scripts-first actually better with Claude Code? Claude's models are significantly more capable than Qwen 32B at following instructions. The scripts-first pattern was designed partly because local models can't be trusted — Claude can. The overhead of templating, validating, and auditing every file change might slow down a workflow that Claude Code handles well natively.

**Recommendation**: Make scripts-first **optional and configurable** rather than mandatory. Use it for high-risk operations (database changes, deployment, multi-file refactoring) but let Claude Code handle simple file edits directly. The five-gate pipeline adds clear value for risky operations; it's overhead for adding a comment to a file.

---

### 3. FIVE-GATE SCRIPT EXECUTION PIPELINE

**Crux**: Gate 1 (preflight) → Gate 2 (8B adversarial audit) → Gate 3 (32B second opinion) → Gate 4 (human approval) → Gate 5 (DRY_RUN)

**Claude Code equivalent**: Partially covered by hooks + permissions.

- **Gate 1 (preflight)**: Implementable as a PreToolUse hook on Bash tool
- **Gate 2 (adversarial audit)**: Implementable as a `type: "prompt"` hook — Claude Code can use a separate model to evaluate scripts
- **Gate 3 (second opinion)**: Same mechanism, `type: "agent"` hook with different prompt
- **Gate 4 (human approval)**: Native — Claude Code's permission system already asks for approval on Bash commands
- **Gate 5 (DRY_RUN)**: Implementable as a PreToolUse hook that modifies the command to prepend `DRY_RUN=true`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/preflight-check.sh",
            "statusMessage": "Running pre-flight validation..."
          },
          {
            "type": "prompt",
            "prompt": "You are a security auditor. Analyze this script for: data loss, corruption, unintended side effects, scope creep. Assume it's WRONG until proven safe. Script: $ARGUMENTS. If safe, respond {\"ok\": true}. If concerns, respond {\"ok\": false, \"reason\": \"details\"}.",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Verdict**: ✅ **Additive and implementable.** The five-gate pipeline is a genuine safety innovation. Claude Code's hooks can implement all five gates. The adversarial audit (using a separate model to red-team scripts) is particularly valuable because it catches things the primary model misses due to self-enhancement bias.

**Key difference**: In Crux, Gate 2 uses the 8B model (different architecture = different biases). In Claude Code, the `type: "prompt"` hook uses Claude's own model family. You could mitigate this by using haiku for audit (different capability level = different failure modes), but it's the same model family. For true adversarial diversity, you'd need an MCP server that calls a different model (e.g., calling Ollama locally).

---

### 4. SESSION LOGGING

**Crux**: JSONL append-only logging of every interaction, tool call, correction, mode switch. Crash recovery from checkpoints. Resume context.

**Claude Code equivalent**: **Already built-in.**

Claude Code stores session transcripts at:
```
~/.claude/projects/<project>/<session-id>/transcript.jsonl
```

It includes: full conversation history, tool calls, file snapshots for rewinding, subagent transcripts.

Session management: `/continue` resumes last session. `--fork-session` creates a branch.

**What Crux adds beyond Claude Code's native logging:**
- Structured correction entries (reflections with wrong_approach/correct_approach)
- Mode tracking per interaction
- Script creation tracking
- Checkpoint updates every 5 interactions
- Resume context markdown for human-readable recovery

**Verdict**: ⚠️ **Mostly redundant.** Claude Code's session persistence is more robust than what Crux builds from scratch. The JSONL format, crash recovery, and resumption are all native.

**What's genuinely additive**: The structured correction/reflection entries. Claude Code doesn't extract learning patterns from sessions. A PostToolUse hook could write correction entries to a supplementary JSONL, but the correction detection logic itself (analyzing conversation for negation/redirection patterns) would need to be a hook script.

---

### 5. CORRECTION DETECTION

**Crux**: Plugin watches for negation language ("no," "wrong," "actually"), model self-correction ("sorry," "let me fix"), tool retries, and script audit failures. Writes structured reflections to JSONL.

**Claude Code equivalent**: **No native equivalent.** Claude Code doesn't track when users correct it or extract patterns from corrections.

**Implementation path**: Two approaches:

**Approach A: PostToolUse hook** — After every tool call, log tool name and result. After every user message (via UserPromptSubmit hook), scan for correction patterns. Write reflections to a supplementary log.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/detect-corrections.sh"
          }
        ]
      }
    ]
  }
}
```

**Approach B: External service** — HTTP hook that receives all interactions, maintains sliding window in memory, and detects correction patterns server-side.

**Verdict**: ✅ **Genuinely additive.** This is one of Crux's strongest unique contributions. No other Claude Code tooling does this.

---

### 6. KNOWLEDGE BASE (Organic, Three-Tier)

**Crux**: Project → user → public knowledge entries, automatically generated from correction patterns, with promotion pipeline.

**Claude Code equivalent**: **Partial overlap with auto-memory.**

Claude Code has:
- `~/.claude/projects/<project>/memory/MEMORY.md` — auto-memory that Claude writes to when asked to "remember" something
- `CLAUDE.md` at multiple scopes (project, user, managed)
- `.claude/rules/` for path-specific knowledge

**What Crux adds:**
- **Automatic knowledge generation** from correction patterns (no manual "remember" needed)
- **Promotion pipeline** (project → user → public) with privacy checks
- **Cross-project learning** (corrections in Project A help Project B)
- **Confidence scoring** based on correction count

**Verdict**: ✅ **Significantly additive.** Claude Code's memory is manual ("remember to use Bun"). Crux's knowledge base is organic (learns from mistakes automatically). The promotion pipeline and cross-project learning have no Claude Code equivalent.

**Implementation**: Knowledge entries stored as `.claude/rules/` files (they load automatically based on path patterns). Promotion script moves entries from project rules to user-level rules. A SessionStart hook injects relevant knowledge entries.

---

### 7. TOOL HIERARCHY (5 Tiers)

**Crux**: LSP → Custom Tools → MCP → Library Scripts → New Scripts → Raw Bash

**Claude Code equivalent**: **Partially native.**

Claude Code has:
- **MCP servers** (Tier 2 equivalent) — full native support
- **Built-in tools** (Read, Write, Edit, Bash, etc.) — not tiered
- **Skills** — can guide tool selection but don't enforce hierarchy
- **Hooks** — can block tools (PreToolUse) to enforce constraints

**What's missing:**
- **LSP integration** as Tier 0 — Claude Code doesn't natively use LSP for code intelligence (it uses Grep/Read instead). However, LSP servers can be added via MCP.
- **Tiered enforcement** — No mechanism to say "try MCP first, fall back to Bash only if MCP fails"
- **Script promotion** — No concept of promoting one-off scripts to reusable library status

**Verdict**: ⚠️ **Partially additive.** The hierarchy concept is sound, but enforcement in Claude Code would require complex hook logic that inspects tool calls and suggests alternatives. A simpler approach: document the hierarchy in CLAUDE.md and trust Claude's instruction-following (which is strong with Anthropic models).

**Recommendation**: Don't enforce the hierarchy mechanically. Instead, put it in CLAUDE.md as guidance. Claude Code's models are much better at following instructions than Qwen 32B, so prompt-based guidance works where code-based enforcement was needed before.

---

### 8. COMPACTION INJECTION

**Crux**: Plugin injects critical context (scripts, mode, decisions, handoff context) into compaction summary.

**Claude Code equivalent**: **Native hook support.**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "cat .claude/critical-context.md"
          }
        ]
      }
    ]
  }
}
```

Also: `PreCompact` hook fires before compaction starts, and `InstructionsLoaded` fires when CLAUDE.md reloads (which happens after compaction).

**Verdict**: ✅ **Implementation mechanism exists natively.** Crux's specific logic (preserving script paths, mode context, key decisions) is additive — Claude Code doesn't auto-generate this critical context. But the hook mechanism to inject it is already there.

---

### 9. TOKEN BUDGET ENFORCEMENT

**Crux**: Per-mode token budgets, soft warnings at 70-80%, read-only enforcement in plan/review modes.

**Claude Code equivalent**: **Partial.**

- **Read-only enforcement**: Subagents with `permissionMode: plan` or `disallowedTools: Write, Edit` handle this natively
- **Token budgets**: Claude Code has NO mechanism for per-interaction token budgets. You can't track or limit how many tokens a response uses.
- **Context window management**: Auto-compaction at ~95% capacity

**What's additive**: Token budget awareness. A PreToolUse hook could track cumulative tool output size and inject warnings, but can't enforce hard limits.

**Verdict**: ⚠️ **Partially additive.** Read-only enforcement is native. Token budgets are novel but hard to implement without access to token counts. Consider whether this is even necessary — Claude Code's models manage context more efficiently than local models, and auto-compaction handles runaway usage.

---

### 10. THINK/NO-THINK ROUTING

**Crux**: Automatically prepends `/think` or `/no_think` to Qwen messages based on mode.

**Claude Code equivalent**: **Not directly applicable.**

Claude's models don't use `/think` directives. Instead, they have:
- **Extended thinking** (`alwaysThinkingEnabled: true/false`) — global toggle
- **Effort level** (low/medium/high) — per-session, affects reasoning depth
- **Model selection** — haiku (fast/shallow) vs sonnet (balanced) vs opus (deep)

The closest mapping: use `model: haiku` for execution-focused subagents (equivalent to no_think) and `model: opus` for reasoning-heavy subagents (equivalent to think).

**Verdict**: ❌ **Not applicable.** This is a Qwen-specific optimization. Drop it for Claude Code.

---

### 11. DAILY DIGEST / ANALYTICS

**Crux**: Daily session startup shows mode usage, correction rates, tool tier usage, knowledge promotion candidates, escalated items, actionable recommendations.

**Claude Code equivalent**: **No native equivalent.**

**Implementation path**: A SessionStart hook that runs `generate-digest.sh`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/daily-digest.sh"
          }
        ]
      }
    ]
  }
}
```

The script reads from supplementary logs (correction entries, tool usage), generates a digest, and outputs it to stdout (which gets injected into Claude's context).

**Verdict**: ✅ **Genuinely additive.** Self-assessment and daily reporting is a novel capability. The SessionStart hook mechanism makes it clean.

---

### 12. MODE HANDOFFS

**Crux**: suggest_handoff tool writes context to handoff-context.md, new mode reads it, preserves continuity.

**Claude Code equivalent**: **No native equivalent.** Subagents have isolated contexts. When a subagent returns, only its summary goes back to the main conversation.

**Implementation path**: A skill (`/handoff`) that:
1. Writes current context to `.claude/handoff-context.md`
2. Suggests which subagent to delegate to
3. The target subagent's SKILL.md includes `@.claude/handoff-context.md`

**Verdict**: ✅ **Genuinely additive.** Context-preserving mode switches are a significant workflow improvement.

---

### 13. PROJECT CONTEXT (PROJECT.md)

**Crux**: Auto-generated PROJECT.md with tech stack, directory structure, key files, naming conventions, recent changes.

**Claude Code equivalent**: **Partially covered by CLAUDE.md + auto-memory.**

Claude Code reads CLAUDE.md at session start. You can put project context there. Auto-memory (`MEMORY.md`) accumulates project knowledge over time.

**What Crux adds**: Automated regeneration. CLAUDE.md is static until manually updated. Crux's `/init-project` script dynamically detects tech stack, hot files, and recent changes.

**Verdict**: ⚠️ **Partially additive.** The auto-detection is nice but Claude Code figures out project structure by reading files. The real value is the "hot files" tracking (which files were modified most recently), which helps Claude focus on relevant code.

**Recommendation**: Implement as a skill (`/init-project`) that generates/updates CLAUDE.md programmatically.

---

### 14. MODEL MANAGEMENT / GRACEFUL DEGRADATION

**Crux**: Model registry, auto-discovery, auto-evaluation, hardware-aware recommendations, cloud fallback.

**Claude Code equivalent**: **Not applicable in the same way.**

Claude Code uses Anthropic's API models exclusively. There's no local model management, no Ollama, no quantization decisions. Model selection is limited to haiku/sonnet/opus with effort levels.

**What IS relevant**: The graceful degradation concept. When a task is too hard for sonnet, suggest switching to opus. When opus isn't enough, suggest breaking the task down.

**Verdict**: ❌ **Mostly not applicable.** Claude Code's model selection is simpler. The degradation concept has some value but the implementation is completely different.

---

### 15. CONTINUOUS LEARNING (5 Levels)

**Crux**: Interaction → session → cross-session → cross-project → ecosystem learning, with threshold-triggered processing.

**Claude Code equivalent**: **Auto-memory is the only overlap.**

Claude Code's auto-memory captures things when you say "remember this." It doesn't:
- Automatically detect and learn from corrections
- Aggregate patterns across sessions
- Promote knowledge across projects
- Generate new mode suggestions from drift detection
- Process learning in the background continuously

**Verdict**: ✅ **Highly additive.** This is Crux's most unique and valuable contribution. Implementation would involve:
- PostToolUse/UserPromptSubmit hooks for correction detection
- SessionStart hooks for digest generation
- A background service (or scheduled task) for cross-session analysis
- Shared files in `~/.claude/` for cross-project knowledge

---

## What Crux Should Become for Claude Code

Based on this analysis, Crux for Claude Code should be a **plugin** (Claude Code's native plugin system) that provides:

### High Value (Build These)

1. **Correction Detection Engine** — PostToolUse + UserPromptSubmit hooks that detect corrections and write structured reflections. Nothing else does this.

2. **Knowledge Base with Organic Generation** — Rules files auto-generated from correction patterns, with promotion pipeline. Transforms Claude Code's manual memory into automatic learning.

3. **Daily Digest** — SessionStart hook showing correction rates, knowledge candidates, tool usage patterns, and actionable recommendations.

4. **Mode System** — 15 subagent definitions with handoff context management. Skills for `/mode <name>` switching and `/handoff` context transfer.

5. **Safety Pipeline for Risky Operations** — PreToolUse hooks that validate Bash commands with escalating gates (preflight → prompt audit → human approval). Not for every file edit, but for deployment, database changes, and multi-file operations.

### Medium Value (Consider Building)

6. **Compaction Context Injection** — SessionStart hook with "compact" matcher that preserves critical operational context.

7. **Project Context Auto-Generation** — Skill that generates/updates CLAUDE.md with detected tech stack, hot files, and recent changes.

8. **Scripts-First for High-Risk Ops** — Optional discipline enforced by hooks for operations classified as medium/high risk.

### Low Value (Skip or Simplify)

9. ~~Think/No-Think Routing~~ — Not applicable to Claude's models.

10. ~~Token Budget Enforcement~~ — Claude Code manages context better natively. Auto-compaction handles runaway usage.

11. ~~Model Registry/Auto-Discovery~~ — Claude Code uses API models only.

12. ~~Hardware-Aware Quantization~~ — No local models to optimize.

13. ~~Tool Hierarchy Enforcement~~ — Put in CLAUDE.md as guidance; Claude follows instructions well enough that code enforcement isn't needed.

---

## Proposed Plugin Structure

```
crux/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── agents/
│   ├── build-py.md              # Python specialist
│   ├── build-ex.md              # Elixir specialist
│   ├── debug.md                 # Debugger
│   ├── plan.md                  # Architect (read-only)
│   ├── review.md                # Code reviewer (read-only)
│   ├── writer.md                # Technical writer
│   ├── analyst.md               # Data analyst
│   ├── psych.md                 # Psychological support
│   ├── legal.md                 # Legal reasoning
│   ├── strategist.md            # Strategic planning
│   ├── explain.md               # Teaching/explanation
│   ├── infra-architect.md       # Infrastructure planning
│   ├── ai-infra.md              # AI infrastructure
│   ├── mac.md                   # macOS operations
│   └── docker.md                # Container operations
├── skills/
│   ├── mode/SKILL.md            # /mode <name> — switch modes
│   ├── handoff/SKILL.md         # /handoff — transfer context
│   ├── init-project/SKILL.md    # /init-project — generate context
│   ├── digest/SKILL.md          # /digest — show daily analytics
│   └── review-knowledge/SKILL.md # /review-knowledge — manage KB
├── hooks/
│   ├── hooks.json               # Hook configuration
│   └── scripts/
│       ├── correction-detector.sh
│       ├── daily-digest.sh
│       ├── compaction-context.sh
│       ├── safety-preflight.sh
│       └── audit-log.sh
├── rules/
│   └── crux-defaults.md         # Default behavioral rules
├── templates/
│   ├── script-template.sh
│   └── knowledge-entry.md
└── README.md
```

---

## Does It Actually Improve Claude Code?

**Yes, in specific ways:**

1. **Learning from mistakes** — Claude Code has no mechanism to learn from corrections between sessions. Crux's correction detection + knowledge generation is genuinely novel and valuable.

2. **Self-assessment** — Claude Code doesn't tell you how it's performing. Daily digests with correction rates and tool usage patterns provide actionable self-improvement data.

3. **Specialized personas** — While Claude Code has subagents, pre-built specialized agents for 15 domains (with researched prompts, tool constraints, and behavioral rules) save significant setup effort.

4. **Safety for risky operations** — Claude Code's permission system is binary (allow/deny). The five-gate pipeline with adversarial audit adds graduated, intelligent safety.

5. **Context continuity** — Mode handoffs with context transfer solve a real pain point in Claude Code's subagent architecture.

**No, in other ways:**

1. **Scripts-first for simple edits** — Overhead without proportional safety gain. Claude Code's models are trustworthy enough for direct file edits.

2. **Token budgets** — Claude Code's context management is already good. Adding artificial limits creates friction without clear benefit.

3. **Tool hierarchy enforcement** — Prompt-based guidance works with Claude's models. Code enforcement is unnecessary overhead.

4. **Model management** — Not relevant for Claude Code's API-based architecture.

---

## Migration Priority

If Bryan wants to bring Crux to Claude Code, build in this order:

**Phase 1: Foundation** (Immediate value)
- 15 subagent definitions (modes)
- `/mode` skill for switching
- CLAUDE.md with Crux behavioral rules
- Basic hook infrastructure (audit logging)

**Phase 2: Learning** (Unique value)
- Correction detection hooks
- Knowledge entry generation
- Daily digest on session startup
- Knowledge promotion pipeline

**Phase 3: Safety** (Graduated value)
- Pre-flight validation hook for Bash commands
- Prompt-based adversarial audit for risky operations
- Handoff context management

**Phase 4: Ecosystem** (Long-term value)
- Cross-project knowledge aggregation
- Mode drift detection
- Community knowledge sharing
- Plugin marketplace distribution
