"""Tests for expanded MCP handlers — pipeline, TDD, security, design gates."""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_mcp_handlers import (
    _validate_path_param,
    _validate_date_format,
    _validate_mode,
    _safe_path_join,
    _sanitize_error_message,
    MAX_LIST_RESULTS,
    MAX_DRAFT_SIZE,
    handle_lookup_knowledge,
    handle_get_digest,
    handle_get_mode_prompt,
    handle_list_modes,
    handle_promote_knowledge,
    handle_get_pipeline_config,
    handle_get_active_gates,
    handle_start_tdd_gate,
    handle_check_tdd_status,
    handle_start_security_audit,
    handle_security_audit_summary,
    handle_start_design_validation,
    handle_design_validation_summary,
    handle_check_contrast,
    handle_log_interaction,
    handle_verify_health,
    handle_audit_script_8b,
    handle_audit_script_32b,
    handle_check_processor_thresholds,
    handle_run_background_processors,
    handle_get_processor_status,
    handle_register_project,
    handle_get_cross_project_digest,
    handle_figma_get_tokens,
    handle_figma_get_components,
    handle_restore_context,
    handle_bip_approve,
    handle_bip_status,
)
from scripts.lib.crux_session import SessionState, save_session


@pytest.fixture
def env(tmp_path):
    """Full Crux environment for handler testing."""
    home = tmp_path / "home"
    home.mkdir()
    project = home / "project"
    project.mkdir()
    init_user(home=str(home))
    init_project(project_dir=str(project))
    return {"home": str(home), "project": str(project)}


# ---------------------------------------------------------------------------
# Pipeline config handlers
# ---------------------------------------------------------------------------

class TestHandleGetPipelineConfig:
    def test_returns_default_config(self, env):
        result = handle_get_pipeline_config(env["project"])
        assert "metadata" in result
        assert "pipeline" in result
        assert result["metadata"]["version"] == "2.0"

    def test_returns_tdd_section(self, env):
        result = handle_get_pipeline_config(env["project"])
        assert "tdd_enforcement" in result["pipeline"]
        assert result["pipeline"]["tdd_enforcement"]["level"] == "standard"


class TestHandleGetActiveGates:
    def test_build_mode_high_risk(self, env):
        result = handle_get_active_gates("build-py", "high", env["project"])
        assert result["mode"] == "build-py"
        assert 1 in result["active_gates"]  # preflight
        assert 2 in result["active_gates"]  # tdd
        assert 3 in result["active_gates"]  # security

    def test_review_mode_excludes_tdd(self, env):
        result = handle_get_active_gates("review", "high", env["project"])
        assert 2 not in result["active_gates"]

    def test_design_mode_includes_gate_7(self, env):
        result = handle_get_active_gates("design-ui", "high", env["project"])
        assert 7 in result["active_gates"]


# ---------------------------------------------------------------------------
# TDD gate handlers
# ---------------------------------------------------------------------------

class TestHandleStartTddGate:
    def test_starts_gate(self, env):
        result = handle_start_tdd_gate(
            mode="build-py",
            feature="user_registration",
            components=["UserService"],
            edge_cases=["duplicate email"],
            project_dir=env["project"],
        )
        assert result["mode"] == "build-py"
        assert result["spec"]["feature"] == "user_registration"
        assert result["passed"] is False

    def test_creates_gate_file(self, env):
        handle_start_tdd_gate(
            mode="build-py",
            feature="login",
            components=[],
            edge_cases=[],
            project_dir=env["project"],
        )
        gate_file = os.path.join(env["project"], ".crux", "gates", "tdd.json")
        assert os.path.exists(gate_file)


class TestHandleCheckTddStatus:
    def test_not_started(self, env):
        result = handle_check_tdd_status(env["project"])
        assert result["started"] is False

    def test_in_progress(self, env):
        handle_start_tdd_gate(
            mode="build-py", feature="f",
            components=[], edge_cases=[],
            project_dir=env["project"],
        )
        result = handle_check_tdd_status(env["project"])
        assert result["started"] is True
        assert result["current_phase"] == "plan"


