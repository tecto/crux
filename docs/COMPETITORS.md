# Crux — Competitive Analysis

Competitive landscape for Crux in the AI coding intelligence layer category.

## Official Competitors

### Cursor
**URL:** https://cursor.com
**Category:** official
**Pricing:** $20/mo Pro, $40/mo Business

AI-first code editor on VS Code

**Strengths:**
- Polished UX
- $2B+ ARR
- Large user base

**Weaknesses:**
- Vendor lock-in
- No cross-tool portability
- No learning
**Revenue Model:** subscription

### Claude Code
**URL:** https://claude.ai/code
**Category:** official
**Pricing:** API usage ($3-15/MTok)

Anthropic CLI agent — hooks, MCP, agentic workflows

**Strengths:**
- Best instruction-following
- Hook system
- MCP ecosystem
- Opus/Sonnet quality

**Weaknesses:**
- Intelligence locked in .claude/
- Expensive API
- No cross-tool portability
**Revenue Model:** usage

### Windsurf
**URL:** https://windsurf.com
**Category:** official
**Pricing:** Free tier, $15/mo Pro

AI IDE with Cascade agent and flows

**Strengths:**
- Good free tier
- Growing fast

**Weaknesses:**
- Global-only MCP
- No portability
**Revenue Model:** freemium

### Aider
**URL:** https://aider.chat
**Category:** official
**Pricing:** Free (open source)

Open-source AI pair programming — repo map, git integration

**Strengths:**
- Open source
- Excellent repo map
- Multi-model

**Weaknesses:**
- No MCP
- No portability
- No learning
- No safety
**Revenue Model:** open_source

### Codex CLI
**URL:** https://github.com/openai/codex
**Category:** official
**Pricing:** API usage

OpenAI terminal coding agent — recently rewritten in Rust

**Strengths:**
- OpenAI backing
- Rust performance
- Growing fast

**Weaknesses:**
- New entrant
- No learning system
- No safety pipeline
- No tool switching
**Revenue Model:** usage

## Watch Competitors

### Copilot
**URL:** https://github.com/features/copilot
**Category:** watch
**Pricing:** $10/mo Individual, $19/mo Business

GitHub AI coding assistant

**Strengths:**
- Massive distribution
- Enterprise adoption

**Weaknesses:**
- Autocomplete-focused
- No agentic workflows
- Locked to GitHub
**Revenue Model:** subscription

### Replit
**URL:** https://replit.com
**Category:** watch
**Pricing:** $25/mo Hacker

Cloud IDE and deployment platform with AI agent

**Strengths:**
- $9B valuation
- Full platform

**Weaknesses:**
- Code quality crisis
- Agent reliability
- Locked to platform
**Revenue Model:** subscription

### Roo Code
**URL:** https://roocode.com
**Category:** watch
**Pricing:** Free (open source)

VS Code AI assistant with MCP and custom modes

**Strengths:**
- Customizable
- Growing community

**Weaknesses:**
- VS Code only
- No portability
- No learning
**Revenue Model:** open_source

### Gemini CLI
**URL:** https://github.com/google/gemini-cli
**Category:** watch
**Pricing:** Free (with API key)

Google terminal AI agent

**Strengths:**
- Google backing
- Gemini 2.5 model

**Weaknesses:**
- New entrant
- Limited ecosystem
- No learning
**Revenue Model:** usage

## Gap Analysis

