# Crux Ecosystem — Competitive Analysis

**Date:** March 2026

---

## The Ecosystem: Three Products, Three Competitive Lanes

The Crux ecosystem is three separate, tightly integrated products. Each competes in a distinct lane. Understanding this structure is the foundation of the analysis.

```
┌──────────────────────────────────────────────────────────────┐
│                      Crux Ecosystem                           │
│                                                               │
│  Crux (platform)       CruxCLI (agent)      CruxDev (method) │
│  ─────────────         ──────────────       ────────────────  │
│  Intelligence layer    Hard fork of          Autonomous        │
│  Modes, MCP server,    OpenCode              convergence       │
│  Safety pipeline,      Crux-native           framework         │
│  Continuous learning   terminal agent        16 skills +       │
│  Cross-tool continuity `cruxcli` binary      engine           │
│                                                               │
│  Lane: Platform/OS     Lane: Terminal agent  Lane: Agentic    │
│  Competitor: none      Competitor: OpenCode  methodology      │
│  (new category)        (125k stars)          Competitor:      │
│                                              Superpowers      │
│                                              (98.8k stars)    │
└──────────────────────────────────────────────────────────────┘
```

The products interlock: Crux is the intelligence layer. CruxCLI is the runtime that absorbs Crux natively. CruxDev is the convergence methodology that runs inside any agent, including CruxCLI. Each can be adopted independently, but together they form a system designed to surpass any single competing tool.

**Development status as of March 2026:**
- **Crux**: Shipped. 1,561+ tests, 100% coverage enforced, 37-tool MCP server, 24 modes, MIT
- **CruxCLI**: Hard fork plan written; v0.1 bridge plugin complete and in dogfooding; hard fork not yet started
- **CruxDev**: Design document complete (~1,700 lines); implementation not yet started

---

## Competitor Map

| Competitor | Stars | Competes With | Lane |
|-----------|-------|--------------|------|
| OpenCode | 125k | CruxCLI | Terminal AI coding agent |
| Superpowers | 98.8k | CruxDev | Agentic skills / methodology framework |
| Cline | 59k | CruxCLI (indirect), Crux | VS Code AI coding agent |
| Aider | 42k | CruxCLI (indirect) | Terminal AI coding agent |
| Roo Code | 22k | Crux (modes), CruxCLI (indirect) | VS Code AI coding agent with custom modes |

Claude Code is discussed separately — it is primarily a Crux integration target (Full tier), not a direct competitor to any of the three products.

---

## 1. OpenCode

**GitHub:** github.com/anomalyco/opencode · **Stars:** ~125k · **License:** MIT  
**Primary competitor to:** CruxCLI  
**Also relevant to:** Crux (integration host)

### What OpenCode Is

OpenCode is the upstream source that CruxCLI forks. Built by the SST team (creators of terminal.shop), it is the most TUI-native and technically ambitious terminal coding agent. Its client/server architecture, LSP support, and plugin API are the specific reasons the Crux ecosystem chose it as the fork base over Claude Code or Aider.

### What OpenCode Does Well

- **Plugin API with 15 hook points**: JS plugins with access to `experimental.chat.system.transform`, `experimental.chat.messages.transform`, `chat.params`, and more. This is what makes Crux's bridge plugin (and the eventual CruxCLI fork) possible.
- **Client/server architecture**: The TUI is one client among many — web, mobile, or IDE can all drive the same session. No other terminal agent has this.
- **LSP integration**: Out-of-the-box Language Server Protocol for code intelligence. Unique among terminal agents.
- **Provider agnostic**: Any model via API or Ollama locally. OpenCode Zen curates vetted model recommendations.
- **Custom tools, modes, commands**: All configurable via files. The symlink-based Crux installation exploits this.
- **Rapid development**: 10,388 commits, 737 releases, 125k stars, near-daily releases.
- **ACP (Agent Communication Protocol)** and skill system emerging.

### What OpenCode Lacks (Where CruxCLI Wins)

| Dimension | OpenCode | CruxCLI |
|-----------|----------|---------|
| Crux intelligence layer | Via plugin/MCP (addon) | Native in binary |
| Mode prompt system | Configurable, but generic | Crux's 24 research-optimized modes |
| Correction detection | Via Crux plugin only | Built-in |
| Learning / knowledge | Via Crux MCP only | Built-in |
| Safety pipeline | Via Crux plugin only | Built-in |
| System prompt control | Via `experimental` hooks (fragile) | Native in forked source |
| Prompt bloat | 200-word "STRICTLY FORBIDDEN" plan mode block; `<system-reminder>` wrapping; verbose defaults | Replaced with positive framing, 90% reduction |
| Token budget enforcement | Step-count limits (prompt instructions) | `toolChoice: none` (infrastructure) |
| Branding | OpenCode | CruxCLI, fully independent namespace |