# ---------------------------------------------------------------------------
# Security audit handlers
# ---------------------------------------------------------------------------

class TestHandleStartSecurityAudit:
    def test_starts_audit(self, env):
        result = handle_start_security_audit(env["project"])
        assert result["max_iterations"] == 3
        assert len(result["categories"]) == 7

    def test_creates_audit_file(self, env):
        handle_start_security_audit(env["project"])
        audit_file = os.path.join(env["project"], ".crux", "gates", "security.json")
        assert os.path.exists(audit_file)


class TestHandleSecurityAuditSummary:
    def test_empty_audit(self, env):
        handle_start_security_audit(env["project"])
        result = handle_security_audit_summary(env["project"])
        assert result["total_findings"] == 0
        assert result["total_iterations"] == 0


# ---------------------------------------------------------------------------
# Design validation handlers
# ---------------------------------------------------------------------------

class TestHandleStartDesignValidation:
    def test_starts_validation(self, env):
        result = handle_start_design_validation(env["project"])
        assert result["wcag_level"] == "AA"
        assert result["check_brand"] is True

    def test_creates_file(self, env):
        handle_start_design_validation(env["project"])
        val_file = os.path.join(env["project"], ".crux", "gates", "design.json")
        assert os.path.exists(val_file)


class TestHandleDesignValidationSummary:
    def test_empty_validation(self, env):
        handle_start_design_validation(env["project"])
        result = handle_design_validation_summary(env["project"])
        assert result["total_findings"] == 0
        assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# Contrast check handler
# ---------------------------------------------------------------------------

class TestHandleCheckContrast:
    def test_black_on_white(self):
        result = handle_check_contrast("#000000", "#FFFFFF")
        assert result["ratio"] == 21.0
        assert result["passes_aa"] is True
        assert result["passes_aaa"] is True

    def test_low_contrast(self):
        result = handle_check_contrast("#FFFFFF", "#FFFFFF")
        assert result["ratio"] == 1.0
        assert result["passes_aa"] is False


# ---------------------------------------------------------------------------
# log_interaction handler (OpenCode full-text logging)
# ---------------------------------------------------------------------------

class TestHandleLogInteraction:
    """Tests for the log_interaction MCP tool handler.

    This tool lets OpenCode (or any MCP client) log full-text conversation
    messages to .crux/analytics/conversations/<date>.jsonl.
    """

    def test_logs_user_message(self, env):
        result = handle_log_interaction(
            role="user",
            content="build the login page",
            project_dir=env["project"],
        )
        assert result["logged"] is True

    def test_logs_assistant_message(self, env):
        result = handle_log_interaction(
            role="assistant",
            content="Here's the implementation...",
            project_dir=env["project"],
        )
        assert result["logged"] is True

    def test_persists_to_conversations_jsonl(self, env):
        handle_log_interaction(
            role="user",
            content="test persistence",
            project_dir=env["project"],
        )
        log_dir = os.path.join(env["project"], ".crux", "analytics", "conversations")
        assert os.path.isdir(log_dir)
        log_files = os.listdir(log_dir)
        assert len(log_files) == 1

        with open(os.path.join(log_dir, log_files[0])) as f:
            entry = json.loads(f.readline())
        assert entry["role"] == "user"
        assert entry["content"] == "test persistence"
        assert "timestamp" in entry

    def test_includes_tool_field_from_session(self, env):
        """The tool field should come from session state active_tool."""
        state = SessionState(active_mode="debug", active_tool="opencode")
        crux_dir = os.path.join(env["project"], ".crux")
        save_session(state, project_crux_dir=crux_dir)

        handle_log_interaction(
            role="user",
            content="investigate the bug",
            project_dir=env["project"],
        )
        log_dir = os.path.join(env["project"], ".crux", "analytics", "conversations")
        log_files = os.listdir(log_dir)
        with open(os.path.join(log_dir, log_files[0])) as f:
            entry = json.loads(f.readline())
        assert entry["tool"] == "opencode"
        assert entry["mode"] == "debug"

    def test_rejects_empty_content(self, env):
        result = handle_log_interaction(
            role="user",
            content="",
            project_dir=env["project"],
        )
        assert result["logged"] is False

    def test_rejects_invalid_role(self, env):
        result = handle_log_interaction(
            role="system",
            content="some content",
            project_dir=env["project"],
        )
        assert result["logged"] is False
        assert "error" in result

    def test_multiple_messages_append(self, env):
        for i in range(3):
            handle_log_interaction(
                role="user", content=f"message {i}", project_dir=env["project"],
            )
        log_dir = os.path.join(env["project"], ".crux", "analytics", "conversations")
        log_files = os.listdir(log_dir)
        with open(os.path.join(log_dir, log_files[0])) as f:
            lines = f.readlines()
        assert len(lines) == 3

    def test_optional_metadata_field(self, env):
        handle_log_interaction(
            role="user",
            content="with metadata",
            project_dir=env["project"],
            metadata={"source": "opencode-mcp"},
        )
        log_dir = os.path.join(env["project"], ".crux", "analytics", "conversations")
        log_files = os.listdir(log_dir)
        with open(os.path.join(log_dir, log_files[0])) as f:
            entry = json.loads(f.readline())
        assert entry["metadata"] == {"source": "opencode-mcp"}


