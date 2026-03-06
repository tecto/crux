"""Shell entry point for Crux Claude Code hooks.

Claude Code hooks invoke this via:
    python -m scripts.lib.crux_hook_runner <EventName>

Reads event JSON from stdin, dispatches to crux_hooks handlers,
writes any context output to stdout (for SessionStart/UserPromptSubmit).
"""

from __future__ import annotations

import json
import os
import sys


def main() -> None:
    project_dir = os.environ.get("CRUX_PROJECT", os.getcwd())
    home = os.environ.get("CRUX_HOME", os.environ.get("HOME", ""))

    event_json = sys.stdin.read()

    from scripts.lib.crux_hooks import run_hook

    result = run_hook(
        event_json=event_json,
        project_dir=project_dir,
        home=home,
    )

    # For SessionStart, output context so Claude Code adds it to conversation
    if result.get("context"):
        print(result["context"])
    elif result.get("status") == "error":
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    # TDD enforcement: if Stop hook found untested source files, output directive
    if result.get("tdd_compliant") is False and result.get("tdd_warnings"):
        uncovered = result.get("tdd_warnings", [])
        expected = result.get("tdd_expected", [])
        lines = [
            "STOP — TDD VIOLATION DETECTED",
            "",
            "You modified source files without updating their tests.",
            "Write or update the following test files before proceeding:",
            "",
        ]
        for warning in uncovered:
            lines.append(f"  - {warning}")
        if expected:
            lines.append("")
            lines.append("Expected test files:")
            for test_file in expected:
                lines.append(f"  - {test_file}")
        lines.append("")
        lines.append("Do not continue with other work until these tests are written.")
        print("\n".join(lines))


if __name__ == "__main__":  # pragma: no cover
    main()
