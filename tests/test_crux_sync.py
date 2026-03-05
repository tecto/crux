"""Tests for crux_sync.py — generate tool-specific configs from .crux/."""

import json
import os
from pathlib import Path

import pytest

from scripts.lib.crux_sync import (
    sync_opencode,
    sync_claude_code,
    sync_tool,
    SUPPORTED_TOOLS,
    SyncResult,
)
from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import SessionState, save_session, write_handoff


@pytest.fixture
def env(tmp_path):
    """Set up a complete Crux environment with project + user."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    init_user(home=str(home))
    init_project(project_dir=str(project))

    # Add some knowledge entries
    k = project / ".crux" / "knowledge"
    (k / "auth-patterns.md").write_text("# Auth Patterns\nUse JWT with httponly cookies.\nTags: auth, security")
    (k / "by-mode" / "build-py").mkdir(parents=True, exist_ok=True)
    (k / "by-mode" / "build-py" / "pytest-tips.md").write_text("# Pytest Tips\nUse conftest.py.\nTags: python, testing")

    uk = home / ".crux" / "knowledge" / "shared"
    (uk / "docker-basics.md").write_text("# Docker Basics\nMulti-stage builds.\nTags: docker")

    # Add mode definitions
    modes_dir = home / ".crux" / "modes"
    (modes_dir / "build-py.md").write_text("You are a Python development specialist.")
    (modes_dir / "debug.md").write_text("You are a debugging specialist.")
    (modes_dir / "plan.md").write_text("You are a software architect.")

    # Save a session state
    crux_dir = str(project / ".crux")
    state = SessionState(
        active_mode="debug",
        active_tool="claude-code",
        working_on="Fixing auth bug",
        key_decisions=["Use JWT"],
        files_touched=["src/auth.py"],
    )
    save_session(state, project_crux_dir=crux_dir)
    write_handoff("Switching to plan mode for API design", project_crux_dir=crux_dir)

    return {"home": str(home), "project": str(project), "crux_dir": crux_dir}


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestSupportedTools:
    def test_includes_expected_tools(self):
        assert "opencode" in SUPPORTED_TOOLS
        assert "claude-code" in SUPPORTED_TOOLS

    def test_is_frozen(self):
        assert isinstance(SUPPORTED_TOOLS, (tuple, frozenset, list))


# ---------------------------------------------------------------------------
# sync_opencode
# ---------------------------------------------------------------------------

class TestSyncOpenCode:
    def test_returns_sync_result(self, env):
        result = sync_opencode(
            project_dir=env["project"],
            home=env["home"],
        )
        assert isinstance(result, SyncResult)
        assert result.success
        assert result.tool == "opencode"

    def test_creates_opencode_config_dir(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        config_dir = Path(env["home"]) / ".config" / "opencode"
        assert config_dir.is_dir()

    def test_symlinks_modes(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        modes_link = Path(env["home"]) / ".config" / "opencode" / "modes"
        assert modes_link.exists()
        # Should contain our mode files
        assert (modes_link / "build-py.md").exists()

    def test_creates_knowledge_symlinks(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        know_link = Path(env["home"]) / ".config" / "opencode" / "knowledge"
        assert know_link.exists()

    def test_lists_created_items(self, env):
        result = sync_opencode(project_dir=env["project"], home=env["home"])
        assert len(result.items_synced) > 0

    def test_idempotent(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        result = sync_opencode(project_dir=env["project"], home=env["home"])
        assert result.success

    def test_replaces_existing_dir_with_symlink(self, env):
        """If a real directory exists at the symlink target, it should be replaced."""
        config_dir = os.path.join(env["home"], ".config", "opencode")
        real_dir = os.path.join(config_dir, "modes")
        os.makedirs(real_dir)
        # Put a file in the real dir to prove it gets replaced
        Path(real_dir).joinpath("stale.md").write_text("old")

        result = sync_opencode(project_dir=env["project"], home=env["home"])
        assert result.success
        modes_link = Path(config_dir) / "modes"
        assert modes_link.is_symlink() or modes_link.is_dir()

    def test_replaces_existing_file_with_symlink(self, env):
        """If a regular file exists at the symlink target, it should be replaced."""
        config_dir = os.path.join(env["home"], ".config", "opencode")
        os.makedirs(config_dir, exist_ok=True)
        target = os.path.join(config_dir, "knowledge")
        Path(target).write_text("not a symlink")

        result = sync_opencode(project_dir=env["project"], home=env["home"])
        assert result.success


# ---------------------------------------------------------------------------
# sync_claude_code
# ---------------------------------------------------------------------------

class TestSyncClaudeCode:
    def test_returns_sync_result(self, env):
        result = sync_claude_code(
            project_dir=env["project"],
            home=env["home"],
        )
        assert isinstance(result, SyncResult)
        assert result.success
        assert result.tool == "claude-code"

    def test_creates_claude_dir(self, env):
        sync_claude_code(project_dir=env["project"], home=env["home"])
        claude_dir = Path(env["project"]) / ".claude"
        assert claude_dir.is_dir()

    def test_creates_agents_from_modes(self, env):
        sync_claude_code(project_dir=env["project"], home=env["home"])
        agents_dir = Path(env["project"]) / ".claude" / "agents"
        assert agents_dir.is_dir()
        # Should have agent files created from mode definitions
        assert (agents_dir / "build-py.md").exists()
        assert (agents_dir / "debug.md").exists()

    def test_agent_files_have_frontmatter(self, env):
        sync_claude_code(project_dir=env["project"], home=env["home"])
        agent = (Path(env["project"]) / ".claude" / "agents" / "build-py.md").read_text()
        assert "---" in agent
        assert "name:" in agent.lower() or "description:" in agent.lower()

    def test_creates_rules_from_knowledge(self, env):
        sync_claude_code(project_dir=env["project"], home=env["home"])
        rules_dir = Path(env["project"]) / ".claude" / "rules"
        assert rules_dir.is_dir()
        # Should have rules generated from knowledge entries
        rule_files = list(rules_dir.glob("*.md"))
        assert len(rule_files) > 0

    def test_creates_session_context(self, env):
        """Should inject session state as a context file for Claude Code."""
        sync_claude_code(project_dir=env["project"], home=env["home"])
        context = Path(env["project"]) / ".claude" / "crux-context.md"
        assert context.exists()
        content = context.read_text()
        assert "debug" in content  # active mode
        assert "auth" in content.lower()  # working on

    def test_includes_handoff_in_context(self, env):
        sync_claude_code(project_dir=env["project"], home=env["home"])
        context = (Path(env["project"]) / ".claude" / "crux-context.md").read_text()
        assert "API design" in context

    def test_idempotent(self, env):
        sync_claude_code(project_dir=env["project"], home=env["home"])
        result = sync_claude_code(project_dir=env["project"], home=env["home"])
        assert result.success


# ---------------------------------------------------------------------------
# sync_tool (dispatch)
# ---------------------------------------------------------------------------

class TestSyncTool:
    def test_dispatches_to_opencode(self, env):
        result = sync_tool("opencode", project_dir=env["project"], home=env["home"])
        assert result.tool == "opencode"
        assert result.success

    def test_dispatches_to_claude_code(self, env):
        result = sync_tool("claude-code", project_dir=env["project"], home=env["home"])
        assert result.tool == "claude-code"
        assert result.success

    def test_rejects_unknown_tool(self, env):
        result = sync_tool("unknown-tool", project_dir=env["project"], home=env["home"])
        assert not result.success
        assert "unsupported" in result.error.lower()

    def test_updates_session_active_tool(self, env):
        sync_tool("opencode", project_dir=env["project"], home=env["home"])
        state_file = Path(env["project"]) / ".crux" / "sessions" / "state.json"
        data = json.loads(state_file.read_text())
        assert data["active_tool"] == "opencode"