class TestHandleVerifyHealth:
    def test_returns_static_liveness_summary(self, env):
        result = handle_verify_health(project_dir=env["project"], home=env["home"])
        assert "static" in result
        assert "liveness" in result
        assert "summary" in result

    def test_summary_has_counts(self, env):
        result = handle_verify_health(project_dir=env["project"], home=env["home"])
        s = result["summary"]
        assert "total" in s
        assert "passed" in s
        assert "failed" in s
        assert "all_passed" in s
        assert s["total"] == s["passed"] + s["failed"]


# ---------------------------------------------------------------------------
# Audit script handlers
# ---------------------------------------------------------------------------

class TestAuditScriptHandlers:
    def test_audit_8b_returns_dict(self):
        result = handle_audit_script_8b("echo hello", "low")
        assert isinstance(result, dict)
        assert "passed" in result

    def test_audit_32b_skips_non_high_risk(self):
        result = handle_audit_script_32b("echo hello", "low")
        assert result["passed"] is True
        assert result.get("skipped") is True


# ---------------------------------------------------------------------------
# Background processor handlers
# ---------------------------------------------------------------------------

class TestProcessorHandlers:
    def test_check_thresholds(self, env):
        result = handle_check_processor_thresholds(
            project_dir=env["project"], home=env["home"],
        )
        assert "corrections_exceeded" in result
        assert "interactions_exceeded" in result

    def test_run_processors_nothing_due(self, env):
        result = handle_run_background_processors(
            project_dir=env["project"], home=env["home"],
        )
        assert result["success"] is True
        assert len(result["processors_run"]) == 0

    def test_get_processor_status(self, env):
        result = handle_get_processor_status(project_dir=env["project"])
        assert "last_digest" in result
        assert result["last_digest"] == "never"


# ---------------------------------------------------------------------------
# Cross-project handlers
# ---------------------------------------------------------------------------

class TestCrossProjectHandlers:
    def test_register_project(self, env):
        result = handle_register_project(
            project_dir=env["project"], home=env["home"],
        )
        assert result["registered"] is True

    def test_get_cross_project_digest(self, env):
        result = handle_get_cross_project_digest(home=env["home"])
        assert "date" in result
        assert "content" in result


# ---------------------------------------------------------------------------
# Figma handlers
# ---------------------------------------------------------------------------

