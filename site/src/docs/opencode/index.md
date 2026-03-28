---
layout: base.njk
title: "Crux + CruxCLI / OpenCode"
description: "Crux integration with CruxCLI and OpenCode via MCP"
---

# Crux + CruxCLI / OpenCode

CruxCLI is a hard fork of OpenCode, rebranded for the Crux ecosystem. Both connect to Crux via MCP.

## Setup

```bash
# Adopt the project
crux adopt cruxcli   # or: crux adopt opencode

# Or manually create .cruxcli/cruxcli.jsonc:
```

```json
{
  "mcp": {
    "crux": {
      "type": "local",
      "command": ["/path/to/crux", "mcp", "start"],
      "environment": {
        "CRUX_HOME": "~"
      }
    }
  }
}
```

## MCP Integration

All 57 Crux MCP tools are available. The Rust binary starts in under 1ms.

## Supported Features

| Feature | Support |
|---------|---------|
| MCP Tools (57) | Full |
| Knowledge lookup | Yes |
| Session state | Yes |
| Session recovery | Yes |
| Modes (24) | Yes |
| Corrections | Yes |
| Safety pipeline (7 gates) | Yes |
| Impact analysis (AST) | Yes |
| Memory system | Yes |
| Git context | Yes |

## Tool Switching

```bash
# Switch to CruxCLI from another tool
crux switch cruxcli

# Switch away
crux switch claude-code
```

Session state, knowledge, corrections, and handoff context transfer automatically.

## See Also

- [Tool Switching](/switching/) — How switching works
- [MCP Server](/docs/mcp-server/) — All 57 tools
- [Modes](/modes/) — 24 specialized modes
