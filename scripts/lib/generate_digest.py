"""Generate daily analytics digest from session logs and reflections."""

import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class DigestMetrics:
    total_sessions: int = 0
    total_interactions: int = 0
    modes_used: dict[str, int] = field(default_factory=dict)
    tools_used: dict[str, int] = field(default_factory=dict)
    corrections_by_category: dict[str, int] = field(default_factory=dict)
    corrections_total: int = 0
    knowledge_lookups: int = 0
    scripts_run: int = 0

    def to_dict(self) -> dict:
        return {
            "total_sessions": self.total_sessions,
            "total_interactions": self.total_interactions,
            "modes_used": dict(self.modes_used),
            "tools_used": dict(self.tools_used),
            "corrections_by_category": dict(self.corrections_by_category),
            "corrections_total": self.corrections_total,
            "knowledge_lookups": self.knowledge_lookups,
            "scripts_run": self.scripts_run,
        }


def scan_session_logs(logs_dir: str, date_str: Optional[str] = None) -> DigestMetrics:
    """Scan session log files for the given date."""
    metrics = DigestMetrics()

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    try:
        for filename in os.listdir(logs_dir):
            if not filename.endswith(".jsonl"):
                continue
            filepath = os.path.join(logs_dir, filename)
            try:
                with open(filepath, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        ts = entry.get("timestamp", "")
                        if date_str and not ts.startswith(date_str):
                            continue

                        event = entry.get("event", "")

                        if event == "session_start":
                            metrics.total_sessions += 1
                        elif event == "interaction":
                            metrics.total_interactions += 1
                            mode = entry.get("mode", "unknown")
                            metrics.modes_used[mode] = metrics.modes_used.get(mode, 0) + 1
                        elif event == "tool_call":
                            tool = entry.get("tool", "unknown")
                            metrics.tools_used[tool] = metrics.tools_used.get(tool, 0) + 1
                            if tool == "lookup_knowledge":
                                metrics.knowledge_lookups += 1
                            elif tool == "run_script":
                                metrics.scripts_run += 1
            except (OSError, IOError):
                continue
    except FileNotFoundError:
        pass

    return metrics


def scan_reflections(reflections_dir: str, date_str: Optional[str] = None) -> dict[str, int]:
    """Scan reflections for the given date."""
    corrections: dict[str, int] = {}

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    target_file = os.path.join(reflections_dir, f"{date_str}.jsonl")
    try:
        with open(target_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "self-correction":
                        cat = entry.get("category", "unknown")
                        corrections[cat] = corrections.get(cat, 0) + 1
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass

    return corrections


def generate_digest_content(metrics: DigestMetrics, date_str: str) -> str:
    """Format digest as markdown."""
    lines = [
        f"# Daily Digest: {date_str}",
        "",
        "## Summary",
        "",
        f"- Sessions: {metrics.total_sessions}",
        f"- Interactions: {metrics.total_interactions}",
        f"- Corrections: {metrics.corrections_total}",
        f"- Knowledge Lookups: {metrics.knowledge_lookups}",
        f"- Scripts Run: {metrics.scripts_run}",
        "",
    ]

    if metrics.modes_used:
        lines.extend(["## Modes Used", ""])
        for mode, count in sorted(metrics.modes_used.items(), key=lambda x: -x[1]):
            lines.append(f"- {mode}: {count}")
        lines.append("")

    if metrics.tools_used:
        lines.extend(["## Tools Used", ""])
        for tool, count in sorted(metrics.tools_used.items(), key=lambda x: -x[1]):
            lines.append(f"- {tool}: {count}")
        lines.append("")

    if metrics.corrections_by_category:
        lines.extend(["## Corrections by Category", ""])
        for cat, count in sorted(metrics.corrections_by_category.items(), key=lambda x: -x[1]):
            lines.append(f"- {cat}: {count}")
        lines.append("")

    return "\n".join(lines)


def generate_digest(
    logs_dir: Optional[str] = None,
    reflections_dir: Optional[str] = None,
    date_str: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """Main entry point: scan logs, scan reflections, generate digest."""
    home = os.environ.get("HOME", "")

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    if logs_dir is None:
        logs_dir = os.path.join(home, ".crux", "analytics", "sessions")

    if reflections_dir is None:
        reflections_dir = os.path.join(home, ".crux", "corrections")

    if output_dir is None:
        output_dir = os.path.join(home, ".crux", "analytics", "digests")

    metrics = scan_session_logs(logs_dir, date_str)
    corrections = scan_reflections(reflections_dir, date_str)
    metrics.corrections_by_category = corrections
    metrics.corrections_total = sum(corrections.values())

    content = generate_digest_content(metrics, date_str)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{date_str}.md")
    with open(output_path, "w") as f:
        f.write(content)

    return {
        "date": date_str,
        "output_path": output_path,
        "metrics": metrics.to_dict(),
        "content": content,
    }


def main() -> None:
    """CLI entry point."""
    import sys

    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    result = generate_digest(date_str=date_str)
    print(result["content"])


if __name__ == "__main__":  # pragma: no cover
    main()
