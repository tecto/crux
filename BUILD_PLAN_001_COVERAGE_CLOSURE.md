# BUILD_PLAN_001: Coverage Closure (93% → 100%)

**Created:** 2026-03-18
**Last Updated:** 2026-03-18
**Status:** COMPLETE (2026-03-18) — 1517 tests, 100% coverage, two clean audit passes
**Goal:** Close all 357 uncovered statements across 11 modules in `scripts/lib/`, achieving the `--cov-fail-under=100` gate.

**Constraint:** All LLM work stays in Claude Code (Pro Max).
**Constraint:** Work happens in the Crux repo (`/Users/user/personal/crux`).
**Rule:** TDD — write failing test first, then verify it hits the missing lines.
**Rule:** Follow DEVELOPMENT_PATTERNS_CRUXDEV.md methodology.
**Rule:** After writing each test, verify with `--cov-report=term-missing` that the specific lines disappeared from "Missing." Do not trust test names as proof of coverage (coverage-by-coincidence rule).

---

## Architecture Overview

No architecture changes. This plan adds tests only — no production code changes.

```
Before: 1290 tests, 93.04% coverage, 357 missing statements
After:  1290+N tests, 100% coverage, 0 missing statements
```

---

## Phase Ordering & Dependencies

```
Phase 1: Low-coverage modules (73-77%)     ← Most missing lines per module
Phase 2: Medium-coverage modules (82-88%)  ← Bulk of remaining lines
Phase 3: High-coverage modules (91-99%)    ← Small gaps, quick wins
Phase 4: Verification                      ← Full suite + coverage gate
```

All phases are sequential. Each phase builds on prior phases' test patterns.

---

## Phase 1: Low-Coverage Modules (73-77%) — 56 lines

**Purpose:** Close the worst coverage gaps first. These modules have the most uncovered error handling and edge cases.

### 1A. `crux_security.py` (73% → 100%, 21 lines)

**File:** `tests/test_crux_security.py` (existing or new)

Missing line analysis:
| Lines | Code Path | Test Strategy |
|-------|-----------|---------------|
| 49-50 | `except (ValueError, OSError)` in `validate_path_within_base` | Mock `Path.resolve()` to raise `ValueError` |
| 64 | `return []` when directory is not a dir in `safe_glob_files` | Pass a file path as `directory` arg |
| 72 | `continue` on symlink in `safe_glob_files` | Create a symlink in tmp dir, glob it |
| 75 | `continue` on path-outside-base in `safe_glob_files` | Create symlink pointing outside base |
| 105-111 | `except OSError` in `atomic_symlink` + inner `os.unlink` catch | Mock `os.rename` to raise `OSError`; mock `os.unlink` to also raise |
| 146-152 | `except Exception` in `secure_write_file` + inner `os.unlink` catch | Mock `os.write` to raise; mock `os.unlink` to raise in cleanup |
| 187-189 | `except (OSError, ValueError)` + `return None` in `validate_and_canonicalize_dir` | Pass non-directory path; mock to raise `OSError` |

Tests to write:
```
test_validate_path_resolve_error
test_safe_glob_not_a_directory
test_safe_glob_skips_symlinks
test_safe_glob_skips_outside_base
test_atomic_symlink_rename_oserror
test_atomic_symlink_cleanup_oserror
test_secure_write_file_write_exception
test_secure_write_file_cleanup_oserror
test_validate_canonicalize_not_a_dir
test_validate_canonicalize_oserror
```

### 1B. `crux_hook_runner.py` (76% → 100%, 10 lines)

**File:** `tests/test_crux_hook_runner.py` (existing, 10 tests)

Missing line analysis:
| Lines | Code Path | Test Strategy |
|-------|-----------|---------------|
| 25-34 | `_validate_event_data` body — non-dict, missing field, bad event name, valid | Call function directly with each case |
| 44-45 | `main()` input-too-large guard (>= 1MB stdin) | Mock `sys.stdin` with oversized input |

Tests to write:
```
test_validate_event_data_non_dict
test_validate_event_data_missing_hook_event_name
test_validate_event_data_non_string_event_name
test_validate_event_data_invalid_event_name
test_validate_event_data_valid
test_main_input_too_large
```

### 1C. `crux_cross_domain.py` (77% → 100%, 25 lines)

**File:** `tests/test_crux_cross_domain.py` (existing, 11 tests)

