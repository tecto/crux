# Crux Ecosystem Integration Analysis

## What This Document Covers

A deep technical analysis of how Crux's concepts map onto every major AI coding tool, what's redundant, what's additive, and where Crux should focus its energy. This covers Aider, Claude Code, Continue.dev, Cursor, Cline, Windsurf, Roo Code, Goose, Amp, and Zed.

---

## The Landscape at a Glance

| Tool | Open Source | Local Models | Hook/Plugin System | Custom Modes | MCP Support | Correction Learning |
|------|-----------|-------------|-------------------|-------------|-------------|-------------------|
| **Claude Code** | No | No (API only) | 20 hook events | Subagents | Yes | No |
| **Aider** | Yes | Yes (Ollama) | None | Architect/Code/Ask | Community only | No |
| **Continue.dev** | Yes | Yes (Ollama) | MCP-based | No | Yes (full) | Memory MCP only |
| **Cursor** | No | Workaround | Cursor Hooks | Rules-based | Yes | No |
| **Cline** | Yes | Yes (Ollama) | User approval | No | Yes (full) | No |
| **Windsurf** | No | No | Cascade Hooks | Rules-based | Yes | No |
| **Roo Code** | Yes | Yes | MCP-based | **Yes (full)** | Yes | No |
| **Goose** | Yes | Yes | MCP-first | No | Yes (core) | No |
| **Amp** | No | No | Subagent API | Subagents | Limited | No |
| **Zed** | Yes | Via agents | Slash commands | No | Yes | No |

The standout finding: **no tool in the ecosystem has correction detection, organic knowledge generation, or continuous self-improvement**. This is Crux's unique value proposition across every integration target.

---

## AIDER — Deep Analysis

### Architecture Summary

Aider is a Python CLI tool centered on a `Coder` class that orchestrates: user input → repo map (tree-sitter AST) → LLM call → file edits → git commit. It uses LiteLLM as a model abstraction layer, supporting 75+ providers including Ollama.

Three chat modes: Code (direct edits), Architect (two-stage: reason then edit), Ask (information only, no edits).

### What Crux Concepts Map To

| Crux Concept | Aider Equivalent | Gap? |
|-------------|-----------------|------|
| 15 Modes | Code/Architect/Ask (3 modes) | **Massive gap** — only 3 modes, no customization |
| Scripts-first | No equivalent | **Full gap** — Aider edits files directly |
| Five-gate pipeline | No equivalent | **Full gap** — no safety validation layer |
| Session logging | Basic (LiteLLM logging) | **Partial gap** — no structured JSONL, no corrections |
| Correction detection | No equivalent | **Full gap** |
| Knowledge base | No equivalent | **Full gap** |
| Tool hierarchy | No equivalent | **Full gap** — no tool tiering concept |
| Compaction injection | Summarization thread | **Partial** — background summarization exists, no injection |
| Think routing | N/A (model-dependent) | Not applicable |
| Daily digest | No equivalent | **Full gap** |
| Mode handoffs | No equivalent | **Full gap** |
| Project context | Repo map (tree-sitter) | **Partial** — repo map is excellent but different purpose |
| Model management | LiteLLM registry | **Covered** — LiteLLM handles model routing well |
| Git integration | Excellent (auto-commit, undo) | **No gap** — Aider's git integration is best-in-class |
| Lint/test loops | Excellent (auto-lint, auto-test) | **No gap** — tight feedback loops already exist |

### The Core Problem with Aider Integration

**Aider has no extensibility system.** No hooks, no plugins, no custom commands, no interception points. The Python API exists but is unsupported and undocumented.

This means Crux can't plug into Aider the way it plugs into Claude Code (hooks) or OpenCode (plugins). Integration requires one of:

