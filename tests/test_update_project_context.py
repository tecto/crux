"""Tests for update_project_context.py — PROJECT.md generation."""

import os
import subprocess
import tempfile

import pytest

from scripts.lib.update_project_context import (
    detect_key_files,
    detect_tech_stack,
    generate_directory_tree,
    generate_project_md,
    get_recent_git_changes,
    main,
    update_project_context,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestDetectTechStack:
    def test_detects_python(self, temp_dir):
        open(os.path.join(temp_dir, "pyproject.toml"), "w").close()
        stack = detect_tech_stack(temp_dir)
        assert "Python" in stack

    def test_detects_node(self, temp_dir):
        open(os.path.join(temp_dir, "package.json"), "w").close()
        stack = detect_tech_stack(temp_dir)
        assert "Node.js" in stack

    def test_detects_multiple(self, temp_dir):
        open(os.path.join(temp_dir, "pyproject.toml"), "w").close()
        open(os.path.join(temp_dir, "package.json"), "w").close()
        open(os.path.join(temp_dir, "Dockerfile"), "w").close()
        stack = detect_tech_stack(temp_dir)
        assert len(stack) == 3

    def test_no_duplicates(self, temp_dir):
        # Both pyproject.toml and requirements.txt indicate Python
        open(os.path.join(temp_dir, "pyproject.toml"), "w").close()
        open(os.path.join(temp_dir, "requirements.txt"), "w").close()
        stack = detect_tech_stack(temp_dir)
        assert stack.count("Python") == 1

    def test_empty_dir(self, temp_dir):
        stack = detect_tech_stack(temp_dir)
        assert stack == []

    def test_detects_elixir(self, temp_dir):
        open(os.path.join(temp_dir, "mix.exs"), "w").close()
        stack = detect_tech_stack(temp_dir)
        assert "Elixir" in stack

    def test_detects_typescript(self, temp_dir):
        open(os.path.join(temp_dir, "tsconfig.json"), "w").close()
        stack = detect_tech_stack(temp_dir)
        assert "TypeScript" in stack


class TestGenerateDirectoryTree:
    def test_basic_tree(self, temp_dir):
        os.makedirs(os.path.join(temp_dir, "src"))
        open(os.path.join(temp_dir, "src", "main.py"), "w").close()
        tree = generate_directory_tree(temp_dir)
        assert "src/" in tree
        assert "main.py" in tree

    def test_excludes_noise_dirs(self, temp_dir):
        os.makedirs(os.path.join(temp_dir, "node_modules", "pkg"))
        os.makedirs(os.path.join(temp_dir, "__pycache__"))
        os.makedirs(os.path.join(temp_dir, "src"))
        tree = generate_directory_tree(temp_dir)
        assert "node_modules" not in tree
        assert "__pycache__" not in tree
        assert "src/" in tree

    def test_respects_max_depth(self, temp_dir):
        deep = os.path.join(temp_dir, "a", "b", "c", "d", "e")
        os.makedirs(deep)
        open(os.path.join(deep, "file.txt"), "w").close()
        tree = generate_directory_tree(temp_dir, max_depth=2)
        # Should not show deeply nested file
        assert "file.txt" not in tree

    def test_empty_dir(self, temp_dir):
        tree = generate_directory_tree(temp_dir)
        assert tree == ""

    def test_excludes_hidden_dirs(self, temp_dir):
        os.makedirs(os.path.join(temp_dir, ".hidden"))
        os.makedirs(os.path.join(temp_dir, "visible"))
        tree = generate_directory_tree(temp_dir)
        assert ".hidden" not in tree
        assert "visible/" in tree


class TestGenerateDirectoryTreeEdgeCases:
    def test_permission_error(self, temp_dir):
        """Covers PermissionError branch in _walk."""
        restricted = os.path.join(temp_dir, "restricted")
        inner = os.path.join(restricted, "inner")
        os.makedirs(inner)
        open(os.path.join(inner, "secret.txt"), "w").close()
        os.chmod(restricted, 0o000)
        tree = generate_directory_tree(temp_dir)
        # Should not crash; restricted dir shows but its contents don't
        assert "secret.txt" not in tree
        os.chmod(restricted, 0o755)


class TestDetectKeyFiles:
    def test_finds_standard_files(self, temp_dir):
        open(os.path.join(temp_dir, "README.md"), "w").close()
        open(os.path.join(temp_dir, "package.json"), "w").close()
        files = detect_key_files(temp_dir)
        assert "README.md" in files
        assert "package.json" in files

    def test_empty_dir(self, temp_dir):
        files = detect_key_files(temp_dir)
        assert files == []


class TestGetRecentGitChanges:
    def test_with_git_repo(self, temp_dir):
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=temp_dir, capture_output=True)
        open(os.path.join(temp_dir, "file.txt"), "w").close()
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True)
        changes = get_recent_git_changes(temp_dir)
        assert len(changes) >= 1
        assert "Initial commit" in changes[0]

    def test_without_git_repo(self, temp_dir):
        changes = get_recent_git_changes(temp_dir)
        assert changes == []


