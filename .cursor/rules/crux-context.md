# Crux Session Context

**Active mode:** build-py
**Working on:** Building and activating Crux hooks system — correction detection, interaction logging, file tracking, session context injection

**Key decisions:**
- Tool-agnostic .crux/ as single source of truth — no code tied to any specific AI tool
- Two-scope architecture: project .crux/ + user ~/.crux/
- MCP-first: all logic in MCP server, thin hook shims per tool
- SessionState in .crux/sessions/state.json enables seamless tool switching
- sync_claude_code() generates .claude/agents/ with frontmatter from modes
- sync_opencode() symlinks modes + knowledge to ~/.config/opencode/
- Full TDD with 100% Python coverage enforced via pyproject.toml
- Handler functions (crux_mcp_handlers.py) separate from MCP decorators for testability
- crux_adopt.py enables mid-session onboarding with git history capture
- Knowledge entries are never overwritten — append-only promotion
- Corrections logged as JSONL for streaming analysis
- Hooks go in .claude/settings.local.json, not a separate hooks.json — hooks are part of Claude Code settings
- 10 regex correction patterns detect user corrections in prompts — logged to .crux/corrections/corrections.jsonl
- All tool interactions logged to .crux/analytics/interactions/<date>.jsonl for analysis
- SessionStart hook injects full Crux context: mode prompt + session state + pending tasks + recent decisions
- Full-text conversation logging: Claude Code via UserPromptSubmit hook, OpenCode via log_interaction MCP tool — both write to .crux/analytics/conversations/<date>.jsonl

