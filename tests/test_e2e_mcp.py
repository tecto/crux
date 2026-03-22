"""E2E tests for the Crux MCP server.

Tests the full path: MCP tool function -> handler -> result, using real
file-system state in isolated temp directories. Validates that the MCP
server module loads correctly and that each tool produces expected output.
"""

import os

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import SessionState, save_session


@pytest.fixture
def mcp_env(tmp_path, monkeypatch):
    """Full Crux environment wired to MCP server env vars."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    init_user(home=str(home))
    init_project(project_dir=str(project))

    # Mode files
    modes_dir = home / ".crux" / "modes"
    (modes_dir / "build-py.md").write_text(
        "You are a Python development specialist. Use pytest for testing."
    )
    (modes_dir / "debug.md").write_text(
        "You are a debugging specialist. Find root causes systematically."
    )
    (modes_dir / "plan.md").write_text(
        "You are a software architect. Think before building."
    )

    # Project knowledge
    pk = project / ".crux" / "knowledge"
    (pk / "auth-flow.md").write_text(
        "# Auth Flow\nUse JWT with httponly cookies.\nTags: auth, security"
    )
    (pk / "api-design.md").write_text(
        "# API Design\nREST conventions for all endpoints.\nTags: api, rest"
    )

    # User knowledge
    uk = home / ".crux" / "knowledge" / "shared"
    (uk / "docker-basics.md").write_text(
        "# Docker Basics\nAlways use multi-stage builds.\nTags: docker"
    )

    # Session state
    crux_dir = str(project / ".crux")
    state = SessionState(
        active_mode="build-py",
        active_tool="claude-code",
        working_on="Implementing OAuth2",
        key_decisions=["Use JWT", "Use httponly cookies"],
        files_touched=["src/auth.py"],
        pending=["Add refresh token support"],
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


class TestMCPServerLoads:
    """Verify the MCP server module can be imported and tools are registered."""

    def test_mcp_object_exists(self, mcp_env):
        assert mcp_env["mod"].mcp is not None

    def test_mcp_server_name(self, mcp_env):
        assert mcp_env["mod"].mcp.name == "crux"

    def test_tools_are_registered(self, mcp_env):
        tools = mcp_env["mod"].mcp._tool_manager._tools
        assert len(tools) >= 30

    def test_expected_tools_present(self, mcp_env):
        tools = set(mcp_env["mod"].mcp._tool_manager._tools.keys())
        must_have = {
            "lookup_knowledge",
            "get_session_state",
            "update_session",
            "list_modes",
            "verify_health",
            "bip_status",
        }
        assert must_have.issubset(tools), f"Missing: {must_have - tools}"


class TestVerifyHealth:
    """E2E: verify_health tool returns structured health data."""

    def test_returns_static_and_liveness(self, mcp_env):
        result = mcp_env["mod"].verify_health()
        assert "static" in result
        assert "liveness" in result
        assert "summary" in result

    def test_summary_has_counts(self, mcp_env):
        result = mcp_env["mod"].verify_health()
        summary = result["summary"]
        assert isinstance(summary["total"], int)
        assert summary["total"] > 0
        assert isinstance(summary["passed"], int)
        assert isinstance(summary["failed"], int)
        assert summary["passed"] + summary["failed"] == summary["total"]

    def test_static_checks_are_list(self, mcp_env):
        result = mcp_env["mod"].verify_health()
        assert isinstance(result["static"], list)
        for check in result["static"]:
            assert "name" in check
            assert "passed" in check
            assert "message" in check

    def test_liveness_checks_are_list(self, mcp_env):
        result = mcp_env["mod"].verify_health()
        assert isinstance(result["liveness"], list)
        for check in result["liveness"]:
            assert "name" in check
            assert "passed" in check
            assert "message" in check

    def test_session_check_passes(self, mcp_env):
        result = mcp_env["mod"].verify_health()
        session_check = next(
            c for c in result["static"] if c["name"] == "Session state"
        )
        assert session_check["passed"]
        assert "build-py" in session_check["message"]


class TestListModes:
    """E2E: list_modes tool returns all defined modes."""

    def test_returns_modes_list(self, mcp_env):
        result = mcp_env["mod"].list_modes()
        assert "modes" in result
        assert isinstance(result["modes"], list)

    def test_mode_count(self, mcp_env):
        result = mcp_env["mod"].list_modes()
        assert len(result["modes"]) >= 3  # build-py, debug, plan

    def test_mode_entries_have_name_and_excerpt(self, mcp_env):
        result = mcp_env["mod"].list_modes()
        for mode in result["modes"]:
            assert "name" in mode
            assert "excerpt" in mode

    def test_known_modes_present(self, mcp_env):
        result = mcp_env["mod"].list_modes()
        names = {m["name"] for m in result["modes"]}
        assert "build-py" in names
        assert "debug" in names
        assert "plan" in names


class TestSessionRoundtrip:
    """E2E: get_session_state / update_session roundtrip."""

    def test_get_session_returns_initial_state(self, mcp_env):
        result = mcp_env["mod"].get_session_state()
        assert result["active_mode"] == "build-py"
        assert result["active_tool"] == "claude-code"
        assert result["working_on"] == "Implementing OAuth2"

    def test_update_session_changes_working_on(self, mcp_env):
        mcp_env["mod"].update_session(working_on="Writing E2E tests")
        result = mcp_env["mod"].get_session_state()
        assert result["working_on"] == "Writing E2E tests"

    def test_update_session_adds_decision(self, mcp_env):
        mcp_env["mod"].update_session(add_decision="Use E2E tests for validation")
        result = mcp_env["mod"].get_session_state()
        assert "Use E2E tests for validation" in result["key_decisions"]

    def test_update_session_adds_file(self, mcp_env):
        mcp_env["mod"].update_session(add_file="tests/test_e2e.py")
        result = mcp_env["mod"].get_session_state()
        assert "tests/test_e2e.py" in result["files_touched"]

    def test_update_session_adds_pending(self, mcp_env):
        mcp_env["mod"].update_session(add_pending="Deploy to staging")
        result = mcp_env["mod"].get_session_state()
        assert "Deploy to staging" in result["pending"]

    def test_update_session_switches_mode(self, mcp_env):
        mcp_env["mod"].update_session(active_mode="debug")
        result = mcp_env["mod"].get_session_state()
        assert result["active_mode"] == "debug"

    def test_multiple_updates_accumulate(self, mcp_env):
        mcp_env["mod"].update_session(add_decision="Decision A")
        mcp_env["mod"].update_session(add_decision="Decision B")
        result = mcp_env["mod"].get_session_state()
        # Should have the original 2 decisions plus the 2 new ones
        assert len(result["key_decisions"]) >= 4


class TestLookupKnowledge:
    """E2E: lookup_knowledge tool returns matching entries."""

    def test_finds_project_knowledge(self, mcp_env):
        result = mcp_env["mod"].lookup_knowledge(query="auth")
        assert result["total_found"] >= 1
        names = [r["name"] for r in result["results"]]
        assert "auth-flow" in names

    def test_finds_user_knowledge(self, mcp_env):
        result = mcp_env["mod"].lookup_knowledge(query="docker")
        assert result["total_found"] >= 1
        names = [r["name"] for r in result["results"]]
        assert "docker-basics" in names

    def test_no_results_for_nonexistent(self, mcp_env):
        result = mcp_env["mod"].lookup_knowledge(query="zzznonexistent999")
        assert result["total_found"] == 0

    def test_results_have_expected_fields(self, mcp_env):
        result = mcp_env["mod"].lookup_knowledge(query="api")
        assert result["total_found"] >= 1
        entry = result["results"][0]
        assert "name" in entry
        assert "excerpt" in entry
        assert "source" in entry
        assert "path" in entry

    def test_mode_scoped_lookup(self, mcp_env):
        # Add mode-scoped knowledge
        pk = os.path.join(mcp_env["project"], ".crux", "knowledge", "by-mode", "build-py")
        os.makedirs(pk, exist_ok=True)
        with open(os.path.join(pk, "pytest-tips.md"), "w") as f:
            f.write("# Pytest Tips\nUse conftest.py for shared fixtures.")

        result = mcp_env["mod"].lookup_knowledge(query="pytest", mode="build-py")
        assert result["total_found"] >= 1
        names = [r["name"] for r in result["results"]]
        assert "pytest-tips" in names


class TestRestoreContext:
    """E2E: restore_context rebuilds full session context."""

    def test_returns_context_string(self, mcp_env):
        result = mcp_env["mod"].restore_context()
        assert "context" in result
        assert isinstance(result["context"], str)

    def test_context_includes_mode(self, mcp_env):
        result = mcp_env["mod"].restore_context()
        assert "build-py" in result["context"]

    def test_context_includes_working_on(self, mcp_env):
        result = mcp_env["mod"].restore_context()
        assert "Implementing OAuth2" in result["context"]

    def test_context_includes_decisions(self, mcp_env):
        result = mcp_env["mod"].restore_context()
        assert "Use JWT" in result["context"]

    def test_context_includes_pending(self, mcp_env):
        result = mcp_env["mod"].restore_context()
        assert "refresh token" in result["context"]


class TestBipStatus:
    """E2E: bip_status returns counters and state."""

    def test_returns_expected_fields(self, mcp_env):
        result = mcp_env["mod"].bip_status()
        assert "commits_since_last_post" in result
        assert "interactions_since_last_post" in result
        assert "tokens_since_last_post" in result
        assert "posts_today" in result
        assert "cooldown_ok" in result
        assert "thresholds" in result
        assert "total_posts" in result

    def test_initial_counters_are_zero(self, mcp_env):
        result = mcp_env["mod"].bip_status()
        assert result["commits_since_last_post"] == 0
        assert result["interactions_since_last_post"] == 0
        assert result["tokens_since_last_post"] == 0
        assert result["posts_today"] == 0
