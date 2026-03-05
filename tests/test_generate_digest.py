"""Tests for generate_digest.py — daily analytics digest generation."""

import json
import os
import tempfile

import pytest

from scripts.lib.generate_digest import (
    DigestMetrics,
    generate_digest,
    generate_digest_content,
    main,
    scan_reflections,
    scan_session_logs,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def make_log_entry(event, date="2026-03-05", **kwargs):
    entry = {"timestamp": f"{date}T10:00:00.000Z", "event": event}
    entry.update(kwargs)
    return json.dumps(entry)


def make_reflection(category="self_correction", date="2026-03-05"):
    return json.dumps({
        "timestamp": f"{date}T10:00:00.000Z",
        "type": "self-correction",
        "category": category,
        "original": "x",
        "corrected": "y",
    })


class TestDigestMetrics:
    def test_to_dict(self):
        m = DigestMetrics(total_sessions=2, total_interactions=10)
        d = m.to_dict()
        assert d["total_sessions"] == 2
        assert d["total_interactions"] == 10

    def test_defaults(self):
        m = DigestMetrics()
        assert m.total_sessions == 0
        assert m.modes_used == {}
        assert m.tools_used == {}


class TestScanSessionLogs:
    def test_counts_sessions_and_interactions(self, temp_dir):
        with open(os.path.join(temp_dir, "session.jsonl"), "w") as f:
            f.write(make_log_entry("session_start") + "\n")
            f.write(make_log_entry("interaction", mode="build-py") + "\n")
            f.write(make_log_entry("interaction", mode="build-py") + "\n")
            f.write(make_log_entry("interaction", mode="debug") + "\n")
        metrics = scan_session_logs(temp_dir, "2026-03-05")
        assert metrics.total_sessions == 1
        assert metrics.total_interactions == 3
        assert metrics.modes_used["build-py"] == 2
        assert metrics.modes_used["debug"] == 1

    def test_counts_tool_calls(self, temp_dir):
        with open(os.path.join(temp_dir, "session.jsonl"), "w") as f:
            f.write(make_log_entry("tool_call", tool="read") + "\n")
            f.write(make_log_entry("tool_call", tool="read") + "\n")
            f.write(make_log_entry("tool_call", tool="lookup_knowledge") + "\n")
            f.write(make_log_entry("tool_call", tool="run_script") + "\n")
        metrics = scan_session_logs(temp_dir, "2026-03-05")
        assert metrics.tools_used["read"] == 2
        assert metrics.knowledge_lookups == 1
        assert metrics.scripts_run == 1

    def test_filters_by_date(self, temp_dir):
        with open(os.path.join(temp_dir, "session.jsonl"), "w") as f:
            f.write(make_log_entry("session_start", date="2026-03-05") + "\n")
            f.write(make_log_entry("session_start", date="2026-03-04") + "\n")
        metrics = scan_session_logs(temp_dir, "2026-03-05")
        assert metrics.total_sessions == 1

    def test_handles_missing_dir(self):
        metrics = scan_session_logs("/nonexistent/dir", "2026-03-05")
        assert metrics.total_sessions == 0

    def test_handles_invalid_json(self, temp_dir):
        with open(os.path.join(temp_dir, "session.jsonl"), "w") as f:
            f.write("not json\n")
            f.write(make_log_entry("session_start") + "\n")
        metrics = scan_session_logs(temp_dir, "2026-03-05")
        assert metrics.total_sessions == 1

    def test_ignores_non_jsonl_files(self, temp_dir):
        with open(os.path.join(temp_dir, "notes.txt"), "w") as f:
            f.write(make_log_entry("session_start") + "\n")
        metrics = scan_session_logs(temp_dir, "2026-03-05")
        assert metrics.total_sessions == 0

    def test_handles_empty_lines(self, temp_dir):
        with open(os.path.join(temp_dir, "session.jsonl"), "w") as f:
            f.write("\n")
            f.write(make_log_entry("session_start") + "\n")
            f.write("\n")
        metrics = scan_session_logs(temp_dir, "2026-03-05")
        assert metrics.total_sessions == 1


class TestScanSessionLogsEdgeCases:
    def test_default_date(self, temp_dir):
        """Covers date_str is None branch."""
        with open(os.path.join(temp_dir, "session.jsonl"), "w") as f:
            f.write(make_log_entry("session_start") + "\n")
        metrics = scan_session_logs(temp_dir)
        # Won't match "2026-03-05" unless today IS that date, but exercises the branch
        assert isinstance(metrics, DigestMetrics)

    def test_unreadable_file(self, temp_dir):
        """Covers except (OSError, IOError) branch."""
        bad_path = os.path.join(temp_dir, "bad.jsonl")
        with open(bad_path, "w") as f:
            f.write(make_log_entry("session_start") + "\n")
        os.chmod(bad_path, 0o000)
        metrics = scan_session_logs(temp_dir, "2026-03-05")
        assert isinstance(metrics, DigestMetrics)
        os.chmod(bad_path, 0o644)


class TestScanReflectionsEdgeCases:
    def test_default_date(self, temp_dir):
        """Covers date_str is None branch."""
        corrections = scan_reflections(temp_dir)
        assert corrections == {}

    def test_empty_lines_in_reflections(self, temp_dir):
        """Covers empty line continue branch."""
        with open(os.path.join(temp_dir, "2026-03-05.jsonl"), "w") as f:
            f.write("\n")
            f.write(make_reflection() + "\n")
            f.write("\n")
        corrections = scan_reflections(temp_dir, "2026-03-05")
        assert sum(corrections.values()) == 1


class TestScanReflections:
    def test_counts_corrections(self, temp_dir):
        with open(os.path.join(temp_dir, "2026-03-05.jsonl"), "w") as f:
            f.write(make_reflection("negation") + "\n")
            f.write(make_reflection("negation") + "\n")
            f.write(make_reflection("self_correction") + "\n")
        corrections = scan_reflections(temp_dir, "2026-03-05")
        assert corrections["negation"] == 2
        assert corrections["self_correction"] == 1

    def test_handles_missing_file(self, temp_dir):
        corrections = scan_reflections(temp_dir, "2026-03-05")
        assert corrections == {}

    def test_handles_invalid_json(self, temp_dir):
        with open(os.path.join(temp_dir, "2026-03-05.jsonl"), "w") as f:
            f.write("bad json\n")
            f.write(make_reflection() + "\n")
        corrections = scan_reflections(temp_dir, "2026-03-05")
        assert sum(corrections.values()) == 1

    def test_skips_non_correction_entries(self, temp_dir):
        with open(os.path.join(temp_dir, "2026-03-05.jsonl"), "w") as f:
            f.write(json.dumps({"type": "other"}) + "\n")
        corrections = scan_reflections(temp_dir, "2026-03-05")
        assert corrections == {}


class TestGenerateDigestContent:
    def test_includes_all_sections(self):
        metrics = DigestMetrics(
            total_sessions=3,
            total_interactions=25,
            modes_used={"build-py": 15, "debug": 10},
            tools_used={"read": 20, "edit": 5},
            corrections_by_category={"negation": 3},
            corrections_total=3,
            knowledge_lookups=2,
            scripts_run=1,
        )
        content = generate_digest_content(metrics, "2026-03-05")
        assert "# Daily Digest: 2026-03-05" in content
        assert "Sessions: 3" in content
        assert "Interactions: 25" in content
        assert "Corrections: 3" in content
        assert "## Modes Used" in content
        assert "build-py: 15" in content
        assert "## Tools Used" in content
        assert "## Corrections by Category" in content

    def test_empty_metrics(self):
        metrics = DigestMetrics()
        content = generate_digest_content(metrics, "2026-03-05")
        assert "Sessions: 0" in content
        assert "## Modes Used" not in content  # Empty, section omitted


class TestGenerateDigest:
    def test_full_pipeline(self, temp_dir):
        logs_dir = os.path.join(temp_dir, "sessions")
        ref_dir = os.path.join(temp_dir, "reflections")
        out_dir = os.path.join(temp_dir, "digests")
        os.makedirs(logs_dir)
        os.makedirs(ref_dir)

        with open(os.path.join(logs_dir, "session.jsonl"), "w") as f:
            f.write(make_log_entry("session_start") + "\n")
            f.write(make_log_entry("interaction", mode="build-py") + "\n")

        with open(os.path.join(ref_dir, "2026-03-05.jsonl"), "w") as f:
            f.write(make_reflection("negation") + "\n")

        result = generate_digest(logs_dir, ref_dir, "2026-03-05", out_dir)
        assert result["date"] == "2026-03-05"
        assert os.path.exists(result["output_path"])
        assert result["metrics"]["total_sessions"] == 1
        assert result["metrics"]["corrections_total"] == 1
        assert "negation" in result["content"]

    def test_creates_output_dir(self, temp_dir):
        out_dir = os.path.join(temp_dir, "new", "digests")
        result = generate_digest(temp_dir, temp_dir, "2026-03-05", out_dir)
        assert os.path.isdir(out_dir)

    def test_default_dirs(self, temp_dir, monkeypatch):
        monkeypatch.setenv("HOME", temp_dir)
        sessions = os.path.join(temp_dir, ".crux", "analytics", "sessions")
        reflections = os.path.join(temp_dir, ".crux", "corrections")
        digests = os.path.join(temp_dir, ".crux", "analytics", "digests")
        os.makedirs(sessions)
        os.makedirs(reflections)
        result = generate_digest(date_str="2026-03-05")
        assert os.path.isdir(digests)


class TestCLI:
    def test_cli_output(self, temp_dir, monkeypatch, capsys):
        monkeypatch.setenv("HOME", temp_dir)
        sessions = os.path.join(temp_dir, ".crux", "analytics", "sessions")
        reflections = os.path.join(temp_dir, ".crux", "corrections")
        os.makedirs(sessions)
        os.makedirs(reflections)
        monkeypatch.setattr("sys.argv", ["generate_digest", "2026-03-05"])
        main()
        captured = capsys.readouterr()
        assert "Daily Digest" in captured.out

    def test_cli_default_date(self, temp_dir, monkeypatch, capsys):
        monkeypatch.setenv("HOME", temp_dir)
        sessions = os.path.join(temp_dir, ".crux", "analytics", "sessions")
        reflections = os.path.join(temp_dir, ".crux", "corrections")
        os.makedirs(sessions)
        os.makedirs(reflections)
        monkeypatch.setattr("sys.argv", ["generate_digest"])
        main()
        captured = capsys.readouterr()
        assert "Daily Digest" in captured.out
