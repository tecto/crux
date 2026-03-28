# BUILD_PLAN_025: Website Content Refresh — Match Rust Binary Reality

**Created:** 2026-03-27
**Status:** IN PROGRESS
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

- [ ] 1.1 Update `site/src/index.njk`: "37-tool" → "57-tool", add "single Rust binary" feature, add CruxCLI to tools list
- [ ] 1.2 Update `site/src/docs/index.md`: remove setup.sh install, replace with `curl` install or binary download. Update 43→57 tools. Fix clone URL.
- [ ] 1.3 Add Codex CLI and Gemini CLI to "works with" list (they support MCP)

## Phase 2: Architecture + MCP Server Docs

- [ ] 2.1 Update `site/src/architecture/index.md`: Python → Rust architecture, 6.6MB binary, tree-sitter AST
- [ ] 2.2 Update `site/src/docs/mcp-server/index.md`: list all 57 tools (generate from `crux mcp status`)
- [ ] 2.3 Update `site/src/safety-pipeline/index.md`: ensure 7 gates described correctly

## Phase 3: Tool-Specific Docs

- [ ] 3.1 Update `site/src/docs/claude-code/index.md`: 57 tools, Rust binary hook runner, session recovery
- [ ] 3.2 Update `site/src/docs/opencode/index.md`: update for CruxCLI fork, Rust MCP binary
- [ ] 3.3 Review all other tool docs (cursor, windsurf, aider, roo-code, qwen-agent) for accuracy

## Phase 4: About + Changelog

- [ ] 4.1 Update `site/src/about/index.md`: current stats (57 tools, Rust binary, 109+ tests)
- [ ] 4.2 Update `site/src/changelog/index.njk`: add Rust migration milestone entry
- [ ] 4.3 Update `site/src/adopt/index.md`: describe `crux adopt` Rust command

## Phase 5: Build + Deploy

- [ ] 5.1 Build site: `cd site && npm install && npm run build`
- [ ] 5.2 Verify build output
- [ ] 5.3 Deploy: `./deploy-runcrux.io.sh --build --force`
- [ ] 5.4 Verify live at runcrux.io

## Phase 6: Add Comparison Pages

- [ ] 6.1 Add `site/src/vs/` directory with comparison pages from docs/vs/
- [ ] 6.2 Link from landing page: "See how Crux compares"
- [ ] 6.3 Build and deploy

---

## Convergence Criteria
- All pages reference 57 MCP tools
- No Python/setup.sh/pip references
- Install instructions use Rust binary
- Architecture describes Rust implementation
- Site deployed and live
- Two consecutive clean audit passes