Missing line analysis:
| Lines | Code Path | Test Strategy |
|-------|-----------|---------------|
| 45-49 | `_truncate_field` truncation branch | Pass value exceeding `max_length` |
| 56 | `_validate_string` with `None` | Pass `value=None` |
| 58 | `_validate_string` non-string coercion | Pass `value=42` |
| 65, 67-68 | `_validate_list` with `None` and non-list | Pass `None`, then `"not a list"` |
| 70-74 | `_validate_list` list-too-long truncation | Pass list exceeding `max_items` |
| 225-228 | Exception in `cross_domain_sync` for security findings | Pass malformed `SecurityFinding` |
| 235-238 | Exception in `cross_domain_sync` for design findings | Pass malformed `ValidationFinding` |
| 245-246 | Non-dict in `test_design_updates` | Pass non-dict item in list |
| 251-252 | Missing fields in `test_design_updates` dict | Pass dict missing required fields |
| 262-265 | Exception in `testing_to_design_pattern` | Mock to raise during `cross_domain_sync` |

Tests to write:
```
test_truncate_field_exceeds_max
test_validate_string_none
test_validate_string_non_string
test_validate_list_none
test_validate_list_non_list
test_validate_list_too_long
test_cross_domain_sync_security_finding_error
test_cross_domain_sync_design_finding_error
test_cross_domain_sync_non_dict_update
test_cross_domain_sync_missing_fields_update
test_cross_domain_sync_test_insight_error
```

---

## Phase 2: Medium-Coverage Modules (82-88%) — 226 lines

### 2A. `crux_audit_backend.py` (82% → 100%, 60 lines)

**File:** `tests/test_crux_audit_backend.py` (existing, 78 tests)

Uncovered lines concentrated in:
- Exception/error branches in backend `audit()` methods
- `detect_opencode_context` edge cases
- `_parse_audit_response` edge cases
- Backend caching/selection fallback paths

Tests to write (targeting specific uncovered line ranges):
```
test_ollama_backend_timeout
test_anthropic_backend_api_error
test_openai_backend_api_error
test_claude_subagent_stderr_output
test_detect_opencode_env_variable
test_parse_audit_response_malformed_json
test_parse_audit_response_missing_fields
test_get_audit_backend_cache_invalidation
test_get_adversarial_backend_fallback_chain
test_backend_status_all_unavailable
```
(Exact test list refined after reading specific uncovered lines during execution)

### 2B. `crux_cross_project.py` (83% → 100%, 50 lines)

**File:** `tests/test_crux_cross_project.py` (existing, 28 tests)

Uncovered lines in:
- Registry validation edge cases
- `_scan_directory_bounded` depth limit
- `_is_safe_path` rejections
- `_read_corrections` strict mode
- `aggregate_digests` error paths

Tests to write:
```
test_register_project_path_traversal
test_register_project_too_many_entries
test_scan_directory_depth_limit
test_is_safe_path_rejects_dotdot
test_read_corrections_strict_mode_rejects
test_aggregate_digests_missing_project
test_aggregate_corrections_corrupt_file
test_unregister_nonexistent_project
test_discover_projects_permission_error
test_generate_digest_empty_corrections
```

### 2C. `extract_corrections.py` (84% → 100%, 24 lines)

**File:** `tests/test_extract_corrections.py` (existing, 20 tests)

Uncovered lines in:
- Field validation in `CorrectionEntry` (oversized fields)
- `parse_reflections_file` line-length guard
- `scan_reflections_dir` file-count limit
- `main()` CLI edge cases

Tests to write:
```
test_correction_entry_oversized_field
test_correction_entry_missing_required
test_parse_reflections_line_too_long
test_parse_reflections_too_many_entries
test_scan_reflections_too_many_files
test_cluster_corrections_single_entry
test_main_no_reflections_dir
test_main_with_min_cluster_size
```

### 2D. `crux_typefully.py` (85% → 100%, 13 lines)

**File:** `tests/test_crux_typefully.py` (existing, 18 tests)

Uncovered lines in:
- `_validate_path` rejections
- API key file permission check (world-readable rejection)
- `_request` auth header sanitization in `finally`
- Error response handling

Tests to write:
```
test_validate_path_traversal
test_validate_path_none
test_api_key_world_readable_rejected
test_request_clears_headers_on_error
test_request_non_200_response
test_create_draft_api_error
```

### 2E. `crux_background_processor.py` (87% → 100%, 33 lines)

