"""Tests for mode prompt improvement from corrections."""

import os

import pytest

from scripts.lib.crux_prompt_improvement import (
    analyze_corrections_by_mode,
    count_prompt_rules,
    format_proposals_report,
    generate_all_proposals,
    generate_proposal,
)
from scripts.lib.extract_corrections import CorrectionCluster, CorrectionEntry


def _make_cluster(mode="build-py", category="code_patterns", count=5):
    entries = [
        CorrectionEntry(
            timestamp="2026-03-22T00:00:00Z",
            original=f"wrong code {i}",
            corrected=f"correct code {i}",
            category=category,
            mode=mode,
            pattern=f"pattern {i}",
        )
        for i in range(count)
    ]
    return CorrectionCluster(category=category, mode=mode, entries=entries, count=count)


def test_analyze_by_mode():
    clusters = [
        _make_cluster(mode="build-py", count=5),
        _make_cluster(mode="build-py", category="test_patterns", count=3),
        _make_cluster(mode="review", count=2),  # Below threshold
    ]
    result = analyze_corrections_by_mode(clusters, min_corrections=3)
    assert "build-py" in result
    assert len(result["build-py"]) == 2
    assert "review" not in result


def test_count_prompt_rules(tmp_path):
    mode_file = tmp_path / "test.md"
    mode_file.write_text("---\ntemperature: 0.4\n---\n- Rule 1\n- Rule 2\n**Bold rule**\nNot a rule\n")
    assert count_prompt_rules(str(mode_file)) == 3


def test_count_prompt_rules_missing():
    assert count_prompt_rules("/nonexistent/file.md") == 0


def test_generate_proposal(tmp_path):
    modes_dir = str(tmp_path / "modes")
    os.makedirs(modes_dir)
    (tmp_path / "modes" / "build-py.md").write_text("- Rule 1\n- Rule 2\n")

    cluster = _make_cluster()
    proposal = generate_proposal("build-py", cluster, modes_dir)

    assert proposal.mode == "build-py"
    assert proposal.correction_count == 5
    assert proposal.current_rule_count == 2
    assert len(proposal.example_corrections) <= 3
    assert len(proposal.proposed_addition) > 0
    assert len(proposal.rationale) > 0


def test_generate_all_proposals(tmp_path):
    modes_dir = str(tmp_path / "modes")
    os.makedirs(modes_dir)
    (tmp_path / "modes" / "build-py.md").write_text("- Rule\n")

    clusters = [
        _make_cluster(mode="build-py", count=5),
        _make_cluster(mode="review", count=4),
    ]
    proposals = generate_all_proposals(clusters, modes_dir, min_corrections=3)
    assert len(proposals) == 2
    # Should be sorted by correction count
    assert proposals[0].correction_count >= proposals[1].correction_count


def test_generate_all_proposals_empty():
    proposals = generate_all_proposals([], "/fake/modes")
    assert proposals == []


def test_format_proposals_report():
    from scripts.lib.crux_prompt_improvement import PromptProposal
    proposals = [
        PromptProposal(
            mode="build-py",
            current_rule_count=5,
            proposed_addition="New rule here",
            rationale="5 corrections in code_patterns",
            correction_count=5,
            example_corrections=["'fix 1'", "'fix 2'"],
        )
    ]
    report = format_proposals_report(proposals)
    assert "build-py" in report
    assert "5 corrections" in report


def test_format_proposals_report_empty():
    report = format_proposals_report([])
    assert "No prompt improvement" in report
