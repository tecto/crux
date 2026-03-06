"""Tests for crux_status.py — runtime health and insight reporting."""

import json
import os
from datetime import datetime, timezone

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import SessionState, save_session


@pytest.fixture
def env(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    init_user(home=str(home))
    init_project(project_dir=str(project))

    crux_dir = str(project / ".crux")
    state = SessionState(
        active_mode="build-py",
        active_tool="claude-code",
        working_on="Building API",
        key_decisions=["Use REST", "Use JWT"],
        files_touched=["src/app.py", "tests/test_app.py"],
        pending=["Add auth", "Write docs"],
    )
    save_session(state, project_crux_dir=crux_dir)

    # Knowledge
    pk = project / ".crux" / "knowledge"
    (pk / "api-design.md").write_text("# API Design\nREST conventions.")
    (pk / "auth-patterns.md").write_text("# Auth\nJWT patterns.")

    # Modes
    modes_dir = home / ".crux" / "modes"
    (modes_dir / "build-py.md").write_text("Python mode.")
    (modes_dir / "debug.md").write_text("Debug mode.")

    return {"home": str(home), "project": str(project), "crux_dir": crux_dir}


def _write_interactions(project_dir, entries):
    """Helper to write interaction log entries."""
    log_dir = os.path.join(project_dir, ".crux", "analytics", "interactions")
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{today}.jsonl")
    with open(log_file, "a") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _write_corrections(project_dir, entries):
    """Helper to write correction entries."""
    corr_dir = os.path.join(project_dir, ".crux", "corrections")
    os.makedirs(corr_dir, exist_ok=True)
    corr_file = os.path.join(corr_dir, "corrections.jsonl")
    with open(corr_file, "a") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# get_status — the main status report
# ---------------------------------------------------------------------------

class TestGetStatus:
    def test_returns_dict(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert isinstance(result, dict)

    def test_includes_session_section(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert "session" in result
        assert result["session"]["active_mode"] == "build-py"
        assert result["session"]["active_tool"] == "claude-code"
        assert result["session"]["working_on"] == "Building API"

    def test_includes_knowledge_section(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert "knowledge" in result
        assert result["knowledge"]["project_entries"] == 2
        assert isinstance(result["knowledge"]["entry_names"], list)

    def test_includes_modes_section(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert "modes" in result
        assert result["modes"]["total"] == 2
        assert "build-py" in result["modes"]["available"]

    def test_includes_hooks_section(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert "hooks" in result
        assert isinstance(result["hooks"]["active"], bool)

    def test_hooks_active_when_settings_has_hooks(self, env):
        from scripts.lib.crux_status import get_status
        claude_dir = os.path.join(env["project"], ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        settings = {"hooks": {"PostToolUse": [{"hooks": [{"type": "command", "command": "crux_hook_runner"}]}]}}
        with open(os.path.join(claude_dir, "settings.local.json"), "w") as f:
            json.dump(settings, f)

        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["hooks"]["active"] is True
        assert result["hooks"]["events_registered"] >= 1

    def test_hooks_inactive_when_no_settings(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["hooks"]["active"] is False

    def test_includes_interactions_section(self, env):
        from scripts.lib.crux_status import get_status

        _write_interactions(env["project"], [
            {"timestamp": "2026-03-06T01:00:00Z", "tool_name": "Bash", "tool_input": {}},
            {"timestamp": "2026-03-06T01:01:00Z", "tool_name": "Edit", "tool_input": {}},
            {"timestamp": "2026-03-06T01:02:00Z", "tool_name": "Bash", "tool_input": {}},
        ])

        result = get_status(project_dir=env["project"], home=env["home"])
        assert "interactions" in result
        assert result["interactions"]["today"] == 3
        assert result["interactions"]["tool_breakdown"]["Bash"] == 2
        assert result["interactions"]["tool_breakdown"]["Edit"] == 1

    def test_interactions_zero_when_no_log(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["interactions"]["today"] == 0

    def test_interactions_handles_empty_and_corrupt_lines(self, env):
        from scripts.lib.crux_status import get_status
        log_dir = os.path.join(env["project"], ".crux", "analytics", "interactions")
        os.makedirs(log_dir, exist_ok=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with open(os.path.join(log_dir, f"{today}.jsonl"), "w") as f:
            f.write('{"tool_name":"Bash","tool_input":{},"timestamp":"t"}\n')
            f.write("\n")  # empty line
            f.write("not json\n")  # corrupt line
            f.write('{"tool_name":"Edit","tool_input":{},"timestamp":"t"}\n')

        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["interactions"]["today"] == 2

    def test_includes_corrections_section(self, env):
        from scripts.lib.crux_status import get_status

        _write_corrections(env["project"], [
            {"original": "bad", "corrected": "good", "category": "style", "mode": "build-py", "timestamp": "2026-03-06T01:00:00Z"},
            {"original": "wrong", "corrected": "right", "category": "logic", "mode": "build-py", "timestamp": "2026-03-06T01:01:00Z"},
        ])

        result = get_status(project_dir=env["project"], home=env["home"])
        assert "corrections" in result
        assert result["corrections"]["total"] == 2
        assert result["corrections"]["by_category"]["style"] == 1
        assert result["corrections"]["by_category"]["logic"] == 1

    def test_corrections_zero_when_no_file(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["corrections"]["total"] == 0

    def test_corrections_handles_empty_and_corrupt_lines(self, env):
        from scripts.lib.crux_status import get_status
        corr_dir = os.path.join(env["project"], ".crux", "corrections")
        os.makedirs(corr_dir, exist_ok=True)
        with open(os.path.join(corr_dir, "corrections.jsonl"), "w") as f:
            f.write('{"category":"style","original":"x","corrected":"y","mode":"m","timestamp":"t"}\n')
            f.write("\n")
            f.write("bad\n")
            f.write('{"category":"logic","original":"a","corrected":"b","mode":"m","timestamp":"t"}\n')

        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["corrections"]["total"] == 2

    def test_includes_mcp_section(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert "mcp" in result
        assert isinstance(result["mcp"]["registered"], bool)

    def test_mcp_registered_when_config_exists(self, env):
        from scripts.lib.crux_status import get_status
        claude_dir = os.path.join(env["project"], ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        mcp_config = {"mcpServers": {"crux": {"command": "python"}}}
        with open(os.path.join(claude_dir, "mcp.json"), "w") as f:
            json.dump(mcp_config, f)

        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["mcp"]["registered"] is True
        assert result["mcp"]["tool_count"] == 24

    def test_mcp_not_registered_when_no_config(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["mcp"]["registered"] is False

    def test_mcp_tool_count_zero_on_import_error(self, env, monkeypatch):
        from scripts.lib.crux_status import get_status
        claude_dir = os.path.join(env["project"], ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        mcp_config = {"mcpServers": {"crux": {"command": "python"}}}
        with open(os.path.join(claude_dir, "mcp.json"), "w") as f:
            json.dump(mcp_config, f)

        # Simulate import failure
        import scripts.lib.crux_status as status_mod
        original_check = status_mod._check_mcp

        def broken_check(project_dir):
            # Temporarily break the import
            import builtins
            real_import = builtins.__import__
            def fail_import(name, *args, **kwargs):
                if "crux_mcp_server" in name:
                    raise ImportError("simulated")
                return real_import(name, *args, **kwargs)
            builtins.__import__ = fail_import
            try:
                result = original_check(project_dir)
            finally:
                builtins.__import__ = real_import
            return result

        monkeypatch.setattr(status_mod, "_check_mcp", broken_check)
        result = get_status(project_dir=env["project"], home=env["home"])
        assert result["mcp"]["registered"] is True
        assert result["mcp"]["tool_count"] == 0

    def test_includes_pending_section(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert "pending" in result
        assert result["pending"]["count"] == 2
        assert "Add auth" in result["pending"]["items"]

    def test_includes_files_section(self, env):
        from scripts.lib.crux_status import get_status
        result = get_status(project_dir=env["project"], home=env["home"])
        assert "files" in result
        assert result["files"]["tracked"] == 2


# ---------------------------------------------------------------------------
# format_status — human-readable output
# ---------------------------------------------------------------------------

class TestFormatStatus:
    def test_returns_string(self, env):
        from scripts.lib.crux_status import get_status, format_status
        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_includes_session_info(self, env):
        from scripts.lib.crux_status import get_status, format_status
        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "build-py" in output
        assert "Building API" in output

    def test_includes_hook_status(self, env):
        from scripts.lib.crux_status import get_status, format_status
        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "HOOK" in output or "Hook" in output or "hook" in output

    def test_includes_interaction_count(self, env):
        from scripts.lib.crux_status import get_status, format_status
        _write_interactions(env["project"], [
            {"timestamp": "t", "tool_name": "Bash", "tool_input": {}},
        ])
        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "1" in output

    def test_includes_knowledge_count(self, env):
        from scripts.lib.crux_status import get_status, format_status
        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "2" in output  # 2 knowledge entries

    def test_includes_corrections_count(self, env):
        from scripts.lib.crux_status import get_status, format_status
        _write_corrections(env["project"], [
            {"original": "x", "corrected": "y", "category": "style", "mode": "m", "timestamp": "t"},
        ])
        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "correction" in output.lower()

    def test_shows_pending_tasks(self, env):
        from scripts.lib.crux_status import get_status, format_status
        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "Add auth" in output

    def test_shows_mcp_status(self, env):
        from scripts.lib.crux_status import get_status, format_status
        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "MCP" in output

    def test_shows_hooks_events_when_active(self, env):
        from scripts.lib.crux_status import get_status, format_status
        claude_dir = os.path.join(env["project"], ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        settings = {"hooks": {"PostToolUse": [{"hooks": [{"type": "command", "command": "x"}]}]}}
        with open(os.path.join(claude_dir, "settings.local.json"), "w") as f:
            json.dump(settings, f)

        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "ACTIVE" in output
        assert "PostToolUse" in output

    def test_shows_pending_none_when_empty(self, env):
        from scripts.lib.crux_status import get_status, format_status
        from scripts.lib.crux_session import load_session, save_session
        state = load_session(env["crux_dir"])
        state.pending = []
        save_session(state, project_crux_dir=env["crux_dir"])

        status = get_status(project_dir=env["project"], home=env["home"])
        output = format_status(status)
        assert "PENDING: none" in output


# ---------------------------------------------------------------------------
# check_health — pass/fail health checks
# ---------------------------------------------------------------------------

class TestCheckHealth:
    def test_returns_list_of_checks(self, env):
        from scripts.lib.crux_status import check_health
        checks = check_health(project_dir=env["project"], home=env["home"])
        assert isinstance(checks, list)
        assert len(checks) > 0
        assert all("name" in c and "passed" in c for c in checks)

    def test_session_exists_check(self, env):
        from scripts.lib.crux_status import check_health
        checks = check_health(project_dir=env["project"], home=env["home"])
        session_check = next(c for c in checks if "session" in c["name"].lower())
        assert session_check["passed"] is True

    def test_knowledge_check(self, env):
        from scripts.lib.crux_status import check_health
        checks = check_health(project_dir=env["project"], home=env["home"])
        kb_check = next(c for c in checks if "knowledge" in c["name"].lower())
        assert kb_check["passed"] is True

    def test_hooks_check_fails_when_no_hooks(self, env):
        from scripts.lib.crux_status import check_health
        checks = check_health(project_dir=env["project"], home=env["home"])
        hooks_check = next(c for c in checks if "hook" in c["name"].lower())
        assert hooks_check["passed"] is False

    def test_hooks_check_passes_when_hooks_active(self, env):
        from scripts.lib.crux_status import check_health
        claude_dir = os.path.join(env["project"], ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        settings = {"hooks": {"PostToolUse": [{"hooks": [{"type": "command", "command": "crux_hook_runner"}]}]}}
        with open(os.path.join(claude_dir, "settings.local.json"), "w") as f:
            json.dump(settings, f)

        checks = check_health(project_dir=env["project"], home=env["home"])
        hooks_check = next(c for c in checks if "hook" in c["name"].lower())
        assert hooks_check["passed"] is True

    def test_interactions_check_fails_when_no_logs(self, env):
        from scripts.lib.crux_status import check_health
        checks = check_health(project_dir=env["project"], home=env["home"])
        int_check = next(c for c in checks if "interaction" in c["name"].lower())
        assert int_check["passed"] is False

    def test_interactions_check_passes_with_logs(self, env):
        from scripts.lib.crux_status import check_health
        _write_interactions(env["project"], [
            {"timestamp": "t", "tool_name": "Bash", "tool_input": {}},
        ])
        checks = check_health(project_dir=env["project"], home=env["home"])
        int_check = next(c for c in checks if "interaction" in c["name"].lower())
        assert int_check["passed"] is True

    def test_mcp_check(self, env):
        from scripts.lib.crux_status import check_health
        checks = check_health(project_dir=env["project"], home=env["home"])
        mcp_check = next(c for c in checks if "mcp" in c["name"].lower())
        assert mcp_check["passed"] is False

    def test_modes_check(self, env):
        from scripts.lib.crux_status import check_health
        checks = check_health(project_dir=env["project"], home=env["home"])
        modes_check = next(c for c in checks if "mode" in c["name"].lower())
        assert modes_check["passed"] is True

    def test_all_checks_have_message(self, env):
        from scripts.lib.crux_status import check_health
        checks = check_health(project_dir=env["project"], home=env["home"])
        for c in checks:
            assert "message" in c
            assert len(c["message"]) > 0