**File:** `tests/test_crux_background_processor.py` (existing, 25 tests)

Uncovered lines in:
- `_load_processor_state` corrupt file handling
- `_save_processor_state` atomic write failure
- `_safe_import` import failure
- `_run_with_timeout` timeout + exception paths
- Rate limit increment/check edge cases
- Individual processor error handling in `run_processors`

Tests to write:
```
test_load_state_corrupt_json
test_load_state_missing_file
test_save_state_atomic_write
test_safe_import_module_not_found
test_run_with_timeout_exceeds
test_run_with_timeout_exception
test_rate_limit_exceeded
test_rate_limit_increment
test_run_processors_correction_error
test_run_processors_digest_error
test_run_processors_audit_error
```

### 2F. `crux_mcp_handlers.py` (88% → 100%, 53 lines)

**File:** `tests/test_mcp_handlers_expanded.py` (existing, 37 tests)

Uncovered lines concentrated in PLAN-166 security validators and error paths across handlers.

Tests to write:
```
test_validate_path_param_traversal
test_validate_path_param_null_bytes
test_validate_date_format_invalid
test_validate_mode_invalid_chars
test_safe_path_join_traversal
test_sanitize_error_truncation
test_lookup_knowledge_source_classify
test_get_digest_validation_error
test_get_mode_prompt_missing_mode
test_list_modes_no_directory
test_promote_knowledge_validation
test_log_interaction_oversized
test_bip_generate_handler
test_bip_approve_handler
test_bip_status_handler
```

### 2G. `crux_bip_gather.py` (88% → 100%, 15 lines)

**File:** `tests/test_crux_bip_gather.py` (existing, 14 tests)

Uncovered lines in:
- `_gather_git` subprocess error handling
- `_gather_corrections` file read error
- `_gather_knowledge` empty/missing dir
- `_gather_session` missing state file
- Date filtering edge cases

Tests to write:
```
test_gather_git_subprocess_error
test_gather_git_no_commits
test_gather_corrections_read_error
test_gather_corrections_bad_json_line
test_gather_knowledge_missing_dir
test_gather_session_missing_state
test_gather_content_all_posted
```

---

## Phase 3: High-Coverage Modules (91-99%) — 75 lines

### 3A. `crux_hooks.py` (91% → 100%, 25 lines)

**File:** `tests/test_crux_hooks.py` (existing, 74 tests)

Scattered uncovered lines across:
- `_is_safe_name` edge cases
- `_sanitize_value` / `_sanitize_dict` branches
- `handle_post_tool_use` edge cases
- `_try_background_processors` error handling
- `handle_stop` edge cases
- `run_hook` unknown event handling

Tests to write:
```
test_is_safe_name_with_dotdot
test_is_safe_name_with_null
test_sanitize_value_sensitive_key
test_sanitize_dict_nested
test_post_tool_use_missing_tool_name
test_try_background_processors_import_error
test_handle_stop_no_session
test_run_hook_unknown_event
test_bip_counter_threshold
```

### 3B. Small gaps (97-99%) — ~50 lines across 6 modules

| Module | Lines | Missing |
|--------|-------|---------|
| `crux_adopt.py` | 63, 108, 235, 275-276 | 5 |
| `crux_bip.py` | 135, 138-139, 156, 161-162 | 5 |
| `crux_mcp_server.py` | 448, 467, 478 | 3 |
| `crux_paths.py` | 149, 153, 157, 189 | 4 |
| `crux_status.py` | 443-450 | 4 |
| `crux_sync.py` | 149-150, 302, 327, 436, 481 | 6 |

Tests to write for each (1-3 per module targeting specific lines).

---

## Phase 4: Verification

**Purpose:** Verify 100% coverage gate passes and no regressions.

### 4A. Full Suite Run

```bash
cd /Users/user/personal/crux
python3 -m pytest tests/ -v --tb=short --cov=scripts/lib --cov-report=term-missing --cov-fail-under=100
```

**Pass criteria:** 0 failures, 100.00% coverage, `--cov-fail-under=100` gate passes.

### 4B. Code Audit Convergence

After all tests written, run autonomous code audit convergence:
- Audit all new test files (8 dimensions)
- Two consecutive independent clean passes
- Safety valve: max 5 rounds

---

## Progress Tracker

