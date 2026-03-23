"""Knowledge staleness detection — validate entries against current codebase.

Periodically scan knowledge entries, check if referenced files/functions
still exist. Flag stale entries for retirement.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StalenessCheck:
    entry_path: str
    entry_name: str
    is_stale: bool
    reason: str


def check_entry_staleness(
    entry_path: str,
    project_dir: str,
) -> StalenessCheck:
    """Check if a single knowledge entry is stale.

    Looks for file references, function names, and module names
    in the entry content. If referenced artifacts no longer exist
    in the project, the entry is flagged as stale.
    """
    entry_name = os.path.basename(entry_path)

    try:
        with open(entry_path) as f:
            content = f.read()
    except (FileNotFoundError, OSError):
        return StalenessCheck(
            entry_path=entry_path,
            entry_name=entry_name,
            is_stale=True,
            reason="Entry file not found",
        )

    # Extract file references (paths ending in .py, .ts, .js, .ex, etc.)
    file_refs = re.findall(r'[`"]([a-zA-Z0-9_/.-]+\.[a-zA-Z]+)[`"]', content)
    # Filter to likely source file references (not URLs or generic text)
    source_refs = [
        f for f in file_refs
        if any(f.endswith(ext) for ext in (".py", ".ts", ".js", ".ex", ".exs", ".rs", ".go"))
        and not f.startswith("http")
    ]

    if not source_refs:
        # No file references to check — can't determine staleness
        return StalenessCheck(
            entry_path=entry_path,
            entry_name=entry_name,
            is_stale=False,
            reason="No source file references to validate",
        )

    missing = []
    for ref in source_refs:
        full_path = os.path.join(project_dir, ref)
        if not os.path.exists(full_path):
            missing.append(ref)

    if missing:
        return StalenessCheck(
            entry_path=entry_path,
            entry_name=entry_name,
            is_stale=True,
            reason=f"Referenced files no longer exist: {', '.join(missing[:5])}",
        )

    return StalenessCheck(
        entry_path=entry_path,
        entry_name=entry_name,
        is_stale=False,
        reason="All referenced files exist",
    )


def scan_knowledge_dir(
    knowledge_dir: str,
    project_dir: str,
) -> list[StalenessCheck]:
    """Scan all knowledge entries in a directory for staleness."""
    results = []

    if not os.path.isdir(knowledge_dir):
        return results

    for entry in sorted(os.listdir(knowledge_dir)):
        if not entry.endswith(".md"):
            continue
        entry_path = os.path.join(knowledge_dir, entry)
        result = check_entry_staleness(entry_path, project_dir)
        results.append(result)

    return results


def soft_retire(entry_path: str) -> None:
    """Soft-retire a stale entry by prepending a staleness warning.

    Does not delete the file — just marks it as potentially stale.
    """
    try:
        with open(entry_path) as f:
            content = f.read()
    except (FileNotFoundError, OSError):
        return

    if content.startswith("<!-- STALE"):
        return  # Already marked

    warning = (
        "<!-- STALE: This knowledge entry may be outdated. "
        "Referenced files no longer exist in the codebase. "
        f"Flagged: {__import__('time').strftime('%Y-%m-%d')} -->\n\n"
    )
    with open(entry_path, "w") as f:
        f.write(warning + content)


def auto_staleness_scan(
    project_dir: str,
) -> list[StalenessCheck]:
    """Run a full staleness scan on a project's knowledge entries.

    Soft-retires any stale entries found.
    """
    knowledge_dir = os.path.join(project_dir, ".crux", "knowledge")
    results = scan_knowledge_dir(knowledge_dir, project_dir)

    for result in results:
        if result.is_stale:
            soft_retire(result.entry_path)

    return results
