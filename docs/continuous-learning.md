# Continuous Learning System

## Overview

Crux learns from real session data without manual curation. The five-level learning pipeline detects patterns, generates knowledge, and promotes insights across projects.

## Level 1: Real-Time Correction Detection

The `correction-detector.js` plugin monitors every message for:
- **Self-corrections**: "actually", "wait", "let me fix", "I was wrong"
- **Negations**: "no", "wrong", "that's not right", "not what I asked"
- **Retry requests**: "try again", "redo that", "start over"
- **Tool retries**: Same tool called with different params (excludes read/glob/grep)

Detections are written to `~/.config/opencode/reflections/{date}.jsonl` in real-time.

## Level 2: Session Logging

The `session-logger.js` plugin captures 100% of interactions:
- Append-only JSONL format (survives truncation)
- Checkpoints every 5 interactions for crash recovery
- Tracks mode usage, tool calls, knowledge lookups, active scripts

## Level 3: Batch Extraction

`extract_corrections.py` runs at session end or on demand:
- Scans JSONL reflections for correction patterns
- Clusters corrections by category and mode
- Generates knowledge entry candidates from clusters meeting threshold

## Level 4: Knowledge Promotion

`promote_knowledge.py` promotes entries through three tiers:
- **Project** (`.opencode/knowledge/`): Project-specific patterns
- **User** (`~/.config/opencode/knowledge/`): Cross-project patterns
- **Public** (this repo): Community-shared patterns

## Level 5: Analytics and Evaluation

- `generate_digest.py`: Daily analytics aggregation (sessions, interactions, corrections, tool usage)
- `model_auto_evaluate.py`: Tests models against real correction scenarios for quality comparison
- `audit_modes.py`: Validates mode prompts against empirical design rules

## Data Flow

```
User interaction
    ↓
correction-detector (real-time) → reflections.jsonl
session-logger (real-time) → session.jsonl
    ↓
extract_corrections (batch) → knowledge candidates
    ↓
promote_knowledge → project → user → public
    ↓
generate_digest (daily) → daily analytics
model_auto_evaluate (periodic) → model comparison
```
