"""Tests for promote_knowledge.py — knowledge entry promotion."""

import os
import tempfile

import pytest

from scripts.lib.promote_knowledge import (
    PromotionResult,
    determine_promotion_target,
    find_knowledge_entry,
    list_promotable_entries,
    main,
    promote_entry,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def env(temp_dir):
    """Create separate project and home directories."""
    home = os.path.join(temp_dir, "home")
    project = os.path.join(temp_dir, "project")
    os.makedirs(home)
    os.makedirs(project)
    return {"home": home, "project": project}


def setup_knowledge(project_dir, home_dir):
    """Create project and user knowledge directories."""
    project_k = os.path.join(project_dir, ".crux", "knowledge")
    user_k = os.path.join(home_dir, ".crux", "knowledge")
    os.makedirs(project_k, exist_ok=True)
    os.makedirs(user_k, exist_ok=True)
    return project_k, user_k


class TestPromotionResult:
    def test_to_dict(self):
        r = PromotionResult(promoted=True, source="/a", destination="/b", entry_name="test")
        d = r.to_dict()
        assert d["promoted"] is True
        assert d["entry_name"] == "test"
        assert d["error"] is None

    def test_to_dict_with_error(self):
        r = PromotionResult(promoted=False, source="", destination="", entry_name="x", error="not found")
        d = r.to_dict()
        assert d["error"] == "not found"


class TestFindKnowledgeEntry:
    def test_finds_in_directory(self, env):
        pk, _ = setup_knowledge(env["project"], env["home"])
        with open(os.path.join(pk, "redis-setup.md"), "w") as f:
            f.write("# Redis Setup\n")
        result = find_knowledge_entry("redis-setup", [pk])
        assert result is not None
        assert result.endswith("redis-setup.md")

    def test_finds_in_subdirectory(self, env):
        pk, _ = setup_knowledge(env["project"], env["home"])
        subdir = os.path.join(pk, "build-py")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "pytest-tips.md"), "w") as f:
            f.write("# Pytest\n")
        result = find_knowledge_entry("pytest-tips", [pk])
        assert result is not None

    def test_returns_none_when_not_found(self, env):
        pk, _ = setup_knowledge(env["project"], env["home"])
        result = find_knowledge_entry("nonexistent", [pk])
        assert result is None

    def test_handles_missing_dir(self):
        result = find_knowledge_entry("test", ["/nonexistent/dir"])
        assert result is None


class TestDeterminePromotionTarget:
    def test_project_to_user(self):
        target = determine_promotion_target(
            "/project/.crux/knowledge/redis.md",
            "/project/.crux/knowledge",
            "/home/user/.crux/knowledge",
        )
        assert target == "/home/user/.crux/knowledge/redis.md"

    def test_preserves_subdirectory(self):
        target = determine_promotion_target(
            "/project/.crux/knowledge/build-py/tips.md",
            "/project/.crux/knowledge",
            "/home/user/.crux/knowledge",
        )
        assert target.endswith("build-py/tips.md")

    def test_returns_none_for_unknown_source(self):
        target = determine_promotion_target(
            "/other/path/entry.md",
            "/project/.crux/knowledge",
            "/home/user/.crux/knowledge",
        )
        assert target is None


class TestPromoteEntry:
    def test_promotes_successfully(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        pk, uk = setup_knowledge(env["project"], env["home"])
        with open(os.path.join(pk, "docker-tips.md"), "w") as f:
            f.write("# Docker Tips\n")

        result = promote_entry("docker-tips", env["project"])
        assert result.promoted is True
        assert os.path.exists(result.destination)

    def test_entry_not_found(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        setup_knowledge(env["project"], env["home"])
        result = promote_entry("nonexistent", env["project"])
        assert result.promoted is False
        assert "not found" in result.error

    def test_already_exists_at_target(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        pk, uk = setup_knowledge(env["project"], env["home"])
        with open(os.path.join(pk, "entry.md"), "w") as f:
            f.write("# Project Entry\n")
        with open(os.path.join(uk, "entry.md"), "w") as f:
            f.write("# User Entry\n")

        result = promote_entry("entry", env["project"])
        assert result.promoted is False
        assert "already exists" in result.error

    def test_default_project_dir(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        monkeypatch.chdir(env["project"])
        pk, _ = setup_knowledge(env["project"], env["home"])
        with open(os.path.join(pk, "test.md"), "w") as f:
            f.write("# Test\n")
        result = promote_entry("test")
        assert result.promoted is True

    def test_promotes_from_subdirectory(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        pk, _ = setup_knowledge(env["project"], env["home"])
        subdir = os.path.join(pk, "build-py")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "venv.md"), "w") as f:
            f.write("# Venv\n")
        result = promote_entry("venv", env["project"])
        assert result.promoted is True
        assert "build-py" in result.destination


class TestListPromotableEntries:
    def test_lists_entries(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        pk, _ = setup_knowledge(env["project"], env["home"])
        with open(os.path.join(pk, "entry1.md"), "w") as f:
            f.write("# Entry 1\n")
        with open(os.path.join(pk, "entry2.md"), "w") as f:
            f.write("# Entry 2\n")

        entries = list_promotable_entries(env["project"])
        assert len(entries) == 2
        names = [e["name"] for e in entries]
        assert "entry1" in names
        assert "entry2" in names

    def test_marks_already_promoted(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        pk, uk = setup_knowledge(env["project"], env["home"])
        with open(os.path.join(pk, "promoted.md"), "w") as f:
            f.write("# Promoted\n")
        with open(os.path.join(uk, "promoted.md"), "w") as f:
            f.write("# Already there\n")

        entries = list_promotable_entries(env["project"])
        promoted = [e for e in entries if e["name"] == "promoted"]
        assert len(promoted) == 1
        assert promoted[0]["already_promoted"] is True

    def test_empty_project(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        entries = list_promotable_entries(env["project"])
        assert entries == []

    def test_default_dir(self, env, monkeypatch):
        monkeypatch.setenv("HOME", env["home"])
        monkeypatch.chdir(env["project"])
        entries = list_promotable_entries()
        assert entries == []

    def test_missing_knowledge_dir(self, env, monkeypatch):
        """Covers FileNotFoundError in os.walk."""
        monkeypatch.setenv("HOME", env["home"])
        # No .crux/knowledge dir at all
        entries = list_promotable_entries(env["project"])
        assert entries == []


class TestCLI:
    def test_cli_success(self, env, monkeypatch, capsys):
        monkeypatch.setenv("HOME", env["home"])
        pk, _ = setup_knowledge(env["project"], env["home"])
        with open(os.path.join(pk, "cli-test.md"), "w") as f:
            f.write("# CLI Test\n")
        monkeypatch.setattr("sys.argv", ["promote_knowledge", "cli-test", env["project"]])
        main()
        captured = capsys.readouterr()
        assert "Promoted" in captured.out

    def test_cli_failure(self, env, monkeypatch, capsys):
        monkeypatch.setenv("HOME", env["home"])
        setup_knowledge(env["project"], env["home"])
        monkeypatch.setattr("sys.argv", ["promote_knowledge", "nonexistent", env["project"]])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def test_cli_no_args(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["promote_knowledge"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Usage" in captured.out
