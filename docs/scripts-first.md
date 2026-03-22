# Scripts-First Philosophy

## Principle

The AI does not directly modify files. Everything flows through scripts in `.crux/scripts/`. Scripts are templated, validated, tested, and can be promoted to reusable library status.

## Why Scripts-First

1. **Auditability**: Every file modification is traceable to a specific script with metadata (risk level, author, timestamp)
2. **Reversibility**: Scripts can be re-run, DRY_RUN tested, and rolled back
3. **Safety**: The five-gate pipeline validates every script before execution
4. **Learning**: Script patterns are captured, successful scripts promote to library status
5. **Reproducibility**: Library scripts work across projects and sessions

## Script Lifecycle

```
Session Script (.crux/scripts/session/)
    ↓ promote_script tool
Library Script (.crux/scripts/lib/)
    ↓ manual promotion
Archive (.crux/scripts/archive/)
```

## Script Template

Every script must include:
- Shebang (`#!/bin/bash`)
- Risk classification header (low/medium/high)
- `set -euo pipefail` safety clause
- `main()` function pattern
- DRY_RUN support (medium+ risk)
- Transaction pattern (multi-file modifications)

## Validation

The `preflight_validator.py` performs 8 deterministic checks on every script before execution. Scripts that fail validation never execute.
