"""Tests for crux_session.py — tool-agnostic session state management."""

import json
import os
import time
from pathlib import Path

import pytest

from scripts.lib.crux_session import (
    load_session,
    save_session,
    update_session,
    write_handoff,
    read_handoff,
    archive_session,
    SessionState,
)


@pytest.fixture
def crux_dir(tmp_path):
    """Create a minimal .crux/sessions/ structure."""
    sessions = tmp_path / ".crux" / "sessions" / "history"
    sessions.mkdir(parents=True)
    return tmp_path / ".crux"


# ---------------------------------------------------------------------------
# SessionState dataclass
# ---------------------------------------------------------------------------

class TestSessionState:
    def test_default_values(self):
        s = SessionState()
        assert s.active_mode == "build-py"
        assert s.active_tool == ""
        assert s.working_on == ""
        assert s.key_decisions == []
        assert s.files_touched == []
        assert s.pending == []
        assert s.context_summary == ""

    def test_to_dict(self):
        s = SessionState(active_mode="debug", active_tool="claude-code")
        d = s.to_dict()
        assert d["active_mode"] == "debug"
        assert d["active_tool"] == "claude-code"
        assert "started_at" in d
        assert "updated_at" in d

    def test_from_dict(self):
        d = {
            "active_mode": "plan",
            "active_tool": "opencode",
            "started_at": "2026-03-05T10:00:00Z",
            "updated_at": "2026-03-05T11:00:00Z",
            "working_on": "Auth flow",
            "key_decisions": ["Use JWT"],
            "files_touched": ["auth.py"],
            "pending": ["Add tests"],
            "context_summary": "Working on auth",
        }
        s = SessionState.from_dict(d)
        assert s.active_mode == "plan"
        assert s.active_tool == "opencode"
        assert s.working_on == "Auth flow"
        assert s.key_decisions == ["Use JWT"]

    def test_from_dict_missing_fields(self):
        """Should handle missing fields with defaults."""
        s = SessionState.from_dict({"active_mode": "debug"})
        assert s.active_mode == "debug"
        assert s.active_tool == ""
        assert s.key_decisions == []

    def test_from_dict_empty(self):
        s = SessionState.from_dict({})
        assert s.active_mode == "build-py"


# ---------------------------------------------------------------------------
# save_session / load_session
# ---------------------------------------------------------------------------

class TestSaveLoadSession:
    def test_save_creates_file(self, crux_dir):
        state = SessionState(active_mode="debug", active_tool="claude-code")
        save_session(state, project_crux_dir=str(crux_dir))
        state_file = crux_dir / "sessions" / "state.json"
        assert state_file.exists()

    def test_save_writes_valid_json(self, crux_dir):
        state = SessionState(active_mode="debug")
        save_session(state, project_crux_dir=str(crux_dir))
        data = json.loads((crux_dir / "sessions" / "state.json").read_text())
        assert data["active_mode"] == "debug"

    def test_load_reads_saved_state(self, crux_dir):
        state = SessionState(
            active_mode="plan",
            active_tool="opencode",
            working_on="Designing API",
        )
        save_session(state, project_crux_dir=str(crux_dir))
        loaded = load_session(project_crux_dir=str(crux_dir))
        assert loaded.active_mode == "plan"
        assert loaded.active_tool == "opencode"
        assert loaded.working_on == "Designing API"

    def test_load_returns_default_when_no_file(self, crux_dir):
        loaded = load_session(project_crux_dir=str(crux_dir))
        assert loaded.active_mode == "build-py"
        assert loaded.active_tool == ""

    def test_load_handles_corrupt_json(self, crux_dir):
        state_file = crux_dir / "sessions" / "state.json"
        state_file.write_text("not json{{{")
        loaded = load_session(project_crux_dir=str(crux_dir))
        assert loaded.active_mode == "build-py"

    def test_save_updates_timestamp(self, crux_dir):
        state = SessionState(active_mode="debug")
        save_session(state, project_crux_dir=str(crux_dir))
        data = json.loads((crux_dir / "sessions" / "state.json").read_text())
        assert "updated_at" in data
        assert len(data["updated_at"]) > 0


# ---------------------------------------------------------------------------
# update_session
# ---------------------------------------------------------------------------