class TestFigmaHandlers:
    def test_figma_get_tokens_error(self):
        # No mock — will fail to connect to Figma
        result = handle_figma_get_tokens("fake-key", "fake-token")
        assert result["success"] is False

    def test_figma_get_components_error(self):
        result = handle_figma_get_components("fake-key", "fake-token")
        assert result["success"] is False

    def test_figma_get_tokens_success(self, monkeypatch):
        import scripts.lib.crux_figma as figma_mod
        monkeypatch.setattr(figma_mod, "get_file", lambda fk, t: {
            "success": True,
            "data": {"document": {"name": "test", "type": "CANVAS", "children": []}},
        })
        result = handle_figma_get_tokens("test-key", "test-token")
        assert result["success"] is True
        assert "tokens" in result
        assert "css" in result
        assert "tailwind" in result


# ---------------------------------------------------------------------------
# Validation helpers coverage
# ---------------------------------------------------------------------------

class TestValidatePathParam:
    def test_empty_value_raises(self):
        """Line 36: empty value raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_path_param("", "test_param")

    def test_invalid_chars_raises(self):
        """Line 38: invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="invalid characters"):
            _validate_path_param("foo/bar", "test_param")

    def test_path_traversal_raises(self):
        """Lines 40-41: path traversal attempts raise ValueError."""
        with pytest.raises(ValueError, match="path traversal"):
            _validate_path_param("a..b", "test_param")


class TestValidateDateFormat:
    def test_invalid_date_raises(self):
        """Lines 49-50: invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            _validate_date_format("not-a-date")

    def test_valid_date_passes(self):
        _validate_date_format("2026-03-18")


class TestValidateMode:
    def test_unknown_mode_raises(self):
        """Lines 58-59: unknown mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown mode"):
            _validate_mode("nonexistent-mode")

    def test_known_mode_passes(self):
        _validate_mode("code")


class TestSafePathJoin:
    def test_traversal_raises(self, tmp_path):
        """Line 70: path traversal detected raises ValueError."""
        with pytest.raises(ValueError, match="traversal"):
            _safe_path_join(str(tmp_path / "base"), "..", "..", "etc", "passwd")


class TestSanitizeErrorMessage:
    def test_returns_generic_message(self):
        """Line 76: returns generic error message."""
        result = _sanitize_error_message(RuntimeError("secret info"))
        assert result == "An error occurred while processing the request"


# ---------------------------------------------------------------------------
# Knowledge lookup error paths
# ---------------------------------------------------------------------------

class TestLookupKnowledgeErrors:
    def test_unreadable_knowledge_file(self, env, monkeypatch):
        """Lines 142-144: OSError reading knowledge file skips it."""
        from scripts.lib.crux_paths import get_project_paths
        project_paths = get_project_paths(env["project"])
        k_dir = project_paths.knowledge
        os.makedirs(k_dir, exist_ok=True)
        Path(k_dir, "test-entry.md").write_text("test content")

        # Make read_text raise OSError
        original_read_text = Path.read_text
        def failing_read(self, *a, **kw):
            if "test-entry" in str(self):
                raise OSError("Permission denied")
            return original_read_text(self, *a, **kw)

        monkeypatch.setattr(Path, "read_text", failing_read)
        result = handle_lookup_knowledge("test", env["project"], env["home"])
        # Should not crash, just skip the file
        assert "results" in result

    def test_max_list_results_truncation(self, env, monkeypatch):
        """Line 166: results exceeding MAX_LIST_RESULTS get truncated."""
        from scripts.lib.crux_paths import get_project_paths
        project_paths = get_project_paths(env["project"])
        k_dir = project_paths.knowledge
        os.makedirs(k_dir, exist_ok=True)

        # Create many knowledge files
        import scripts.lib.crux_mcp_handlers as mh
        original_max = mh.MAX_LIST_RESULTS
        monkeypatch.setattr(mh, "MAX_LIST_RESULTS", 2)

        for i in range(5):
            Path(k_dir, f"entry-{i}.md").write_text(f"test content {i}")

        result = handle_lookup_knowledge("test", env["project"], env["home"])
        assert result["total_found"] <= 2


# ---------------------------------------------------------------------------
# Digest handler error paths
# ---------------------------------------------------------------------------

