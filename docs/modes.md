# Mode Design Principles

## Overview

Crux uses 24 specialized modes instead of a single general-purpose system prompt. Each mode is optimized for a specific domain with its own persona, tool access, and reasoning style.

## Design Rules

Every mode prompt follows four empirically-validated rules:

1. **Positive framing only**: Research shows negative instructions ("don't do X") measurably degrade LLM output. All instructions use positive framing ("do Y instead").

2. **Simple task-relevant personas**: Each mode defines a clear, domain-specific persona. Complex or multi-faceted personas reduce coherence.

3. **Critical rules at prime positions**: The model pays most attention to the start and end of system prompts. Critical behavioral constraints appear in these positions.

4. **150-200 word target**: Research indicates this is the optimal length range for mode prompts. Shorter prompts lack specificity; longer prompts waste context and increase drift.

## Mode Categories

### Core Coding (3)
- **build-py**: Python development (no_think, full tools)
- **build-ex**: Elixir/Phoenix/Ash (no_think, full tools)
- **test**: Test-first development (no_think, full tools)

### Architecture and Planning (3)
- **plan**: Software architecture (think, read-only)
- **infra-architect**: Deployment/CI-CD (think, read-only)
- **debug**: Root cause analysis (think, full tools)

### Quality (2)
- **review**: Code review (think, read-only)
- **security**: Adversarial vulnerability analysis (think, read-only)

### Creative and Communication (5)
- **writer**: Professional writing (no_think, read-only)
- **analyst**: Data analysis (no_think, full tools)
- **explain**: Teaching/mentoring (no_think, read-only)
- **marketing**: Marketing strategy/copywriting (no_think, read-only)
- **build-in-public**: Shipping update content (no_think, full tools)

### Domain Expertise (3)
- **psych**: ACT/Attachment/Shadow/Somatic (think, read-only)
- **legal**: Legal research (think, read-only)
- **strategist**: First principles strategy (think, read-only)

### Infrastructure (4)
- **ai-infra**: LLM infrastructure (no_think, full tools)
- **mac**: macOS systems (no_think, read-only)
- **docker**: Container operations (no_think, full tools)

### Design (5)
- **design-ui**: UI component implementation (no_think, full tools)
- **design-system**: Design system creation (no_think, full tools)
- **design-review**: Design quality review (think, read-only)
- **design-responsive**: Responsive layout (no_think, full tools)
- **design-accessibility**: WCAG compliance (think, read-only)

## Think vs No-Think Routing

The `think-router` plugin automatically prepends `/think` or `/no_think` based on mode. Think modes use higher temperature (0.6) for reasoning. No-think modes use lower temperature (0.7) for direct execution.

## Mode Auditing

The `audit_modes.py` script validates all mode prompts against the four design rules, checking word count, positive framing, and persona presence.
