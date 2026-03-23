"""Knowledge clustering — auto-elevate correction clusters into knowledge entries.

When 3+ corrections share a category+mode, synthesize them into a knowledge entry
and promote to project scope. When a pattern appears in 2+ projects, promote to
user scope.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from scripts.lib.crux_security import secure_makedirs, secure_write_file
from scripts.lib.extract_corrections import (
    CorrectionCluster,
    cluster_corrections,
    extract_corrections,
    generate_knowledge_candidate,
)


DEFAULT_MIN_CLUSTER_SIZE = 3
DEFAULT_KNOWLEDGE_DIR = "knowledge"


def find_elevatable_clusters(
    reflections_dir: str | None = None,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
) -> list[CorrectionCluster]:
    """Find correction clusters large enough to elevate to knowledge entries."""
    result = extract_corrections(reflections_dir, min_cluster_size=min_cluster_size)
    return result.get("clusters", [])


def elevate_cluster_to_knowledge(
    cluster: CorrectionCluster,
    knowledge_dir: str,
) -> str:
    """Write a correction cluster as a knowledge entry file.

    Returns the path to the created file.
    """
    content = generate_knowledge_candidate(cluster)
    slug = f"correction-{cluster.category}-{cluster.mode}".replace(" ", "-").lower()
    filename = f"{slug}.md"
    filepath = os.path.join(knowledge_dir, filename)

    secure_makedirs(knowledge_dir)
    secure_write_file(filepath, content)

    return filepath


def auto_elevate(
    project_dir: str,
    reflections_dir: str | None = None,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
) -> list[str]:
    """Run the full auto-elevation pipeline.

    1. Find clusters >= min_cluster_size
    2. Write as knowledge entries
    3. Return list of created file paths
    """
    clusters = find_elevatable_clusters(reflections_dir, min_cluster_size)
    knowledge_dir = os.path.join(project_dir, ".crux", DEFAULT_KNOWLEDGE_DIR)
    created = []

    for cluster in clusters:
        path = elevate_cluster_to_knowledge(cluster, knowledge_dir)
        created.append(path)

    return created


def check_cross_project_promotion(
    home: str,
    pattern_slug: str,
    min_projects: int = 2,
) -> bool:
    """Check if a pattern appears in enough projects to promote to user scope.

    Scans all .crux/knowledge/ directories under home for the pattern slug.
    """
    count = 0
    home_path = Path(home)

    for crux_dir in home_path.rglob(".crux"):
        knowledge_dir = crux_dir / DEFAULT_KNOWLEDGE_DIR
        if not knowledge_dir.is_dir():
            continue
        for entry in knowledge_dir.iterdir():
            if pattern_slug in entry.name:
                count += 1
                if count >= min_projects:
                    return True

    return False


def promote_to_user_scope(
    home: str,
    pattern_slug: str,
    content: str,
) -> str:
    """Promote a knowledge entry to user scope (~/.crux/knowledge/)."""
    user_knowledge = os.path.join(home, ".crux", DEFAULT_KNOWLEDGE_DIR)
    secure_makedirs(user_knowledge)

    filepath = os.path.join(user_knowledge, f"{pattern_slug}.md")
    secure_write_file(filepath, content)

    return filepath