class TestGetDigestErrors:
    def test_invalid_date_format(self, env):
        """Lines 253-254: invalid date format returns error."""
        # Create digest dir so we get past the isdir check
        from scripts.lib.crux_paths import get_user_paths
        user_paths = get_user_paths(env["home"])
        os.makedirs(user_paths.analytics_digests, exist_ok=True)

        result = handle_get_digest(env["home"], date="bad-date")
        assert result["found"] is False
        assert "error" in result

    def test_date_path_traversal(self, env, monkeypatch):
        """Lines 259-260: path traversal in date returns error."""
        from scripts.lib.crux_paths import get_user_paths
        user_paths = get_user_paths(env["home"])
        os.makedirs(user_paths.analytics_digests, exist_ok=True)

        # Mock _validate_date_format to pass, but _safe_path_join to fail
        import scripts.lib.crux_mcp_handlers as mh
        monkeypatch.setattr(mh, "_validate_date_format", lambda d: None)
        monkeypatch.setattr(mh, "_safe_path_join", lambda *a: (_ for _ in ()).throw(ValueError("traversal")))

        result = handle_get_digest(env["home"], date="2026-03-18")
        assert result["found"] is False
        assert "error" in result

    def test_digest_file_read_error(self, env, monkeypatch):
        """Lines 266-268: OSError reading digest file."""
        from scripts.lib.crux_paths import get_user_paths
        user_paths = get_user_paths(env["home"])
        digest_dir = user_paths.analytics_digests
        os.makedirs(digest_dir, exist_ok=True)
        Path(digest_dir, "2026-03-18.md").write_text("digest content")

        # Make os.path.exists raise after path join succeeds
        original_exists = os.path.exists
        def error_exists(path):
            if "2026-03-18.md" in str(path):
                raise OSError("disk error")
            return original_exists(path)

        monkeypatch.setattr(os.path, "exists", error_exists)
        result = handle_get_digest(env["home"], date="2026-03-18")
        assert result["found"] is False
        assert "error" in result

    def test_digest_dir_read_error(self, env, monkeypatch):
        """Lines 281-283: OSError reading digest directory."""
        from scripts.lib.crux_paths import get_user_paths
        user_paths = get_user_paths(env["home"])
        os.makedirs(user_paths.analytics_digests, exist_ok=True)

        # Make glob raise
        original_glob = Path.glob
        def error_glob(self, pattern):
            raise OSError("permission denied")

        monkeypatch.setattr(Path, "glob", error_glob)
        result = handle_get_digest(env["home"])
        assert result["found"] is False
        assert "error" in result


# ---------------------------------------------------------------------------
# Mode prompt handler error paths
# ---------------------------------------------------------------------------

class TestGetModePromptErrors:
    def test_invalid_mode_param(self, env):
        """Lines 295-296: invalid mode parameter returns error."""
        result = handle_get_mode_prompt("../../etc/passwd", env["home"])
        assert result["found"] is False
        assert "error" in result

    def test_mode_path_traversal(self, env, monkeypatch):
        """Lines 303-304: safe path join failure for mode."""
        import scripts.lib.crux_mcp_handlers as mh
        monkeypatch.setattr(mh, "_validate_path_param", lambda v, p: None)
        monkeypatch.setattr(mh, "_safe_path_join", lambda *a: (_ for _ in ()).throw(ValueError("traversal")))

        result = handle_get_mode_prompt("test", env["home"])
        assert result["found"] is False
        assert "error" in result

    def test_mode_file_read_error(self, env, monkeypatch):
        """Lines 316-318: OSError reading mode file."""
        from scripts.lib.crux_paths import get_user_paths
        user_paths = get_user_paths(env["home"])
        os.makedirs(user_paths.modes, exist_ok=True)
        Path(user_paths.modes, "code.md").write_text("# Code mode")

        original_exists = os.path.exists
        def error_exists(path):
            if "code.md" in str(path):
                raise OSError("disk error")
            return original_exists(path)

        monkeypatch.setattr(os.path, "exists", error_exists)
        result = handle_get_mode_prompt("code", env["home"])
        assert result["found"] is False
        assert "error" in result