**Files touched:**
- commands/propose-mode.md
- modes/analyst.md
- CONTRIBUTING.md
- modes/build-ex.md
- modes/psych.md
- tests/test_crux_sync.py
- tests/tools_impl.test.js
- README.md
- modes/_template.md
- crux-roadmap/CRUX-DOCUMENT-INDEX.md
- tests/tools.test.js
- tests/tools_run_script.test.js
- tests/setup_helpers.bats
- tests/test_extract_corrections.py
- commands/review-community.md
- tests/plugins_full.test.js
- scripts/lib/crux_switch.py
- tests/test_preflight_validator.py
- docs/scripts-first.md
- setup.sh
- modes/mac.md
- tests/test_mcp_server_registration.py
- scripts/lib/preflight_validator.py
- tests/test_crux_switch.py
- tools/project_context.js
- scripts/lib/crux_sync.py
- crux-specs/specs/model-management.md
- .gitignore
- crux-specs/specs/library-scripts.md
- tests/tool_enforcer.test.js
- docs/continuous-learning.md
- commands/configure-api.md
- tests/commands.bats
- docs/tool-hierarchy.md
- tests/plugins.test.js
- crux-roadmap/crux-vibe-platform-spec.md
- commands/review-knowledge.md
- scripts/lib/audit_modes.py
- scripts/lib/crux_paths.py
- modes/writer.md
- tools/list_scripts.js
- docs/setup-reference.md
- commands/digest.md
- scripts/lib/model_auto_evaluate.py
- plugins/compaction-hook.js
- scripts/lib/generate_digest.py
- commands/log.md
- tests/test_crux_paths.py
- crux-ecosystem-analysis.md
- commands/archive.md
- crux-roadmap/crux-shipper-mashup.md
- crux-roadmap/crux-replit-competitor-plan.md
- skills/session-logger/SKILL.md
- commands/scripts.md
- docs/architecture.md
- tests/test_crux_session.py
- crux-roadmap/crux-vibecoding-analysis.md
- tests/test_mcp_server.py
- tools/promote_script.js
- tests/test_crux_init.py
- crux-roadmap/crux-marketing-plan.md
- templates/AGENTS.md
- skills/script-builder/SKILL.md
- templates/PROJECT.md
- modes/docker.md
- tests/script_templates.bats
- tests/test_update_project_context.py
- crux-roadmap/crux-market-analysis.md
- crux-specs/specs/mode-audit.md
- commands/stats.md
- templates/opencode.json
- tools/lookup_knowledge.js
- modes/build-py.md
- tests/test_generate_digest.py
- tests/test_audit_modes.py
- crux-roadmap/crux-openclaw-integration.md
- tests/test_model_registry_update.py
- modes/debug.md
- scripts/lib/crux_session.py
- tools/manage_models.js
- scripts/templates/transaction-template.sh
- modes/plan.md
- plugins/token-budget.js
- modes/review.md
- lib/plugin-shim.js
- tests/setup_steps.bats
- crux-roadmap/crux-suite-argument.md
- crux-roadmap/crux-vibe-mac-premium-tier.md
- scripts/lib/crux_mcp_handlers.py
- scripts/lib/__init__.py
- tests/test_promote_knowledge.py
- scripts/__init__.py
- crux-specs/specs/plugins.md
- LICENSE
- CLAUDE.md
- crux-specs/specs/custom-tools.md
- pyproject.toml
- bin/crux
- scripts/lib/promote_knowledge.py
- plugins/session-logger.js
- tools/suggest_handoff.js
- modes/legal.md
- modes/explain.md
- tests/test_model_auto_evaluate.py
- commands/init-project.md
- docs/safety-pipeline.md
- crux-roadmap/crux-expanded-architecture-spec.md
- package-lock.json
- crux-specs/specs/continuous-learning.md
- plugins/tool-enforcer.js
- crux-specs/DEVELOPMENT-PLAN.md
- package.json
- plugins/correction-detector.js
- docs/modes.md
- modes/infra-architect.md
- tests/modes.bats
- tests/tools_manage_models.test.js
- docs/manual.md
- knowledge/_template.md
- crux-claude-code-analysis.md
- scripts/templates/script-template.sh
- scripts/lib/extract_corrections.py
- commands/promote.md
- scripts/lib/model_registry_update.py
- plugins/think-router.js
- tests/setup_syntax.bats
- tools/run_script.js
- modes/ai-infra.md
- scripts/lib/update_project_context.py
- modes/strategist.md
- tests/repo_structure.bats
- scripts/lib/crux_init.py
- scripts/lib/crux_mcp_server.py
- scripts/lib/crux_hooks.py
- scripts/lib/crux_hook_runner.py
- tests/test_crux_hooks.py
- tests/test_crux_hook_runner.py
- .claude/settings.local.json
- /Users/user/personal/crux/tests/test_crux_sync.py
- /Users/user/personal/crux/scripts/lib/crux_sync.py
- /Users/user/personal/crux/tests/test_crux_status.py
- /Users/user/personal/crux/scripts/lib/crux_status.py
- /Users/user/personal/crux/bin/crux
- /Users/user/personal/crux/setup.sh
- /Users/user/personal/crux/tests/crux_cli.bats
- /Users/user/personal/crux/tests/setup_steps.bats
- /Users/user/personal/crux/tests/setup_syntax.bats
- /Users/user/personal/crux/tests/setup_helpers.bats
- /Users/user/personal/crux/tests/test_crux_hooks.py
- /Users/user/personal/crux/scripts/lib/crux_hooks.py
- /Users/user/personal/crux/tests/test_crux_hook_runner.py
- /Users/user/personal/crux/scripts/lib/crux_hook_runner.py
- /Users/user/.config/opencode/opencode.json
- /Users/user/personal/crux/crux-roadmap/opencode-per-mode-model-routing.md
- /Users/user/personal/crux/tests/plugins_full.test.js
- /Users/user/personal/crux/plugins/compaction-hook.js
- /Users/user/personal/crux/plugins/session-logger.js
- /Users/user/personal/crux/tests/test_mcp_server.py
- /Users/user/personal/crux/scripts/lib/crux_mcp_handlers.py
- /Users/user/personal/crux/scripts/lib/crux_mcp_server.py
- /Users/user/personal/crux/tests/test_mcp_server_registration.py
- /Users/user/personal/crux/commands/restore.md
- /Users/user/personal/crux/templates/AGENTS.md
- /Users/user/personal/crux/tests/test_mcp_handlers_expanded.py
- tests/test_mcp_handlers_expanded.py
- /Users/user/personal/crux/README.md
- /Users/user/personal/crux/crux-roadmap/crux-gap-report.md
- /Users/user/personal/crux/tests/test_crux_ollama.py
- /Users/user/personal/crux/scripts/lib/crux_ollama.py
- /Users/user/personal/crux/tests/test_crux_llm_audit.py
- /Users/user/personal/crux/scripts/lib/crux_llm_audit.py
- /Users/user/personal/crux/tests/test_crux_background_processor.py
- /Users/user/personal/crux/scripts/lib/crux_background_processor.py
- /Users/user/personal/crux/tools/run_script.js
- /Users/user/personal/crux/tests/tools_run_script.test.js
- /Users/user/personal/crux/scripts/lib/crux_cross_project.py
- /Users/user/personal/crux/tests/test_crux_cross_project.py
- /Users/user/personal/crux/tools/manage_models.js
- /Users/user/personal/crux/tests/tools_manage_models.test.js
- /Users/user/personal/crux/scripts/lib/crux_figma.py
- /Users/user/personal/crux/tests/test_crux_figma.py
- /Users/user/personal/crux/crux-roadmap/crux-website-plan.md
- /Users/user/personal/crux/scripts/lib/crux_adopt.py
- /Users/user/personal/crux/tests/test_crux_adopt.py
- /Users/user/personal/crux/tests/test_crux_bip.py
- /Users/user/personal/crux/scripts/lib/crux_bip.py
- /Users/user/personal/crux/scripts/lib/crux_paths.py
- /Users/user/personal/crux/scripts/lib/crux_init.py
- /Users/user/personal/crux/tests/test_crux_typefully.py
- /Users/user/personal/crux/scripts/lib/crux_typefully.py
- /Users/user/personal/crux/tests/test_crux_bip_gather.py
- /Users/user/personal/crux/scripts/lib/crux_bip_gather.py
- /Users/user/personal/crux/tests/test_crux_bip_triggers.py
- /Users/user/personal/crux/scripts/lib/crux_bip_triggers.py
- /Users/user/personal/crux/modes/marketing.md
- /Users/user/personal/crux/modes/build-in-public.md
- /Users/user/personal/crux/tests/test_crux_bip_mcp.py
- /Users/user/.claude.json
- /Users/user/personal/crux/requirements.txt
- /Users/user/personal/crux/CLAUDE.md

