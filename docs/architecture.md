# Crux Architecture

## Overview

Crux is a self-improving AI operating system that wraps any LLM and any agentic tool to maximize effectiveness through specialized modes, continuous learning, and infrastructure-enforced reliability.

## Core Principle

Everything the AI does is enforced by code, not by instructions. Prompts drift. Infrastructure does not.

## System Layers

### Layer 1: Lean Core (~50 tokens)

Baked into the model's system role via Modelfile. Global behavioral rules: numbered lists, narration, directness. Never changes between interactions.

### Layer 2: Mode Prompts (~120-155 tokens)

15 specialized modes loaded one at a time. Each defines persona, domain-specific rules, and tool access constraints. Total system overhead: ~170-205 tokens = 99.4% of context available for work.

### Layer 3: Plugins and Tools

JavaScript plugins using OpenCode hook system. Custom tools with Zod schemas for validated operations.

## Component Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Mode Layer (15 modes)             │
│  build-py | build-ex | debug | plan | review | ...  │
├─────────────────────────────────────────────────────┤
│                   Plugin Layer (6 plugins)           │
│  think-router | token-budget | tool-enforcer |      │
│  session-logger | correction-detector |             │
│  compaction-hook                                    │
├─────────────────────────────────────────────────────┤
│                   Tool Layer (7 tools)               │
│  run_script | lookup_knowledge | suggest_handoff |  │
│  project_context | promote_script | list_scripts |  │
│  manage_models                                      │
├─────────────────────────────────────────────────────┤
│             Python Infrastructure Scripts            │
│  preflight_validator | extract_corrections |        │
│  update_project_context | generate_digest |         │
│  promote_knowledge | model_registry_update |        │
│  model_auto_evaluate | audit_modes                  │
├─────────────────────────────────────────────────────┤
│                   Knowledge Layer                    │
│  Project (.opencode/knowledge/) |                   │
│  User (~/.config/opencode/knowledge/) |             │
│  Public (this repo/knowledge/)                      │
└─────────────────────────────────────────────────────┘
```

## Five-Gate Script Execution Pipeline

All scripts execute through the `run_script` tool which implements:

1. **Pre-flight Validation** (deterministic): Shebang, `set -euo pipefail`, risk classification vs. operations, DRY_RUN support, path containment, transaction pattern compliance
2. **8B Adversarial Audit**: Different model reviews script for data loss, corruption, side effects, scope creep
3. **32B Second-Opinion**: High-risk scripts only; second model validates findings
4. **Human Approval**: High-risk scripts require explicit user approval
5. **DRY_RUN**: Medium+ risk scripts execute in dry-run mode first

## Tool Tier Hierarchy

| Tier | Type | Reliability | Examples |
|------|------|-------------|----------|
| 0 | LSP | Deterministic | pyright, elixir-ls |
| 1 | Custom Tools | Schema-validated | run_script, lookup_knowledge |
| 2 | MCP Servers | Protocol-enforced | GitHub MCP, filesystem MCP |
| 3 | Library Scripts | Tested, versioned | backup_database.sh |
| 4 | New Scripts | Templated, audited | One-off scripts via pipeline |
| 5 | Raw Bash | Minimal, logged | ls, grep (read-only) |

The `tool-enforcer` plugin intercepts tool calls and enforces tier access per mode. Read-only modes cannot call write/edit tools. Tier 5 usage is tracked for optimization.

## Continuous Learning Pipeline

```
Correction Detection (real-time, correction-detector.js)
    ↓
Session Logging (append-only JSONL, session-logger.js)
    ↓
Correction Extraction (batch, extract_corrections.py)
    ↓
Knowledge Clustering (pattern → knowledge candidate)
    ↓
Knowledge Promotion (project → user → public)
    ↓
Daily Digest (analytics aggregation, generate_digest.py)
```

## Token Budget System

Per-mode token budgets enforced by `token-budget.js`:

| Tier | Budget | Modes |
|------|--------|-------|
| Tight | 4,000 | plan, review, strategist, legal, psych, infra-architect |
| Standard | 6,000 | writer, analyst, explain, mac, ai-infra |
| Generous | 8,000 | build-py, build-ex, debug, docker |

Warnings at 70-80% usage, hard ceiling at 90-95%. Read-only modes physically cannot call write tools.

## Session Recovery

Session logger creates checkpoints every 5 interactions. On crash, the next session start recovers from the checkpoint: mode context, interaction count, recent knowledge lookups, and active scripts are preserved.

## Three-Tier Scope

| Scope | Location | Purpose |
|-------|----------|---------|
| Project | `.opencode/` | Project-specific config, scripts, knowledge |
| User | `~/.config/opencode/` | Cross-project config, promoted knowledge |
| Public | This repository | Shared modes, templates, community knowledge |

Artifacts promote upward as they prove value: session scripts → library, project knowledge → user knowledge.
