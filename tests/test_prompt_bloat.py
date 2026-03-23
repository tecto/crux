"""Tests for prompt bloat detection."""

import os

import pytest

from scripts.lib.crux_prompt_bloat import (
    BloatFinding,
    WORD_BUDGET_CRITICAL,
    WORD_BUDGET_WARNING,
    analyze_all_modes,
    analyze_mode,
    check_budget,
    check_redundancy,
    check_relevance,
    count_words,
    extract_rules,
    format_bloat_report,
)


def test_count_words_simple():
    assert count_words("hello world foo bar") == 4


def test_count_words_strips_frontmatter():
    text = "---\ntemperature: 0.4\n---\nhello world"
    assert count_words(text) == 2


def test_count_words_strips_comments():
    text = "hello <!-- hidden --> world"
    assert count_words(text) == 2


def test_extract_rules():
    text = "# Title\n- Rule 1\n- Rule 2\nNot a rule\n**Bold rule**\n1. Numbered"
    rules = extract_rules(text)
    assert len(rules) == 4


def test_check_budget_ok():
    text = " ".join(["word"] * 100)
    findings = check_budget("test", text)
    assert findings == []


def test_check_budget_warning():
    text = " ".join(["word"] * (WORD_BUDGET_WARNING + 10))
    findings = check_budget("test", text)
    assert len(findings) == 1
    assert findings[0].severity == "warning"


def test_check_budget_critical():
    text = " ".join(["word"] * (WORD_BUDGET_CRITICAL + 10))
    findings = check_budget("test", text)
    assert len(findings) == 1
    assert findings[0].severity == "critical"


def test_check_redundancy_none():
    text = "- Use snake_case for functions\n- Always write tests first"
    findings = check_redundancy("test", text)
    assert findings == []


def test_check_redundancy_found():
    text = "- Always use snake_case for function names\n- Function names must use snake_case always"
    findings = check_redundancy("test", text)
    assert len(findings) >= 1
    assert findings[0].finding_type == "redundant"


def test_check_relevance_ok(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1")
    text = "Use `src/main.py` for entry point."
    findings = check_relevance("test", text, str(tmp_path))
    assert findings == []


def test_check_relevance_missing(tmp_path):
    text = "The module `src/deleted.py` handles authentication."
    findings = check_relevance("test", text, str(tmp_path))
    assert len(findings) == 1
    assert findings[0].finding_type == "irrelevant"
    assert "deleted.py" in findings[0].description


def test_check_relevance_no_refs(tmp_path):
    text = "No file references here."
    findings = check_relevance("test", text, str(tmp_path))
    assert findings == []


def test_analyze_mode(tmp_path):
    mode_file = tmp_path / "test.md"
    mode_file.write_text(" ".join(["word"] * 250) + "\n- Rule\n- Similar rule about same thing\n")
    findings = analyze_mode("test", str(mode_file), str(tmp_path))
    # Should find over_budget at minimum
    assert any(f.finding_type == "over_budget" for f in findings)


def test_analyze_mode_missing():
    findings = analyze_mode("test", "/nonexistent.md", ".")
    assert findings == []


def test_analyze_all_modes(tmp_path):
    modes_dir = tmp_path / "modes"
    modes_dir.mkdir()
    (modes_dir / "bloated.md").write_text(" ".join(["word"] * 350))
    (modes_dir / "clean.md").write_text("Short and clean.")
    (modes_dir / "not_md.txt").write_text("ignored")

    results = analyze_all_modes(str(modes_dir), str(tmp_path))
    assert "bloated" in results
    assert "clean" not in results


def test_analyze_all_modes_empty(tmp_path):
    assert analyze_all_modes(str(tmp_path / "nope"), str(tmp_path)) == {}


def test_format_bloat_report():
    results = {
        "test-mode": [
            BloatFinding(mode="test-mode", finding_type="over_budget",
                        severity="critical", description="Too many words", line_numbers=[]),
        ]
    }
    report = format_bloat_report(results)
    assert "test-mode" in report
    assert "Too many words" in report


def test_format_bloat_report_empty():
    assert "No prompt bloat" in format_bloat_report({})
