# BUILD_PLAN_020: Worktrees — Isolated Branch Workspaces

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** SHOULD-CLOSE
**Competitive Gap:** Claude Code has worktrees (isolated git worktree for experiments). Crux has no workspace isolation.
**Goal:** `crux worktree create <name>` creates a git worktree in `.crux/worktrees/`, switches the session context to it. `crux worktree done` merges or discards. Session state is preserved per-worktree.

**Covers:** worktrees

## Architecture

```
$ crux worktree create auth-experiment
Created worktree at .crux/worktrees/auth-experiment
Switched session context to auth-experiment branch

[work happens in worktree]

$ crux worktree done --merge
Merged auth-experiment into main
Cleaned up worktree
```

## Phase 1: Worktree Management

- [ ] 1.1 `crux worktree create <name>` — `git worktree add .crux/worktrees/<name> -b <name>`
- [ ] 1.2 `crux worktree list` — list active worktrees
- [ ] 1.3 `crux worktree switch <name>` — update session state to point at worktree
- [ ] 1.4 `crux worktree done [--merge|--discard]` — clean up
- [ ] 1.5 Tests

## Phase 2: Session Isolation

- [ ] 2.1 Each worktree gets its own `.crux/sessions/state.json` (in the worktree, not main)
- [ ] 2.2 `restore_context` detects if running in a worktree and loads worktree-specific state
- [ ] 2.3 Handoff carries worktree context when switching back to main
- [ ] 2.4 Tests

## Phase 3: MCP Tools

- [ ] 3.1 `create_worktree(name)` MCP tool
- [ ] 3.2 `list_worktrees()` MCP tool
- [ ] 3.3 `switch_worktree(name)` MCP tool
- [ ] 3.4 `finish_worktree(action)` MCP tool (merge or discard)
- [ ] 3.5 Tests

## Convergence Criteria
- Git worktree creation and cleanup
- Per-worktree session state
- MCP tools for in-session worktree management
- Two consecutive clean audit passes
