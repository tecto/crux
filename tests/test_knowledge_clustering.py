"""Tests for knowledge clustering + auto-elevation."""

import os

import pytest

from scripts.lib.crux_knowledge_clustering import (
    auto_elevate,
    check_cross_project_promotion,
    elevate_cluster_to_knowledge,
    find_elevatable_clusters,
    promote_to_user_scope,
)
from scripts.lib.extract_corrections import CorrectionCluster, CorrectionEntry


def _make_cluster(category="code_patterns", mode="build-py", count=3):
    entries = [
        CorrectionEntry(
            timestamp="2026-03-22T00:00:00Z",
            original=f"wrong {i}",
            corrected=f"right {i}",
            category=category,
            mode=mode,
            pattern=f"pattern {i}",
        )
        for i in range(count)
    ]
    return CorrectionCluster(category=category, mode=mode, entries=entries, count=count)


def test_elevate_cluster_to_knowledge(tmp_path):
    cluster = _make_cluster()
    knowledge_dir = str(tmp_path / "knowledge")
    path = elevate_cluster_to_knowledge(cluster, knowledge_dir)

    assert os.path.exists(path)
    with open(path) as f:
        content = f.read()
    assert "code_patterns" in content
    assert "build-py" in content


def test_elevate_creates_dir(tmp_path):
    cluster = _make_cluster()
    knowledge_dir = str(tmp_path / "new" / "nested" / "knowledge")
    path = elevate_cluster_to_knowledge(cluster, knowledge_dir)
    assert os.path.exists(path)


def test_auto_elevate_empty(tmp_path):
    # No reflections dir → no clusters → no elevations
    result = auto_elevate(str(tmp_path), reflections_dir=str(tmp_path / "empty"))
    assert result == []


def test_check_cross_project_no_projects(tmp_path):
    assert check_cross_project_promotion(str(tmp_path), "some-pattern") is False


def test_check_cross_project_found(tmp_path):
    # Create two projects with the same pattern
    for proj in ["proj1", "proj2"]:
        knowledge_dir = tmp_path / proj / ".crux" / "knowledge"
        knowledge_dir.mkdir(parents=True)
        (knowledge_dir / "my-pattern.md").write_text("pattern content")

    assert check_cross_project_promotion(str(tmp_path), "my-pattern") is True


def test_check_cross_project_not_enough(tmp_path):
    knowledge_dir = tmp_path / "proj1" / ".crux" / "knowledge"
    knowledge_dir.mkdir(parents=True)
    (knowledge_dir / "my-pattern.md").write_text("content")

    assert check_cross_project_promotion(str(tmp_path), "my-pattern", min_projects=2) is False


def test_promote_to_user_scope(tmp_path):
    path = promote_to_user_scope(str(tmp_path), "test-pattern", "# Pattern\nContent")
    assert os.path.exists(path)
    with open(path) as f:
        assert "Pattern" in f.read()