**Phase 1: Low-coverage (56 lines)**
- [x] 1.1 `crux_security.py` tests (21 lines → 0) ✓ 13 tests added
- [x] 1.2 `crux_hook_runner.py` tests (10 lines → 0) ✓ 6 tests added
- [x] 1.3 `crux_cross_domain.py` tests (25 lines → 0) ✓ 18 tests added
- [x] 1.4 Phase 1 coverage verification ✓ all three at 100%

**Phase 2: Medium-coverage (226 lines)**
- [x] 2.1 `crux_audit_backend.py` tests (60 lines → 0) ✓ 34 tests added
- [x] 2.2 `crux_cross_project.py` tests (50 lines → 0) ✓ 29 tests added
- [x] 2.3 `extract_corrections.py` tests (24 lines → 0) ✓ 12 tests added
- [x] 2.4 `crux_typefully.py` tests (13 lines → 0) ✓ 10 tests added
- [x] 2.5 `crux_background_processor.py` tests (33 lines → 0) ✓ 14 tests added
- [x] 2.6 `crux_mcp_handlers.py` tests (53 lines → 0) ✓ 14 tests added
- [x] 2.7 `crux_bip_gather.py` tests (15 lines → 0) ✓ 10 tests added
- [x] 2.8 Phase 2 coverage verification ✓ all seven at 100%

**Phase 3: High-coverage (75 lines)**
- [x] 3.1 `crux_hooks.py` tests (25 lines → 0) ✓ 20 tests added
- [x] 3.2 `crux_adopt.py` tests (5 lines → 0) ✓ 4 tests added
- [x] 3.3 `crux_bip.py` tests (5 lines → 0) ✓ 4 tests added
- [x] 3.4 `crux_mcp_server.py` tests (3 lines → 0) ✓ 3 tests added
- [x] 3.5 `crux_paths.py` tests (4 lines → 0) ✓ 4 tests added
- [x] 3.6 `crux_status.py` tests (4 lines → 0) ✓ 2 tests added
- [x] 3.7 `crux_sync.py` tests (6 lines → 0) ✓ 5 tests added
- [x] 3.8 Phase 3 coverage verification ✓ all seven at 100%

**Phase 4: Verification**
- [x] 4.1 Full suite passes with `--cov-fail-under=100` ✓ 1517 passed, 100.00%
- [x] 4.2 Code audit pass 1 ✓ 12 issues (0 HIGH, 1 MEDIUM fixed, 11 LOW)
- [x] 4.3 Code audit pass 2 (independent, clean) ✓ CLEAN PASS

---

## File Inventory

All new files are test files only:

| File | Phase | Purpose |
|------|-------|---------|
| `tests/test_crux_security.py` | 1 | New or extended — security module edge cases |
| `tests/test_crux_hook_runner.py` | 1 | Extended — validation + oversized input |
| `tests/test_crux_cross_domain.py` | 1 | Extended — validation helpers + sync errors |
| `tests/test_crux_audit_backend.py` | 2 | Extended — backend error/timeout paths |
| `tests/test_crux_cross_project.py` | 2 | Extended — registry/discovery edge cases |
| `tests/test_extract_corrections.py` | 2 | Extended — field validation + CLI |
| `tests/test_crux_typefully.py` | 2 | Extended — security + error handling |
| `tests/test_crux_background_processor.py` | 2 | Extended — timeout/rate-limit/errors |
| `tests/test_mcp_handlers_expanded.py` | 2 | Extended — PLAN-166 validators + BIP handlers |
| `tests/test_crux_bip_gather.py` | 2 | Extended — error handling + edge cases |
| `tests/test_crux_hooks.py` | 3 | Extended — scattered edge cases |
| Various test files | 3 | Extended — small gaps in 6 modules |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Mocking introduces test-only bugs | Tests pass but don't verify real behavior | Use real filesystem (tmp_path) where possible; mock only for OS-level errors |
| Coverage-by-coincidence | Test hits wrong branch, line still uncovered | Verify EVERY test with `--cov-report=term-missing` — check specific line numbers |
| New tests break existing tests | Regression | Run full suite after each module's tests |
| Context pressure from 11 modules | Session crash | Work module by module; checkpoint after each |

---

## Definition of Done

1. `python3 -m pytest tests/ --cov=scripts/lib --cov-fail-under=100` passes
2. 0 test failures
3. 100.00% coverage across all `scripts/lib/` modules
4. No coverage-by-coincidence (every new test verified against `term-missing`)
5. Two consecutive independent clean audit passes on new test code