| Feature | Crux | Aider | Claude Code | Codex CLI | Copilot | Cursor | Gemini CLI | Replit | Roo Code | Windsurf |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 specialized modes | Y | N | N | N | N | N | N | N | N | N |
| 57 MCP tools (Rust binary) | Y | N | N | N | N | N | N | N | N | N |
| 7-gate safety pipeline | Y | N | N | N | N | N | N | N | N | N |
| Agentic coding | N | N | Y | N | N | N | N | N | N | N |
| AI agent | N | N | N | N | N | N | N | Y | N | N |
| AI completion | N | N | N | N | N | Y | N | N | N | N |
| architect mode | N | Y | N | N | N | N | N | N | N | N |
| auto-capture session state (hooks) | Y | N | N | N | N | N | N | N | N | N |
| background agents | N | N | Y | N | N | Y | N | N | N | N |
| BIP pipeline (Typefully) | Y | N | N | N | N | N | N | N | N | N |
| Cascade agent | N | N | N | N | N | N | N | N | N | Y |
| chat | N | N | N | N | Y | N | N | N | N | N |
| Cloud IDE | N | N | N | N | N | N | N | Y | N | N |
| codebase awareness | N | N | N | N | N | N | N | N | N | Y |
| codebase chat | N | N | N | N | N | Y | N | N | N | N |
| codebase indexing | Y | N | N | N | N | N | N | N | N | N |
| composer | N | N | N | N | N | Y | N | N | N | N |
| correction detection (10 patterns) | Y | N | N | N | N | N | N | N | N | N |
| cross-project analytics | Y | N | N | N | N | N | N | N | N | N |
| custom modes | N | N | N | N | N | N | N | N | Y | N |
| database | N | N | N | N | N | N | N | Y | N | N |
| design validation (WCAG) | Y | N | N | N | N | N | N | N | N | N |
| extended thinking | N | N | Y | N | N | N | N | N | N | N |
| file context | N | N | N | N | N | N | N | N | Y | N |
| flows | N | N | N | N | N | N | N | N | N | Y |
| Gemini models | N | N | N | N | N | N | Y | N | N | N |
| git-aware editing | Y | Y | N | N | N | N | N | N | N | N |
| hooks system | N | N | Y | N | N | N | N | N | N | N |
| hosting | N | N | N | N | N | N | N | Y | N | N |
| impact analysis (tree-sitter AST) | Y | N | N | N | N | N | N | N | N | N |
| indexing | N | N | N | N | N | Y | N | N | N | N |
| Inline completions | N | N | N | N | Y | N | N | N | N | N |
| knowledge promotion (project→user→public) | Y | N | N | N | N | N | N | N | N | N |
| MCP support | N | N | Y | Y | N | Y | N | N | Y | Y |
| memory system | N | N | Y | N | N | N | N | N | N | N |
| memory system (remember/recall/forget) | Y | N | N | N | N | N | N | N | N | N |
| model routing (Ollama/Anthropic/OpenAI) | Y | N | N | N | N | N | N | N | N | N |
| multi-file edit | N | N | N | N | N | Y | N | N | N | N |
| multi-IDE | N | N | N | N | Y | N | N | N | N | N |
| multi-model | N | Y | N | Y | N | N | N | N | Y | N |
| one-click deploy | N | N | N | N | N | N | N | Y | N | N |
| plan mode | N | N | Y | N | N | N | N | N | N | N |
| Repo map (AST) | N | Y | N | N | N | N | N | N | N | N |
| Rust binary | N | N | N | Y | N | N | N | N | N | N |
| sandbox | N | N | N | N | N | N | Y | N | N | N |
| sandbox execution | N | N | N | Y | N | N | N | N | N | N |
| seamless tool switching (6 tools) | Y | N | N | N | N | N | N | N | N | N |
| session recovery from corrupted sessions | Y | N | N | N | N | N | N | N | N | N |
| single binary distribution (zero deps) | Y | N | N | N | N | N | N | N | N | N |
| Terminal agent | N | N | N | Y | N | N | Y | N | N | N |
| tool use | N | N | N | N | N | N | Y | N | N | N |
| tool-agnostic intelligence (.crux/) | Y | N | N | N | N | N | N | N | N | N |
| voice coding | N | Y | N | N | N | N | N | N | N | N |
| workspace agent | N | N | N | N | Y | N | N | N | N | N |
| worktrees | N | N | Y | N | N | N | N | N | N | N |

### Must-Close
- **background agents** — has: Claude Code, Cursor
- **MCP support** — has: Roo Code, Codex CLI, Cursor, Windsurf, Claude Code
- **multi-model** — has: Roo Code, Aider, Codex CLI

### Should-Close
- **Agentic coding** — has: Claude Code
- **AI completion** — has: Cursor
- **architect mode** — has: Aider
- **Cascade agent** — has: Windsurf
- **codebase awareness** — has: Windsurf
- **codebase chat** — has: Cursor
- **composer** — has: Cursor
- **extended thinking** — has: Claude Code
- **flows** — has: Windsurf
- **hooks system** — has: Claude Code
- **indexing** — has: Cursor
- **memory system** — has: Claude Code
- **multi-file edit** — has: Cursor
- **plan mode** — has: Claude Code
- **Repo map (AST)** — has: Aider
- **Rust binary** — has: Codex CLI
- **sandbox execution** — has: Codex CLI
- **Terminal agent** — has: Gemini CLI, Codex CLI
- **voice coding** — has: Aider
- **worktrees** — has: Claude Code

### Nice-To-Have
- **AI agent** — has: Replit
- **chat** — has: Copilot
- **Cloud IDE** — has: Replit
- **custom modes** — has: Roo Code
- **database** — has: Replit
- **file context** — has: Roo Code
- **Gemini models** — has: Gemini CLI
- **hosting** — has: Replit
- **Inline completions** — has: Copilot
- **multi-IDE** — has: Copilot
- **one-click deploy** — has: Replit
- **sandbox** — has: Gemini CLI
- **tool use** — has: Gemini CLI
- **workspace agent** — has: Copilot