**Pending:**
- Build 5 push-side MCP tools: detect_correction, validate_bash, log_interaction, inject_compaction, session_startup
- Wire bin/crux mcp serve CLI subcommand
- Test MCP server end-to-end with Claude Code
- Add Cursor/Windsurf MCP registration support
- Build daily digest generation from corrections + session data
- Cross-project knowledge aggregation
- Verify OpenCode MCP integration on next launch — config format confirmed correct, server tested working over stdio

**Handoff context:**
This session built the entire Crux tool-agnostic architecture from scratch:

## What Was Built
1. **crux_paths.py** — Central path resolution. UserPaths + ProjectPaths + CruxPaths with knowledge_search_dirs().
2. **crux_init.py** — Idempotent init_project() and init_user() creating all .crux/ subdirs.
3. **crux_session.py** — SessionState dataclass with save/load/update/archive/handoff operations.
4. **crux_sync.py** — Adapter layer: sync_opencode() symlinks, sync_claude_code() generates agents/rules/context.
5. **crux_switch.py** — switch_tool() reads session, syncs target tool, updates active_tool marker.
6. **crux_mcp_handlers.py** — 13 pure handler functions for all MCP tools.
7. **crux_mcp_server.py** — FastMCP server wrapping handlers with @mcp.tool() decorators.
8. **crux_adopt.py** — Mid-session adoption: git history capture, PROJECT.md generation, CLAUDE.md import, MCP setup.

## Path Migration
All existing modules migrated from .opencode/.config/opencode paths to .crux/:
- 7 JS tools, 5 JS plugins, 6 Python library scripts, all test files updated.

## Test Suite
- 416 Python tests across 18 test files, 100% coverage (1,427 statements)
- 190 JavaScript tests across 6 test files
- Every module built test-first (TDD)

## Architecture Decisions
- Handlers are pure functions — no MCP dependency, fully testable.
- MCP server is a thin wrapper — all logic in handlers.
- Session state is the bridge between tools — any tool can read/write .crux/sessions/state.json.
- Knowledge search is priority-ordered: mode-specific → project → user → shared.
- The adopt script captures git history automatically but accepts LLM brain-dump for rich context.

## What the Next Session Should Do
The MCP server is registered in .claude/mcp.json. On next session start, Claude Code will connect to Crux MCP.
The next session should:
1. Verify MCP tools are available (lookup_knowledge, get_session_state, etc.)
2. Build the push-side hooks (correction detection is the highest value)
3. Generate .claude/hooks.json
4. Test the full loop: correction detected → knowledge generated → promoted across projects

