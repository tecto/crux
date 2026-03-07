"""Tests for crux_hook_runner.py — the shell entry point for hooks."""

import json
import os
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_session import save_session, SessionState


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    init_user(home=str(home))
    init_project(project_dir=str(project))

    crux_dir = str(project / ".crux")
    state = SessionState(active_mode="build-py", active_tool="claude-code")
    save_session(state, project_crux_dir=crux_dir)

    # Mode file
    modes_dir = home / ".crux" / "modes"
    (modes_dir / "build-py.md").write_text("Python mode.")

    monkeypatch.setenv("CRUX_PROJECT", str(project))
    monkeypatch.setenv("CRUX_HOME", str(home))
    return {"home": str(home), "project": str(project)}


class TestHookRunnerMain:
    def test_session_start_outputs_context(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner

        stdin_data = json.dumps({
            "hook_event_name": "SessionStart",
            "source": "startup",
        })
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        assert "build-py" in captured.out

    def test_post_tool_use_no_output(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner

        stdin_data = json.dumps({
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        })
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_invalid_json_exits_with_error(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner

        monkeypatch.setattr("sys.stdin", StringIO("not json"))
        with pytest.raises(SystemExit) as exc_info:
            crux_hook_runner.main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "error" in captured.err

    def test_stop_no_context_output(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner

        stdin_data = json.dumps({"hook_event_name": "Stop"})
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_unknown_event_silent(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner

        stdin_data = json.dumps({"hook_event_name": "SomeOtherEvent"})
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        assert captured.out == ""


class TestHookRunnerTddEnforcement:
    """Stop hook must output a directive when source files lack test coverage."""

    def test_stop_outputs_tdd_warning_when_noncompliant(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner
        from scripts.lib.crux_session import load_session, save_session

        # Simulate touching a source file without its test
        crux_dir = os.path.join(env["project"], ".crux")
        state = load_session(crux_dir)
        state.files_touched = ["scripts/lib/crux_hooks.py"]
        save_session(state, project_crux_dir=crux_dir)

        stdin_data = json.dumps({"hook_event_name": "Stop"})
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        assert "STOP" in captured.out or "TDD" in captured.out
        assert "crux_hooks.py" in captured.out
        assert "write" in captured.out.lower() or "test" in captured.out.lower()

    def test_stop_silent_when_tdd_compliant(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner
        from scripts.lib.crux_session import load_session, save_session

        crux_dir = os.path.join(env["project"], ".crux")
        state = load_session(crux_dir)
        state.files_touched = [
            "scripts/lib/crux_hooks.py",
            "tests/test_crux_hooks.py",
        ]
        save_session(state, project_crux_dir=crux_dir)

        stdin_data = json.dumps({"hook_event_name": "Stop"})
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_stop_silent_when_no_files_touched(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner

        stdin_data = json.dumps({"hook_event_name": "Stop"})
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_stop_lists_all_uncovered_files(self, env, monkeypatch, capsys):
        from scripts.lib import crux_hook_runner
        from scripts.lib.crux_session import load_session, save_session

        crux_dir = os.path.join(env["project"], ".crux")
        state = load_session(crux_dir)
        state.files_touched = [
            "scripts/lib/crux_hooks.py",
            "setup.sh",
        ]
        save_session(state, project_crux_dir=crux_dir)

        stdin_data = json.dumps({"hook_event_name": "Stop"})
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        assert "crux_hooks.py" in captured.out
        assert "setup.sh" in captured.out

    def test_stop_directive_is_actionable(self, env, monkeypatch, capsys):
        """The output must tell the AI exactly what to do, not just warn."""
        from scripts.lib import crux_hook_runner
        from scripts.lib.crux_session import load_session, save_session

        crux_dir = os.path.join(env["project"], ".crux")
        state = load_session(crux_dir)
        state.files_touched = ["scripts/lib/crux_session.py"]
        save_session(state, project_crux_dir=crux_dir)

        stdin_data = json.dumps({"hook_event_name": "Stop"})
        monkeypatch.setattr("sys.stdin", StringIO(stdin_data))
        crux_hook_runner.main()
        captured = capsys.readouterr()
        # Must reference the specific test file needed
        assert "test_crux_session.py" in captured.out
