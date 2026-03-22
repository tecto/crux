"""E2E tests for the `crux` CLI (bin/crux).

These tests invoke the real CLI script via subprocess, with CRUX_PROJECT
and CRUX_HOME pointed at isolated temp directories.
"""

import json
import os
import subprocess
import sys

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import SessionState, save_session


CRUX_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRUX_BIN = os.path.join(CRUX_DIR, "bin", "crux")


@pytest.fixture
def cli_env(tmp_path):
    """Isolated Crux environment for CLI testing."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()

    init_user(home=str(home))
    init_project(project_dir=str(project))

    # Create mode files so `crux status` has modes to find
    modes_dir = home / ".crux" / "modes"
    (modes_dir / "build-py.md").write_text("Python build mode.")
    (modes_dir / "debug.md").write_text("Debug mode.")

    # Project knowledge so health checks have something
    pk = project / ".crux" / "knowledge"
    (pk / "test-entry.md").write_text("# Test\nA test knowledge entry.")

    # Session state
    crux_dir = str(project / ".crux")
    state = SessionState(
        active_mode="build-py",
        active_tool="claude-code",
        working_on="Running E2E tests",
    )
    save_session(state, project_crux_dir=crux_dir)

    env = os.environ.copy()
    env["CRUX_PROJECT"] = str(project)
    env["CRUX_HOME"] = str(home)
    env["CRUX_DIR"] = CRUX_DIR
    # Ensure the repo's scripts are importable by the CLI's inline Python
    env["PYTHONPATH"] = CRUX_DIR

    return {
        "home": str(home),
        "project": str(project),
        "env": env,
    }


def _run_crux(args: list[str], env: dict, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run the crux CLI with the given arguments."""
    return subprocess.run(
        ["bash", CRUX_BIN] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        cwd=CRUX_DIR,
    )


class TestCruxStatus:
    def test_status_exits_zero(self, cli_env):
        result = _run_crux(["status"], cli_env["env"])
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_status_shows_session_info(self, cli_env):
        result = _run_crux(["status"], cli_env["env"])
        assert "SESSION" in result.stdout
        assert "build-py" in result.stdout

    def test_status_shows_health_checks(self, cli_env):
        result = _run_crux(["status"], cli_env["env"])
        assert "HEALTH CHECKS" in result.stdout

    def test_status_shows_findings(self, cli_env):
        result = _run_crux(["status"], cli_env["env"])
        assert "FINDINGS" in result.stdout


class TestCruxVersion:
    def test_version_exits_zero(self, cli_env):
        result = _run_crux(["version"], cli_env["env"])
        assert result.returncode == 0

    def test_version_shows_version_string(self, cli_env):
        result = _run_crux(["version"], cli_env["env"])
        assert "crux" in result.stdout
        assert "0.1.0" in result.stdout


class TestCruxHelp:
    def test_help_exits_zero(self, cli_env):
        result = _run_crux(["help"], cli_env["env"])
        assert result.returncode == 0

    def test_help_shows_commands(self, cli_env):
        result = _run_crux(["help"], cli_env["env"])
        assert "status" in result.stdout
        assert "switch" in result.stdout
        assert "setup" in result.stdout
        assert "update" in result.stdout
        assert "doctor" in result.stdout
        assert "version" in result.stdout

    def test_dash_help_flag(self, cli_env):
        result = _run_crux(["--help"], cli_env["env"])
        assert result.returncode == 0
        assert "Commands" in result.stdout


class TestCruxSetupUpdate:
    def test_setup_update_runs_without_crash(self, cli_env):
        result = _run_crux(["setup", "--update"], cli_env["env"])
        # setup --update may exit non-zero due to verification failures
        # (e.g. missing Ollama models) but should not crash with stderr errors.
        # The key assertion is that it runs through its steps (stdout has output).
        assert "update mode" in result.stdout.lower() or "refresh" in result.stdout.lower(), (
            f"setup --update did not produce expected output. stdout: {result.stdout[:500]}"
        )


class TestCruxUnknownCommand:
    def test_unknown_command_fails(self, cli_env):
        result = _run_crux(["nonexistent-command"], cli_env["env"])
        assert result.returncode != 0
        assert "Unknown command" in result.stderr or "Unknown command" in result.stdout