class TestUpdateSession:
    def test_update_mode(self, crux_dir):
        state = SessionState(active_mode="debug")
        save_session(state, project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            active_mode="plan",
        )
        assert updated.active_mode == "plan"
        # Verify persisted
        loaded = load_session(project_crux_dir=str(crux_dir))
        assert loaded.active_mode == "plan"

    def test_update_tool(self, crux_dir):
        state = SessionState(active_tool="claude-code")
        save_session(state, project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            active_tool="opencode",
        )
        assert updated.active_tool == "opencode"

    def test_update_working_on(self, crux_dir):
        save_session(SessionState(), project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            working_on="Implementing OAuth",
        )
        assert updated.working_on == "Implementing OAuth"

    def test_update_preserves_unmodified_fields(self, crux_dir):
        state = SessionState(
            active_mode="debug",
            active_tool="claude-code",
            working_on="Bug hunt",
        )
        save_session(state, project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            active_mode="plan",
        )
        assert updated.active_mode == "plan"
        assert updated.active_tool == "claude-code"
        assert updated.working_on == "Bug hunt"

    def test_update_add_decision(self, crux_dir):
        state = SessionState(key_decisions=["Use JWT"])
        save_session(state, project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            add_decision="Use httponly cookies",
        )
        assert "Use JWT" in updated.key_decisions
        assert "Use httponly cookies" in updated.key_decisions

    def test_update_add_file_touched(self, crux_dir):
        save_session(SessionState(), project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            add_file="src/auth.py",
        )
        assert "src/auth.py" in updated.files_touched

    def test_update_add_file_deduplicates(self, crux_dir):
        state = SessionState(files_touched=["src/auth.py"])
        save_session(state, project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            add_file="src/auth.py",
        )
        assert updated.files_touched.count("src/auth.py") == 1

    def test_update_add_pending(self, crux_dir):
        save_session(SessionState(), project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            add_pending="Write integration tests",
        )
        assert "Write integration tests" in updated.pending

    def test_update_context_summary(self, crux_dir):
        save_session(SessionState(), project_crux_dir=str(crux_dir))
        updated = update_session(
            project_crux_dir=str(crux_dir),
            context_summary="Halfway through OAuth implementation",
        )
        assert updated.context_summary == "Halfway through OAuth implementation"

    def test_update_creates_file_if_missing(self, crux_dir):
        updated = update_session(
            project_crux_dir=str(crux_dir),
            active_mode="debug",
        )
        assert updated.active_mode == "debug"
        assert (crux_dir / "sessions" / "state.json").exists()


# ---------------------------------------------------------------------------
# Handoff context
# ---------------------------------------------------------------------------

class TestHandoff:
    def test_write_handoff(self, crux_dir):
        write_handoff(
            "Switching to plan mode to design the API",
            project_crux_dir=str(crux_dir),
        )
        handoff = crux_dir / "sessions" / "handoff.md"
        assert handoff.exists()
        assert "design the API" in handoff.read_text()

    def test_read_handoff(self, crux_dir):
        write_handoff("Context for next mode", project_crux_dir=str(crux_dir))
        content = read_handoff(project_crux_dir=str(crux_dir))
        assert content == "Context for next mode"

    def test_read_handoff_missing(self, crux_dir):
        content = read_handoff(project_crux_dir=str(crux_dir))
        assert content is None

    def test_write_handoff_overwrites(self, crux_dir):
        write_handoff("First", project_crux_dir=str(crux_dir))
        write_handoff("Second", project_crux_dir=str(crux_dir))
        content = read_handoff(project_crux_dir=str(crux_dir))
        assert content == "Second"


# ---------------------------------------------------------------------------
# Archive session
# ---------------------------------------------------------------------------

class TestArchiveSession:
    def test_archive_moves_to_history(self, crux_dir):
        state = SessionState(active_mode="debug", working_on="Bug fix")
        save_session(state, project_crux_dir=str(crux_dir))
        archive_path = archive_session(project_crux_dir=str(crux_dir))
        assert archive_path is not None
        assert Path(archive_path).exists()
        # state.json should be gone
        assert not (crux_dir / "sessions" / "state.json").exists()

    def test_archive_preserves_content(self, crux_dir):
        state = SessionState(active_mode="debug", working_on="Bug fix")
        save_session(state, project_crux_dir=str(crux_dir))
        archive_path = archive_session(project_crux_dir=str(crux_dir))
        data = json.loads(Path(archive_path).read_text())
        assert data["active_mode"] == "debug"
        assert data["working_on"] == "Bug fix"

    def test_archive_returns_none_when_no_session(self, crux_dir):
        result = archive_session(project_crux_dir=str(crux_dir))
        assert result is None

    def test_archive_clears_handoff(self, crux_dir):
        save_session(SessionState(), project_crux_dir=str(crux_dir))
        write_handoff("Some context", project_crux_dir=str(crux_dir))
        archive_session(project_crux_dir=str(crux_dir))
        assert not (crux_dir / "sessions" / "handoff.md").exists()
