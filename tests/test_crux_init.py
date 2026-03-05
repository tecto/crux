"""Tests for crux_init.py — directory structure initialization."""

import json
import os
from pathlib import Path

import pytest

from scripts.lib.crux_init import init_project, init_user, InitResult


class TestInitProject:
    def test_creates_crux_dir(self, tmp_path):
        result = init_project(project_dir=str(tmp_path))
        assert result.success
        assert (tmp_path / ".crux").is_dir()

    def test_creates_knowledge_dirs(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        assert (tmp_path / ".crux" / "knowledge").is_dir()
        assert (tmp_path / ".crux" / "knowledge" / "by-mode").is_dir()

    def test_creates_corrections_dir(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        assert (tmp_path / ".crux" / "corrections").is_dir()

    def test_creates_sessions_dirs(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        assert (tmp_path / ".crux" / "sessions").is_dir()
        assert (tmp_path / ".crux" / "sessions" / "history").is_dir()

    def test_creates_scripts_dirs(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        assert (tmp_path / ".crux" / "scripts").is_dir()
        assert (tmp_path / ".crux" / "scripts" / "lib").is_dir()
        assert (tmp_path / ".crux" / "scripts" / "session").is_dir()
        assert (tmp_path / ".crux" / "scripts" / "archive").is_dir()
        assert (tmp_path / ".crux" / "scripts" / "templates").is_dir()

    def test_creates_context_dir(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        assert (tmp_path / ".crux" / "context").is_dir()

    def test_creates_models_dir(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        assert (tmp_path / ".crux" / "models").is_dir()

    def test_creates_project_json(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        config = tmp_path / ".crux" / "project.json"
        assert config.exists()
        data = json.loads(config.read_text())
        assert "active_mode" in data
        assert "active_tool" in data

    def test_creates_gitignore(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        gitignore = tmp_path / ".crux" / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "sessions/" in content
        assert "corrections/" in content
        assert "scripts/session/" in content
        assert "scripts/archive/" in content

    def test_gitignore_allows_tracked_dirs(self, tmp_path):
        init_project(project_dir=str(tmp_path))
        content = (tmp_path / ".crux" / ".gitignore").read_text()
        assert "!knowledge/" in content
        assert "!scripts/lib/" in content
        assert "!scripts/templates/" in content
        assert "!project.json" in content
        assert "!context/" in content

    def test_idempotent(self, tmp_path):
        """Running init twice should not fail or overwrite config."""
        init_project(project_dir=str(tmp_path))
        config = tmp_path / ".crux" / "project.json"
        data = json.loads(config.read_text())
        data["active_mode"] = "debug"
        config.write_text(json.dumps(data))

        result = init_project(project_dir=str(tmp_path))
        assert result.success
        # Should not overwrite existing config
        data2 = json.loads(config.read_text())
        assert data2["active_mode"] == "debug"

    def test_result_contains_created_dirs(self, tmp_path):
        result = init_project(project_dir=str(tmp_path))
        assert result.root == str(tmp_path / ".crux")
        assert len(result.dirs_created) > 0

    def test_uses_cwd_by_default(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = init_project()
        assert result.root == str(tmp_path / ".crux")


class TestInitUser:
    def test_creates_user_crux_dir(self, tmp_path):
        result = init_user(home=str(tmp_path))
        assert result.success
        assert (tmp_path / ".crux").is_dir()

    def test_creates_knowledge_dirs(self, tmp_path):
        init_user(home=str(tmp_path))
        assert (tmp_path / ".crux" / "knowledge").is_dir()
        assert (tmp_path / ".crux" / "knowledge" / "shared").is_dir()
        assert (tmp_path / ".crux" / "knowledge" / "by-mode").is_dir()

    def test_creates_modes_dir(self, tmp_path):
        init_user(home=str(tmp_path))
        assert (tmp_path / ".crux" / "modes").is_dir()

    def test_creates_corrections_dir(self, tmp_path):
        init_user(home=str(tmp_path))
        assert (tmp_path / ".crux" / "corrections").is_dir()

    def test_creates_analytics_dirs(self, tmp_path):
        init_user(home=str(tmp_path))
        assert (tmp_path / ".crux" / "analytics").is_dir()
        assert (tmp_path / ".crux" / "analytics" / "digests").is_dir()

    def test_creates_templates_dir(self, tmp_path):
        init_user(home=str(tmp_path))
        assert (tmp_path / ".crux" / "templates").is_dir()

    def test_creates_scripts_lib(self, tmp_path):
        init_user(home=str(tmp_path))
        assert (tmp_path / ".crux" / "scripts" / "lib").is_dir()

    def test_creates_models_dir(self, tmp_path):
        init_user(home=str(tmp_path))
        assert (tmp_path / ".crux" / "models").is_dir()

    def test_creates_adapters_dir(self, tmp_path):
        init_user(home=str(tmp_path))
        assert (tmp_path / ".crux" / "adapters").is_dir()

    def test_creates_config_json(self, tmp_path):
        init_user(home=str(tmp_path))
        config = tmp_path / ".crux" / "config.json"
        assert config.exists()
        data = json.loads(config.read_text())
        assert "default_mode" in data
        assert "digest_cadence" in data

    def test_idempotent(self, tmp_path):
        init_user(home=str(tmp_path))
        config = tmp_path / ".crux" / "config.json"
        data = json.loads(config.read_text())
        data["default_mode"] = "debug"
        config.write_text(json.dumps(data))

        result = init_user(home=str(tmp_path))
        assert result.success
        data2 = json.loads(config.read_text())
        assert data2["default_mode"] == "debug"

    def test_creates_mode_knowledge_dirs(self, tmp_path):
        """Should create per-mode subdirectories in knowledge/by-mode/."""
        init_user(home=str(tmp_path))
        by_mode = tmp_path / ".crux" / "knowledge" / "by-mode"
        # Should have dirs for all 15 modes
        subdirs = [d.name for d in by_mode.iterdir() if d.is_dir()]
        assert "build-py" in subdirs
        assert "build-ex" in subdirs
        assert "debug" in subdirs
        assert "plan" in subdirs
        assert len(subdirs) == 15

    def test_default_home_from_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        result = init_user()
        assert result.root == str(tmp_path / ".crux")
