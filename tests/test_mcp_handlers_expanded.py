"""Tests for expanded MCP handlers — pipeline, TDD, security, design gates."""

import json
import os

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_mcp_handlers import (
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
)
from scripts.lib.crux_session import SessionState, save_session


@pytest.fixture
def env(tmp_path):
    """Full Crux environment for handler testing."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
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
