"""Threshold-triggered background processor for continuous learning.

Checks data thresholds and runs processors (correction extraction,
digest generation, mode auditing) only when thresholds are exceeded.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from scripts.lib.crux_paths import get_project_paths


@dataclass
class ProcessorConfig:
    correction_queue_size: int = 10
    interaction_count: int = 50
    digest_age_hours: int = 24


def _load_processor_state(project_dir: str) -> dict:
    state_path = os.path.join(project_dir, ".crux", "analytics", "processor_state.json")
    try:
        with open(state_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_processor_state(project_dir: str, state: dict) -> None:
    state_dir = os.path.join(project_dir, ".crux", "analytics")
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, "processor_state.json"), "w") as f:
        json.dump(state, f, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _count_todays_interactions(project_dir: str) -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    int_file = os.path.join(project_dir, ".crux", "analytics", "interactions", f"{today}.jsonl")
    if not os.path.exists(int_file):
        return 0
    count = 0
    with open(int_file) as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _hours_since(iso_timestamp: str) -> float:
    try:
        ts = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds() / 3600
    except (ValueError, TypeError):
        return float("inf")


def check_thresholds(
    project_dir: str,
    home: str,
    config: ProcessorConfig | None = None,
) -> dict:
    """Check which processing thresholds are exceeded."""
    cfg = config or ProcessorConfig()
    state = _load_processor_state(project_dir)

    correction_count = _count_corrections(project_dir)
    interaction_count = _count_todays_interactions(project_dir)

    last_digest = state.get("last_digest", "")
    digest_age = _hours_since(last_digest) if last_digest else float("inf")
    # Only flag stale if there's actually data to process
    has_data = interaction_count > 0 or correction_count > 0
    digest_stale = digest_age > cfg.digest_age_hours and has_data

    return {
        "corrections_exceeded": correction_count >= cfg.correction_queue_size,
        "correction_count": correction_count,
        "interactions_exceeded": interaction_count >= cfg.interaction_count,
        "interaction_count": interaction_count,
        "digest_stale": digest_stale,
        "digest_age_hours": round(digest_age, 1) if digest_age != float("inf") else None,
    }


def should_process(project_dir: str, home: str, config: ProcessorConfig | None = None) -> bool:
    """Quick check if any processing is due."""
    t = check_thresholds(project_dir, home, config)
    return t["corrections_exceeded"] or t["interactions_exceeded"] or t["digest_stale"]


def run_processors(project_dir: str, home: str, config: ProcessorConfig | None = None) -> dict:
    """Run all due processors and update state."""
    t = check_thresholds(project_dir, home, config)
    state = _load_processor_state(project_dir)
    processors_run: list[dict] = []
    now = _now_iso()

    # Processor 1: Correction extraction
    if t["corrections_exceeded"]:
        try:
            from scripts.lib.extract_corrections import extract_corrections
            corr_dir = os.path.join(project_dir, ".crux", "corrections")
            results = extract_corrections(reflections_dir=corr_dir)
            processors_run.append({
                "name": "corrections",
                "status": "completed",
                "entries": len(results),
            })
        except Exception as exc:
            processors_run.append({
                "name": "corrections",
                "status": "error",
                "error": str(exc),
            })
        state["last_corrections"] = now

    # Processor 2: Digest generation
    if t["digest_stale"] or t["interactions_exceeded"]:
        try:
            from scripts.lib.generate_digest import generate_digest
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            logs_dir = os.path.join(project_dir, ".crux", "analytics", "interactions")
            corr_dir = os.path.join(project_dir, ".crux", "corrections")
            digest_dir = os.path.join(project_dir, ".crux", "analytics", "digests")
            result_digest = generate_digest(
                logs_dir=logs_dir,
                reflections_dir=corr_dir,
                date_str=today,
                output_dir=digest_dir,
            )
            processors_run.append({
                "name": "digest",
                "status": "completed",
                "result": "generated",
            })
        except Exception as exc:
            processors_run.append({
                "name": "digest",
                "status": "error",
                "error": str(exc),
            })
        state["last_digest"] = now

    # Processor 3: Mode audit
    if t["corrections_exceeded"]:
        try:
            from scripts.lib.audit_modes import audit_all_modes
            from scripts.lib.crux_paths import get_user_paths
            user_paths = get_user_paths(home)
            audit_results = audit_all_modes(modes_dir=user_paths.modes)
            processors_run.append({
                "name": "mode_audit",
                "status": "completed",
                "modes_audited": audit_results.get("total_modes", 0),
            })
        except Exception as exc:
            processors_run.append({
                "name": "mode_audit",
                "status": "error",
                "error": str(exc),
            })
        state["last_mode_audit"] = now

    _save_processor_state(project_dir, state)

    return {
        "success": True,
        "processors_run": processors_run,
        "thresholds": t,
    }


def get_processor_status(project_dir: str) -> dict:
    """Return when each processor last ran."""
    state = _load_processor_state(project_dir)
    return {
        "last_digest": state.get("last_digest", "never"),
        "last_corrections": state.get("last_corrections", "never"),
        "last_mode_audit": state.get("last_mode_audit", "never"),
    }
