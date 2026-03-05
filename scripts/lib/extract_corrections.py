"""Extract correction patterns from session JSONL logs and cluster into knowledge candidates."""

import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CorrectionEntry:
    timestamp: str
    category: str
    original: str
    corrected: str
    pattern: str
    mode: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "category": self.category,
            "original": self.original,
            "corrected": self.corrected,
            "pattern": self.pattern,
            "mode": self.mode,
        }


@dataclass
class CorrectionCluster:
    category: str
    mode: str
    entries: list[CorrectionEntry] = field(default_factory=list)
    count: int = 0

    @property
    def key(self) -> str:
        return f"{self.category}:{self.mode}"

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "mode": self.mode,
            "count": self.count,
            "entries": [e.to_dict() for e in self.entries[:5]],  # Keep top 5 examples
        }


def parse_reflections_file(file_path: str) -> list[CorrectionEntry]:
    """Parse a JSONL reflections file into CorrectionEntry objects."""
    entries = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") == "self-correction":
                        entries.append(CorrectionEntry(
                            timestamp=data.get("timestamp", ""),
                            category=data.get("category", "unknown"),
                            original=data.get("original", ""),
                            corrected=data.get("corrected", ""),
                            pattern=data.get("pattern", ""),
                            mode=data.get("mode", "unknown"),
                        ))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return entries


def scan_reflections_dir(reflections_dir: str) -> list[CorrectionEntry]:
    """Scan all .jsonl files in the reflections directory."""
    all_entries = []
    try:
        for filename in sorted(os.listdir(reflections_dir)):
            if filename.endswith(".jsonl"):
                filepath = os.path.join(reflections_dir, filename)
                all_entries.extend(parse_reflections_file(filepath))
    except FileNotFoundError:
        pass
    return all_entries


def cluster_corrections(entries: list[CorrectionEntry]) -> list[CorrectionCluster]:
    """Cluster corrections by category and mode."""
    clusters: dict[str, CorrectionCluster] = {}

    for entry in entries:
        key = f"{entry.category}:{entry.mode}"
        if key not in clusters:
            clusters[key] = CorrectionCluster(
                category=entry.category,
                mode=entry.mode,
            )
        cluster = clusters[key]
        cluster.entries.append(entry)
        cluster.count += 1

    # Sort by count descending
    return sorted(clusters.values(), key=lambda c: c.count, reverse=True)


def generate_knowledge_candidate(cluster: CorrectionCluster) -> str:
    """Generate a knowledge entry markdown from a correction cluster."""
    examples = cluster.entries[:3]
    example_lines = []
    for e in examples:
        example_lines.append(f"- Original: {e.original}")
        example_lines.append(f"  Corrected: {e.corrected}")

    return "\n".join([
        f"# Correction Pattern: {cluster.category} in {cluster.mode}",
        "",
        f"**Category**: {cluster.category}",
        f"**Mode**: {cluster.mode}",
        f"**Occurrences**: {cluster.count}",
        "",
        "## Examples",
        "",
        *example_lines,
        "",
        f"Tags: {cluster.category}, {cluster.mode}, correction",
    ])


def extract_corrections(
    reflections_dir: Optional[str] = None,
    min_cluster_size: int = 2,
) -> dict:
    """Main extraction pipeline: scan, cluster, generate candidates."""
    if reflections_dir is None:
        reflections_dir = os.path.join(
            os.environ.get("HOME", ""),
            ".crux", "corrections",
        )

    entries = scan_reflections_dir(reflections_dir)
    clusters = cluster_corrections(entries)

    # Filter to clusters with enough occurrences
    significant = [c for c in clusters if c.count >= min_cluster_size]

    candidates = []
    for cluster in significant:
        candidates.append({
            "cluster": cluster.to_dict(),
            "knowledge_entry": generate_knowledge_candidate(cluster),
        })

    return {
        "total_entries": len(entries),
        "total_clusters": len(clusters),
        "significant_clusters": len(significant),
        "candidates": candidates,
    }


def main() -> None:
    """CLI entry point."""
    import sys

    reflections_dir = sys.argv[1] if len(sys.argv) > 1 else None
    min_size = int(sys.argv[2]) if len(sys.argv) > 2 else 2

    result = extract_corrections(reflections_dir, min_size)

    if result["significant_clusters"] == 0:
        print("No significant correction patterns found.")
        sys.exit(0)

    print(f"Found {result['total_entries']} corrections in {result['total_clusters']} clusters.")
    print(f"{result['significant_clusters']} clusters meet threshold (>= {min_size}).\n")

    for candidate in result["candidates"]:
        print("---")
        print(candidate["knowledge_entry"])
        print()


if __name__ == "__main__":  # pragma: no cover
    main()