# ---------------------------------------------------------------------------
# List modes error paths
# ---------------------------------------------------------------------------

class TestListModesErrors:
    def test_unreadable_mode_file(self, env, monkeypatch):
        """Lines 334-336: OSError reading a mode file in listing."""
        from scripts.lib.crux_paths import get_user_paths
        user_paths = get_user_paths(env["home"])
        modes_dir = user_paths.modes
        os.makedirs(modes_dir, exist_ok=True)
        Path(modes_dir, "code.md").write_text("# Code")
        Path(modes_dir, "debug.md").write_text("# Debug")

        original_read_text = Path.read_text
        def failing_read(self, *a, **kw):
            if "code.md" in str(self):
                raise OSError("Permission denied")
            return original_read_text(self, *a, **kw)

        monkeypatch.setattr(Path, "read_text", failing_read)
        result = handle_list_modes(env["home"])
        # code.md should be skipped, debug.md should be present
        names = [m["name"] for m in result["modes"]]
        assert "debug" in names


# ---------------------------------------------------------------------------
# Promote knowledge error paths
# ---------------------------------------------------------------------------

class TestPromoteKnowledgeErrors:
    def test_invalid_entry_name(self, env):
        """Lines 393-394: invalid entry_name returns error."""
        result = handle_promote_knowledge("../../etc/passwd", env["project"], env["home"])
        assert result["promoted"] is False
        assert "error" in result

    def test_safe_path_join_failure(self, env, monkeypatch):
        """Lines 403-404: safe path join failure."""
        import scripts.lib.crux_mcp_handlers as mh
        monkeypatch.setattr(mh, "_validate_path_param", lambda v, p: None)
        monkeypatch.setattr(mh, "_safe_path_join", lambda *a: (_ for _ in ()).throw(ValueError("traversal")))

        result = handle_promote_knowledge("test", env["project"], env["home"])
        assert result["promoted"] is False
        assert "error" in result

    def test_symlink_entry_rejected(self, env):
        """Line 408: symlinked entries are rejected."""
        from scripts.lib.crux_paths import get_project_paths
        project_paths = get_project_paths(env["project"])
        k_dir = project_paths.knowledge
        os.makedirs(k_dir, exist_ok=True)

        # Create a real file and a symlink
        real_file = Path(k_dir, "real.md")
        real_file.write_text("content")
        link_file = Path(k_dir, "linked.md")
        link_file.symlink_to(real_file)

        result = handle_promote_knowledge("linked", env["project"], env["home"])
        assert result["promoted"] is False
        assert "symlink" in result["error"].lower()

    def test_promote_oserror(self, env, monkeypatch):
        """Lines 417-419: OSError during copy."""
        from scripts.lib.crux_paths import get_project_paths
        project_paths = get_project_paths(env["project"])
        k_dir = project_paths.knowledge
        os.makedirs(k_dir, exist_ok=True)
        Path(k_dir, "test-entry.md").write_text("content")

        import shutil
        def failing_copy(*a, **kw):
            raise OSError("disk full")
        monkeypatch.setattr(shutil, "copy2", failing_copy)

        result = handle_promote_knowledge("test-entry", env["project"], env["home"])
        assert result["promoted"] is False
        assert "error" in result


# ---------------------------------------------------------------------------
# Log interaction write error
# ---------------------------------------------------------------------------

class TestLogInteractionWriteError:
    def test_write_oserror(self, env, monkeypatch):
        """Lines 656-658: OSError writing interaction log."""
        import builtins
        original_open = builtins.open

        def failing_open(path, mode="r", *a, **kw):
            if "conversations" in str(path) and "a" in mode:
                raise OSError("disk full")
            return original_open(path, mode, *a, **kw)

        monkeypatch.setattr(builtins, "open", failing_open)
        result = handle_log_interaction(
            role="user", content="test", project_dir=env["project"],
        )
        assert result["logged"] is False
        assert "error" in result


