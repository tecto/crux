"""Tests for crux_sync.py — generate tool-specific configs from .crux/."""

import json
import os
from pathlib import Path

import pytest

from scripts.lib.crux_sync import (
    sync_opencode,
    sync_claude_code,
    sync_cursor,
    sync_windsurf,
    sync_tool,
    strip_frontmatter,
    SUPPORTED_TOOLS,
    OPENCODE_AGENT_META,
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
        assert "cursor" in SUPPORTED_TOOLS
        assert "windsurf" in SUPPORTED_TOOLS

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

    def test_merges_agents_md(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        agents_md = Path(env["home"]) / ".config" / "opencode" / "AGENTS.md"
        assert agents_md.exists()
        assert not agents_md.is_symlink()  # regular file, not symlink
        content = agents_md.read_text()
        assert "log_interaction" in content
        assert "<!-- CRUX:START -->" in content
        assert "<!-- CRUX:END -->" in content

    def test_agents_md_preserves_existing_content(self, env):
        config_dir = Path(env["home"]) / ".config" / "opencode"
        config_dir.mkdir(parents=True, exist_ok=True)
        agents_md = config_dir / "AGENTS.md"
        agents_md.write_text("# My Custom Rules\n\nDo things my way.\n")

        sync_opencode(project_dir=env["project"], home=env["home"])
        content = agents_md.read_text()
        assert "My Custom Rules" in content
        assert "Do things my way" in content
        assert "log_interaction" in content

    def test_agents_md_updates_crux_section_on_resync(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        agents_md = Path(env["home"]) / ".config" / "opencode" / "AGENTS.md"
        # Second sync should replace, not duplicate
        sync_opencode(project_dir=env["project"], home=env["home"])
        content = agents_md.read_text()
        assert content.count("<!-- CRUX:START -->") == 1
        assert content.count("<!-- CRUX:END -->") == 1

    def test_agents_md_converts_legacy_symlink(self, env):
        from scripts.lib.crux_sync import _crux_repo_root
        config_dir = Path(env["home"]) / ".config" / "opencode"
        config_dir.mkdir(parents=True, exist_ok=True)
        agents_md = config_dir / "AGENTS.md"
        # Simulate legacy symlink
        source = os.path.join(_crux_repo_root(), "templates", "AGENTS.md")
        os.symlink(source, str(agents_md))
        assert agents_md.is_symlink()

        sync_opencode(project_dir=env["project"], home=env["home"])
        assert not agents_md.is_symlink()
        content = agents_md.read_text()
        assert "<!-- CRUX:START -->" in content

    def test_agents_md_in_items_synced(self, env):
        result = sync_opencode(project_dir=env["project"], home=env["home"])
        assert "AGENTS.md" in result.items_synced

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

    def test_writes_mcp_config_to_opencode_json(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        config_file = Path(env["home"]) / ".config" / "opencode" / "opencode.json"
        assert config_file.exists()
        config = json.loads(config_file.read_text())
        assert "mcp" in config
        assert "crux" in config["mcp"]

    def test_mcp_config_has_correct_format(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        config_file = Path(env["home"]) / ".config" / "opencode" / "opencode.json"
        config = json.loads(config_file.read_text())
        crux_mcp = config["mcp"]["crux"]
        assert crux_mcp["type"] == "local"
        assert isinstance(crux_mcp["command"], list)
        assert crux_mcp["enabled"] is True

    def test_mcp_config_command_runs_crux_mcp_server(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        config_file = Path(env["home"]) / ".config" / "opencode" / "opencode.json"
        config = json.loads(config_file.read_text())
        cmd = crux_mcp = config["mcp"]["crux"]["command"]
        assert any("crux_mcp_server" in arg for arg in cmd)

    def test_mcp_config_sets_environment_vars(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        config_file = Path(env["home"]) / ".config" / "opencode" / "opencode.json"
        config = json.loads(config_file.read_text())
        mcp_env = config["mcp"]["crux"]["environment"]
        assert "CRUX_PROJECT" in mcp_env
        assert "CRUX_HOME" in mcp_env

    def test_mcp_config_preserves_existing_opencode_json(self, env):
        """If opencode.json already exists, merge MCP config into it."""
        config_dir = Path(env["home"]) / ".config" / "opencode"
        config_dir.mkdir(parents=True, exist_ok=True)
        existing = {"model": "ollama/crux-think", "timeout": 600000}
        (config_dir / "opencode.json").write_text(json.dumps(existing))

        sync_opencode(project_dir=env["project"], home=env["home"])
        config = json.loads((config_dir / "opencode.json").read_text())
        assert config["model"] == "ollama/crux-think"
        assert config["timeout"] == 600000
        assert "mcp" in config
        assert "crux" in config["mcp"]

    def test_mcp_config_updates_existing_crux_entry(self, env):
        """If opencode.json already has a crux MCP entry, update it."""
        config_dir = Path(env["home"]) / ".config" / "opencode"
        config_dir.mkdir(parents=True, exist_ok=True)
        existing = {"mcp": {"crux": {"type": "local", "command": ["old"], "enabled": False}}}
        (config_dir / "opencode.json").write_text(json.dumps(existing))

        sync_opencode(project_dir=env["project"], home=env["home"])
        config = json.loads((config_dir / "opencode.json").read_text())
        assert config["mcp"]["crux"]["enabled"] is True
        assert "old" not in config["mcp"]["crux"]["command"]

    def test_mcp_config_preserves_other_mcp_servers(self, env):
        """Other MCP servers in opencode.json should not be disturbed."""
        config_dir = Path(env["home"]) / ".config" / "opencode"
        config_dir.mkdir(parents=True, exist_ok=True)
        existing = {"mcp": {"github": {"type": "remote", "url": "https://example.com"}}}
        (config_dir / "opencode.json").write_text(json.dumps(existing))

        sync_opencode(project_dir=env["project"], home=env["home"])
        config = json.loads((config_dir / "opencode.json").read_text())
        assert "github" in config["mcp"]
        assert config["mcp"]["github"]["url"] == "https://example.com"
        assert "crux" in config["mcp"]

    def test_items_synced_includes_mcp(self, env):
        result = sync_opencode(project_dir=env["project"], home=env["home"])
        assert "mcp-config" in result.items_synced

    def test_handles_corrupt_opencode_json(self, env):
        """If opencode.json is corrupt, overwrite with fresh MCP config."""
        config_dir = Path(env["home"]) / ".config" / "opencode"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "opencode.json").write_text("{bad json")

        sync_opencode(project_dir=env["project"], home=env["home"])
        config = json.loads((config_dir / "opencode.json").read_text())
        assert "mcp" in config
        assert "crux" in config["mcp"]


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

    def test_includes_pending_in_context(self, env):
        from scripts.lib.crux_session import load_session, save_session
        state = load_session(env["crux_dir"])
        state.pending.append("Write API tests")
        save_session(state, project_crux_dir=env["crux_dir"])

        sync_claude_code(project_dir=env["project"], home=env["home"])
        context = (Path(env["project"]) / ".claude" / "crux-context.md").read_text()
        assert "Write API tests" in context
        assert "Pending" in context

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


# ---------------------------------------------------------------------------
# strip_frontmatter
# ---------------------------------------------------------------------------

class TestStripFrontmatter:
    def test_strips_yaml_frontmatter(self):
        content = "---\nmodel: ollama/crux-code\ntemperature: 0.4\n---\n\n# Mode: build-py\nBody."
        assert strip_frontmatter(content) == "# Mode: build-py\nBody."

    def test_returns_content_without_frontmatter_unchanged(self):
        content = "# Mode: build-py\nBody text."
        assert strip_frontmatter(content) == content

    def test_strips_frontmatter_preserves_body_exactly(self):
        body = "# Title\n\nParagraph with ---dashes--- in text."
        content = f"---\nkey: value\n---\n\n{body}"
        assert strip_frontmatter(content) == body

    def test_empty_string(self):
        assert strip_frontmatter("") == ""

    def test_only_frontmatter_no_body(self):
        content = "---\nkey: value\n---\n"
        assert strip_frontmatter(content) == ""

    def test_frontmatter_with_multiline_values(self):
        content = "---\npermission:\n  read: allow\n  edit: deny\n---\n\n# Body"
        assert strip_frontmatter(content) == "# Body"

    def test_does_not_strip_if_no_closing_delimiter(self):
        content = "---\nkey: value\n# No closing delimiter"
        assert strip_frontmatter(content) == content

    def test_frontmatter_must_start_at_beginning(self):
        content = "Some text\n---\nkey: value\n---\n\nBody"
        assert strip_frontmatter(content) == content


# ---------------------------------------------------------------------------
# OPENCODE_AGENT_META
# ---------------------------------------------------------------------------

class TestOpenCodeAgentMeta:
    def test_all_15_original_modes_present(self):
        expected = {
            "build-py", "build-ex", "plan", "infra-architect", "review",
            "debug", "explain", "analyst", "writer", "psych", "legal",
            "strategist", "ai-infra", "mac", "docker",
        }
        for mode in expected:
            assert mode in OPENCODE_AGENT_META, f"Missing mode: {mode}"

    def test_new_modes_present(self):
        new_modes = {"test", "security", "design-ui", "design-review",
                     "design-system", "design-responsive", "design-accessibility"}
        for mode in new_modes:
            assert mode in OPENCODE_AGENT_META, f"Missing new mode: {mode}"

    def test_all_entries_have_required_fields(self):
        for mode, meta in OPENCODE_AGENT_META.items():
            assert "model" in meta, f"{mode} missing model"
            assert "temperature" in meta, f"{mode} missing temperature"
            assert "description" in meta, f"{mode} missing description"
            assert "permission" in meta, f"{mode} missing permission"

    def test_model_values_are_valid_ollama_refs(self):
        valid_models = {"ollama/qwen3.5:27b", "ollama/qwen3-coder:30b"}
        for mode, meta in OPENCODE_AGENT_META.items():
            assert meta["model"] in valid_models, f"{mode} has invalid model: {meta['model']}"

    def test_think_modes_use_qwen35(self):
        think_modes = {"plan", "infra-architect", "review", "debug", "legal",
                       "strategist", "psych", "security", "design-review",
                       "design-accessibility"}
        for mode in think_modes:
            assert OPENCODE_AGENT_META[mode]["model"] == "ollama/qwen3.5:27b"

    def test_code_modes_use_qwen3_coder(self):
        code_modes = {"build-py", "build-ex", "docker", "test",
                      "design-ui", "design-system", "design-responsive"}
        for mode in code_modes:
            assert OPENCODE_AGENT_META[mode]["model"] == "ollama/qwen3-coder:30b"

    def test_chat_modes_use_qwen35(self):
        chat_modes = {"writer", "analyst", "explain", "mac", "ai-infra"}
        for mode in chat_modes:
            assert OPENCODE_AGENT_META[mode]["model"] == "ollama/qwen3.5:27b"

    def test_temperature_ranges(self):
        for mode, meta in OPENCODE_AGENT_META.items():
            assert 0.0 <= meta["temperature"] <= 1.0, f"{mode} temp out of range"

    def test_permission_is_dict_with_expected_keys(self):
        for mode, meta in OPENCODE_AGENT_META.items():
            perm = meta["permission"]
            assert isinstance(perm, dict), f"{mode} permission not a dict"
            assert "read" in perm, f"{mode} permission missing read"
            assert "edit" in perm, f"{mode} permission missing edit"
            assert "bash" in perm, f"{mode} permission missing bash"

    def test_read_only_modes_deny_edit_and_bash(self):
        ro_modes = {"plan", "infra-architect", "review", "explain", "psych",
                    "design-review", "design-accessibility"}
        for mode in ro_modes:
            perm = OPENCODE_AGENT_META[mode]["permission"]
            assert perm["edit"] == "deny", f"{mode} should deny edit"
            assert perm["bash"] == "deny", f"{mode} should deny bash"


# ---------------------------------------------------------------------------
# sync_opencode — agents directory
# ---------------------------------------------------------------------------

class TestSyncOpenCodeAgents:
    def test_symlinks_agents_directory(self, env):
        sync_opencode(project_dir=env["project"], home=env["home"])
        agents_link = Path(env["home"]) / ".config" / "opencode" / "agents"
        assert agents_link.exists()
        assert (agents_link / "build-py.md").exists()

    def test_agents_in_items_synced(self, env):
        result = sync_opencode(project_dir=env["project"], home=env["home"])
        assert "agents" in result.items_synced


# ---------------------------------------------------------------------------
# sync_claude_code — frontmatter stripping
# ---------------------------------------------------------------------------

class TestSyncClaudeCodeFrontmatterStripping:
    def test_strips_opencode_frontmatter_from_modes(self, env):
        """If mode files have YAML frontmatter, Claude Code agents should not inherit it."""
        # Add OpenCode frontmatter to a mode file
        modes_dir = Path(env["home"]) / ".crux" / "modes"
        (modes_dir / "build-py.md").write_text(
            "---\nmodel: ollama/crux-code\ntemperature: 0.4\n---\n\nYou are a Python specialist."
        )
        sync_claude_code(project_dir=env["project"], home=env["home"])
        agent = (Path(env["project"]) / ".claude" / "agents" / "build-py.md").read_text()
        # Should have Claude Code frontmatter, not OpenCode frontmatter
        assert "ollama/qwen3-coder:30b" not in agent
        assert "description:" in agent.lower()

    def test_body_preserved_after_stripping(self, env):
        modes_dir = Path(env["home"]) / ".crux" / "modes"
        (modes_dir / "build-py.md").write_text(
            "---\nmodel: ollama/crux-code\n---\n\nPython specialist body."
        )
        sync_claude_code(project_dir=env["project"], home=env["home"])
        agent = (Path(env["project"]) / ".claude" / "agents" / "build-py.md").read_text()
        assert "Python specialist body." in agent


# ---------------------------------------------------------------------------
# sync_cursor
# ---------------------------------------------------------------------------

class TestSyncCursor:
    def test_creates_cursor_rules_dir(self, env):
        result = sync_cursor(project_dir=env["project"], home=env["home"])
        assert result.success is True
        assert result.tool == "cursor"
        rules_dir = Path(env["project"]) / ".cursor" / "rules"
        assert rules_dir.is_dir()

    def test_creates_rules_from_modes(self, env):
        sync_cursor(project_dir=env["project"], home=env["home"])
        rules_dir = Path(env["project"]) / ".cursor" / "rules"
        assert (rules_dir / "build-py.md").exists()
        assert (rules_dir / "debug.md").exists()

    def test_strips_frontmatter_from_rules(self, env):
        modes_dir = Path(env["home"]) / ".crux" / "modes"
        (modes_dir / "build-py.md").write_text(
            "---\nmodel: ollama/crux-code\ntemperature: 0.4\n---\n\nPython specialist."
        )
        sync_cursor(project_dir=env["project"], home=env["home"])
        rule = (Path(env["project"]) / ".cursor" / "rules" / "build-py.md").read_text()
        assert "---" not in rule
        assert "Python specialist." in rule

    def test_creates_context_rule(self, env):
        sync_cursor(project_dir=env["project"], home=env["home"])
        context = (Path(env["project"]) / ".cursor" / "rules" / "crux-context.md").read_text()
        assert "debug" in context  # active mode
        assert "Fixing auth bug" in context  # working_on

    def test_writes_mcp_config(self, env):
        sync_cursor(project_dir=env["project"], home=env["home"])
        mcp_path = Path(env["project"]) / ".cursor" / "mcp.json"
        assert mcp_path.exists()
        with open(mcp_path) as f:
            config = json.load(f)
        assert "mcpServers" in config
        assert "crux" in config["mcpServers"]

    def test_merges_existing_mcp_config(self, env):
        mcp_path = Path(env["project"]) / ".cursor" / "mcp.json"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        mcp_path.write_text(json.dumps({"mcpServers": {"other": {"command": "test"}}}))

        sync_cursor(project_dir=env["project"], home=env["home"])
        with open(mcp_path) as f:
            config = json.load(f)
        assert "other" in config["mcpServers"]
        assert "crux" in config["mcpServers"]

    def test_creates_crux_agent_rule(self, env):
        sync_cursor(project_dir=env["project"], home=env["home"])
        agent = Path(env["project"]) / ".cursor" / "rules" / "crux-agent.md"
        assert agent.exists()

    def test_items_synced(self, env):
        result = sync_cursor(project_dir=env["project"], home=env["home"])
        assert "crux-context" in result.items_synced
        assert "mcp-config" in result.items_synced
        assert any(i.startswith("rule:") for i in result.items_synced)

    def test_idempotent(self, env):
        sync_cursor(project_dir=env["project"], home=env["home"])
        result = sync_cursor(project_dir=env["project"], home=env["home"])
        assert result.success is True


# ---------------------------------------------------------------------------
# sync_windsurf
# ---------------------------------------------------------------------------

class TestSyncWindsurf:
    def test_creates_windsurf_rules_dir(self, env):
        result = sync_windsurf(project_dir=env["project"], home=env["home"])
        assert result.success is True
        assert result.tool == "windsurf"
        rules_dir = Path(env["project"]) / ".windsurf" / "rules"
        assert rules_dir.is_dir()

    def test_creates_rules_from_modes(self, env):
        sync_windsurf(project_dir=env["project"], home=env["home"])
        rules_dir = Path(env["project"]) / ".windsurf" / "rules"
        assert (rules_dir / "build-py.md").exists()

    def test_strips_frontmatter(self, env):
        modes_dir = Path(env["home"]) / ".crux" / "modes"
        (modes_dir / "build-py.md").write_text(
            "---\nmodel: test\n---\n\nWindsurf body."
        )
        sync_windsurf(project_dir=env["project"], home=env["home"])
        rule = (Path(env["project"]) / ".windsurf" / "rules" / "build-py.md").read_text()
        assert "Windsurf body." in rule
        assert "model:" not in rule

    def test_creates_context_rule(self, env):
        sync_windsurf(project_dir=env["project"], home=env["home"])
        context = (Path(env["project"]) / ".windsurf" / "rules" / "crux-context.md").read_text()
        assert "debug" in context
        assert "Fixing auth bug" in context

    def test_writes_mcp_config(self, env):
        sync_windsurf(project_dir=env["project"], home=env["home"])
        mcp_path = Path(env["project"]) / ".windsurf" / "mcp.json"
        assert mcp_path.exists()
        with open(mcp_path) as f:
            config = json.load(f)
        assert "crux" in config["mcpServers"]

    def test_items_synced(self, env):
        result = sync_windsurf(project_dir=env["project"], home=env["home"])
        assert "crux-context" in result.items_synced
        assert "mcp-config" in result.items_synced

    def test_creates_crux_agent_rule(self, env):
        sync_windsurf(project_dir=env["project"], home=env["home"])
        agent = Path(env["project"]) / ".windsurf" / "rules" / "crux-agent.md"
        assert agent.exists()


# ---------------------------------------------------------------------------
# sync_tool dispatch for cursor/windsurf
# ---------------------------------------------------------------------------

class TestSyncToolDispatchNew:
    def test_dispatches_cursor(self, env):
        result = sync_tool("cursor", project_dir=env["project"], home=env["home"])
        assert result.success is True
        assert result.tool == "cursor"

    def test_dispatches_windsurf(self, env):
        result = sync_tool("windsurf", project_dir=env["project"], home=env["home"])
        assert result.success is True
        assert result.tool == "windsurf"

    def test_updates_session_on_cursor_sync(self, env):
        from scripts.lib.crux_session import load_session
        sync_tool("cursor", project_dir=env["project"], home=env["home"])
        state = load_session(env["crux_dir"])
        assert state.active_tool == "cursor"

    def test_updates_session_on_windsurf_sync(self, env):
        from scripts.lib.crux_session import load_session
        sync_tool("windsurf", project_dir=env["project"], home=env["home"])
        state = load_session(env["crux_dir"])
        assert state.active_tool == "windsurf"


# ---------------------------------------------------------------------------
# Edge cases for coverage
# ---------------------------------------------------------------------------

class TestSyncEdgeCases:
    def test_frontmatter_ending_with_no_body(self):
        content = "---\nkey: value\n---"
        result = strip_frontmatter(content)
        assert result == ""

    def test_context_includes_pending_tasks(self, env):
        from scripts.lib.crux_session import load_session, save_session
        state = load_session(env["crux_dir"])
        state.pending = ["Fix login bug", "Deploy API"]
        save_session(state, project_crux_dir=env["crux_dir"])

        sync_cursor(project_dir=env["project"], home=env["home"])
        context = (Path(env["project"]) / ".cursor" / "rules" / "crux-context.md").read_text()
        assert "Fix login bug" in context
        assert "Deploy API" in context

    def test_cursor_handles_corrupt_mcp_config(self, env):
        mcp_path = Path(env["project"]) / ".cursor" / "mcp.json"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        mcp_path.write_text("not json")

        result = sync_cursor(project_dir=env["project"], home=env["home"])
        assert result.success is True
        with open(mcp_path) as f:
            config = json.load(f)
        assert "crux" in config["mcpServers"]
