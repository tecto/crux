"""Cross-project aggregation — analytics across all Crux-enabled projects.

Discovers projects, aggregates digests and corrections, and generates
user-level insights spanning multiple codebases.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


_DEFAULT_SCAN_DIRS = ["", "projects", "personal", "work", "src", "dev"]


def _registry_path(home: str) -> str:
    return os.path.join(home, ".crux", "projects.json")


def _load_registry(home: str) -> list[str]:
    path = _registry_path(home)
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("projects", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_registry(home: str, projects: list[str]) -> None:
    path = _registry_path(home)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"projects": projects}, f, indent=2)


def discover_projects(home: str) -> list[str]:
    """Scan common locations for directories containing .crux/.

    Also includes any projects from the registry. Returns deduplicated,
    sorted list of project paths.
    """
    found: set[str] = set()

    # Check registry first
    for p in _load_registry(home):
        if os.path.isdir(os.path.join(p, ".crux")):
            found.add(p)

    # Scan common directories
    for subdir in _DEFAULT_SCAN_DIRS:
        scan_root = os.path.join(home, subdir) if subdir else home
        if not os.path.isdir(scan_root):
            continue
        try:
            for entry in os.listdir(scan_root):
                full = os.path.join(scan_root, entry)
                if os.path.isdir(full) and os.path.isdir(os.path.join(full, ".crux")):
                    found.add(full)
        except PermissionError:
            continue

    return sorted(found)


def register_project(project_dir: str, home: str) -> dict:
    """Add a project to the registry."""
    project_dir = os.path.abspath(project_dir)
    projects = _load_registry(home)
    if project_dir in projects:
        return {"registered": False, "reason": "already registered", "projects": projects}
    projects.append(project_dir)
    _save_registry(home, projects)
    return {"registered": True, "project": project_dir, "total_projects": len(projects)}


def unregister_project(project_dir: str, home: str) -> dict:
    """Remove a project from the registry."""
    project_dir = os.path.abspath(project_dir)
    projects = _load_registry(home)
    if project_dir not in projects:
        return {"unregistered": False, "reason": "not in registry"}
    projects.remove(project_dir)
    _save_registry(home, projects)
    return {"unregistered": True, "project": project_dir, "total_projects": len(projects)}


def _count_interactions_for_date(project_dir: str, date_str: str) -> int:
    int_file = os.path.join(project_dir, ".crux", "analytics", "interactions", f"{date_str}.jsonl")
    if not os.path.exists(int_file):
        return 0
    count = 0
    with open(int_file) as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _count_corrections(project_dir: str) -> int:
    corr_file = os.path.join(project_dir, ".crux", "corrections", "corrections.jsonl")
    if not os.path.exists(corr_file):
        return 0
    count = 0
    with open(corr_file) as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _read_corrections(project_dir: str) -> list[dict]:
    corr_file = os.path.join(project_dir, ".crux", "corrections", "corrections.jsonl")
    entries: list[dict] = []
    if not os.path.exists(corr_file):
        return entries
    with open(corr_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def _get_active_mode(project_dir: str) -> str | None:
    state_file = os.path.join(project_dir, ".crux", "sessions", "state.json")
    try:
        with open(state_file) as f:
            data = json.load(f)
        return data.get("active_mode")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def aggregate_digests(home: str, date_str: str | None = None) -> dict:
    """Merge analytics from all registered projects for a given date."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    projects = discover_projects(home)
    total_interactions = 0
    total_corrections = 0
    modes_used: Counter[str] = Counter()
    project_summaries: list[dict] = []

    for proj in projects:
        interactions = _count_interactions_for_date(proj, date_str)
        corrections = _count_corrections(proj)
        mode = _get_active_mode(proj)

        total_interactions += interactions
        total_corrections += corrections
        if mode:
            modes_used[mode] += 1

        project_summaries.append({
            "project": proj,
            "interactions": interactions,
            "corrections": corrections,
            "active_mode": mode,
        })

    return {
        "date": date_str,
        "total_projects": len(projects),
        "total_interactions": total_interactions,
        "total_corrections": total_corrections,
        "modes_used": dict(modes_used),
        "projects": project_summaries,
    }


def aggregate_corrections(home: str) -> dict:
    """Find correction patterns that appear across multiple projects."""
    projects = discover_projects(home)
    # Track category counts per project
    category_projects: dict[str, set[str]] = {}
    category_counts: Counter[str] = Counter()

    for proj in projects:
        corrections = _read_corrections(proj)
        proj_categories: set[str] = set()
        for corr in corrections:
            cat = corr.get("category", "unknown")
            category_counts[cat] += 1
            proj_categories.add(cat)
        for cat in proj_categories:
            if cat not in category_projects:
                category_projects[cat] = set()
            category_projects[cat].add(proj)

    # Cross-project patterns: categories appearing in 2+ projects
    cross_project: list[dict] = []
    for cat, projs in category_projects.items():
        cross_project.append({
            "category": cat,
            "project_count": len(projs),
            "total_occurrences": category_counts[cat],
            "cross_project": len(projs) > 1,
        })
    cross_project.sort(key=lambda x: (-x["project_count"], -x["total_occurrences"]))

    return {
        "total_projects_scanned": len(projects),
        "patterns": cross_project,
        "cross_project_patterns": [p for p in cross_project if p["cross_project"]],
    }


def generate_user_digest(home: str, date_str: str | None = None) -> dict:
    """Generate a user-level digest spanning all projects."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    digest_data = aggregate_digests(home, date_str)
    correction_data = aggregate_corrections(home)

    # Write to user-level digest directory
    digest_dir = os.path.join(home, ".crux", "analytics", "digests")
    os.makedirs(digest_dir, exist_ok=True)

    lines = [
        f"# User Digest: {date_str}",
        "",
        "## Summary",
        f"- Projects: {digest_data['total_projects']}",
        f"- Total Interactions: {digest_data['total_interactions']}",
        f"- Total Corrections: {digest_data['total_corrections']}",
        "",
    ]

    if digest_data["modes_used"]:
        lines.extend(["## Modes Used Across Projects", ""])
        for mode, count in sorted(digest_data["modes_used"].items(), key=lambda x: -x[1]):
            lines.append(f"- {mode}: {count} project(s)")
        lines.append("")

    if correction_data["cross_project_patterns"]:
        lines.extend(["## Cross-Project Correction Patterns", ""])
        for p in correction_data["cross_project_patterns"]:
            lines.append(f"- {p['category']}: {p['total_occurrences']} occurrences across {p['project_count']} projects")
        lines.append("")

    if digest_data["projects"]:
        lines.extend(["## Per-Project Breakdown", ""])
        for proj in digest_data["projects"]:
            name = os.path.basename(proj["project"])
            lines.append(f"### {name}")
            lines.append(f"- Interactions: {proj['interactions']}")
            lines.append(f"- Corrections: {proj['corrections']}")
            if proj["active_mode"]:
                lines.append(f"- Active Mode: {proj['active_mode']}")
            lines.append("")

    content = "\n".join(lines)
    output_path = os.path.join(digest_dir, f"{date_str}.md")
    with open(output_path, "w") as f:
        f.write(content)

    return {
        "date": date_str,
        "output_path": output_path,
        "digest": digest_data,
        "corrections": correction_data,
        "content": content,
    }