# ---------------------------------------------------------------------------
# Restore context error paths
# ---------------------------------------------------------------------------

class TestRestoreContextErrors:
    def test_invalid_mode_in_session(self, env):
        """Lines 696-697: invalid active_mode triggers warning."""
        # Set session with invalid mode
        state = SessionState(active_mode="", active_tool="claude-code")
        crux_dir = os.path.join(env["project"], ".crux")
        save_session(state, project_crux_dir=crux_dir)

        result = handle_restore_context(env["project"], env["home"])
        assert "context" in result


# ---------------------------------------------------------------------------
# BIP approve handler coverage
# ---------------------------------------------------------------------------

class TestBipApproveHandler:
    def test_draft_too_large(self, env):
        """Line 924: draft exceeding MAX_DRAFT_SIZE returns error."""
        # Set up bip dir
        bip_dir = os.path.join(env["project"], ".crux", "bip")
        os.makedirs(os.path.join(bip_dir, "drafts"), exist_ok=True)

        result = handle_bip_approve(
            project_dir=env["project"],
            draft_text="x" * (MAX_DRAFT_SIZE + 1),
        )
        assert result["status"] == "error"
        assert "exceeds" in result["error"]

    def test_approve_single_tweet(self, env):
        """Lines 949-955, 969: approve a single tweet draft (Typefully will fail gracefully)."""
        bip_dir = os.path.join(env["project"], ".crux", "bip")
        os.makedirs(os.path.join(bip_dir, "drafts"), exist_ok=True)

        result = handle_bip_approve(
            project_dir=env["project"],
            draft_text="Shipped a new feature today!",
            source_keys=["git:abc123"],
        )
        # Typefully will fail (no API key), but draft should be saved
        assert result["status"] in ("queued", "saved")

    def test_approve_thread(self, env, monkeypatch):
        """Lines 949-955: approve a multi-tweet thread with successful Typefully."""
        bip_dir = os.path.join(env["project"], ".crux", "bip")
        os.makedirs(os.path.join(bip_dir, "drafts"), exist_ok=True)

        import scripts.lib.crux_typefully as tf_mod
        monkeypatch.setattr(tf_mod, "TypefullyClient", lambda **kw: MagicMock())
        monkeypatch.setattr(tf_mod, "create_thread", lambda client, tweets, publish_at=None: {"id": "thread-123"})
        monkeypatch.setattr(tf_mod, "create_draft", lambda client, text, publish_at=None: {"id": "draft-123"})

        result = handle_bip_approve(
            project_dir=env["project"],
            draft_text="Tweet 1\n\nTweet 2\n\nTweet 3",
            source_keys=["git:abc123"],
        )
        assert result["status"] == "queued"
        assert result["draft_id"] == "thread-123"

    def test_approve_single_with_draft_id(self, env, monkeypatch):
        """Line 969: draft_id gets set on state when Typefully succeeds."""
        bip_dir = os.path.join(env["project"], ".crux", "bip")
        os.makedirs(os.path.join(bip_dir, "drafts"), exist_ok=True)

        import scripts.lib.crux_typefully as tf_mod
        monkeypatch.setattr(tf_mod, "TypefullyClient", lambda **kw: MagicMock())
        monkeypatch.setattr(tf_mod, "create_draft", lambda client, text, publish_at=None: {"id": "draft-456"})

        result = handle_bip_approve(
            project_dir=env["project"],
            draft_text="Single tweet",
        )
        assert result["status"] == "queued"
        assert result["draft_id"] == "draft-456"


# ---------------------------------------------------------------------------
# BIP status handler coverage
# ---------------------------------------------------------------------------

class TestBipStatusHandler:
    def test_returns_status(self, env):
        """Cover handle_bip_status."""
        bip_dir = os.path.join(env["project"], ".crux", "bip")
        os.makedirs(bip_dir, exist_ok=True)

        result = handle_bip_status(env["project"])
        assert "commits_since_last_post" in result
        assert "cooldown_ok" in result
        assert "thresholds" in result
