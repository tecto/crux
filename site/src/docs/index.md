---
layout: base.njk
title: Documentation
description: Get started with Crux - installation, setup, and tool integration
---

# Getting Started with Crux

## Quick Install

```bash
# Download the binary (macOS ARM64)
curl -fsSL https://github.com/trinsiklabs/crux/releases/latest/download/crux-aarch64-apple-darwin -o /usr/local/bin/crux
chmod +x /usr/local/bin/crux

# Or build from source
git clone https://github.com/trinsiklabs/crux.git
cd crux && cargo build --release
# Binary at target/release/crux (6.6MB, zero dependencies)
```

## Adopt a Project

```bash
cd your-project
crux adopt claude-code   # or: cruxcli, opencode, cursor, windsurf, zed
```

This creates `.crux/`, generates the MCP config for your tool, sets up hooks (Claude Code), and imports any existing session history.

## What You Get

- **57 MCP tools** — Knowledge, sessions, modes, safety, impact analysis, memory, git context, session recovery
- **24 specialized modes** — build-py, security, debug, design-ui, and more
- **Session persistence** — State survives across sessions and tools
- **Correction detection** — Learn from AI mistakes automatically
- **Safety pipeline** — 7-gate validation for code changes
- **Session recovery** — Recover context from corrupted Claude Code sessions
- **Single Rust binary** — 6.6MB, zero runtime dependencies

## Tool-Specific Setup

Choose your AI coding tool:

- [Claude Code](/docs/claude-code/) — Full integration with hooks + MCP
- [CruxCLI / OpenCode](/docs/opencode/) — Full integration via MCP
- [Cursor](/docs/cursor/) — MCP integration
- [Windsurf](/docs/windsurf/) — MCP integration
- [Aider](/docs/aider/) — MCP integration
- [Roo Code](/docs/roo-code/) — MCP integration
- [Qwen-Agent](/docs/qwen-agent/) — MCP integration

Any tool with MCP support can connect — just point it at `crux mcp start`.

## Verify Installation

```bash
crux version    # shows version
crux health     # runs health checks
crux status     # shows session state
crux mcp status # lists all 57 MCP tools
```

## Next Steps

- [Architecture](/architecture/) — how the system works
- [All 57 Tools](/docs/mcp-server/) — MCP tool reference
- [Modes](/modes/) — 24 specialized modes
- [Safety Pipeline](/safety-pipeline/) — 7-gate validation
- [Tool Switching](/switching/) — switch tools seamlessly