### Strategic Relationship

CruxCLI does not try to outcompete OpenCode in raw feature development — OpenCode has 823+ contributors and releases daily. The strategy is "digest, don't track": monitor OpenCode for valuable concepts, integrate selectively, but do not maintain a rebase relationship. The CruxCLI fork is a clean break.

The moat is not feature parity with OpenCode. The moat is the Crux intelligence layer running natively inside the binary, not as a third-party plugin.

### Crux (platform) relationship

OpenCode is Crux's primary Full-tier integration host today. Crux's 7 JS plugins and 9 custom tools run inside OpenCode. This relationship persists until CruxCLI v1.0 ships — at which point CruxCLI becomes the primary dogfood environment and OpenCode becomes a secondary integration target.

---

## 2. Superpowers

**GitHub:** github.com/obra/superpowers · **Stars:** ~98.8k · **License:** MIT  
**Primary competitor to:** CruxDev  
**Also relevant to:** Crux (philosophical overlap on modes/skills)

### What Superpowers Is

Superpowers is a modular "agentic skills framework" by Jesse Vincent (obra). It is the closest existing competitor to CruxDev and one of the key sources CruxDev was synthesized from. It defines a composable `SKILL.md` architecture where skills auto-activate based on conversation context, chaining together into a software development workflow.

The framework is installed as a Claude Code plugin (official marketplace), a Cursor plugin, a Codex symlink setup, or an OpenCode manual install.

### What Superpowers Does Well

- **Modular SKILL.md architecture**: Skills are self-contained markdown files with frontmatter (`description`, `loads`, `chains-to`). They compose and auto-trigger without user intervention.
- **Comprehensive workflow coverage**: brainstorming → git worktrees → writing plans → subagent-driven-development → TDD → code review → branch finishing. A complete methodology.
- **Platform breadth**: Claude Code (official marketplace), Cursor, Codex, OpenCode, Gemini CLI — the widest platform support of any agentic framework.
- **Subagent-driven-development**: Fresh subagent per task with two-stage review (spec compliance, then code quality). CruxDev adopts this pattern.
- **TDD "Iron Law"**: RED-GREEN-REFACTOR enforced with persuasion language. CruxDev adopts and extends this.
- **Systematic debugging**: 4-phase root-cause-first methodology. CruxDev adopts this.
- **98.8k stars**: The highest-starred agentic framework in the ecosystem by a large margin.
- **Official Claude Code plugin**: Listed in Anthropic's official marketplace — massive distribution advantage.

### What Superpowers Lacks (Where CruxDev Wins)

This is the precise gap CruxDev is designed to fill. From the CruxDev design document directly:

| Dimension | Superpowers | CruxDev |
|-----------|-------------|---------|
| **Loop control** | Human-driven: user says "do it again" until quality converges | Agent-driven: convergence engine runs the loop autonomously |
| **Audit model** | Two-stage review (spec compliance + code quality) per task | Multi-dimensional: 8 code + 5 doc dimensions with convergence loop |
| **Convergence criterion** | Task passes review | Two consecutive independent clean passes across all dimensions |
| **Plan auditing** | Plans reviewed once before execution | Focused + full-plan + viability audit loops, each converging independently |
| **Environment verification** | Not present | Viability assessment checks actual machine state before execution |
| **Coverage enforcement** | TDD skill enforces write-test-first | TDD + coverage-by-coincidence detection + empirical line-number verification |
| **Deferred tracking** | Not formalized | Severity-based triage, Known Gaps section, machine-readable state |
| **Checkpoint honesty** | Not addressed | Honest annotation rule: caveats on every checked box |
| **Error handling** | Not formalized | 5 error types (test failure, subagent failure, file system, context overflow, build failure) with recovery |
| **Prompt patterns** | Not formalized | 7 field-tested patterns encoded as triggerable skill chains |
| **Autonomous termination** | Human decides when done | Two-consecutive-clean-pass rule with safety valves |

The one-sentence summary: **Superpowers is skills that the human chains. CruxDev is skills the engine chains to convergence — the human provides the goal and the engine converges.**

