"""Tests for crux_mcp_server.py — Crux MCP server tool functions.

Tests the tool handler functions directly, not through MCP protocol.
The MCP decorators are thin wrappers; the logic lives in testable functions.
"""

import json
import os
import unittest.mock
from pathlib import Path

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import SessionState, save_session, write_handoff

# Import the handler module (not the server — we test functions, not protocol)
from scripts.lib.crux_mcp_handlers import (
    handle_lookup_knowledge,
    handle_get_session_state,
    handle_update_session,
    handle_write_handoff,
    handle_read_handoff,
    handle_get_digest,
    handle_get_mode_prompt,
    handle_validate_script,
    handle_promote_knowledge,
    handle_get_project_context,
    handle_switch_tool,
    handle_list_modes,
    handle_log_correction,
    handle_restore_context,
)


@pytest.fixture
def env(tmp_path):
    """Full Crux environment for MCP handler testing."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    init_user(home=str(home))
    init_project(project_dir=str(project))

    # Mode definitions
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
    (pk / "by-mode" / "build-py").mkdir(parents=True, exist_ok=True)
    (pk / "by-mode" / "build-py" / "pytest-tips.md").write_text(
        "# Pytest Tips\nUse conftest.py for shared fixtures.\nTags: pytest, python"
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
        key_decisions=["Use python-jose for JWT"],
        files_touched=["src/auth.py"],
        pending=["Add refresh token endpoint"],
    )
    save_session(state, project_crux_dir=crux_dir)

    return {
        "home": str(home),
        "project": str(project),
        "crux_dir": crux_dir,
    }


# ---------------------------------------------------------------------------
# lookup_knowledge
# ---------------------------------------------------------------------------

class TestLookupKnowledge:
    def test_finds_matching_entries(self, env):
        result = handle_lookup_knowledge(
            query="auth",
            project_dir=env["project"],
            home=env["home"],
        )
        assert result["total_found"] > 0
        names = [r["name"] for r in result["results"]]
        assert "auth-flow" in names

    def test_mode_scoped_search(self, env):
        result = handle_lookup_knowledge(
            query="pytest",
            mode="build-py",
            project_dir=env["project"],
            home=env["home"],
        )
        assert result["total_found"] > 0
        names = [r["name"] for r in result["results"]]
        assert "pytest-tips" in names

    def test_no_results(self, env):
        result = handle_lookup_knowledge(
            query="nonexistent-xyzzy",
            project_dir=env["project"],
            home=env["home"],
        )
        assert result["total_found"] == 0
        assert result["results"] == []

    def test_cross_scope_search(self, env):
        result = handle_lookup_knowledge(
            query="docker",
            project_dir=env["project"],
            home=env["home"],
        )
        assert result["total_found"] > 0


# ---------------------------------------------------------------------------
# get_session_state / update_session
# ---------------------------------------------------------------------------

class TestSessionState:
    def test_get_session_state(self, env):
        result = handle_get_session_state(
            project_dir=env["project"],
        )
        assert result["active_mode"] == "build-py"
        assert result["active_tool"] == "claude-code"
        assert result["working_on"] == "Implementing OAuth2"
        assert "python-jose" in result["key_decisions"][0]

    def test_get_session_state_no_session(self, tmp_path):
        project = tmp_path / "empty"
        project.mkdir()
        init_project(project_dir=str(project))
        result = handle_get_session_state(project_dir=str(project))
        assert result["active_mode"] == "build-py"

    def test_update_session_mode(self, env):
        result = handle_update_session(
            project_dir=env["project"],
            active_mode="debug",
        )
        assert result["active_mode"] == "debug"
        # Verify persisted
        loaded = handle_get_session_state(project_dir=env["project"])
        assert loaded["active_mode"] == "debug"

    def test_update_session_working_on(self, env):
        result = handle_update_session(
            project_dir=env["project"],
            working_on="Debugging timeout bug",
        )
        assert result["working_on"] == "Debugging timeout bug"

    def test_update_session_add_decision(self, env):
        result = handle_update_session(
            project_dir=env["project"],
            add_decision="Use Redis for session cache",
        )
        assert "Use Redis for session cache" in result["key_decisions"]
        assert "Use python-jose for JWT" in result["key_decisions"]

    def test_update_session_add_file(self, env):
        result = handle_update_session(
            project_dir=env["project"],
            add_file="src/cache.py",
        )
        assert "src/cache.py" in result["files_touched"]

    def test_update_session_add_pending(self, env):
        result = handle_update_session(
            project_dir=env["project"],
            add_pending="Write cache tests",
        )
        assert "Write cache tests" in result["pending"]

    def test_update_session_tool(self, env):
        result = handle_update_session(
            project_dir=env["project"],
            active_tool="opencode",
        )
        assert result["active_tool"] == "opencode"


# ---------------------------------------------------------------------------
# Handoff
# ---------------------------------------------------------------------------

class TestHandoff:
    def test_write_and_read_handoff(self, env):
        handle_write_handoff(
            content="Switching to plan mode. Need to design the cache layer.",
            project_dir=env["project"],
        )
        result = handle_read_handoff(project_dir=env["project"])
        assert "cache layer" in result["content"]
        assert result["exists"]

    def test_read_handoff_missing(self, env):
        result = handle_read_handoff(project_dir=env["project"])
        assert not result["exists"]
        assert result["content"] is None


# ---------------------------------------------------------------------------
# get_mode_prompt / list_modes
# ---------------------------------------------------------------------------

class TestModes:
    def test_get_mode_prompt(self, env):
        result = handle_get_mode_prompt(
            mode="build-py",
            home=env["home"],
        )
        assert result["found"]
        assert "Python" in result["prompt"]
        assert result["mode"] == "build-py"

    def test_get_mode_prompt_not_found(self, env):
        result = handle_get_mode_prompt(
            mode="nonexistent-mode",
            home=env["home"],
        )
        assert not result["found"]

    def test_list_modes(self, env):
        result = handle_list_modes(home=env["home"])
        assert len(result["modes"]) == 3
        names = [m["name"] for m in result["modes"]]
        assert "build-py" in names
        assert "debug" in names
        assert "plan" in names

    def test_list_modes_includes_descriptions(self, env):
        result = handle_list_modes(home=env["home"])
        build_py = [m for m in result["modes"] if m["name"] == "build-py"][0]
        assert len(build_py["excerpt"]) > 0


# ---------------------------------------------------------------------------
# validate_script
# ---------------------------------------------------------------------------

class TestValidateScript:
    def test_valid_script(self, env):
        script = (
            "#!/bin/bash\n"
            "################################################################################\n"
            "# Name: test-script\n"
            "# Risk: low\n"
            "# Created: 2026-03-05\n"
            "# Status: session\n"
            "# Description: Lists files\n"
            "################################################################################\n"
            "set -euo pipefail\n"
            "main() { ls -la; }\n"
            'if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then main "$@"; fi\n'
        )
        result = handle_validate_script(content=script)
        assert result["passed"]
        assert result["errors"] == []

    def test_invalid_script_no_shebang(self, env):
        script = "echo hello"
        result = handle_validate_script(content=script)
        assert not result["passed"]
        assert len(result["errors"]) > 0


# ---------------------------------------------------------------------------
# promote_knowledge
# ---------------------------------------------------------------------------

class TestPromoteKnowledge:
    def test_promote_entry(self, env):
        result = handle_promote_knowledge(
            entry_name="auth-flow",
            project_dir=env["project"],
            home=env["home"],
        )
        assert result["promoted"]
        # Verify it exists in user scope now
        user_k = Path(env["home"]) / ".crux" / "knowledge" / "auth-flow.md"
        assert user_k.exists()

    def test_promote_not_found(self, env):
        result = handle_promote_knowledge(
            entry_name="nonexistent-entry",
            project_dir=env["project"],
            home=env["home"],
        )
        assert not result["promoted"]
        assert "not found" in result["error"]


# ---------------------------------------------------------------------------
# get_project_context
# ---------------------------------------------------------------------------

class TestProjectContext:
    def test_get_project_context_with_file(self, env):
        ctx_dir = Path(env["project"]) / ".crux" / "context"
        ctx_dir.mkdir(parents=True, exist_ok=True)
        (ctx_dir / "PROJECT.md").write_text(
            "# Project: test-app\n\n## Tech Stack\n- Python\n- FastAPI"
        )
        result = handle_get_project_context(project_dir=env["project"])
        assert result["found"]
        assert "FastAPI" in result["content"]

    def test_get_project_context_missing(self, env):
        result = handle_get_project_context(project_dir=env["project"])
        assert not result["found"]


# ---------------------------------------------------------------------------
# get_digest
# ---------------------------------------------------------------------------

class TestDigest:
    def test_get_digest_when_exists(self, env):
        digest_dir = Path(env["home"]) / ".crux" / "analytics" / "digests"
        digest_dir.mkdir(parents=True, exist_ok=True)
        (digest_dir / "2026-03-05.md").write_text(
            "# Daily Digest: 2026-03-05\n\n## Corrections: 3\n## Mode Usage: build-py (80%)"
        )
        result = handle_get_digest(home=env["home"], date="2026-03-05")
        assert result["found"]
        assert "Corrections" in result["content"]

    def test_get_digest_missing(self, env):
        result = handle_get_digest(home=env["home"], date="2026-03-05")
        assert not result["found"]

    def test_get_digest_latest(self, env):
        digest_dir = Path(env["home"]) / ".crux" / "analytics" / "digests"
        digest_dir.mkdir(parents=True, exist_ok=True)
        (digest_dir / "2026-03-04.md").write_text("# Digest 4th")
        (digest_dir / "2026-03-05.md").write_text("# Digest 5th")
        result = handle_get_digest(home=env["home"])
        assert result["found"]
        assert "5th" in result["content"]


# ---------------------------------------------------------------------------
# log_correction
# ---------------------------------------------------------------------------

class TestLogCorrection:
    def test_log_correction(self, env):
        result = handle_log_correction(
            original="Used raw SQL query",
            corrected="Use SQLAlchemy ORM instead",
            category="code-pattern",
            mode="build-py",
            project_dir=env["project"],
        )
        assert result["logged"]
        # Verify JSONL file
        corrections_file = (
            Path(env["project"]) / ".crux" / "corrections" / "corrections.jsonl"
        )
        assert corrections_file.exists()
        line = corrections_file.read_text().strip()
        data = json.loads(line)
        assert data["original"] == "Used raw SQL query"
        assert data["category"] == "code-pattern"

    def test_log_multiple_corrections(self, env):
        handle_log_correction(
            original="First mistake",
            corrected="First fix",
            category="style",
            mode="build-py",
            project_dir=env["project"],
        )
        handle_log_correction(
            original="Second mistake",
            corrected="Second fix",
            category="logic",
            mode="debug",
            project_dir=env["project"],
        )
        corrections_file = (
            Path(env["project"]) / ".crux" / "corrections" / "corrections.jsonl"
        )
        lines = corrections_file.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_log_correction_oserror(self, env):
        corrections_dir = Path(env["project"]) / ".crux" / "corrections"
        corrections_dir.mkdir(parents=True, exist_ok=True)
        corrections_file = corrections_dir / "corrections.jsonl"
        with unittest.mock.patch("builtins.open", side_effect=OSError("disk full")):
            result = handle_log_correction(
                original="fail",
                corrected="fix",
                category="code-pattern",
                mode="build-py",
                project_dir=env["project"],
            )
        assert result["logged"] is False
        assert "disk full" in result["error"]


# ---------------------------------------------------------------------------
# switch_tool
# ---------------------------------------------------------------------------

class TestSwitchTool:
    def test_switch_to_opencode(self, env):
        result = handle_switch_tool(
            target_tool="opencode",
            project_dir=env["project"],
            home=env["home"],
        )
        assert result["success"]
        assert result["from_tool"] == "claude-code"
        assert result["to_tool"] == "opencode"
        assert len(result["items_synced"]) > 0

    def test_switch_to_unsupported(self, env):
        result = handle_switch_tool(
            target_tool="vim-copilot",
            project_dir=env["project"],
            home=env["home"],
        )
        assert not result["success"]
        assert "unsupported" in result["error"].lower()


# ---------------------------------------------------------------------------
# Edge cases for coverage
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_lookup_knowledge_skips_nonexistent_dirs(self, env):
        """Ensure non-existent search dirs are skipped gracefully."""
        result = handle_lookup_knowledge(
            query="auth",
            mode="nonexistent-mode",
            project_dir=env["project"],
            home=env["home"],
        )
        # Should still find auth-flow from project knowledge
        assert result["total_found"] > 0

    def test_get_digest_no_digest_dir(self, tmp_path):
        """Digest dir doesn't exist at all — no date arg (latest path)."""
        result = handle_get_digest(home=str(tmp_path))
        assert not result["found"]

    def test_get_digest_latest_empty_dir(self, env):
        """Digest dir exists but is empty."""
        from pathlib import Path
        digest_dir = Path(env["home"]) / ".crux" / "analytics" / "digests"
        digest_dir.mkdir(parents=True, exist_ok=True)
        result = handle_get_digest(home=env["home"])
        assert not result["found"]

    def test_list_modes_no_modes_dir(self, tmp_path):
        """Modes dir doesn't exist."""
        result = handle_list_modes(home=str(tmp_path))
        assert result["modes"] == []

    def test_validate_script_missing_single_field(self, env):
        """Script with header block but missing one field."""
        script = (
            "#!/bin/bash\n"
            "################################################################################\n"
            "# Name: test\n"
            "# Risk: low\n"
            "# Created: 2026-03-05\n"
            "# Status: session\n"
            "################################################################################\n"
            "set -euo pipefail\n"
        )
        result = handle_validate_script(content=script)
        assert not result["passed"]
        assert any("Description" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# restore_context
# ---------------------------------------------------------------------------

class TestRestoreContext:
    def test_returns_context_string(self, env):
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        assert "context" in result
        assert isinstance(result["context"], str)
        assert len(result["context"]) > 0

    def test_includes_active_mode(self, env):
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        # Default mode is build-py (from session fixture)
        assert "build-py" in result["context"] or "debug" in result["context"]

    def test_includes_working_on(self, env):
        from scripts.lib.crux_session import update_session
        crux_dir = os.path.join(env["project"], ".crux")
        update_session(crux_dir, working_on="Fixing auth bug in login flow")
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        assert "Fixing auth bug" in result["context"]

    def test_includes_key_decisions(self, env):
        from scripts.lib.crux_session import update_session
        crux_dir = os.path.join(env["project"], ".crux")
        update_session(crux_dir, add_decision="Use JWT for auth")
        update_session(crux_dir, add_decision="PostgreSQL for persistence")
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        assert "JWT" in result["context"]
        assert "PostgreSQL" in result["context"]

    def test_includes_pending_tasks(self, env):
        from scripts.lib.crux_session import update_session
        crux_dir = os.path.join(env["project"], ".crux")
        update_session(crux_dir, add_pending="Write API tests")
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        assert "Write API tests" in result["context"]

    def test_includes_files_touched(self, env):
        from scripts.lib.crux_session import update_session
        crux_dir = os.path.join(env["project"], ".crux")
        update_session(crux_dir, add_file="src/auth.py")
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        assert "src/auth.py" in result["context"]

    def test_includes_handoff_when_present(self, env):
        from scripts.lib.crux_session import write_handoff
        crux_dir = os.path.join(env["project"], ".crux")
        write_handoff("Switching to plan mode for API design", project_crux_dir=crux_dir)
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        assert "API design" in result["context"]

    def test_excludes_handoff_when_absent(self, env):
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        assert "Handoff" not in result["context"]

    def test_includes_mode_prompt(self, env):
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        # The env fixture creates build-py.md and debug.md mode files
        # Session state has active_mode from save_session
        assert "specialist" in result["context"].lower() or "Mode" in result["context"]

    def test_empty_session_still_returns_context(self, tmp_path):
        """Fresh project with no session state should return minimal context."""
        from scripts.lib.crux_init import init_project, init_user
        home = tmp_path / "home"
        project = tmp_path / "project"
        home.mkdir()
        project.mkdir()
        init_user(home=str(home))
        init_project(project_dir=str(project))
        result = handle_restore_context(project_dir=str(project), home=str(home))
        assert "context" in result
        assert "Mode:" in result["context"]

    def test_includes_context_summary(self, env):
        from scripts.lib.crux_session import update_session
        crux_dir = os.path.join(env["project"], ".crux")
        update_session(crux_dir, context_summary="Building Crux hooks system for TDD enforcement")
        result = handle_restore_context(project_dir=env["project"], home=env["home"])
        assert "TDD enforcement" in result["context"]
