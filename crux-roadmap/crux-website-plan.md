# Crux Website Plan: runcrux.io

## Current State

The site exists as an 11ty project in `site/` with:
- Landing page (index.njk) — hero, works-with, what-is, features, latest posts
- Blog index + 3 blog posts (day-1, crux-adopt, mcp-server)
- Docs stub (/docs/) — install instructions + broken links to tool-specific pages
- Changelog stub (/changelog/) — "no releases yet"
- RSS feed (feed.njk)
- Post layout (post.njk) with tweet cross-reference support
- Base layout (base.njk) with nav: blog, docs, changelog, github
- Minimal CSS with dark/light mode, monospace headings, system font body
- Deployment via rsync to runcrux.io

## Broken Links (must fix)

1. `/docs/claude-code/` — linked from docs index, page does not exist
2. `/docs/opencode/` — linked from docs index, page does not exist
3. `/docs/cursor/` — linked from docs index, page does not exist
4. `/docs/aider/` — linked from docs index, page does not exist
5. `/docs/roo-code/` — linked from docs index, page does not exist
6. `/docs/qwen-agent/` — linked from docs index, page does not exist
7. `/modes/` — linked from docs index ("see modes directory"), page does not exist

## Pages to Build

### Tier 1: Fix broken links and fill stubs (required)

| # | Page | Path | Description |
|---|------|------|-------------|
| 1 | Docs: Claude Code | `/docs/claude-code/` | How Crux works with Claude Code — hooks, MCP, setup |
| 2 | Docs: OpenCode | `/docs/opencode/` | How Crux works with OpenCode — plugins, MCP, setup |
| 3 | Docs: Cursor | `/docs/cursor/` | How Crux works with Cursor — MCP-only, .cursor/rules/, setup |
| 4 | Docs: Aider | `/docs/aider/` | How Crux works with Aider — MCP connection, limitations |
| 5 | Docs: Roo Code | `/docs/roo-code/` | How Crux works with Roo Code — MCP connection |
| 6 | Docs: Qwen-Agent | `/docs/qwen-agent/` | How Crux works with Qwen-Agent — MCP connection |
| 7 | Modes directory | `/modes/` | All 23 modes listed with category, description, think/no-think |
| 8 | Docs index rewrite | `/docs/` | Expand from stub to proper getting-started guide |
| 9 | Changelog | `/changelog/` | Populate from git history or write manual entries |

### Tier 2: Pages specified in marketing plan (high value)

| # | Page | Path | Description |
|---|------|------|-------------|
| 10 | About | `/about/` | Solo founder story, philosophy, .crux/ explained, the "why" |
| 11 | Docs: Windsurf | `/docs/windsurf/` | How Crux works with Windsurf — MCP, .windsurf/rules/ |

### Tier 3: Recommended additions (differentiation and SEO)

| # | Page | Path | Rationale |
|---|------|------|-----------|
| 12 | Architecture | `/architecture/` | Visual architecture diagram, MCP server as brain, .crux/ directory structure. This is the single most compelling technical page — shows Crux isn't a wrapper, it's infrastructure. |
| 13 | Safety Pipeline | `/docs/safety-pipeline/` | The 7-gate pipeline explained with diagram. Unique differentiator — no other tool has this. |
| 14 | Docs: MCP Server | `/docs/mcp-server/` | All 34 tools listed with descriptions. For developers integrating Crux into any MCP-compatible tool. |
| 15 | Docs: Modes deep-dive | `/docs/modes/` | How modes work, how to create custom modes, frontmatter spec. Complements the /modes/ directory listing. |
| 16 | Docs: crux switch | `/docs/switching/` | The killer feature explained — how tool switching works, what state transfers, demo walkthrough. |
| 17 | Docs: crux adopt | `/docs/adopt/` | Mid-session onboarding explained. The cold-start problem and how adopt solves it. |
| 18 | 404 page | `/404.html` | Custom 404 with nav back to home. Professional touch. |

## Pages NOT recommended right now

- Pricing / commercial page (cruxvibe.io is separate, product not ready)
- Discord/community page (no community yet)
- Comparison pages (Crux vs Cursor, etc.) — better as blog posts for SEO
- Contributors page (no contributors yet)
- Roadmap page (changes too fast, better in GitHub)

## Site Map (final)

```
runcrux.io/
├── /                           # Landing page
├── /about/                     # Founder story + philosophy (top-level)
├── /architecture/              # Architecture diagram + MCP explanation (top-level)
├── /safety-pipeline/           # 7-gate pipeline explained (top-level)
├── /switching/                 # Tool switching guide (top-level)
├── /adopt/                     # Mid-session onboarding guide (top-level)
├── /modes/                     # Mode directory — 23 modes listed (top-level)
├── /blog/                      # Build-in-public blog index
│   ├── /blog/day-1-starting-crux/
│   ├── /blog/wiring-crux-adopt/
│   └── /blog/mcp-server-is-product/
├── /docs/                      # Getting started guide (top-level dropdown nav)
│   ├── /docs/claude-code/      # Tool: Claude Code
│   ├── /docs/opencode/         # Tool: OpenCode
│   ├── /docs/cursor/           # Tool: Cursor
│   ├── /docs/windsurf/         # Tool: Windsurf
│   ├── /docs/aider/            # Tool: Aider
│   ├── /docs/roo-code/         # Tool: Roo Code
│   ├── /docs/qwen-agent/       # Tool: Qwen-Agent
│   ├── /docs/mcp-server/       # MCP server reference (34 tools)
│   └── /docs/modes/            # Modes system deep-dive (how to create/customize)
├── /changelog/                 # Release history
├── /feed.xml                   # RSS feed
└── /404.html                   # Custom 404
```

## Navigation Update

Current nav: `blog | docs | changelog | github`

New nav: `docs (dropdown) | modes | blog | changelog | github`

Docs dropdown contains:
- Getting Started
- Claude Code
- OpenCode
- Cursor
- Windsurf
- Aider
- Roo Code
- Qwen-Agent
- MCP Server
- Modes System

Top-level pages (not in dropdown): architecture, safety-pipeline, switching, adopt, about, modes

## Footer Update

Add links: `github | docs | blog | rss | about`

## Build Order

1. Fix broken links first (Tier 1: pages 1-9)
2. Add About and Windsurf docs (Tier 2: pages 10-11)
3. Add differentiation pages (Tier 3: pages 12-18)

Total: 18 pages to build.

## Design Notes

Per marketing plan:
- All lowercase copy (matching voice), proper nouns capitalized
- Monospace headings, system font body
- Dark mode default, light mode via prefers-color-scheme
- No tracking, no cookies, no JavaScript
- Target < 50ms TTFB, < 100KB page weight
- No Tailwind, no framework — hand-written CSS

## Content Sources

Each page can be built from existing repo content:
- Tool docs: `scripts/lib/crux_sync.py` (adapter logic), `README.md` (tool descriptions)
- Modes: `modes/*.md` (23 mode files with frontmatter)
- Safety pipeline: `docs/` directory, `README.md` pipeline table
- MCP server: `scripts/lib/crux_mcp_server.py` (34 tool definitions)
- Architecture: `crux-roadmap/crux-marketing-plan.md` (ASCII diagram), `README.md`
- About: Marketing plan Section 0 (core message) + Section 1 (build-in-public philosophy)
