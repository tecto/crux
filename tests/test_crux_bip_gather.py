"""Tests for crux_bip_gather.py — content gathering for build-in-public drafts."""

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from scripts.lib.crux_bip_gather import gather_content, BIPContext
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
