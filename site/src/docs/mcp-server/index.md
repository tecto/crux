---
layout: base.njk
title: MCP Server Reference
description: All 57 Crux MCP tools — single Rust binary
---

# MCP Server Reference

The Crux MCP server is a single 6.6MB Rust binary (`crux mcp start`) exposing 57 tools via the Model Context Protocol. Any MCP-compatible AI assistant connects with one config line.

## Connection

```json
{
  "type": "stdio",
  "command": "/path/to/crux",
  "args": ["mcp", "start"]
}
```

## Session Tools

| Tool | Description |
|------|-------------|
| `get_session_state` | Current mode, tool, working_on, decisions |
| `update_session` | Update working_on, add decision, add file |
| `restore_context` | Restore full session context — call at session start |
| `write_handoff` | Write handoff for next session |
| `read_handoff` | Read handoff from previous session |
| `recover_session` | Recover context from corrupted Claude Code sessions |

## Knowledge & Memory

| Tool | Description |
|------|-------------|
| `lookup_knowledge` | Search knowledge entries by keyword |
| `promote_knowledge` | Promote project knowledge to user scope |
| `remember_fact` | Remember a fact for future sessions |
| `recall_memories` | Search stored memories |
| `forget_fact` | Remove a stored memory |
| `list_all_memories` | List all stored memories |

## Impact Analysis

| Tool | Description |
|------|-------------|
| `analyze_impact` | Rank files by relevance (git + grep + AST) |
| `search_code` | Search codebase for files and symbols |
| `index_codebase` | Build/refresh the codebase index |

## Git Context

| Tool | Description |
|------|-------------|
| `git_context` | File history, risk score |
| `git_diff` | Current uncommitted changes |
| `git_risky_files` | Files with highest churn |
| `git_suggest_commit` | Suggest commit message from staged changes |

## Safety Pipeline

| Tool | Description |
|------|-------------|
| `validate_script` | Gate 1: preflight validation |
| `get_active_gates` | Active gates for a risk level |
| `get_pipeline_config` | Current pipeline configuration |
| `start_tdd_gate` | Gate 2: start TDD enforcement |
| `check_tdd_status` | TDD gate status |
| `start_security_audit` | Gate 3: start security audit |
| `security_audit_summary` | Security audit results |
| `audit_script_8b` | Gate 4: 8B adversarial audit (Ollama) |
| `audit_script_32b` | Gate 5: 32B second opinion (Ollama) |

## Design Validation

| Tool | Description |
|------|-------------|
| `start_design_validation` | WCAG/brand checks |
| `design_validation_summary` | Validation results |
| `check_contrast` | WCAG contrast ratio for two colors |

## Modes

| Tool | Description |
|------|-------------|
| `get_mode_prompt` | Full prompt text for a mode |
| `list_modes` | All available modes |

## Logging

| Tool | Description |
|------|-------------|
| `log_correction` | Log a correction for learning |
| `log_interaction` | Log a conversation message |

## Tool Switching

| Tool | Description |
|------|-------------|
| `switch_tool_to` | Switch to another AI tool |

## MCP Server Registry

| Tool | Description |
|------|-------------|
| `register_mcp_server` | Register an external MCP server |
| `remove_mcp_server` | Remove a server |
| `list_mcp_servers` | List registered servers |

## Build-in-Public

| Tool | Description |
|------|-------------|
| `bip_generate` | Check triggers, gather content for a draft |
| `bip_approve` | Approve and queue to Typefully |
| `bip_status` | Current BIP state and counters |
| `bip_get_analytics` | Engagement analytics |

## Model Routing

| Tool | Description |
|------|-------------|
| `get_model_for_task` | Recommended model for a task type |
| `get_available_tiers` | Available models at each tier (auto-discovers Ollama) |
| `get_mode_model` | Recommended model for a mode |
| `get_model_quality_stats` | Success rates per model per task |

## Figma Integration

| Tool | Description |
|------|-------------|
| `figma_get_tokens` | Extract design tokens from Figma |
| `figma_get_components` | Get component library |

## Cross-Project

| Tool | Description |
|------|-------------|
| `register_project` | Register for cross-project analytics |
| `get_cross_project_digest` | Digest spanning all projects |

## Background Processors

| Tool | Description |
|------|-------------|
| `check_processor_thresholds` | Which thresholds are exceeded |
| `run_background_processors` | Run due processors |
| `get_processor_status` | When each processor last ran |

## Diagnostics

| Tool | Description |
|------|-------------|
| `verify_health` | Health checks report |
| `get_project_context` | Auto-generated PROJECT.md |
| `get_digest` | Daily digest |
