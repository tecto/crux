# BUILD_PLAN_017: AI Completion — Inline Code Suggestions

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** SHOULD-CLOSE
**Competitive Gap:** Cursor has AI completion (inline suggestions as you type). Crux has no real-time completion — only tool-based interactions.
**Goal:** Crux provides completion suggestions via MCP resources or a completion-specific tool that IDEs can query for inline suggestions.

**Covers:** AI completion, codebase chat, multi-file edit

## Architecture

Crux can't inject into editor keystroke handling directly. Instead:
- Expose completion context via MCP resources (file content + cursor position)
- Provide `suggest_completion(file, line, column)` MCP tool
- IDE plugins (Cursor, VS Code, Zed) call this tool for suggestions

## Phase 1: Completion Context

- [ ] 1.1 MCP tool: `suggest_completion(file, line, context_before, context_after)` — returns completion candidates
- [ ] 1.2 Use codebase index + knowledge base for context-aware suggestions
- [ ] 1.3 Tests

## Phase 2: Codebase Chat

- [ ] 2.1 MCP tool: `chat_about_code(question, files)` — answer questions about specific files using indexed knowledge
- [ ] 2.2 Use analyze_impact to find relevant files for context
- [ ] 2.3 Tests

## Phase 3: Multi-File Edit Coordination

- [ ] 3.1 MCP tool: `plan_multi_edit(description)` — plan edits across multiple files
- [ ] 3.2 Returns: list of {file, change_description, dependencies}
- [ ] 3.3 Tests

## Convergence Criteria
- Completion suggestions from codebase context
- Code chat with file-aware answers
- Multi-file edit planning
- Two consecutive clean audit passes
