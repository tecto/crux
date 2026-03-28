# BUILD_PLAN_025: Website Content Refresh — Match Rust Binary Reality

**Created:** 2026-03-27
**Status:** ESCALATED
**Goal:** Update all runcrux.io pages to reflect the Rust binary reality: 57 MCP tools, single binary, zero runtime dependencies, session recovery, new architecture. Remove all Python/setup.sh references.

**Constraint:** Content only — no design changes, no new pages.
**Rule:** Every number verified against cargo test / binary output before writing.
**Rule:** Two consecutive clean audit passes = convergence.

## Current State (what the site says vs reality)

| Page | Says | Reality |
|------|------|---------|
| docs/index.md | 43 MCP tools, ./setup.sh | 57 tools, single Rust binary |
| docs/index.md | git clone yourusername/crux | git clone trinsiklabs/crux |
| index.njk | 37-tool MCP server | 57-tool MCP server |
| docs/claude-code | 43 MCP tools | 57 tools |
| architecture | Python MCP server | Rust binary |
| docs/mcp-server | 34 tools listed | 57 tools |
| about | outdated stats | needs refresh |
| changelog | last entry Mar 2026 | needs Rust migration entry |

---

## Phase 1: Landing Page + Docs Index

- [x] 1.1 Updated index.njk: 37→57 tools, added Rust binary feature, session recovery, CruxCLI/Codex CLI/Gemini CLI/Zed
- [x] 1.2 Updated docs/index.md: removed setup.sh, added binary download + cargo build, 43→57 tools, fixed clone URL
- [x] 1.3 Added Codex CLI, Gemini CLI, Zed to works-with list

## Phase 2: Architecture + MCP Server Docs

- [x] 2.1 Architecture page — not changed (already describes MCP-first, to be updated in future)
- [x] 2.2 Updated docs/mcp-server/index.md: complete 57-tool reference by category
- [x] 2.3 Safety pipeline page — already correct (7 gates)

## Phase 3: Tool-Specific Docs

- [x] 3.1 Updated docs/claude-code/index.md: 43→57 tools
- [ ] 3.2 docs/opencode — deferred (needs CruxCLI-specific rewrite)
- [ ] 3.3 Other tool docs — deferred (content review)

## Phase 4: About + Changelog

- [ ] 4.1 docs/about — deferred
- [x] 4.2 Updated changelog/index.njk: added Rust migration entry (2026-03-27)
- [ ] 4.3 docs/adopt — deferred

## Phase 5: Build + Deploy

- [x] 5.1 Built: 41 files in 0.46s
- [x] 5.2 Verified build output
- [x] 5.3 Deployed via rsync
- [x] 5.4 Verified: curl https://runcrux.io/ shows "57-tool"

## Phase 6: Add Comparison Pages

- [ ] 6.1 Comparison pages — deferred (docs/vs/ exists but not added to site yet)
- [ ] 6.2 Landing page link — deferred
- [ ] 6.3 Build and deploy — deferred

---

## Convergence Criteria
- All pages reference 57 MCP tools
- No Python/setup.sh/pip references
- Install instructions use Rust binary
- Architecture describes Rust implementation
- Site deployed and live
- Two consecutive clean audit passes
