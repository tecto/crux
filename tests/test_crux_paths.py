"""Tests for crux_paths.py — tool-agnostic path resolution for Crux."""

import json
import os
from pathlib import Path

import pytest

from scripts.lib.crux_paths import (
    CruxPaths,
    get_project_paths,
    get_user_paths,
    CRUX_DIR_NAME,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_crux_dir_name(self):
        assert CRUX_DIR_NAME == ".crux"


# ---------------------------------------------------------------------------
# User-level paths (~/.crux/)
# ---------------------------------------------------------------------------

class TestGetUserPaths:
    def test_returns_user_paths(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.root == str(tmp_path / ".crux")

    def test_knowledge_dir(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.knowledge == str(tmp_path / ".crux" / "knowledge")

    def test_knowledge_shared(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.knowledge_shared == str(tmp_path / ".crux" / "knowledge" / "shared")

    def test_knowledge_by_mode(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.knowledge_by_mode == str(tmp_path / ".crux" / "knowledge" / "by-mode")

    def test_modes_dir(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.modes == str(tmp_path / ".crux" / "modes")

    def test_corrections_dir(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.corrections == str(tmp_path / ".crux" / "corrections")

    def test_analytics_dir(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.analytics == str(tmp_path / ".crux" / "analytics")

    def test_analytics_digests(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.analytics_digests == str(tmp_path / ".crux" / "analytics" / "digests")

    def test_templates_dir(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.templates == str(tmp_path / ".crux" / "templates")

    def test_scripts_lib(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.scripts_lib == str(tmp_path / ".crux" / "scripts" / "lib")

    def test_config_file(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.config_file == str(tmp_path / ".crux" / "config.json")

    def test_models_dir(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.models == str(tmp_path / ".crux" / "models")

    def test_models_registry(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.models_registry == str(tmp_path / ".crux" / "models" / "registry.json")

    def test_adapters_dir(self, tmp_path):
        paths = get_user_paths(home=str(tmp_path))
        assert paths.adapters == str(tmp_path / ".crux" / "adapters")

    def test_default_home_from_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        paths = get_user_paths()
        assert paths.root == str(tmp_path / ".crux")


# ---------------------------------------------------------------------------
# Project-level paths (.crux/)
# ---------------------------------------------------------------------------

class TestGetProjectPaths:
    def test_returns_project_paths(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.root == str(tmp_path / ".crux")

    def test_knowledge_dir(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.knowledge == str(tmp_path / ".crux" / "knowledge")

    def test_knowledge_by_mode(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.knowledge_by_mode == str(tmp_path / ".crux" / "knowledge" / "by-mode")

    def test_corrections_dir(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.corrections == str(tmp_path / ".crux" / "corrections")

    def test_corrections_file(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.corrections_file == str(tmp_path / ".crux" / "corrections" / "corrections.jsonl")

    def test_sessions_dir(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.sessions == str(tmp_path / ".crux" / "sessions")

    def test_session_state_file(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.session_state == str(tmp_path / ".crux" / "sessions" / "state.json")

    def test_handoff_file(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.handoff == str(tmp_path / ".crux" / "sessions" / "handoff.md")

    def test_sessions_history(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.sessions_history == str(tmp_path / ".crux" / "sessions" / "history")

    def test_scripts_dir(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.scripts == str(tmp_path / ".crux" / "scripts")

    def test_scripts_lib(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.scripts_lib == str(tmp_path / ".crux" / "scripts" / "lib")

    def test_scripts_session(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.scripts_session == str(tmp_path / ".crux" / "scripts" / "session")

    def test_scripts_archive(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.scripts_archive == str(tmp_path / ".crux" / "scripts" / "archive")

    def test_scripts_templates(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.scripts_templates == str(tmp_path / ".crux" / "scripts" / "templates")

    def test_context_dir(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.context == str(tmp_path / ".crux" / "context")

    def test_project_md(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.project_md == str(tmp_path / ".crux" / "context" / "PROJECT.md")

    def test_project_config(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.config_file == str(tmp_path / ".crux" / "project.json")

    def test_models_dir(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.models == str(tmp_path / ".crux" / "models")

    def test_models_registry(self, tmp_path):
        paths = get_project_paths(project_dir=str(tmp_path))
        assert paths.models_registry == str(tmp_path / ".crux" / "models" / "registry.json")

    def test_default_project_dir_from_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        paths = get_project_paths()
        assert paths.root == str(tmp_path / ".crux")


# ---------------------------------------------------------------------------
# CruxPaths combined helper
# ---------------------------------------------------------------------------

class TestCruxPaths:
    def test_creates_both_project_and_user_paths(self, tmp_path):
        home = tmp_path / "home"
        project = tmp_path / "project"
        home.mkdir()
        project.mkdir()
        cp = CruxPaths(project_dir=str(project), home=str(home))
        assert cp.project.root == str(project / ".crux")
        assert cp.user.root == str(home / ".crux")

    def test_knowledge_search_dirs_with_mode(self, tmp_path):
        home = tmp_path / "home"
        project = tmp_path / "project"
        home.mkdir()
        project.mkdir()
        cp = CruxPaths(project_dir=str(project), home=str(home))
        dirs = cp.knowledge_search_dirs(mode="build-py")
        assert str(project / ".crux" / "knowledge" / "by-mode" / "build-py") in dirs
        assert str(home / ".crux" / "knowledge" / "by-mode" / "build-py") in dirs
        assert str(project / ".crux" / "knowledge") in dirs
        assert str(home / ".crux" / "knowledge") in dirs
        assert str(home / ".crux" / "knowledge" / "shared") in dirs

    def test_knowledge_search_dirs_without_mode(self, tmp_path):
        home = tmp_path / "home"
        project = tmp_path / "project"
        home.mkdir()
        project.mkdir()
        cp = CruxPaths(project_dir=str(project), home=str(home))
        dirs = cp.knowledge_search_dirs()
        assert len(dirs) == 3  # project knowledge, user knowledge, user shared
        assert str(project / ".crux" / "knowledge") in dirs
        assert str(home / ".crux" / "knowledge") in dirs
        assert str(home / ".crux" / "knowledge" / "shared") in dirs

    def test_knowledge_search_dirs_order(self, tmp_path):
        """Project-level should come before user-level (more specific first)."""
        home = tmp_path / "home"
        project = tmp_path / "project"
        home.mkdir()
        project.mkdir()
        cp = CruxPaths(project_dir=str(project), home=str(home))
        dirs = cp.knowledge_search_dirs(mode="debug")
        # Mode-specific before general, project before user
        assert dirs.index(str(project / ".crux" / "knowledge" / "by-mode" / "debug")) < \
               dirs.index(str(home / ".crux" / "knowledge" / "by-mode" / "debug"))
        assert dirs.index(str(project / ".crux" / "knowledge")) < \
               dirs.index(str(home / ".crux" / "knowledge"))


# ---------------------------------------------------------------------------
# Coverage gap tests — lines 149, 153, 157, 189
# ---------------------------------------------------------------------------

class TestProjectPathsBipProperties:
    """Test BIP-related properties on ProjectPaths (lines 149, 153, 157)."""

    def test_bip_config_path(self, tmp_path):
        pp = get_project_paths(str(tmp_path))
        assert pp.bip_config == os.path.join(str(tmp_path), ".crux", "bip", "config.json")

    def test_bip_state_path(self, tmp_path):
        pp = get_project_paths(str(tmp_path))
        assert pp.bip_state == os.path.join(str(tmp_path), ".crux", "bip", "state.json")

    def test_bip_history_path(self, tmp_path):
        pp = get_project_paths(str(tmp_path))
        assert pp.bip_history == os.path.join(str(tmp_path), ".crux", "bip", "history.jsonl")


class TestGetCruxPython:
    """Test get_crux_python (line 189 — fallback to sys.executable)."""

    def test_returns_sys_executable_when_no_venv(self, tmp_path, monkeypatch):
        import sys
        import scripts.lib.crux_paths as paths_mod
        # Point get_crux_repo to a directory without .venv
        monkeypatch.setattr(paths_mod, "get_crux_repo", lambda: str(tmp_path))
        result = paths_mod.get_crux_python()
        assert result == sys.executable
