"""Tests for crux_switch.py — seamless switching between AI coding tools."""

import json
import os
from pathlib import Path

import pytest

from scripts.lib.crux_switch import switch_tool, SwitchResult
from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import SessionState, save_session, write_handoff


@pytest.fixture
def env(tmp_path):
    """Set up a complete Crux environment simulating real usage."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    init_user(home=str(home))
    init_project(project_dir=str(project))

    # Add mode definitions
    modes_dir = home / ".crux" / "modes"
    (modes_dir / "build-py.md").write_text("You are a Python specialist.")
    (modes_dir / "debug.md").write_text("You are a debugging specialist.")

    # Add knowledge
    k = project / ".crux" / "knowledge"
    (k / "api-patterns.md").write_text("# API Patterns\nUse REST conventions.\nTags: api")

    uk = home / ".crux" / "knowledge" / "shared"
    (uk / "git-workflow.md").write_text("# Git Workflow\nAlways use feature branches.")

    # Simulate an active Claude Code session
    crux_dir = str(project / ".crux")
    state = SessionState(
        active_mode="build-py",
        active_tool="claude-code",
        working_on="Building REST API",
        key_decisions=["Use FastAPI", "PostgreSQL for storage"],
        files_touched=["src/api/routes.py", "src/api/models.py"],
        pending=["Add auth middleware", "Write integration tests"],
        context_summary="Halfway through API implementation",
    )
    save_session(state, project_crux_dir=crux_dir)

    return {"home": str(home), "project": str(project), "crux_dir": crux_dir}


class TestSwitchTool:
    def test_switch_from_claude_to_opencode(self, env):
        result = switch_tool(
            target_tool="opencode",
            project_dir=env["project"],
            home=env["home"],
        )
        assert isinstance(result, SwitchResult)
        assert result.success
        assert result.from_tool == "claude-code"
        assert result.to_tool == "opencode"

    def test_updates_session_active_tool(self, env):
        switch_tool(target_tool="opencode", project_dir=env["project"], home=env["home"])
        state_file = Path(env["project"]) / ".crux" / "sessions" / "state.json"
        data = json.loads(state_file.read_text())
        assert data["active_tool"] == "opencode"

    def test_preserves_session_state(self, env):
        switch_tool(target_tool="opencode", project_dir=env["project"], home=env["home"])
        state_file = Path(env["project"]) / ".crux" / "sessions" / "state.json"
        data = json.loads(state_file.read_text())
        assert data["active_mode"] == "build-py"
        assert data["working_on"] == "Building REST API"
        assert "Use FastAPI" in data["key_decisions"]
        assert "src/api/routes.py" in data["files_touched"]

    def test_generates_target_tool_configs(self, env):
        switch_tool(target_tool="opencode", project_dir=env["project"], home=env["home"])
        # OpenCode should have modes symlinked
        opencode_modes = Path(env["home"]) / ".config" / "opencode" / "modes"
        assert opencode_modes.exists()

    def test_switch_to_claude_code_creates_agents(self, env):
        # First simulate being in OpenCode
        from scripts.lib.crux_session import update_session
        update_session(project_crux_dir=env["crux_dir"], active_tool="opencode")

        result = switch_tool(
            target_tool="claude-code",
            project_dir=env["project"],
            home=env["home"],
        )
        assert result.success
        agents_dir = Path(env["project"]) / ".claude" / "agents"
        assert agents_dir.is_dir()

    def test_switch_to_claude_code_injects_context(self, env):
        from scripts.lib.crux_session import update_session
        update_session(project_crux_dir=env["crux_dir"], active_tool="opencode")

        switch_tool(target_tool="claude-code", project_dir=env["project"], home=env["home"])
        context = (Path(env["project"]) / ".claude" / "crux-context.md").read_text()
        assert "Building REST API" in context
        assert "FastAPI" in context

    def test_rejects_unsupported_tool(self, env):
        result = switch_tool(
            target_tool="vim-copilot",
            project_dir=env["project"],
            home=env["home"],
        )
        assert not result.success
        assert "unsupported" in result.error.lower()

    def test_switch_to_same_tool(self, env):
        """Switching to the same tool should still succeed (re-sync)."""
        result = switch_tool(
            target_tool="claude-code",
            project_dir=env["project"],
            home=env["home"],
        )
        assert result.success
        assert result.from_tool == "claude-code"
        assert result.to_tool == "claude-code"

    def test_switch_with_no_prior_session(self, tmp_path):
        """Should work even with no prior session state."""
        home = tmp_path / "home"
        project = tmp_path / "project"
        home.mkdir()
        project.mkdir()
        init_user(home=str(home))
        init_project(project_dir=str(project))

        # Add at least one mode
        modes_dir = home / ".crux" / "modes"
        (modes_dir / "build-py.md").write_text("Python specialist.")

        result = switch_tool(
            target_tool="opencode",
            project_dir=str(project),
            home=str(home),
        )
        assert result.success

    def test_result_includes_synced_items(self, env):
        result = switch_tool(
            target_tool="claude-code",
            project_dir=env["project"],
            home=env["home"],
        )
        assert len(result.items_synced) > 0


class TestSwitchSyncFailure:
    def test_propagates_sync_error(self, env, monkeypatch):
        """If sync_tool fails internally, switch_tool should propagate the error."""
        from scripts.lib import crux_switch
        from scripts.lib.crux_sync import SyncResult

        def failing_sync(tool_name, project_dir, home):
            return SyncResult(success=False, tool=tool_name, error="Simulated sync failure")

        monkeypatch.setattr(crux_switch, "sync_tool", failing_sync)
        result = switch_tool(
            target_tool="opencode",
            project_dir=env["project"],
            home=env["home"],
        )
        assert not result.success
        assert "Simulated sync failure" in result.error


class TestRoundTrip:
    """Test switching back and forth between tools preserves state."""

    def test_claude_to_opencode_to_claude(self, env):
        # Start in Claude Code, switch to OpenCode
        r1 = switch_tool(target_tool="opencode", project_dir=env["project"], home=env["home"])
        assert r1.success

        # While in OpenCode, add a decision
        from scripts.lib.crux_session import update_session
        update_session(
            project_crux_dir=env["crux_dir"],
            add_decision="Add Redis caching",
            add_file="src/cache.py",
        )

        # Switch back to Claude Code
        r2 = switch_tool(target_tool="claude-code", project_dir=env["project"], home=env["home"])
        assert r2.success

        # Claude Code context should include the new decision
        context = (Path(env["project"]) / ".claude" / "crux-context.md").read_text()
        assert "Redis caching" in context
        assert "src/cache.py" in context
        # Original state should still be there
        assert "FastAPI" in context
        assert "src/api/routes.py" in context