1. **Wrapper approach** — Crux wraps Aider, intercepting at the process level
2. **MCP bridge** — When Aider gets native MCP support (open issue #4506), Crux becomes an MCP server
3. **Fork approach** — Fork Aider, add Crux integration points into the coder loop
4. **Watch-files mode** — Use Aider's file watching to trigger Crux actions via file-system signaling

### Recommended Integration: The Wrapper

The most practical approach today:

```
┌──────────────────────────────┐
│       Crux Orchestrator       │
│  (Python process wrapping     │
│   Aider's Python API)         │
├──────────────────────────────┤
│  Pre-call hooks:              │
│  - Mode-specific system prompt│
│  - Knowledge injection        │
│  - Project context injection  │
│                               │
│  Post-call hooks:             │
│  - Correction detection       │
│  - Session logging            │
│  - Script extraction          │
│                               │
│  Periodic:                    │
│  - Digest generation          │
│  - Knowledge promotion        │
│  - Mode drift detection       │
├──────────────────────────────┤
│       Aider Coder API         │
│  (Unsupported but functional) │
└──────────────────────────────┘
```

```python
from aider.coders import Coder
from aider.models import Model

class CruxAiderWrapper:
    def __init__(self, mode="build-py"):
        self.mode = mode
        self.knowledge = KnowledgeBase()
        self.logger = SessionLogger()
        self.correction_detector = CorrectionDetector()

    def run(self, instruction):
        # Pre-call: inject mode prompt + knowledge
        system_prompt = self.load_mode_prompt(self.mode)
        knowledge_context = self.knowledge.query(instruction, self.mode)

        enriched_instruction = f"{knowledge_context}\n\n{instruction}"

        # Call Aider
        coder = Coder.create(
            model=Model(self.select_model()),
            fnames=self.active_files,
        )
        response = coder.run(enriched_instruction)

        # Post-call: detect corrections, log session
        self.logger.log_interaction(instruction, response, self.mode)
        correction = self.correction_detector.analyze(instruction, response)
        if correction:
            self.knowledge.add_reflection(correction)
```

### What Crux Adds to Aider

1. **Specialized modes** — Aider's 3 modes become 15+, each with domain-specific prompts and constraints
2. **Safety pipeline** — Pre-flight validation before Aider commits changes (Aider auto-commits aggressively)
3. **Correction learning** — Track when Aider makes mistakes, build knowledge base
4. **Project context beyond repo map** — Hot files, recent decisions, naming conventions
5. **Cross-session knowledge** — Aider starts every session fresh; Crux carries knowledge forward

### What Aider Already Does Well (Don't Replicate)

1. **Git integration** — Auto-commit, undo, diff. Best in class. Don't wrap this.
2. **Repo map** — Tree-sitter AST analysis for context. Superior to Crux's file-listing approach.
3. **Lint/test loops** — Auto-lint, auto-test, fix-retry cycles. Already tight.
4. **Multi-model routing** — LiteLLM handles 75+ providers. Don't rebuild model management.
5. **Edit formats** — Search/replace blocks with fuzzy matching. Don't touch the editing layer.

### Aider Integration Verdict

**Integration difficulty: HIGH.** No extensibility system means everything is external wrapping. The Python API is unsupported. MCP support is pending. Fork maintenance is expensive.

**Value of integration: MEDIUM-HIGH.** Aider has a large user base (13.5K+ GitHub stars) and excellent foundations (git, lint, repo map). Crux fills genuine gaps (modes, safety, learning). But the integration friction is significant.

**Recommendation**: Wait for native MCP support (#4506), then integrate as an MCP server. In the meantime, document a "Crux + Aider" workflow guide that uses Crux's knowledge base and digest system alongside Aider as a standalone tool.

---

## Tool-by-Tool Integration Assessment

### Continue.dev

**Integration path**: MCP server. Continue already has full MCP support with three transport types (stdio, HTTP, SSE). Crux becomes a Continue MCP server exposing: knowledge lookup, correction logging, mode-specific context injection, safety validation.

**What Crux adds**: Modes (Continue has none), correction learning (Continue has basic memory MCP only), safety pipeline (Continue has no tool interception).

**What Continue already does**: Model routing, context providers, slash commands, .prompt file sharing.

**Integration difficulty: LOW.** MCP is native. Build one MCP server, plug in.

**Value: MEDIUM.** Continue's user base is growing but smaller than Aider or Cursor.

---

### Cursor

**Integration path**: MCP server + .cursor/rules. Cursor supports MCP servers (1800+ in ecosystem) and has a rules system (.cursor/rules/*.mdc). Crux modes could map to Cursor rules files. Safety pipeline via Cursor Hooks (pre/post execution interception).

**What Crux adds**: Organic learning (Cursor has no memory system), correction detection, daily digest, cross-project knowledge.

**What Cursor already does**: Agent mode with multi-step planning, rules-based behavior modification, MCP integration.

**Limitation**: Cursor is closed-source. Deep integration is impossible. Surface-level integration via MCP + rules is the ceiling.

**Integration difficulty: LOW-MEDIUM.** MCP is native, but rules require manual mapping. Can't modify Cursor internals.

**Value: HIGH.** Cursor has massive market share. Even surface-level Crux integration reaches many users.

---

### Cline

**Integration path**: MCP server (Cline has full MCP support, can even auto-create MCP servers). Crux becomes an MCP server that Cline calls for knowledge, safety validation, and correction logging.

**What Crux adds**: Modes (Cline has none), organic learning, safety pipeline beyond user-approval (Cline's safety is binary approve/deny).

**What Cline already does**: User-in-the-loop approval for every action, MCP marketplace, gRPC protocol buffers for type-safe communication.

**Integration difficulty: LOW.** Cline's MCP system is well-documented and actively maintained.

**Value: MEDIUM.** Cline has a solid user base. The approval system is a natural fit for Crux's safety pipeline concepts.

---

### Windsurf

**Integration path**: MCP server + Cascade Hooks alignment. Windsurf has the most sophisticated hook system in the ecosystem (pre-prompt, post-response, transcript logging). Crux's safety pipeline concepts are already partially implemented by Windsurf natively.

**What Crux adds**: Organic learning (Windsurf has no correction detection), cross-project knowledge, mode system beyond simple rules.

**What Windsurf already does**: SOC 2 compliant audit logging, pre-prompt filtering, full transcript collection, team customization rules.

**Limitation**: Closed-source. Integration limited to MCP.

**Integration difficulty: LOW.** MCP is supported. Cascade Hooks do some of Crux's work already.

**Value: MEDIUM.** Windsurf's enterprise focus means Crux's safety pipeline would resonate with its user base.

---

### Roo Code — THE MOST RELEVANT TOOL

**Integration path**: Native mode system + MCP. Roo Code already has a **full custom modes system** that is architecturally almost identical to Crux's:

```yaml
# .roo/modes/build-ex.yaml
name: Elixir Builder
slug: build-ex
roleDefinition: |
  You are an Elixir specialist. Follow Ash First principles...
groups:
  - read
  - edit
  - command
customInstructions: |
  Always use pattern matching. Prefer Ash resources over raw Ecto.
```

**What Crux adds**: Safety pipeline (Roo Code has basic approval only), correction detection (no equivalent), organic knowledge base (no equivalent), daily digest, cross-project learning.

**What Roo Code already does**: Custom modes with tool access control, mode switching, subtask spawning in alternate modes, per-mode model selection, YAML configuration.

**This is the highest-synergy integration target.** Roo Code has already solved the modes problem. Crux's unique value (learning, safety, knowledge) fills Roo Code's genuine gaps.

**Integration difficulty: LOW.** Open source (Apache 2.0), MCP-native, YAML config matches Crux's approach.

**Value: VERY HIGH.** Roo Code's modes system + Crux's learning system = the most complete AI operating system in the ecosystem.

---

### Goose

**Integration path**: MCP server (Goose is MCP-first by design). Every Goose extension is an MCP server. Crux becomes a Goose extension.

**What Crux adds**: Modes (Goose has none), safety pipeline (Goose uses Docker isolation instead), correction learning, knowledge base.

**What Goose already does**: Docker containerization for safety, MCP-first extensibility, AAIF compliance.

**Integration difficulty: VERY LOW.** Goose expects MCP servers. Build one, register it.

**Value: MEDIUM.** Goose is well-designed but smaller user base. Docker isolation is an interesting alternative to Crux's script-validation approach.

---

### Amp

**Integration path**: Limited. Amp is closed-source with a proprietary subagent system. No MCP support documented. Integration would require Amp to expose extension points.

**What Crux adds**: Knowledge persistence (Amp subagents are ephemeral), correction learning, mode customization.

**What Amp already does**: Sophisticated subagent architecture (Finder, Oracle, Librarian, Kraken), context isolation, 200K token window management.

**Integration difficulty: HIGH.** Closed-source, limited extensibility.

**Value: LOW for now.** Watch for MCP support.

---

### Zed

**Integration path**: Slash commands + MCP server. Zed supports custom slash commands via extensions (Rust + Wasm) and MCP servers. Crux could be a Zed extension providing /crux-mode, /crux-knowledge, /crux-digest commands.

**What Crux adds**: Modes, safety pipeline, correction learning, knowledge base.

**What Zed already does**: Agent Communication Protocol (ACP) for external agent integration, slash commands, MCP support.

**Integration difficulty: MEDIUM.** Extensions require Rust + Wasm compilation. MCP path is simpler.

**Value: MEDIUM.** Zed is growing but still niche.

---

## The Universal Integration Layer: MCP

The clearest pattern across all tools: **MCP is the universal extensibility protocol.** Every tool either supports it natively or has it on their roadmap.

This means Crux's optimal form factor for multi-tool integration is:

```
┌─────────────────────────────────────────────┐
│              Crux MCP Server                 │
│                                              │
│  Tools exposed:                              │
│  ├─ crux_lookup_knowledge(mode, query)       │
│  ├─ crux_log_interaction(data)               │
│  ├─ crux_detect_correction(before, after)    │
│  ├─ crux_get_mode_prompt(mode_name)          │
│  ├─ crux_get_project_context(project_path)   │
│  ├─ crux_validate_script(script_content)     │
│  ├─ crux_get_digest()                        │
│  ├─ crux_promote_knowledge(entry, from, to)  │
│  └─ crux_suggest_handoff(from_mode, context) │
│                                              │
│  Resources exposed:                          │
│  ├─ crux://modes/{mode_name}                 │
│  ├─ crux://knowledge/{scope}/{topic}         │
│  ├─ crux://digest/today                      │
│  └─ crux://project-context/{project}         │
│                                              │
│  Prompts exposed:                            │
│  ├─ crux_mode_system_prompt                  │
│  ├─ crux_safety_audit                        │
│  └─ crux_correction_analysis                 │
└─────────────────────────────────────────────┘
         │
    Connects to ANY tool via MCP:
    ├─ Claude Code (native MCP)
    ├─ Continue.dev (native MCP)
    ├─ Cursor (native MCP)
    ├─ Cline (native MCP)
    ├─ Windsurf (native MCP)
    ├─ Roo Code (native MCP)
    ├─ Goose (MCP-first)
    ├─ Zed (MCP via extensions)
    └─ Aider (pending MCP support)
```

One MCP server. Every tool in the ecosystem.

---

## What's Genuinely Unique About Crux (Across All Tools)

After researching every major tool, these Crux capabilities exist in **none of them**:

### 1. Automatic Correction Detection
No tool tracks when users correct it. No tool extracts structured reflections from correction patterns. No tool builds knowledge from mistakes. This is Crux's single most differentiating capability.

### 2. Organic Knowledge Generation
Every tool's "memory" is manual ("remember this"). Crux generates knowledge entries automatically from correction clusters, promotes them across projects, and surfaces them in daily digests. No equivalent anywhere.

### 3. Daily Self-Assessment Digest
No tool generates analytics about its own performance. Correction rates, mode usage patterns, tool tier distribution, escalated recommendations — none of this exists elsewhere.

### 4. Cross-Project Learning
Tools are project-siloed. Corrections in Project A don't help Project B. Crux's three-tier knowledge scope (project → user → public) with automated promotion is unique.

### 5. Graduated Safety Pipeline
Most tools have binary safety: approve or deny. Crux's five-gate pipeline (preflight → adversarial audit → second opinion → human approval → dry run) with risk-based escalation is the most sophisticated safety architecture in the ecosystem. Windsurf's Cascade Hooks come closest but lack the adversarial audit concept.

### 6. Mode Handoffs with Context
Even Roo Code (which has excellent modes) loses context on mode switch. Crux's handoff-context.md mechanism for preserving continuity across mode transitions is unique.

---

## Strategic Recommendations

### Priority 1: Build the Crux MCP Server
One MCP server that exposes knowledge lookup, correction logging, mode prompts, safety validation, digest generation, and project context. This instantly integrates with 8 of 9 tools researched.

### Priority 2: Deep Integration with Roo Code
Roo Code is the highest-synergy target. It already has modes. Crux adds learning, safety, and knowledge. The combination is the most complete AI operating system possible. Consider contributing Crux features directly to Roo Code or building a Crux plugin for Roo Code.

### Priority 3: Claude Code Plugin
Claude Code has the most sophisticated hook system (20 events) and the best model quality. Crux as a Claude Code plugin gets maximum feature expressiveness. Build this alongside the MCP server (they share the same backend).

### Priority 4: Aider Wrapper (When MCP Lands)
Aider has the largest open-source user base. Wait for native MCP support, then integrate via the MCP server. In the meantime, publish a "Crux + Aider" workflow guide.

### Priority 5: Cursor/Continue MCP Integration
These tools have large user bases and native MCP support. The generic Crux MCP server works here with no tool-specific adaptation.

### What NOT to Build
- Don't build tool-specific plugins for every tool. Build one MCP server.
- Don't replicate git integration (Aider does it best).
- Don't replicate repo map / AST analysis (Aider's tree-sitter is excellent).
- Don't replicate model routing (LiteLLM handles this).
- Don't replicate lint/test loops (Aider and Claude Code handle these).
- Don't build a custom IDE or editor integration. Use MCP.

---

## The Vision

Crux isn't an alternative to any of these tools. It's a **learning layer** that sits alongside whichever tool you use. You code with Aider, Claude Code, Cursor, or Roo Code. Crux watches, learns from your corrections, builds knowledge, generates safety checks, and carries that intelligence forward across sessions, projects, and tools.

The end state: you switch from Cursor to Claude Code to Aider depending on the task, and Crux ensures your accumulated knowledge, safety rules, and mode preferences follow you everywhere.
