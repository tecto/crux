"""Promote knowledge entries from project to user to public scope."""

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PromotionResult:
    promoted: bool
    source: str
    destination: str
    entry_name: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "promoted": self.promoted,
            "source": self.source,
            "destination": self.destination,
            "entry_name": self.entry_name,
            "error": self.error,
        }


def find_knowledge_entry(entry_name: str, search_dirs: list[str]) -> Optional[str]:
    """Find a knowledge entry by name across search directories."""
    for directory in search_dirs:
        # Check in the directory directly
        candidate = os.path.join(directory, f"{entry_name}.md")
        if os.path.exists(candidate):
            return candidate
        # Check in subdirectories
        try:
            for subdir in os.listdir(directory):
                subpath = os.path.join(directory, subdir)
                if os.path.isdir(subpath):
                    candidate = os.path.join(subpath, f"{entry_name}.md")
                    if os.path.exists(candidate):
                        return candidate
        except FileNotFoundError:
            continue
    return None


def determine_promotion_target(
    source_path: str,
    project_knowledge: str,
    user_knowledge: str,
) -> Optional[str]:
    """Determine where to promote the knowledge entry."""
    if source_path.startswith(project_knowledge):
        # Project → User: preserve subdirectory structure
        rel = os.path.relpath(source_path, project_knowledge)
        return os.path.join(user_knowledge, rel)
    return None


def promote_entry(
    entry_name: str,
    project_dir: Optional[str] = None,
) -> PromotionResult:
    """Promote a knowledge entry from project to user scope."""
    if project_dir is None:
        project_dir = os.getcwd()

    home = os.environ.get("HOME", "")
    project_knowledge = os.path.join(project_dir, ".crux", "knowledge")
    user_knowledge = os.path.join(home, ".crux", "knowledge")

    # Find the entry
    source = find_knowledge_entry(entry_name, [project_knowledge])
    if source is None:
        return PromotionResult(
            promoted=False,
            source="",
            destination="",
            entry_name=entry_name,
            error=f"Knowledge entry '{entry_name}' not found in project scope",
        )

    # Determine target
    target = determine_promotion_target(source, project_knowledge, user_knowledge)
    if target is None:  # pragma: no cover
        return PromotionResult(
            promoted=False,
            source=source,
            destination="",
            entry_name=entry_name,
            error="Could not determine promotion target",
        )

    # Check if already exists at target
    if os.path.exists(target):
        return PromotionResult(
            promoted=False,
            source=source,
            destination=target,
            entry_name=entry_name,
            error=f"Entry already exists at user scope: {target}",
        )

    # Copy to target
    os.makedirs(os.path.dirname(target), exist_ok=True)
    shutil.copy2(source, target)

    return PromotionResult(
        promoted=True,
        source=source,
        destination=target,
        entry_name=entry_name,
    )


def list_promotable_entries(project_dir: Optional[str] = None) -> list[dict]:
    """List knowledge entries that could be promoted."""
    if project_dir is None:
        project_dir = os.getcwd()

    home = os.environ.get("HOME", "")
    project_knowledge = os.path.join(project_dir, ".crux", "knowledge")
    user_knowledge = os.path.join(home, ".crux", "knowledge")

    entries = []
    for root, dirs, files in os.walk(project_knowledge):
        for f in files:
            if f.endswith(".md"):
                source = os.path.join(root, f)
                name = os.path.splitext(f)[0]
                rel = os.path.relpath(source, project_knowledge)
                target = os.path.join(user_knowledge, rel)
                entries.append({
                    "name": name,
                    "source": source,
                    "target": target,
                    "already_promoted": os.path.exists(target),
                })

    return entries


def main() -> None:
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: promote_knowledge.py <entry_name> [project_dir]")
        sys.exit(1)

    entry_name = sys.argv[1]
    project_dir = sys.argv[2] if len(sys.argv) > 2 else None

    result = promote_entry(entry_name, project_dir)
    if result.promoted:
        print(f"Promoted '{entry_name}' from {result.source} to {result.destination}")
    else:
        print(f"Failed: {result.error}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
