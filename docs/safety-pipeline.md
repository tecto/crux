# Five-Gate Safety Pipeline

## Overview

All script execution flows through the `run_script` tool which implements five sequential safety gates. The main model calls `run_script`, and all gates run internally. The model cannot bypass or reason about the validation logic.

## Gate 1: Pre-Flight Validation

Deterministic checks (always runs, implemented in `preflight_validator.py`):

1. Shebang present (`#!/bin/bash` or similar)
2. Risk header declared (low/medium/high)
3. `set -euo pipefail` safety clause present
4. `main()` function pattern used
5. Risk level matches operations (low-risk scripts cannot contain destructive ops)
6. DRY_RUN support for medium+ risk
7. Path containment (no writes to root filesystem)
8. Transaction pattern for multi-file modifications

**On failure**: Script never executes. Error returned to model for correction.

## Gate 2: 8B Adversarial Audit

A different model (8B) reviews the script as a security auditor, looking for data loss, corruption, unintended side effects, and scope creep. Using a different model prevents self-enhancement bias.

**On failure**: Concerns returned to the main model for review and resolution.

## Gate 3: 32B Second-Opinion

High-risk scripts only. The primary model (32B) performs a second review of both the script and the 8B audit findings.

## Gate 4: Human Approval

High-risk scripts require explicit user approval. The tool returns a request for approval with full audit results.

## Gate 5: DRY_RUN

Medium+ risk scripts execute with `DRY_RUN=1` environment variable first. The script must handle this variable and simulate operations without side effects.

## Risk Levels

| Level | Examples | Gates |
|-------|----------|-------|
| Low | Read configs, format code | 1 only |
| Medium | Modify configs, update deps | 1, 2, 5 |
| High | Delete data, deploy, modify system | 1, 2, 3, 4, 5 |
