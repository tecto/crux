"""Mode prompt improvement from correction patterns.

Analyzes corrections per mode, identifies recurring issues that could be
prevented by prompt changes, and generates improvement proposals.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field

from scripts.lib.extract_corrections import CorrectionCluster, CorrectionEntry


@dataclass
class PromptProposal:
    mode: str
    current_rule_count: int
    proposed_addition: str
    rationale: str
    correction_count: int
    example_corrections: list[str]


def analyze_corrections_by_mode(
    clusters: list[CorrectionCluster],
    min_corrections: int = 3,
) -> dict[str, list[CorrectionCluster]]:
    """Group clusters by mode and filter by minimum correction count."""
    by_mode: dict[str, list[CorrectionCluster]] = defaultdict(list)
    for cluster in clusters:
        if cluster.count >= min_corrections:
            by_mode[cluster.mode].append(cluster)
    return dict(by_mode)


def count_prompt_rules(mode_file: str) -> int:
    """Count the number of rules/guidelines in a mode prompt file."""
    try:
        with open(mode_file) as f:
            content = f.read()
    except (FileNotFoundError, OSError):
        return 0

    # Count lines that look like rules (numbered items, bullet points, bold headers)
    rule_patterns = [
        line for line in content.split("\n")
        if line.strip().startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "**"))
    ]
    return len(rule_patterns)


def generate_proposal(
    mode: str,
    cluster: CorrectionCluster,
    modes_dir: str,
) -> PromptProposal:
    """Generate a prompt improvement proposal from a correction cluster."""
    mode_file = os.path.join(modes_dir, f"{mode}.md")
    rule_count = count_prompt_rules(mode_file)

    examples = [
        f"'{e.corrected[:100]}'" for e in cluster.entries[:3]
    ]

    # Generate the proposed addition based on the correction pattern
    proposed = (
        f"When working in {mode} mode, {cluster.category}: "
        f"follow the pattern shown in recent corrections "
        f"({cluster.count} occurrences). "
        f"Example: {examples[0] if examples else 'see correction log'}."
    )

    rationale = (
        f"This mode has {cluster.count} corrections in the '{cluster.category}' category. "
        f"Adding this rule to the prompt would prevent recurrence."
    )

    return PromptProposal(
        mode=mode,
        current_rule_count=rule_count,
        proposed_addition=proposed,
        rationale=rationale,
        correction_count=cluster.count,
        example_corrections=examples,
    )


def generate_all_proposals(
    clusters: list[CorrectionCluster],
    modes_dir: str,
    min_corrections: int = 3,
) -> list[PromptProposal]:
    """Generate improvement proposals for all modes with enough corrections."""
    by_mode = analyze_corrections_by_mode(clusters, min_corrections)
    proposals = []

    for mode, mode_clusters in by_mode.items():
        for cluster in mode_clusters:
            proposal = generate_proposal(mode, cluster, modes_dir)
            proposals.append(proposal)

    # Sort by correction count (highest first)
    return sorted(proposals, key=lambda p: p.correction_count, reverse=True)


def format_proposals_report(proposals: list[PromptProposal]) -> str:
    """Format proposals into a human-readable report."""
    if not proposals:
        return "No prompt improvement proposals generated. Not enough correction patterns."

    lines = ["# Prompt Improvement Proposals", ""]
    for i, p in enumerate(proposals, 1):
        lines.extend([
            f"## {i}. Mode: {p.mode} ({p.correction_count} corrections)",
            "",
            f"**Current rules:** {p.current_rule_count}",
            f"**Rationale:** {p.rationale}",
            "",
            "**Proposed addition:**",
            f"> {p.proposed_addition}",
            "",
            "**Example corrections:**",
            *[f"- {ex}" for ex in p.example_corrections],
            "",
        ])

    return "\n".join(lines)