class TestGetRecentGitChangesEdgeCases:
    def test_timeout(self, temp_dir, monkeypatch):
        """Covers subprocess.TimeoutExpired branch."""
        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("git", 5)
        monkeypatch.setattr(subprocess, "run", mock_run)
        changes = get_recent_git_changes(temp_dir)
        assert changes == []

    def test_git_not_found(self, temp_dir, monkeypatch):
        """Covers FileNotFoundError branch."""
        def mock_run(*args, **kwargs):
            raise FileNotFoundError("git not found")
        monkeypatch.setattr(subprocess, "run", mock_run)
        changes = get_recent_git_changes(temp_dir)
        assert changes == []


class TestGenerateProjectMd:
    def test_generates_all_sections(self, temp_dir):
        open(os.path.join(temp_dir, "pyproject.toml"), "w").close()
        os.makedirs(os.path.join(temp_dir, "src"))
        md = generate_project_md(temp_dir)
        assert "# Project:" in md
        assert "## Tech Stack" in md
        assert "Python" in md
        assert "## Directory Structure" in md
        assert "## Key Files" in md
        assert "## Recent Changes" in md

    def test_empty_project(self, temp_dir):
        md = generate_project_md(temp_dir)
        assert "(none detected)" in md
        assert "(empty)" in md

    def test_with_git_history(self, temp_dir):
        """Covers line 148-149: iterating recent_changes."""
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "T"], cwd=temp_dir, capture_output=True)
        open(os.path.join(temp_dir, "f.txt"), "w").close()
        subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Test commit"], cwd=temp_dir, capture_output=True)
        md = generate_project_md(temp_dir)
        assert "Test commit" in md
        assert "(no git history)" not in md


class TestUpdateProjectContext:
    def test_writes_project_md(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        open(os.path.join(temp_dir, "package.json"), "w").close()
        result = update_project_context(temp_dir)
        assert os.path.exists(result["output_path"])
        assert "Node.js" in result["content"]

    def test_creates_context_dir(self, temp_dir):
        result = update_project_context(temp_dir)
        assert os.path.isdir(os.path.join(temp_dir, ".crux", "context"))

    def test_default_dir(self, temp_dir, monkeypatch):
        monkeypatch.chdir(temp_dir)
        result = update_project_context()
        assert temp_dir in result["output_path"]


class TestCLI:
    def test_cli_output(self, temp_dir, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["update_project_context", temp_dir])
        main()
        captured = capsys.readouterr()
        assert "Written to:" in captured.out

    def test_cli_default_dir(self, temp_dir, monkeypatch, capsys):
        monkeypatch.chdir(temp_dir)
        monkeypatch.setattr("sys.argv", ["update_project_context"])
        main()
        captured = capsys.readouterr()
        assert "Written to:" in captured.out
