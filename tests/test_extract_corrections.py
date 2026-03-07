"""Tests for extract_corrections.py — correction pattern extraction and clustering."""

import json
import os
import tempfile

import pytest

from scripts.lib.extract_corrections import (
    CorrectionCluster,
    CorrectionEntry,
    cluster_corrections,
    extract_corrections,
    generate_knowledge_candidate,
    main,
    parse_reflections_file,
    scan_reflections_dir,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def make_reflection(category="self_correction", mode="build-py", original="wrong", corrected="right"):
    return json.dumps({
        "timestamp": "2026-03-05T10:00:00.000Z",
        "type": "self-correction",
        "category": category,
        "original": original,
        "corrected": corrected,
        "pattern": "/test/i",
        "mode": mode,
    })


class TestCorrectionEntry:
    def test_to_dict(self):
        entry = CorrectionEntry(
            timestamp="2026-03-05", category="negation",
            original="x", corrected="y", pattern="/no/i", mode="debug",
        )
        d = entry.to_dict()
        assert d["category"] == "negation"
        assert d["mode"] == "debug"


class TestCorrectionCluster:
    def test_key(self):
        cluster = CorrectionCluster(category="negation", mode="debug")
        assert cluster.key == "negation:debug"

    def test_to_dict_limits_entries(self):
        entries = [
            CorrectionEntry("ts", "cat", f"orig{i}", f"corr{i}", "p", "m")
            for i in range(10)
        ]
        cluster = CorrectionCluster(category="cat", mode="m", entries=entries, count=10)
        d = cluster.to_dict()
        assert len(d["entries"]) == 5  # Capped at 5


class TestParseReflectionsFile:
    def test_parses_valid_jsonl(self, temp_dir):
        path = os.path.join(temp_dir, "2026-03-05.jsonl")
        with open(path, "w") as f:
            f.write(make_reflection() + "\n")
            f.write(make_reflection(category="negation") + "\n")
        entries = parse_reflections_file(path)
        assert len(entries) == 2
        assert entries[0].category == "self_correction"
        assert entries[1].category == "negation"

    def test_skips_non_correction_entries(self, temp_dir):
        path = os.path.join(temp_dir, "test.jsonl")
        with open(path, "w") as f:
            f.write(json.dumps({"type": "other", "data": "irrelevant"}) + "\n")
        entries = parse_reflections_file(path)
        assert len(entries) == 0

    def test_skips_invalid_json(self, temp_dir):
        path = os.path.join(temp_dir, "test.jsonl")
        with open(path, "w") as f:
            f.write("not json\n")
            f.write(make_reflection() + "\n")
        entries = parse_reflections_file(path)
        assert len(entries) == 1

    def test_handles_missing_file(self):
        entries = parse_reflections_file("/nonexistent/path.jsonl")
        assert entries == []

    def test_skips_empty_lines(self, temp_dir):
        path = os.path.join(temp_dir, "test.jsonl")
        with open(path, "w") as f:
            f.write("\n")
            f.write(make_reflection() + "\n")
            f.write("\n")
        entries = parse_reflections_file(path)
        assert len(entries) == 1


class TestScanReflectionsDir:
    def test_scans_multiple_files(self, temp_dir):
        for date in ["2026-03-04", "2026-03-05"]:
            with open(os.path.join(temp_dir, f"{date}.jsonl"), "w") as f:
                f.write(make_reflection() + "\n")
        entries = scan_reflections_dir(temp_dir)
        assert len(entries) == 2

    def test_ignores_non_jsonl(self, temp_dir):
        with open(os.path.join(temp_dir, "notes.txt"), "w") as f:
            f.write("not a jsonl file")
        entries = scan_reflections_dir(temp_dir)
        assert len(entries) == 0

    def test_handles_missing_dir(self):
        entries = scan_reflections_dir("/nonexistent/dir")
        assert entries == []


class TestClusterCorrections:
    def test_clusters_by_category_and_mode(self):
        entries = [
            CorrectionEntry("ts1", "negation", "a", "b", "p", "debug"),
            CorrectionEntry("ts2", "negation", "c", "d", "p", "debug"),
            CorrectionEntry("ts3", "self_correction", "e", "f", "p", "build-py"),
        ]
        clusters = cluster_corrections(entries)
        assert len(clusters) == 2
        # Sorted by count descending
        assert clusters[0].count == 2
        assert clusters[0].category == "negation"

    def test_empty_input(self):
        clusters = cluster_corrections([])
        assert clusters == []


class TestGenerateKnowledgeCandidate:
    def test_generates_markdown(self):
        entries = [
            CorrectionEntry("ts", "negation", "wrong thing", "right thing", "p", "debug"),
            CorrectionEntry("ts", "negation", "bad", "good", "p", "debug"),
        ]
        cluster = CorrectionCluster(category="negation", mode="debug", entries=entries, count=2)
        md = generate_knowledge_candidate(cluster)
        assert "# Correction Pattern: negation in debug" in md
        assert "**Occurrences**: 2" in md
        assert "wrong thing" in md
        assert "Tags: negation, debug, correction" in md


class TestExtractCorrections:
    def test_full_pipeline(self, temp_dir):
        with open(os.path.join(temp_dir, "2026-03-05.jsonl"), "w") as f:
            for _ in range(3):
                f.write(make_reflection(category="negation", mode="debug") + "\n")
            f.write(make_reflection(category="self_correction", mode="build-py") + "\n")

        result = extract_corrections(temp_dir, min_cluster_size=2)
        assert result["total_entries"] == 4
        assert result["total_clusters"] == 2
        assert result["significant_clusters"] == 1  # Only negation:debug has >= 2
        assert len(result["candidates"]) == 1
        assert "knowledge_entry" in result["candidates"][0]

    def test_min_cluster_size_filter(self, temp_dir):
        with open(os.path.join(temp_dir, "test.jsonl"), "w") as f:
            f.write(make_reflection() + "\n")
        result = extract_corrections(temp_dir, min_cluster_size=5)
        assert result["significant_clusters"] == 0

    def test_empty_dir(self, temp_dir):
        result = extract_corrections(temp_dir)
        assert result["total_entries"] == 0
        assert result["candidates"] == []

    def test_default_dir(self, temp_dir, monkeypatch):
        monkeypatch.setenv("HOME", temp_dir)
        ref_dir = os.path.join(temp_dir, ".crux", "corrections")
        os.makedirs(ref_dir)
        with open(os.path.join(ref_dir, "2026-03-05.jsonl"), "w") as f:
            for _ in range(3):
                f.write(make_reflection() + "\n")
        result = extract_corrections(min_cluster_size=2)
        assert result["total_entries"] == 3


class TestCLI:
    def test_cli_with_results(self, temp_dir, monkeypatch, capsys):
        with open(os.path.join(temp_dir, "test.jsonl"), "w") as f:
            for _ in range(3):
                f.write(make_reflection() + "\n")
        monkeypatch.setattr("sys.argv", ["extract_corrections", temp_dir, "2"])
        main()
        captured = capsys.readouterr()
        assert "Found 3 corrections" in captured.out

    def test_cli_no_results(self, temp_dir, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["extract_corrections", temp_dir])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "No significant" in captured.out
