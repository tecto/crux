# Per-Mode Model Routing in OpenCode

## TL;DR

**OpenCode already supports per-mode model switching natively.** No upstream changes needed. Crux just needs to generate the right agent configuration with YAML frontmatter.

## What OpenCode Already Supports

OpenCode's "agent" system (formerly "modes") allows each agent to override the global model, temperature, tool permissions, and system prompt. This is configured either in `opencode.json` or via markdown files with YAML frontmatter.

### JSON Configuration (opencode.json)

```json
{
  "model": "ollama/crux-think",
  "small_model": "ollama/qwen3.5:9b",
  "agent": {
    "build-py": {
      "description": "Python development with security-first principles",
      "model": "ollama/crux-code",
      "temperature": 0.4,
      "permission": {
        "read": "allow",
        "edit": "allow",
        "bash": "ask"
      }
    },
    "plan": {
      "description": "Software architecture and planning",
      "model": "ollama/crux-think",
      "temperature": 0.6,
      "permission": {
        "read": "allow",
        "edit": "deny",
        "bash": "deny"
      }
    }
  }
}
```

### Markdown Agent Files (preferred for Crux)

Place `.md` files in `~/.config/opencode/agents/` (global) or `.opencode/agents/` (project). The filename becomes the agent name. YAML frontmatter becomes config; markdown body becomes the system prompt.

```markdown
---
model: ollama/crux-code
temperature: 0.4
mode: primary
description: Python development with security-first principles
color: "#3776AB"
permission:
  read: allow
  edit: allow
  bash: ask
  webfetch: deny
---

# Mode: build-py

Python development with security and quality as core principles.

## Core Rules
- Security-first: Validate all inputs, use parameterized queries...
```

### Supported Agent Fields

| Field | Type | Purpose |
|-------|------|---------|
| `model` | `string` | Override model: `provider/model-id` |
| `temperature` | `number` | 0.0–1.0 response randomness |
| `top_p` | `number` | Nucleus sampling |
| `mode` | `string` | `primary`, `subagent`, or `all` |
| `description` | `string` | When to use this agent |
| `steps` | `integer` | Max agentic iterations |
| `permission` | `string\|object` | `ask`/`allow`/`deny` per tool |
| `color` | `string` | Hex color or theme name |
| `disable` | `boolean` | Disable agent |
| `options` | `object` | Custom key-value config |

### File Discovery Paths

1. `~/.config/opencode/agents/*.md` — global agents
2. `.opencode/agents/*.md` — project-specific agents
3. `opencode.json` `"agent"` key — JSON config (merged with file agents)

## What Crux Needs to Change

### 1. Map Crux Modes to Ollama Model Variants

Three model variants, mapped by mode domain:

| Variant | Base Model | Temperature | Modes |
|---------|-----------|-------------|-------|
| `crux-think` | qwen3.5:27b | 0.6 | plan, infra-architect, review, debug, legal, strategist, psych, security, design-review, design-accessibility |
| `crux-code` | qwen3-coder:30b | 0.4 | build-py, build-ex, docker, test, design-ui, design-system, design-responsive |
| `crux-chat` | qwen3.5:27b | 0.7 | writer, analyst, explain, mac, ai-infra |

### 2. Add YAML Frontmatter to Mode Files

Currently Crux mode files in `modes/` are pure markdown with no frontmatter. Each file needs frontmatter added:

```markdown
---
model: ollama/crux-code
temperature: 0.4
mode: primary
description: Python development with security-first principles
color: "#3776AB"
permission:
  read: allow
  edit: allow
  bash: ask
---

# Existing mode prompt content unchanged...
```

**Key decision**: Add frontmatter directly to `modes/*.md` files in the repo. OpenCode reads the frontmatter, non-OpenCode tools ignore it (the `crux_sync.py` `sync_claude_code()` function already strips frontmatter when generating Claude Code agent files).

### 3. Update `crux_sync.py` — Symlink Modes to Agents Directory

OpenCode expects agents in `~/.config/opencode/agents/`, not `~/.config/opencode/modes/`. The `sync_opencode()` function needs to:

```python
# Current: symlinks modes/ → ~/.config/opencode/modes/
# New: symlinks modes/ → ~/.config/opencode/agents/
```

