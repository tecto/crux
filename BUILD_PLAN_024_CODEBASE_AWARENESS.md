# BUILD_PLAN_024: Codebase Awareness — Deep Project Understanding

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** SHOULD-CLOSE
**Competitive Gap:** Windsurf has "codebase awareness" — the AI understands project structure deeply. Cursor has indexing. Crux has codebase indexing + analyze_impact but no persistent deep understanding.
**Goal:** Crux maintains a persistent project model — file roles, module boundaries, dependency graph, test coverage map — that informs all tool responses.

**Covers:** codebase awareness, indexing, codebase chat

## Phase 1: Project Model

- [ ] 1.1 `src/awareness.rs` — build and persist project model in `.crux/index/model.json`
- [ ] 1.2 Module detection: identify logical modules from directory structure + imports
- [ ] 1.3 File role classification: source, test, config, documentation, build, generated
- [ ] 1.4 Dependency graph: which modules depend on which (from import graph)
- [ ] 1.5 Auto-refresh: rebuild model on `restore_context` if stale
- [ ] 1.6 Tests

## Phase 2: Context-Aware Tools

- [ ] 2.1 `analyze_impact` uses project model for better file ranking
- [ ] 2.2 `search_code` ranks results by module relevance
- [ ] 2.3 MCP tool: `explain_module(path)` — describe what a module does and its dependencies
- [ ] 2.4 MCP tool: `project_overview()` — high-level project summary with architecture
- [ ] 2.5 Tests

## Convergence Criteria
- Persistent project model with modules, roles, dependencies
- Context-aware tool responses
- Two consecutive clean audit passes
