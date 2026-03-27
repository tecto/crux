# BUILD_PLAN_018: Sandbox Execution — Safe Code Running

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** SHOULD-CLOSE
**Competitive Gap:** Codex CLI has sandbox execution (run code in isolated environment). Gemini CLI has sandbox. Crux's DRY_RUN gate is script-level, not runtime sandbox.
**Goal:** Crux can execute code snippets in an isolated sandbox (container or WASM) and return results without affecting the host system.

**Covers:** Sandbox execution, sandbox

## Architecture

```
crux_sandbox_run(code, language) →
    ├── Docker container (if available)
    ├── WASM runtime (if compiled)
    └── Direct execution with tmpdir isolation (fallback)
```

## Phase 1: Tmpdir Isolation (Fallback)

- [ ] 1.1 MCP tool: `sandbox_run(code, language)` — write to temp dir, execute, capture output
- [ ] 1.2 Supported languages: Python, Bash, Rust (cargo run), Node.js
- [ ] 1.3 Timeout enforcement (30s default)
- [ ] 1.4 Capture stdout, stderr, exit code
- [ ] 1.5 Clean up temp dir after execution
- [ ] 1.6 Tests

## Phase 2: Docker Isolation

- [ ] 2.1 If Docker is available, run code in a container
- [ ] 2.2 Mount only the temp dir — no access to host filesystem
- [ ] 2.3 Network disabled by default
- [ ] 2.4 Memory limit (256MB default)
- [ ] 2.5 Tests

## Phase 3: Integration with Safety Pipeline

- [ ] 3.1 Gate 7 (DRY_RUN) can use sandbox for safe execution
- [ ] 3.2 `validate_script` can optionally run script in sandbox to verify
- [ ] 3.3 Tests

## Convergence Criteria
- Code execution in isolated environment
- Timeout and resource limits enforced
- Docker when available, tmpdir fallback
- Two consecutive clean audit passes
