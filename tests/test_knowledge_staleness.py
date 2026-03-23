"""Tests for knowledge staleness detection."""

import os

import pytest

from scripts.lib.crux_knowledge_staleness import (
    auto_staleness_scan,
    check_entry_staleness,
    scan_knowledge_dir,
    soft_retire,
)


def test_check_staleness_file_not_found(tmp_path):
    result = check_entry_staleness(str(tmp_path / "nonexistent.md"), str(tmp_path))
    assert result.is_stale is True
    assert "not found" in result.reason


def test_check_staleness_no_refs(tmp_path):
    entry = tmp_path / "entry.md"
    entry.write_text("# Some knowledge\nNo file references here.")
    result = check_entry_staleness(str(entry), str(tmp_path))
    assert result.is_stale is False
    assert "No source file" in result.reason


def test_check_staleness_refs_exist(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")

    entry = tmp_path / "entry.md"
    entry.write_text('Use `src/main.py` for the entry point.')
    result = check_entry_staleness(str(entry), str(tmp_path))
    assert result.is_stale is False


def test_check_staleness_refs_missing(tmp_path):
    entry = tmp_path / "entry.md"
    entry.write_text('The file `src/deleted_module.py` handles auth.')
    result = check_entry_staleness(str(entry), str(tmp_path))
    assert result.is_stale is True
    assert "deleted_module.py" in result.reason


def test_scan_knowledge_dir(tmp_path):
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "good.md").write_text("No file refs.")
    (knowledge / "stale.md").write_text('References `gone.py` module.')
    (knowledge / "not_md.txt").write_text("ignored")

    results = scan_knowledge_dir(str(knowledge), str(tmp_path))
    assert len(results) == 2
    stale = [r for r in results if r.is_stale]
    assert len(stale) == 1


def test_scan_empty_dir(tmp_path):
    results = scan_knowledge_dir(str(tmp_path / "nonexistent"), str(tmp_path))
    assert results == []


def test_soft_retire(tmp_path):
    entry = tmp_path / "stale.md"
    entry.write_text("# Old knowledge")
    soft_retire(str(entry))

    content = entry.read_text()
    assert content.startswith("<!-- STALE")
    assert "Old knowledge" in content


def test_soft_retire_idempotent(tmp_path):
    entry = tmp_path / "stale.md"
    entry.write_text("<!-- STALE: already marked -->\n# Old")
    soft_retire(str(entry))

    content = entry.read_text()
    assert content.count("<!-- STALE") == 1


def test_soft_retire_nonexistent(tmp_path):
    soft_retire(str(tmp_path / "gone.md"))  # Should not raise


def test_auto_staleness_scan(tmp_path):
    crux_dir = tmp_path / ".crux" / "knowledge"
    crux_dir.mkdir(parents=True)
    (crux_dir / "good.md").write_text("No refs.")
    (crux_dir / "stale.md").write_text('Uses `missing.py` module.')

    results = auto_staleness_scan(str(tmp_path))
    assert len(results) == 2

    stale_entry = crux_dir / "stale.md"
    assert stale_entry.read_text().startswith("<!-- STALE")