### The Autonomy Gap in Detail

Superpowers is linear: the agent does what it's told, skill by skill. There is no built-in convergence engine. The audit-fix-re-audit loop is driven by the user saying "do it again" (the "Big Bang" and "Do it again" prompts from CruxDev's prompt-patterns skill are precisely this pattern). Most users are not that disciplined — they accept the first clean pass, miss the issues the second pass would have found, and ship work that hasn't fully converged.

CruxDev's convergence engine eliminates this discipline requirement. The two-consecutive-clean-pass rule with an independent second-pass agent catches the ~30% false negatives that the first clean pass misses (empirical anchoring bias). Safety valves prevent infinite loops. Diminishing-returns logic exits gracefully when only low-severity issues remain.

### What CruxDev Doesn't Try to Replicate

Superpowers' official Claude Code marketplace listing is a significant distribution moat. CruxDev does not compete on distribution in the short term — it competes on the convergence engine, which is genuinely novel. CruxDev's platform adapters (Claude Code, Codex, OpenCode) are designed to be easy to install, but the primary adoption path is quality, not marketplace presence.

Superpowers also has a larger, more mature skill library and a stronger community. CruxDev starts with 16 skills vs. Superpowers' larger set. The bet is that the convergence engine is more valuable than skill breadth.

### Crux (platform) relationship

There is meaningful philosophical overlap between Crux modes and Superpowers skills — both are markdown files that configure agent behavior. But they are different abstractions: Crux modes are persistent personas for entire sessions (loaded via system prompt), while Superpowers skills are task-scoped procedures (triggered mid-session). They solve different problems and can coexist.

---

## 3. Cline

**GitHub:** github.com/cline/cline · **Stars:** ~59k · **License:** Apache 2.0  
**Primary competitor to:** CruxCLI (indirect — different interface), Crux (indirectly)  
**Also relevant to:** Crux Standard-tier integration target

### What Cline Is

Cline is the most widely adopted open-source VS Code AI coding agent. It is autonomy-forward with a strong human-in-the-loop UX: every file change and terminal command requires explicit approval with a diff view. It has browser use, workspace checkpoints, and an enterprise tier.

### How It Competes With the Ecosystem

**vs. CruxCLI**: Cline is VS Code, not terminal. For terminal-first developers (neovim users, SSH workflows, server environments), Cline is not the right tool. CruxCLI competes on terminal-native UX, provider agnosticism, and the Crux intelligence layer. Cline competes on IDE integration depth, browser use, and enterprise compliance. These are genuinely different audiences.

**vs. Crux (platform)**: Cline is a Standard-tier Crux integration target. One line in `.cline/mcp.json` connects Crux's MCP server, adding knowledge, modes, safety, and session state. But Cline has no hook system for push-based correction detection. Crux adds significant value to Cline users via MCP; the inverse is not true.

### Cline's Genuine Advantages Over CruxCLI

- **Workspace checkpoints**: Step-by-step snapshot + restore. Crux has no equivalent.
- **Browser automation**: Headless browser for visual debugging and e2e testing. Crux has no equivalent.
- **Enterprise tier**: SSO, SAML/OIDC, audit trails, VPC/private link, self-hosted deployment. Crux has no equivalent.
- **VS Code diff view**: Native IDE diffing with inline edit/revert. Terminal diff UX is inferior for most developers.
- **MCP server auto-creation**: Cline can create new MCP servers on demand from natural language. Novel.

### Crux's Genuine Advantages vs. Cline

| Capability | Cline | Crux Ecosystem |
|-----------|-------|---------------|
| Correction detection | None | Automatic (hook-based in CruxCLI, pull via MCP in Cline) |
| Organic knowledge generation | None | Crux: corrections → knowledge entries automatically |
| Cross-session memory | None | Crux: persistent `.crux/knowledge/` and session state |
| Specialized modes | None (one agent) | Crux: 24 research-optimized modes |
| Multi-gate safety pipeline | Binary approve/deny | Crux: 5 gates (preflight → adversarial audit → second opinion → human → dry-run) |
| Cross-project learning | None | Crux: three-tier knowledge promotion |
| Daily self-assessment digest | None | Crux: daily analytics from `.crux/analytics/` |
| Autonomous convergence | None | CruxDev: engine drives to two consecutive clean passes |
| Terminal-native UX | VS Code panel | CruxCLI: full TUI, client/server, remote-driveable |
| Local model support | Ollama (via config) | CruxCLI: native Ollama integration |

