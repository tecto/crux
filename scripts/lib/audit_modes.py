"""Audit mode prompts against empirical design rules."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


NEGATIVE_PATTERNS = [
    r"\bdon'?t\b",
    r"\bdo not\b",
    r"\bnever\b",
    r"\bavoid\b",
    r"\brefrain\b",
    r"\bstop\b",
    r"\bprohibit\b",
    r"\bforbid\b",
]

WORD_TARGET_MIN = 150
WORD_TARGET_MAX = 200


@dataclass
class ModeAuditResult:
    mode: str
    file_path: str
    word_count: int
    word_count_ok: bool
    negative_phrases: list[str] = field(default_factory=list)
    positive_framing_ok: bool = True
    has_persona: bool = False
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "word_count": self.word_count,
            "word_count_ok": self.word_count_ok,
            "negative_phrases": self.negative_phrases,
            "positive_framing_ok": self.positive_framing_ok,
            "has_persona": self.has_persona,
            "issues": self.issues,
        }


def count_words(content: str) -> int:
    """Count words in content, excluding markdown headers and empty lines."""
    lines = content.split("\n")
    text_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    text = " ".join(text_lines)
    return len(text.split())


def find_negative_phrases(content: str) -> list[str]:
    """Find negative instruction patterns in content."""
    found = []
    for pattern in NEGATIVE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        found.extend(matches)
    return found


def check_persona(content: str) -> bool:
    """Check if the mode prompt defines a persona."""
    persona_indicators = [
        r"\byou are\b",
        r"\byour role\b",
        r"\bas a\b",
        r"\byou serve as\b",
        r"\bpersona\b",
        r"\bexpert\b",
        r"\bspecialist\b",
    ]
    for pattern in persona_indicators:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def audit_mode_file(file_path: str) -> ModeAuditResult:
    """Audit a single mode prompt file."""
    mode_name = os.path.splitext(os.path.basename(file_path))[0]

    with open(file_path, "r") as f:
        content = f.read()

    word_count = count_words(content)
    word_count_ok = WORD_TARGET_MIN <= word_count <= WORD_TARGET_MAX
    negative_phrases = find_negative_phrases(content)
    positive_framing_ok = len(negative_phrases) == 0
    has_persona = check_persona(content)

    issues = []
    if not word_count_ok:
        if word_count < WORD_TARGET_MIN:
            issues.append(f"Word count {word_count} is below target ({WORD_TARGET_MIN}-{WORD_TARGET_MAX})")
        else:
            issues.append(f"Word count {word_count} exceeds target ({WORD_TARGET_MIN}-{WORD_TARGET_MAX})")
    if not positive_framing_ok:
        issues.append(f"Contains negative phrasing: {', '.join(set(negative_phrases))}")
    if not has_persona:
        issues.append("No clear persona definition found")

    return ModeAuditResult(
        mode=mode_name,
        file_path=file_path,
        word_count=word_count,
        word_count_ok=word_count_ok,
        negative_phrases=negative_phrases,
        positive_framing_ok=positive_framing_ok,
        has_persona=has_persona,
        issues=issues,
    )


def audit_all_modes(modes_dir: Optional[str] = None) -> dict:
    """Audit all mode files in the modes directory."""
    if modes_dir is None:
        modes_dir = os.path.join(os.getcwd(), "modes")

    results = []
    try:
        for filename in sorted(os.listdir(modes_dir)):
            if filename.endswith(".md") and not filename.startswith("_"):
                file_path = os.path.join(modes_dir, filename)
                result = audit_mode_file(file_path)
                results.append(result.to_dict())
    except FileNotFoundError:
        pass

    total = len(results)
    passing = sum(1 for r in results if not r["issues"])

    return {
        "total_modes": total,
        "passing": passing,
        "failing": total - passing,
        "results": results,
    }


def main() -> None:
    """CLI entry point."""
    import sys

    modes_dir = sys.argv[1] if len(sys.argv) > 1 else None
    result = audit_all_modes(modes_dir)

    print(f"Mode Audit: {result['passing']}/{result['total_modes']} passing\n")
    for r in result["results"]:
        status = "PASS" if not r["issues"] else "FAIL"
        print(f"  [{status}] {r['mode']} ({r['word_count']} words)")
        for issue in r["issues"]:
            print(f"    - {issue}")

    if result["failing"] > 0:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
