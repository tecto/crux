"""Preflight validator for Crux scripts.

Deterministic pre-flight checks run before any script execution:
1. Shebang present
2. Risk header present and valid
3. set -euo pipefail present
4. main() function defined
5. Risk classification matches behavior (low + destructive = reject)
6. DRY_RUN support for medium+ risk
7. No writes to absolute root paths
8. Multi-file writes require transaction pattern
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    passed: bool
    errors: list[str]
    script_path: str

    def to_dict(self) -> dict:
        return {"passed": self.passed, "errors": self.errors, "script_path": self.script_path}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


_DESTRUCTIVE_PATTERNS = re.compile(
    r'\b(rm\s|rm$|rmdir\b|delete\w*\b|drop\b|truncate\b)', re.IGNORECASE
)

_RISK_LEVELS = {"low", "medium", "high"}


def _strip_comments(lines: list[str]) -> list[str]:
    """Return only executable (non-comment, non-blank) lines."""
    result = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        # Remove inline comments (naive but sufficient for validation)
        if " #" in stripped:
            stripped = stripped[:stripped.index(" #")]
        result.append(stripped)
    return result


def _extract_risk(content: str) -> str | None:
    """Extract risk level from header comments."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and "Risk:" in stripped:
            match = re.search(r'Risk:\s*(\w+)', stripped)
            if match:
                return match.group(1).lower()
    return None


def _count_file_redirects(exec_lines: list[str]) -> int:
    """Count lines with output redirection to files (> file or >> file)."""
    count = 0
    for line in exec_lines:
        # Match > or >> followed by a path (not fd redirects like 2>&1)
        if re.search(r'>\s*[./\w]', line) and not re.search(r'[0-9]>&', line):
            count += 1
    return count


def validate_script(script_path: str) -> ValidationResult:
    """Run all preflight checks on a script. Returns ValidationResult."""
    errors: list[str] = []
    path = Path(script_path)

    # File existence
    if not path.exists():
        return ValidationResult(passed=False, errors=["Script not found: file does not exist"], script_path=script_path)

    content = path.read_text()
    lines = content.splitlines()

    # Check 1: Shebang
    if not lines or not lines[0].startswith("#!"):
        errors.append("Missing shebang (first line must start with #!)")

    # Check 2: Risk header
    risk = _extract_risk(content)
    if risk is None:
        errors.append("Missing Risk header in script comments (expected '# Risk: low|medium|high')")
    elif risk not in _RISK_LEVELS:
        errors.append(f"Invalid risk level '{risk}' (expected: low, medium, high)")

    # Check 3: set -euo pipefail
    if "set -euo pipefail" not in content:
        errors.append("Missing 'set -euo pipefail' safety clause")

    # Check 4: main() function
    has_main = bool(re.search(r'^main\s*\(\)', content, re.MULTILINE))
    if not has_main:
        errors.append("Missing main() function definition")

    # Only run behavioral checks if we successfully parsed risk
    if risk and risk in _RISK_LEVELS:
        exec_lines = _strip_comments(lines)

        # Check 5: Risk vs destructive operations
        if risk == "low":
            for line in exec_lines:
                if _DESTRUCTIVE_PATTERNS.search(line):
                    errors.append(
                        f"Low-risk script contains destructive operation: '{line.strip()}'. "
                        "Use medium or high risk level for destructive operations."
                    )
                    break

        # Check 6: DRY_RUN support for medium+ (check executable lines only)
        if risk in ("medium", "high"):
            exec_text = "\n".join(exec_lines)
            if "DRY_RUN" not in exec_text:
                errors.append(
                    f"{risk.capitalize()}-risk script must support DRY_RUN "
                    "(include DRY_RUN variable and check it before destructive operations)"
                )

        # Check 7: Path containment — no writes to absolute paths
        for line in exec_lines:
            if re.search(r'>>?\s*/[a-zA-Z]', line):
                errors.append(
                    f"Write to absolute path detected: '{line.strip()}'. "
                    "Scripts must only write to relative paths within the project."
                )
                break

        # Check 8: Multi-file writes need transaction pattern
        redirect_count = _count_file_redirects(exec_lines)
        if redirect_count > 1:
            # Check for TRANSACTION_STEPS declaration in executable code
            has_transaction = bool(
                re.search(r'^TRANSACTION_STEPS\s*=', content, re.MULTILINE)
            )
            if not has_transaction:
                errors.append(
                    f"Script writes to {redirect_count} files but is not a transaction script. "
                    "Multi-file writes must use the transaction pattern (TRANSACTION_STEPS + rollback)."
                )

    passed = len(errors) == 0
    return ValidationResult(passed=passed, errors=errors, script_path=script_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="preflight_validator",
        description="Preflight validation for Crux scripts"
    )
    parser.add_argument("script", nargs="?", help="Path to script to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.script:
        print("Usage: preflight_validator <script_path> [--json]")
        sys.exit(1)

    result = validate_script(args.script)

    if args.json:
        print(result.to_json())
    else:
        if result.passed:
            print(f"PASS: {args.script}")
        else:
            print(f"FAIL: {args.script}")
            for err in result.errors:
                print(f"  - {err}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":  # pragma: no cover
    main()