Or symlink to both locations for backward compatibility.

### 4. Update `setup.sh` — Symlink to Agents Directory

The `install_modes()` step currently symlinks to `~/.config/opencode/modes/`. It should symlink to `~/.config/opencode/agents/` instead (or both).

### 5. Update `opencode.json` Template

The `configure_opencode()` step should set the global defaults:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "ollama/crux-think",
  "small_model": "ollama/qwen3.5:9b",
  "provider": {
    "ollama": {
      "options": {
        "endpoint": "http://localhost:11434"
      }
    }
  }
}
```

Per-agent model overrides come from the frontmatter in the agent `.md` files, not from `opencode.json`. This keeps the config clean and the mode files self-contained.

### 6. Tool Permissions Per Mode

Map Crux's existing tool access tiers to OpenCode's permission system:

| Crux Tool Access | OpenCode Permission |
|------------------|-------------------|
| `full` | `{ read: allow, edit: allow, bash: ask }` |
| `read-only` | `{ read: allow, edit: deny, bash: deny }` |
| `limited` | `{ read: allow, edit: deny, bash: deny, webfetch: deny }` |

## Implementation Plan

### Phase 1: Frontmatter (no code changes required for OpenCode)

1. **Write tests** for frontmatter parsing in `test_crux_sync.py`
2. Add YAML frontmatter to all 22 mode `.md` files with correct model, temperature, description, permissions
3. Update `sync_claude_code()` in `crux_sync.py` to strip frontmatter when generating Claude Code agents (may already do this)
4. Verify OpenCode reads the frontmatter correctly by starting a session

### Phase 2: Directory Structure

5. Update `install_modes()` in `setup.sh` to symlink `modes/` → `~/.config/opencode/agents/`
6. Update `sync_opencode()` in `crux_sync.py` for the new directory
7. Update `crux doctor` to check `agents/` symlink
8. Update verification step to check `agents/` directory

### Phase 3: Dynamic Model Routing (future, if needed)

If the user wants to switch models dynamically within a session (e.g., start in plan mode with crux-think, switch to build-py with crux-code), this already works via OpenCode's Tab key to cycle agents. Each agent loads its configured model.

For more advanced routing (auto-switch based on task type), this would require an OpenCode plugin:

```typescript
// Hypothetical plugin that intercepts mode switches
export const ModelRouterPlugin = async (ctx) => {
  return {
    'agent.switch': async ({}, { agent }) => {
      // Could log, adjust, or validate model switches
    }
  };
};
```

This is not needed for Phase 1-2 — Tab switching with per-agent models handles the use case.

## Risks and Considerations

1. **OpenCode repo status**: The `opencode-ai/opencode` GitHub repo was archived Sept 2025. The project has moved to [sst/opencode](https://github.com/sst/opencode) and is actively maintained there. The docs at opencode.ai are current (updated 2026). Verify the agent frontmatter format hasn't changed in the `sst/opencode` fork.

2. **Ollama model loading**: With 3 model variants (crux-think, crux-code, crux-chat), switching agents means Ollama may need to swap models in GPU memory. With 64GB RAM and `OLLAMA_MAX_LOADED_MODELS=2`, two models stay hot. The third will have a cold-start delay (~5-10s). Consider setting `OLLAMA_MAX_LOADED_MODELS=3` if RAM allows.

3. **Frontmatter backward compatibility**: Tools that don't understand YAML frontmatter will see `---` as text. Claude Code's agent sync (`sync_claude_code()`) must strip it. Test this explicitly.

4. **Mode file ownership**: Adding frontmatter changes the mode files in the repo. This is a one-time migration. All 22 files need updating simultaneously to avoid partial states.

## Sources

- [OpenCode Modes Documentation](https://opencode.ai/docs/modes/)
- [OpenCode Agents Documentation](https://opencode.ai/docs/agents/)
- [OpenCode Config Documentation](https://opencode.ai/docs/config/)
- [OpenCode Models Documentation](https://opencode.ai/docs/models/)
- [OpenCode Config Schema](https://opencode.ai/config.json)
- [OpenCode GitHub (sst/opencode)](https://github.com/sst/opencode)
- [DeepWiki: OpenCode Agent Architecture](https://deepwiki.com/baumaxt/opencode/8.2-agents)