### Cline's Vulnerability

Cline's safety model is binary: approve or deny. The CruxDev convergence engine + Crux safety pipeline gives a far more nuanced picture: pre-flight validation, adversarial audit, risk classification, dry-run, and empirical convergence over multiple passes. For developers who care about code quality rather than just preventing catastrophic mistakes, the Crux approach is more useful.

---

## 4. Aider

**GitHub:** github.com/Aider-AI/aider · **Stars:** ~42k · **License:** Apache 2.0  
**Primary competitor to:** CruxCLI (terminal overlap)  
**Also relevant to:** Crux Standard-tier integration target (when MCP ships)

### What Aider Is

Aider is the most mature open-source terminal coding agent, built around git integration and a tree-sitter repo map. It auto-commits every change, supports undo via git, routes to 75+ models via LiteLLM, and processes 15B tokens/week. 88% of its latest release was self-authored.

### How It Competes With the Ecosystem

**vs. CruxCLI**: Both are terminal agents. Aider's git integration and repo map are genuinely better than what CruxCLI will ship with initially. However, Aider has no TUI (REPL only), no client/server architecture, no plugin system, no LSP, and no Crux intelligence layer. CruxCLI competes on UX depth, extensibility, and the intelligence layer underneath.

**vs. Crux (platform)**: Aider is a Standard-tier (future) Crux integration target. MCP support is pending (issue #4506). Until then, Crux knowledge can be injected via `--read .crux/knowledge/`. When MCP ships: one config line.

### Aider's Genuine Advantages Over CruxCLI

- **Git integration**: Auto-commit, auto-message, `aider --undo`, `aider --diff`. Best in class. No other tool matches this.
- **Repo map**: Tree-sitter AST analysis of the entire codebase. Produces a symbol-level map that gives the LLM accurate structural context in large projects. Far superior to file listing.
- **Lint/test loops**: Automatically lint and test after every change, fix errors, retry. Tight feedback loop.
- **Voice-to-code**: Whisper transcription for voice-driven development.
- **Self-coding**: 88% of new code written by aider itself — strong dogfood signal.
- **169 contributors**: The most mature open-source contributor community in the terminal agent space.
- **15B weekly tokens**: Strong evidence of real-world usage scale.

### Crux Ecosystem's Genuine Advantages vs. Aider

| Capability | Aider | Crux Ecosystem |
|-----------|-------|---------------|
| TUI with client/server | REPL only | CruxCLI: full TUI, driveable remotely |
| Plugin / extensibility | None | CruxCLI: 15-point plugin API |
| Correction detection | None | Crux: automatic |
| Organic knowledge | None (fresh each session) | Crux: accumulated across sessions and projects |
| Specialized modes | 3 modes (code/architect/ask) | Crux: 24 research-optimized modes |
| Safety pipeline | None | Crux: 5 gates |
| Autonomous convergence | None | CruxDev: multi-pass convergence engine |
| Cross-project learning | None | Crux: three-tier knowledge promotion |
| MCP support | Pending (#4506) | CruxCLI: native |

### The Repo Map Gap

Aider's tree-sitter repo map is the capability the Crux ecosystem most clearly lacks. For large codebases (100k+ lines), the repo map gives the LLM structural context that file listing cannot. CruxCLI will initially ship without this. This is a real gap for power users working in large codebases.

The mitigation in the near term is that Crux's project context detection (`crux_get_project_context()`) provides git history, hot files, and directory structure — which is adequate for most workloads but inferior to AST-level analysis.

---

## 5. Roo Code

**GitHub:** github.com/RooCodeInc/Roo-Code · **Stars:** ~22k · **License:** Apache 2.0  
**Primary competitor to:** Crux (modes system), CruxCLI (indirect)  
**Also relevant to:** Crux Enhanced-tier integration target

### What Roo Code Is

Roo Code is a VS Code extension with the strongest native modes system in the ecosystem — architecturally closest to Crux's mode design. Its `.roomodes` YAML format, per-mode tool access control, per-mode model selection, and subtask spawning in alternate modes are the most sophisticated mode implementation outside of Crux itself.

### How It Competes With the Ecosystem

**vs. Crux (platform)**: Roo Code's modes system covers part of what Crux modes provide — specialized personas with tool access control. But Roo Code's modes are entirely static. They don't learn from corrections, don't carry knowledge between sessions, don't generate analytics, and don't hand off context on mode switch. Crux modes plus Crux's learning infrastructure is what Roo Code modes would be if they had memory.

**vs. CruxCLI**: Different interface (VS Code vs terminal). Different audiences.

### Roo Code's Genuine Advantages Over Crux

- **VS Code native**: Panel-integrated with diff view, file explorer sync, inline diagnostics. Crux has no VS Code native experience (MCP only).
- **Native modes rendering**: Crux modes registered in Roo Code via `crux init --tool roo-code` are first-class — rendered with Roo Code's full mode UI, not just injected via MCP context.
- **Per-mode model selection**: Route expensive tasks to opus, cheap to haiku, in the same session. Crux has per-mode temperature/sampling (think vs no-think) but model routing is manual.
- **Codebase indexing**: Semantic search over the codebase. Better than Crux's file-structure detection.
- **Workspace checkpoints**: Same as Cline — step snapshot and restore.
- **Skills as slash commands** (v3.51+): Reusable workflow definitions as slash commands.

### Crux's Genuine Advantages vs. Roo Code Modes

| Capability | Roo Code Modes | Crux Modes |
|-----------|---------------|-----------|
| Correction learning | None | Automatic correction → knowledge |
| Cross-session persistence | None (modes are static files) | `.crux/knowledge/` persists |
| Mode handoffs with context | Context lost on switch | `crux_write_handoff()` preserves context |
| Cross-project knowledge | None | Three-tier promotion |
| Daily digest of mode effectiveness | None | Daily analytics digest |
| Safety pipeline integration | None per-mode | 5 gates configurable per mode |

### The Integration Opportunity

Roo Code is the highest-synergy Crux integration target. `crux init --tool roo-code` can convert all 24 Crux modes to `.roomodes` YAML and register the MCP server. The result is Roo Code rendering Crux modes natively, while Crux provides the learning layer that Roo Code lacks. This is Enhanced tier in Crux's integration taxonomy.

---

## 6. Claude Code

**GitHub:** github.com/anthropics/claude-code · **Stars:** ~80k · **License:** Proprietary  
**Relationship to ecosystem:** Full-tier Crux integration host; not a direct competitor

Claude Code is not a competitor to any of the three ecosystem products in their primary lanes. It is discussed here because it is Crux's second Full-tier integration target (after CruxCLI) and the platform with the most integration potential.

### Why It Matters for the Ecosystem

- **20 hook events**: UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, SessionStart, and more. Richer event system than any other tool. Enables fully push-based correction detection, safety interception, session logging, and compaction injection without any user action.
- **Primary CruxDev development platform**: All CruxDev development happens in Claude Code (Pro Max). The Claude Code adapter (`adapters/claude-code/`) is CruxDev's primary platform target.
- **Crux integration**: `.claude/mcp.json` registers the Crux MCP server. `crux init --tool claude-code` generates 24 subagent files from Crux modes. 5 hook shims forward events to the Crux MCP server. Full-tier.

### Claude Code's Limitations vs. CruxCLI

- **Locked to Anthropic**: No local model support, no provider switching. CruxCLI is fully provider-agnostic.
- **Closed source**: Cannot modify internals. CruxCLI is a controlled fork.
- **No per-subagent temperature**: No sampling parameter control. CruxCLI's forked binary will enforce Crux's `think` vs `no_think` temperature routing natively.
- **Expensive**: API billing at Anthropic rates. CruxCLI + Ollama = zero inference cost for local models.

---

## Full Feature Matrix

| Feature | Crux | CruxCLI | CruxDev | OpenCode | Superpowers | Cline | Aider | Roo Code |
|---------|------|---------|---------|----------|-------------|-------|-------|---------|
| **Intelligence / Learning** |
| Correction detection | ✅ Auto | ✅ Native | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| Organic knowledge generation | ✅ | ✅ Native | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cross-session memory | ✅ | ✅ | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cross-project learning | ✅ | ✅ | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| Daily self-assessment digest | ✅ | ✅ | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Modes / Skills** |
| Specialized modes | ✅ 24 | ✅ 24 native | — | Configurable | — | ❌ | 3 | ✅ Custom |
| Mode handoffs with context | ✅ | ✅ | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| Per-mode tool access control | ✅ | ✅ | — | Partial | — | ❌ | ❌ | ✅ |
| Per-mode model routing | Guidance | ✅ Native | — | ❌ | — | ❌ | ✅ | ✅ |
| Per-mode temperature routing | ✅ | ✅ Native | — | ❌ | — | ❌ | ❌ | ❌ |
| Agentic skills framework | — | — | ✅ 16 skills | Partial | ✅ | ❌ | ❌ | ✅ Partial |
| **Convergence / Quality** |
| Autonomous convergence engine | — | — | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Two-consecutive-clean-pass rule | — | — | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Multi-dimensional code audit (8) | — | — | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Multi-dimensional doc audit (5) | — | — | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Viability assessment (env check) | — | — | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Honest tracking / Known Gaps | — | — | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Coverage-by-coincidence detection | — | — | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Subagent-driven development | — | — | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| TDD enforcement | — | — | ✅ | ❌ | ✅ | ❌ | ✅ Partial | ❌ |
| **Safety** |
| Multi-gate safety pipeline | ✅ 5 gates | ✅ Native | — | ❌ | ❌ | Binary | ❌ | Binary |
| Adversarial script audit (LLM) | ✅ | ✅ | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cross-tool session continuity | ✅ | ✅ | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Runtime / UX** |
| Terminal TUI | Via OpenCode | ✅ Native | — | ✅ | — | REPL | ✅ |
| Client/server architecture | — | ✅ | — | ✅ | — | ❌ | ❌ | ❌ |
| LSP support | — | ✅ | — | ✅ | — | ❌ | ❌ | ❌ |
| VS Code extension | Via MCP | ❌ | — | ❌ | ✅ | ✅ | Watch | ✅ |
| Local model (Ollama) | ✅ | ✅ | — | ✅ | — | ✅ | ✅ | ✅ |
| MCP server (37 tools) | ✅ | ✅ | — | Client | — | Client | Pending | Client |
| Plugin / hook system | ✅ | ✅ | — | ✅ | — | ❌ | ❌ | ❌ |
| Browser automation | ❌ | ❌ | — | ❌ | — | ✅ | ❌ | ✅ |
| Workspace checkpoints | ❌ | ❌ | — | ❌ | — | ✅ | Via git | ✅ |
| Git integration | Basic | Basic | — | Basic | ✅ | ✅ | ✅ Best | ✅ |
| Repo/AST map | ❌ | ❌ | — | ❌ | — | ✅ | ✅ Best | ✅ |
| Platform adapters | 4 tools | — | 3 platforms | — | 5 platforms | — | — | — |
| Enterprise tier | ❌ | ❌ | — | ❌ | — | ✅ | ❌ | ❌ |
| Open source | ✅ MIT | ✅ MIT (fork) | ✅ (planned) | ✅ MIT | ✅ MIT | ✅ Apache | ✅ Apache | ✅ Apache |

---

## What No Competitor Has

### Unique to the Crux Ecosystem (no equivalent anywhere)

**1. Automatic correction detection**
No tool — OpenCode, Superpowers, Cline, Aider, or Roo Code — tracks when users correct the AI, extracts the pattern, and structures it into reusable knowledge. Crux does this automatically via hooks (CruxCLI, Claude Code) or MCP pull (all others). This is the highest-value differentiator across all three products.

**2. Organic knowledge generation and cross-project promotion**
Every tool's "memory" is manual (MEMORY.md, AGENTS.md, `.clinerules`). Crux generates knowledge automatically from correction clusters, promotes it across projects (project → user → public scope), and surfaces it in daily digests. No equivalent exists.

**3. Daily self-assessment digest with cross-tool analytics**
No tool generates analytics about its own performance. Crux's daily digest analyzes correction rates, mode effectiveness, knowledge promotion candidates, and tool switching patterns — across all tools. Not just one session. All sessions, all tools.

**4. Cross-tool session continuity**
No tool lets you switch between AI coding tools mid-project without losing context. `crux switch opencode` / `crux switch claude-code` captures session state; the next tool picks up exactly where the last one left off. This requires the tool-agnostic intelligence layer that only Crux provides.

**5. Autonomous convergence to two consecutive clean passes (CruxDev)**
Superpowers (the closest competitor) requires the human to say "do it again" to drive audit-fix-re-audit loops. CruxDev's convergence engine drives the loop autonomously. The two-consecutive-clean-pass rule with independent second-pass agents catches the ~30% false negatives that anchoring bias creates after the first clean pass. No framework has formalized this.

**6. Build-in-public pipeline (Crux)**
`crux bip` — threshold-triggered content generation from unposted commits, corrections, and knowledge entries — is unique. No other AI development tool has a content pipeline for building in public.

---

## Honest Gaps

### Where the Ecosystem Is Weaker

**Repo/AST map (Aider, Roo Code > all three Crux products)**
Aider's tree-sitter repo map and Roo Code's semantic codebase indexing give the LLM structural context that the Crux ecosystem's file-listing-based project context cannot match in large codebases. This is a real gap for 100k+ line projects.

**Workspace checkpoints (Cline, Roo Code > CruxCLI)**
Step-by-step snapshot + restore is not in any Crux product. Git covers the same ground at a coarser granularity, but the checkpoint UX is more accessible.

**Browser automation (Cline, Roo Code > all three Crux products)**
No Crux product has a headless browser. This is a real gap for frontend development.

**VS Code native experience (Cline, Roo Code, Claude Code > CruxCLI)**
CruxCLI is terminal-only. VS Code developers get Crux via MCP in their existing tools — which is valuable but not the same as native IDE integration.

**Enterprise compliance (Cline > all three Crux products)**
Cline's enterprise tier (SSO, SAML/OIDC, audit trails, VPC, self-hosted) addresses a market the Crux ecosystem does not currently serve.

**Platform breadth for CruxDev (Superpowers > CruxDev)**
Superpowers supports 5 platforms including Gemini CLI and has an official Claude Code marketplace listing. CruxDev plans 3 platforms with no marketplace strategy yet.

**Community / star count (all competitors > ecosystem)**
The ecosystem is early. OpenCode (125k), Superpowers (98.8k), Cline (59k), Aider (42k), Roo Code (22k) all have established communities. Crux, CruxCLI, and CruxDev are building theirs.

**Implementation status**
The biggest honest gap: CruxCLI and CruxDev are design-phase products. Crux is shipped and tested. The competitive analysis reflects the full target state. The current state is: Crux platform ships today; CruxCLI and CruxDev do not yet.

---

## Strategic Summary

### The Three Bets

**Bet 1 (Crux):** The intelligence layer is a distinct product category. Every agent needs learning, safety, and memory. No agent has built these. First mover in this category, distributable across all agents via MCP. Defensible because it requires architectural decisions (structured logging, knowledge promotion, correction detection) that are hard to retrofit.

**Bet 2 (CruxCLI):** A terminal agent with the intelligence layer native to the binary is better than a terminal agent with an intelligence plugin bolted on. OpenCode + Crux plugin is fragile (experimental hooks), generic (no prompt authority), and unbranded. CruxCLI is none of those things. The bet: developers who care about the intelligence layer will prefer the product that integrates it natively.

**Bet 3 (CruxDev):** Autonomous convergence is more valuable than human-driven convergence. Superpowers proves the market for agentic methodology frameworks (98.8k stars). CruxDev's bet is that the convergence engine — the thing that makes the agent drive itself to two consecutive clean passes without human prompting — is the next step that Superpowers hasn't taken.

### Risk Map

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| OpenCode ships native memory/learning | Medium | High for Crux | Crux's MCP server works with any host; deepen CruxCLI integration |
| Superpowers ships a convergence engine | Low | High for CruxDev | CruxDev's convergence is more sophisticated; ship first |
| Cline or Roo Code adds correction detection | Low-Medium | Medium for Crux | Cross-tool continuity is unreplicable by single-tool vendors |
| CruxCLI fork maintenance burden | High | Medium | "Digest, don't track" strategy explicitly avoids rebase maintenance |
| CruxDev doesn't gain traction vs. Superpowers | Medium | High for CruxDev | Converge on dogfood project; publish empirical results |
| Star count gap limits adoption | High (short-term) | Medium | Build-in-public pipeline (`crux bip`) is the attention strategy |

---

*Sources: GitHub repositories (github.com/anomalyco/opencode, github.com/obra/superpowers, github.com/cline/cline, github.com/Aider-AI/aider, github.com/RooCodeInc/Roo-Code, github.com/anthropics/claude-code), internal documents (crux/README.md, crux/crux-ecosystem-analysis.md, cruxcli/ROADMAP.md, cruxcli/BUILD_PLAN_001_HARD_FORK.md, cruxdev/CruxDev.md, cruxdev/CRUX_ECOSYSTEM_PLAN.md, cruxdev/ORIGIN.md). Data current as of March 2026.*
