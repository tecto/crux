"""Tests for crux_mcp_server.py — MCP tool registration, env helpers, and tool wrappers."""

import os
from pathlib import Path

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import SessionState, save_session


@pytest.fixture
def server_module(monkeypatch):
    """Import the server module with controlled environment."""
    monkeypatch.setenv("CRUX_HOME", "/tmp/test-home")
    monkeypatch.setenv("CRUX_PROJECT", "/tmp/test-project")
    from scripts.lib import crux_mcp_server
    return crux_mcp_server


@pytest.fixture
def live_env(tmp_path, monkeypatch):
    """Full Crux environment wired to the MCP server env vars."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    init_user(home=str(home))
    init_project(project_dir=str(project))

    # Mode definitions
    modes_dir = home / ".crux" / "modes"
    (modes_dir / "build-py.md").write_text("You are a Python specialist.")
    (modes_dir / "debug.md").write_text("You are a debugging specialist.")

    # Knowledge
    pk = project / ".crux" / "knowledge"
    (pk / "api-design.md").write_text("# API Design\nUse REST conventions.\nTags: api")

    # Session
    crux_dir = str(project / ".crux")
    state = SessionState(
        active_mode="build-py",
        active_tool="claude-code",
        working_on="Building API",
    )
    save_session(state, project_crux_dir=crux_dir)

    monkeypatch.setenv("CRUX_HOME", str(home))
    monkeypatch.setenv("CRUX_PROJECT", str(project))

    from scripts.lib import crux_mcp_server
    return {
        "home": str(home),
        "project": str(project),
        "mod": crux_mcp_server,
    }


class TestEnvironmentHelpers:
    def test_home_uses_crux_home_env(self, monkeypatch):
        monkeypatch.setenv("CRUX_HOME", "/custom/home")
        from scripts.lib.crux_mcp_server import _home
        assert _home() == "/custom/home"

    def test_home_falls_back_to_HOME(self, monkeypatch):
        monkeypatch.delenv("CRUX_HOME", raising=False)
        monkeypatch.setenv("HOME", "/fallback/home")
        from scripts.lib.crux_mcp_server import _home
        assert _home() == "/fallback/home"

    def test_project_uses_crux_project_env(self, monkeypatch):
        monkeypatch.setenv("CRUX_PROJECT", "/custom/project")
        from scripts.lib.crux_mcp_server import _project
        assert _project() == "/custom/project"

    def test_project_falls_back_to_cwd(self, monkeypatch):
        monkeypatch.delenv("CRUX_PROJECT", raising=False)
        from scripts.lib.crux_mcp_server import _project
        assert _project() == os.getcwd()


class TestMCPToolRegistration:
    def test_mcp_server_created(self, server_module):
        assert server_module.mcp is not None
        assert server_module.mcp.name == "crux"

    def test_all_tools_registered(self, server_module):
        """All 13 handler functions should be registered as MCP tools."""
        tools = server_module.mcp._tool_manager._tools
        expected = {
            "lookup_knowledge",
            "get_session_state",
            "update_session",
            "write_handoff",
            "read_handoff",
            "get_digest",
            "get_mode_prompt",
            "list_modes",
            "validate_script",
            "promote_knowledge",
            "get_project_context",
            "switch_tool_to",
            "log_correction",
        }
        registered = set(tools.keys())
        assert expected.issubset(registered), f"Missing tools: {expected - registered}"

    def test_tool_count(self, server_module):
        tools = server_module.mcp._tool_manager._tools
        assert len(tools) >= 13


class TestRunFunction:
    def test_run_is_async(self, server_module):
        import inspect
        assert inspect.iscoroutinefunction(server_module.run)


class TestToolWrappers:
    """Call the MCP tool wrapper functions directly to verify they delegate correctly."""

    def test_lookup_knowledge(self, live_env):
        result = live_env["mod"].lookup_knowledge(query="api")
        assert result["total_found"] > 0

    def test_get_session_state(self, live_env):
        result = live_env["mod"].get_session_state()
        assert result["active_mode"] == "build-py"

    def test_update_session(self, live_env):
        result = live_env["mod"].update_session(working_on="New task")
        assert result["working_on"] == "New task"

    def test_write_and_read_handoff(self, live_env):
        live_env["mod"].write_handoff(content="Test handoff")
        result = live_env["mod"].read_handoff()
        assert result["exists"]
        assert "Test handoff" in result["content"]

    def test_get_digest(self, live_env):
        result = live_env["mod"].get_digest()
        assert not result["found"]

    def test_get_mode_prompt(self, live_env):
        result = live_env["mod"].get_mode_prompt(mode="build-py")
        assert result["found"]

    def test_list_modes(self, live_env):
        result = live_env["mod"].list_modes()
        assert len(result["modes"]) >= 2

    def test_validate_script(self, live_env):
        result = live_env["mod"].validate_script(content="echo hello")
        assert not result["passed"]

    def test_promote_knowledge(self, live_env):
        result = live_env["mod"].promote_knowledge(entry_name="api-design")
        assert result["promoted"]

    def test_get_project_context(self, live_env):
        result = live_env["mod"].get_project_context()
        assert not result["found"]

    def test_switch_tool_to(self, live_env):
        result = live_env["mod"].switch_tool_to(target_tool="opencode")
        assert result["success"]

    def test_log_correction(self, live_env):
        result = live_env["mod"].log_correction(
            original="bad", corrected="good", category="style", mode="build-py"
        )
        assert result["logged"]
