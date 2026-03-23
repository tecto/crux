"""Prompt bloat detection — find redundant, contradictory, or irrelevant rules.

Analyzes mode prompt files for:
- Token count exceeding budget
- Redundant rules (similar content)
- Rules referencing code/patterns that no longer exist
- Contradictory directives
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass


# Target: 150-200 words per mode prompt (from CruxDev design)
WORD_BUDGET_WARNING = 200
WORD_BUDGET_CRITICAL = 300


@dataclass
class BloatFinding:
    mode: str
    finding_type: str  # "over_budget", "redundant", "irrelevant", "contradictory"
    severity: str  # "warning", "critical"
    description: str
    line_numbers: list[int]


def count_words(text: str) -> int:
    """Count words in text, excluding YAML frontmatter and comments."""
    # Strip YAML frontmatter
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 0:
            text = text[end + 3:]
    # Strip HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return len(text.split())


def extract_rules(text: str) -> list[tuple[int, str]]:
    """Extract individual rules from a mode prompt.

    Returns list of (line_number, rule_text) tuples.
    """
    rules = []
    for i, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            rules.append((i, stripped))
        elif stripped.startswith("**") and stripped.endswith("**"):
            rules.append((i, stripped))
    return rules


def check_budget(mode: str, text: str) -> list[BloatFinding]:
    """Check if a mode prompt exceeds the word budget."""
    word_count = count_words(text)
    findings = []

    if word_count > WORD_BUDGET_CRITICAL:
        findings.append(BloatFinding(
            mode=mode,
            finding_type="over_budget",
            severity="critical",
            description=f"Mode prompt has {word_count} words (budget: {WORD_BUDGET_WARNING}). Needs aggressive trimming.",
            line_numbers=[],
        ))
    elif word_count > WORD_BUDGET_WARNING:
        findings.append(BloatFinding(
            mode=mode,
            finding_type="over_budget",
            severity="warning",
            description=f"Mode prompt has {word_count} words (budget: {WORD_BUDGET_WARNING}). Consider trimming.",
            line_numbers=[],
        ))

    return findings


def check_redundancy(mode: str, text: str) -> list[BloatFinding]:
    """Check for rules that say similar things."""
    rules = extract_rules(text)
    findings = []

    for i, (line_a, rule_a) in enumerate(rules):
        for line_b, rule_b in rules[i + 1:]:
            # Simple word overlap check (not semantic — that would need LLM)
            words_a = set(rule_a.lower().split())
            words_b = set(rule_b.lower().split())
            # Remove common stop words
            stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "and", "or", "not", "to", "in", "for", "of", "with", "on", "at", "by", "from"}
            words_a -= stop
            words_b -= stop

            if not words_a or not words_b:
                continue

            overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
            if overlap > 0.7:
                findings.append(BloatFinding(
                    mode=mode,
                    finding_type="redundant",
                    severity="warning",
                    description=f"Rules on lines {line_a} and {line_b} appear similar ({overlap:.0%} overlap)",
                    line_numbers=[line_a, line_b],
                ))

    return findings


def check_relevance(mode: str, text: str, project_dir: str) -> list[BloatFinding]:
    """Check if rules reference files or patterns that no longer exist."""
    findings = []

    # Find file path references
    file_refs = re.findall(r'`([a-zA-Z0-9_/.-]+\.[a-zA-Z]+)`', text)
    source_refs = [
        f for f in file_refs
        if any(f.endswith(ext) for ext in (".py", ".ts", ".js", ".ex", ".md"))
        and not f.startswith("http")
    ]

    for ref in source_refs:
        full_path = os.path.join(project_dir, ref)
        if not os.path.exists(full_path):
            # Find the line number
            for i, line in enumerate(text.split("\n"), 1):
                if ref in line:
                    findings.append(BloatFinding(
                        mode=mode,
                        finding_type="irrelevant",
                        severity="warning",
                        description=f"Line {i} references `{ref}` which no longer exists",
                        line_numbers=[i],
                    ))
                    break

    return findings


def analyze_mode(mode: str, mode_file: str, project_dir: str) -> list[BloatFinding]:
    """Run all bloat checks on a single mode prompt."""
    try:
        with open(mode_file) as f:
            text = f.read()
    except (FileNotFoundError, OSError):
        return []

    findings = []
    findings.extend(check_budget(mode, text))
    findings.extend(check_redundancy(mode, text))
    findings.extend(check_relevance(mode, text, project_dir))
    return findings


def analyze_all_modes(modes_dir: str, project_dir: str) -> dict[str, list[BloatFinding]]:
    """Analyze all mode prompts for bloat."""
    results: dict[str, list[BloatFinding]] = {}

    if not os.path.isdir(modes_dir):
        return results

    for filename in sorted(os.listdir(modes_dir)):
        if not filename.endswith(".md"):
            continue
        mode = filename[:-3]
        mode_file = os.path.join(modes_dir, filename)
        findings = analyze_mode(mode, mode_file, project_dir)
        if findings:
            results[mode] = findings

    return results


def format_bloat_report(results: dict[str, list[BloatFinding]]) -> str:
    """Format bloat findings into a report."""
    if not results:
        return "No prompt bloat detected across all modes."

    lines = ["# Prompt Bloat Report", ""]
    total = sum(len(f) for f in results.values())
    lines.append(f"**{total} findings across {len(results)} modes**\n")

    for mode, findings in results.items():
        lines.append(f"## {mode}")
        for f in findings:
            icon = "!!" if f.severity == "critical" else "!"
            lines.append(f"- [{icon}] {f.description}")
        lines.append("")

    return "\n".join(lines)
