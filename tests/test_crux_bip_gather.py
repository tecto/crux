"""Tests for crux_bip_gather.py — content gathering for build-in-public drafts."""

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.lib.crux_bip_gather import (
    gather_content,
    BIPContext,
    _gather_git,
    _gather_corrections,
    _gather_session,
)
from scripts.lib.crux_bip import record_history


@pytest.fixture
def env(tmp_path):
    """A project with .crux/ dirs and git history."""
    project = tmp_path / "project"
    project.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    # .crux dirs
    crux = project / ".crux"
    for d in ["sessions", "corrections", "knowledge", "bip", "bip/drafts",
              "analytics/interactions", "analytics/conversations"]:
        (crux / d).mkdir(parents=True)

    # Git repo
    subprocess.run(["git", "init"], cwd=str(project), capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=str(project), capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(project), capture_output=True)

    # Initial commit
    (project / "main.py").write_text("print('hello')")
    subprocess.run(["git", "add", "."], cwd=str(project), capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(project), capture_output=True)

    return {"project": str(project), "home": str(home), "crux": str(crux)}


# ---------------------------------------------------------------------------
# Git history gathering
# ---------------------------------------------------------------------------

class TestGatherGit:
    def test_gathers_recent_commits(self, env):
        # Add more commits
        p = Path(env["project"])
        (p / "auth.py").write_text("# auth")
        subprocess.run(["git", "add", "."], cwd=env["project"], capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add auth module"], cwd=env["project"], capture_output=True)

        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert any("auth" in c.lower() for c in ctx.commit_messages)

    def test_gathers_files_changed(self, env):
        p = Path(env["project"])
        (p / "cache.py").write_text("# cache")
        subprocess.run(["git", "add", "."], cwd=env["project"], capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add cache layer"], cwd=env["project"], capture_output=True)

        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert "cache.py" in ctx.files_changed

    def test_since_filters_old_commits(self, env):
        ctx = gather_content(
            project_dir=env["project"],
            home=env["home"],
            since="2099-01-01T00:00:00Z",
        )
        assert len(ctx.commit_messages) == 0

    def test_no_git_repo_returns_empty(self, tmp_path):
        project = tmp_path / "nogit"
        project.mkdir()
        (project / ".crux" / "bip").mkdir(parents=True)
        ctx = gather_content(project_dir=str(project), home=str(tmp_path / "h"))
        assert ctx.commit_messages == []
        assert ctx.files_changed == []


# ---------------------------------------------------------------------------
# Corrections gathering
# ---------------------------------------------------------------------------

class TestGatherCorrections:
    def test_gathers_corrections(self, env):
        corrections_file = os.path.join(env["crux"], "corrections", "corrections.jsonl")
        entries = [
            {"pattern": "no, use dataclass", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"pattern": "actually, snake_case", "timestamp": datetime.now(timezone.utc).isoformat()},
        ]
        with open(corrections_file, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert len(ctx.corrections) == 2

    def test_no_corrections_file(self, env):
        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert ctx.corrections == []

    def test_filters_corrections_by_since(self, env):
        corrections_file = os.path.join(env["crux"], "corrections", "corrections.jsonl")
        old = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        new = datetime.now(timezone.utc).isoformat()
        entries = [
            {"pattern": "old correction", "timestamp": old},
            {"pattern": "new correction", "timestamp": new},
        ]
        with open(corrections_file, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

        since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        ctx = gather_content(project_dir=env["project"], home=env["home"], since=since)
        assert len(ctx.corrections) == 1
        assert ctx.corrections[0]["pattern"] == "new correction"


# ---------------------------------------------------------------------------
# Knowledge gathering
# ---------------------------------------------------------------------------

class TestGatherKnowledge:
    def test_gathers_knowledge_entries(self, env):
        k_dir = os.path.join(env["crux"], "knowledge")
        Path(k_dir, "auth-patterns.md").write_text("# Auth\nUse JWT")
        Path(k_dir, "testing.md").write_text("# Testing\nUse pytest")

        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert len(ctx.knowledge_entries) == 2
        names = [k["name"] for k in ctx.knowledge_entries]
        assert "auth-patterns" in names

    def test_empty_knowledge_dir(self, env):
        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert ctx.knowledge_entries == []


# ---------------------------------------------------------------------------
# Session context gathering
# ---------------------------------------------------------------------------

class TestGatherSession:
    def test_gathers_session_state(self, env):
        state = {
            "active_mode": "build-py",
            "active_tool": "claude-code",
            "working_on": "Auth refactor",
            "key_decisions": ["Use JWT"],
        }
        state_path = os.path.join(env["crux"], "sessions", "state.json")
        with open(state_path, "w") as f:
            json.dump(state, f)

        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert ctx.session_mode == "build-py"
        assert ctx.session_tool == "claude-code"
        assert ctx.working_on == "Auth refactor"

    def test_missing_session_state(self, env):
        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert ctx.session_mode == ""
        assert ctx.session_tool == ""


# ---------------------------------------------------------------------------
# History dedup
# ---------------------------------------------------------------------------

class TestGatherHistoryDedup:
    def test_filters_already_posted_commits(self, env):
        # Create two commits
        p = Path(env["project"])
        (p / "a.py").write_text("a")
        subprocess.run(["git", "add", "."], cwd=env["project"], capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add feature A"], cwd=env["project"], capture_output=True)

        # Get the commit hash
        result = subprocess.run(
            ["git", "log", "--pretty=format:%H", "-1"],
            cwd=env["project"], capture_output=True, text=True,
        )
        commit_hash = result.stdout.strip()

        # Mark it as posted
        bip_dir = os.path.join(env["crux"], "bip")
        record_history(bip_dir, source_key=f"git:{commit_hash}", draft_preview="posted")

        (p / "b.py").write_text("b")
        subprocess.run(["git", "add", "."], cwd=env["project"], capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add feature B"], cwd=env["project"], capture_output=True)

        ctx = gather_content(project_dir=env["project"], home=env["home"])
        # Should have feature B but not feature A in unposted
        assert len(ctx.unposted_commits) >= 1
        messages = [c["message"] for c in ctx.unposted_commits]
        assert any("feature B" in m for m in messages)


# ---------------------------------------------------------------------------
# BIPContext
# ---------------------------------------------------------------------------

class TestBIPContext:
    def test_has_material_with_commits(self, env):
        p = Path(env["project"])
        (p / "x.py").write_text("x")
        subprocess.run(["git", "add", "."], cwd=env["project"], capture_output=True)
        subprocess.run(["git", "commit", "-m", "Ship feature X"], cwd=env["project"], capture_output=True)

        ctx = gather_content(project_dir=env["project"], home=env["home"])
        assert ctx.has_material is True

    def test_no_material_empty_project(self, tmp_path):
        project = tmp_path / "empty"
        project.mkdir()
        (project / ".crux" / "bip").mkdir(parents=True)
        ctx = gather_content(project_dir=str(project), home=str(tmp_path))
        assert ctx.has_material is False


# ---------------------------------------------------------------------------
# Coverage gap tests
# ---------------------------------------------------------------------------

class TestGatherGitTimeout:
    def test_subprocess_timeout(self, monkeypatch):
        """Lines 91-92: subprocess.TimeoutExpired returns empty."""
        def timeout_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="git", timeout=10)

        monkeypatch.setattr(subprocess, "run", timeout_run)
        messages, hashes, files = _gather_git("/nonexistent")
        assert messages == []
        assert hashes == []
        assert files == []

    def test_file_not_found(self, monkeypatch):
        """Lines 91-92: FileNotFoundError (git not installed) returns empty."""
        def no_git(*args, **kwargs):
            raise FileNotFoundError("git not found")

        monkeypatch.setattr(subprocess, "run", no_git)
        messages, hashes, files = _gather_git("/nonexistent")
        assert messages == []


class TestGatherCorrectionsEdgeCases:
    def test_since_without_timezone(self, tmp_path):
        """Lines 109-111: since timestamp without timezone gets UTC."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "corrections").mkdir(parents=True)
        corrections_file = crux_dir / "corrections" / "corrections.jsonl"
        now = datetime.now(timezone.utc)
        corrections_file.write_text(
            json.dumps({"pattern": "test", "timestamp": now.isoformat()}) + "\n"
        )
        # since without timezone info
        since = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        entries = _gather_corrections(str(crux_dir), since=since)
        assert len(entries) == 1

    def test_empty_lines_skipped(self, tmp_path):
        """Line 118: empty lines in corrections file are skipped."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "corrections").mkdir(parents=True)
        corrections_file = crux_dir / "corrections" / "corrections.jsonl"
        corrections_file.write_text(
            json.dumps({"pattern": "valid"}) + "\n"
            + "\n"
            + "   \n"
            + json.dumps({"pattern": "also valid"}) + "\n"
        )
        entries = _gather_corrections(str(crux_dir))
        assert len(entries) == 2

    def test_json_decode_error_skipped(self, tmp_path):
        """Lines 121-122: invalid JSON lines are skipped."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "corrections").mkdir(parents=True)
        corrections_file = crux_dir / "corrections" / "corrections.jsonl"
        corrections_file.write_text(
            json.dumps({"pattern": "valid"}) + "\n"
            + "not valid json\n"
            + json.dumps({"pattern": "also valid"}) + "\n"
        )
        entries = _gather_corrections(str(crux_dir))
        assert len(entries) == 2

    def test_entry_timestamp_without_timezone(self, tmp_path):
        """Lines 128: entry timestamp without timezone gets UTC."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "corrections").mkdir(parents=True)
        corrections_file = crux_dir / "corrections" / "corrections.jsonl"
        # Entry timestamp without timezone — use UTC time to avoid comparison issues
        naive_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        corrections_file.write_text(
            json.dumps({"pattern": "test", "timestamp": naive_ts}) + "\n"
        )
        since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        entries = _gather_corrections(str(crux_dir), since=since)
        assert len(entries) == 1

    def test_entry_timestamp_value_error(self, tmp_path):
        """Lines 131-132: invalid entry timestamp is ignored (entry still included)."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "corrections").mkdir(parents=True)
        corrections_file = crux_dir / "corrections" / "corrections.jsonl"
        corrections_file.write_text(
            json.dumps({"pattern": "test", "timestamp": "not-a-timestamp"}) + "\n"
        )
        since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        entries = _gather_corrections(str(crux_dir), since=since)
        # Entry with bad timestamp should still be included (ValueError caught, pass)
        assert len(entries) == 1

    def test_oserror_reading_file(self, tmp_path, monkeypatch):
        """Lines 135-136: OSError reading corrections file returns empty."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "corrections").mkdir(parents=True)
        corrections_file = crux_dir / "corrections" / "corrections.jsonl"
        corrections_file.write_text(json.dumps({"pattern": "test"}) + "\n")

        import builtins
        original_open = builtins.open

        def failing_open(path, *a, **kw):
            if "corrections.jsonl" in str(path):
                raise OSError("permission denied")
            return original_open(path, *a, **kw)

        monkeypatch.setattr(builtins, "open", failing_open)
        entries = _gather_corrections(str(crux_dir))
        assert entries == []

    def test_since_invalid_format(self, tmp_path):
        """Lines 110-111: invalid since format sets since_dt to None."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "corrections").mkdir(parents=True)
        corrections_file = crux_dir / "corrections" / "corrections.jsonl"
        corrections_file.write_text(
            json.dumps({"pattern": "test"}) + "\n"
        )
        entries = _gather_corrections(str(crux_dir), since="not-a-date")
        # Should not filter (since_dt is None), so entry is included
        assert len(entries) == 1


class TestGatherSessionEdgeCases:
    def test_corrupt_session_json(self, tmp_path):
        """Lines 164-165: corrupt session JSON returns empty dict."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "sessions").mkdir(parents=True)
        state_path = crux_dir / "sessions" / "state.json"
        state_path.write_text("not valid json{{{")
        result = _gather_session(str(crux_dir))
        assert result == {}

    def test_session_oserror(self, tmp_path, monkeypatch):
        """Lines 164-165: OSError reading session returns empty dict."""
        crux_dir = tmp_path / ".crux"
        (crux_dir / "sessions").mkdir(parents=True)
        state_path = crux_dir / "sessions" / "state.json"
        state_path.write_text(json.dumps({"active_mode": "code"}))

        import builtins
        original_open = builtins.open

        def failing_open(path, *a, **kw):
            if "state.json" in str(path):
                raise OSError("permission denied")
            return original_open(path, *a, **kw)

        monkeypatch.setattr(builtins, "open", failing_open)
        result = _gather_session(str(crux_dir))
        assert result == {}
