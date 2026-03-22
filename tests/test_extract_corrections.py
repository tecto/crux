"""Tests for extract_corrections.py — correction pattern extraction and clustering."""

import json
import os
import tempfile

import pytest

from scripts.lib.extract_corrections import (
    CorrectionCluster,
    CorrectionEntry,
    _truncate_field,
    _validate_string_field,
    _MAX_ENTRIES_PER_FILE,
    _MAX_FILES_TO_SCAN,
    _MAX_LINE_LENGTH,
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


class TestTruncateField:
    def test_truncates_long_value(self):
        long_val = "x" * 20000
        result = _truncate_field(long_val, max_length=100)
        assert len(result) == 100 + len("...[truncated]")
        assert result.endswith("...[truncated]")


class TestValidateStringField:
    def test_none_returns_empty(self):
        assert _validate_string_field(None, "test") == ""

    def test_non_string_converted(self):
        assert _validate_string_field(42, "test") == "42"

    def test_unconvertible_returns_empty(self):
        class BadObj:
            def __str__(self):
                raise RuntimeError("cannot convert")
        assert _validate_string_field(BadObj(), "test") == ""


class TestParseReflectionsFileSecurity:
    def test_max_entries_limit(self, temp_dir):
        path = os.path.join(temp_dir, "big.jsonl")
        with open(path, "w") as f:
            for _ in range(_MAX_ENTRIES_PER_FILE + 10):
                f.write(make_reflection() + "\n")
        entries = parse_reflections_file(path)
        assert len(entries) == _MAX_ENTRIES_PER_FILE

    def test_oversized_line_skipped(self, temp_dir):
        path = os.path.join(temp_dir, "big_line.jsonl")
        with open(path, "w") as f:
            # Write a line that exceeds _MAX_LINE_LENGTH
            huge = json.dumps({"type": "self-correction", "data": "x" * (_MAX_LINE_LENGTH + 1)})
            f.write(huge + "\n")
            f.write(make_reflection() + "\n")
        entries = parse_reflections_file(path)
        assert len(entries) == 1

    def test_non_dict_json_skipped(self, temp_dir):
        path = os.path.join(temp_dir, "array.jsonl")
        with open(path, "w") as f:
            f.write("[1, 2, 3]\n")
            f.write(make_reflection() + "\n")
        entries = parse_reflections_file(path)
        assert len(entries) == 1

    def test_os_error_returns_empty(self, temp_dir):
        # Create a directory with the same name to trigger an OS error on open
        dir_path = os.path.join(temp_dir, "notafile.jsonl")
        os.mkdir(dir_path)
        entries = parse_reflections_file(dir_path)
        assert entries == []


class TestScanReflectionsDirSecurity:
    def test_os_error_on_listdir(self, temp_dir):
        # Pass a file (not a directory) to trigger OSError on listdir
        file_path = os.path.join(temp_dir, "afile.txt")
        with open(file_path, "w") as f:
            f.write("hi")
        entries = scan_reflections_dir(file_path)
        assert entries == []

    def test_max_files_limit(self, temp_dir):
        for i in range(_MAX_FILES_TO_SCAN + 5):
            with open(os.path.join(temp_dir, f"file_{i:04d}.jsonl"), "w") as f:
                f.write(make_reflection() + "\n")
        entries = scan_reflections_dir(temp_dir)
        assert len(entries) == _MAX_FILES_TO_SCAN

    def test_skips_non_regular_file(self, temp_dir):
        # Create a subdirectory named something.jsonl
        subdir = os.path.join(temp_dir, "subdir.jsonl")
        os.mkdir(subdir)
        # Also add a real file
        with open(os.path.join(temp_dir, "real.jsonl"), "w") as f:
            f.write(make_reflection() + "\n")
        entries = scan_reflections_dir(temp_dir)
        assert len(entries) == 1

    def test_total_entries_limit(self, temp_dir):
        # Create files with many entries to exceed _MAX_ENTRIES_PER_FILE * 10
        entries_per_file = _MAX_ENTRIES_PER_FILE
        # We need > _MAX_ENTRIES_PER_FILE * 10 total entries across files
        num_files = 12  # 12 * 10000 > 100000
        for i in range(num_files):
            with open(os.path.join(temp_dir, f"file_{i:04d}.jsonl"), "w") as f:
                for _ in range(entries_per_file):
                    f.write(make_reflection() + "\n")
        entries = scan_reflections_dir(temp_dir)
        assert len(entries) <= _MAX_ENTRIES_PER_FILE * 10 + entries_per_file
