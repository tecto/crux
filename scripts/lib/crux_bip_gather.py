"""Content gathering for build-in-public draft generation.

Reads git history, corrections, knowledge, and session state to produce
a BIPContext with all available material for generating shipping updates.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.crux_bip import is_in_history


@dataclass
class BIPContext:
    """All gathered material for generating a BIP draft."""
    commit_messages: list[str] = field(default_factory=list)
    commit_hashes: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    unposted_commits: list[dict] = field(default_factory=list)
    corrections: list[dict] = field(default_factory=list)
    knowledge_entries: list[dict] = field(default_factory=list)
    session_mode: str = ""
    session_tool: str = ""
    working_on: str = ""
    key_decisions: list[str] = field(default_factory=list)

    @property
    def has_material(self) -> bool:
        return bool(
            self.unposted_commits
            or self.corrections
            or self.knowledge_entries
            or self.commit_messages
        )


def _gather_git(project_dir: str, since: str | None = None) -> tuple[list[str], list[str], list[str]]:
    """Gather git history. Returns (messages, hashes, files_changed)."""
    messages: list[str] = []
    hashes: list[str] = []
    files: list[str] = []

    git_args_base = ["git", "log", "--pretty=format:%H|%s"]
    if since:
        git_args_base.extend(["--since", since])
    git_args_base.append("-50")

    try:
        result = subprocess.run(
            git_args_base,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|", 1)
                if len(parts) == 2:
                    hashes.append(parts[0])
                    messages.append(parts[1])

        # Files changed
        files_args = ["git", "log", "--pretty=format:", "--name-only"]
        if since:
            files_args.extend(["--since", since])
        files_args.append("-50")

        result = subprocess.run(
            files_args,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line and line not in files:
                    files.append(line)

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return messages, hashes, files


def _gather_corrections(crux_dir: str, since: str | None = None) -> list[dict]:
    """Read corrections from corrections.jsonl, optionally filtered by since."""
    corrections_file = os.path.join(crux_dir, "corrections", "corrections.jsonl")
    if not os.path.exists(corrections_file):
        return []

    entries: list[dict] = []
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            since_dt = None

    try:
        with open(corrections_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if since_dt and "timestamp" in entry:
                    try:
                        entry_dt = datetime.fromisoformat(entry["timestamp"])
                        if entry_dt.tzinfo is None:
                            entry_dt = entry_dt.replace(tzinfo=timezone.utc)
                        if entry_dt < since_dt:
                            continue
                    except ValueError:
                        pass

                entries.append(entry)
    except OSError:
        pass

    return entries


def _gather_knowledge(crux_dir: str) -> list[dict]:
    """Read knowledge entries from .crux/knowledge/."""
    k_dir = os.path.join(crux_dir, "knowledge")
    if not os.path.isdir(k_dir):
        return []

    entries: list[dict] = []
    for md_file in Path(k_dir).glob("*.md"):
        entries.append({
            "name": md_file.stem,
            "content": md_file.read_text()[:500],
        })
    return entries


def _gather_session(crux_dir: str) -> dict:
    """Read session state."""
    state_path = os.path.join(crux_dir, "sessions", "state.json")
    if not os.path.exists(state_path):
        return {}
    try:
        with open(state_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def gather_content(
    project_dir: str,
    home: str,
    since: str | None = None,
) -> BIPContext:
    """Gather all content sources for BIP draft generation."""
    crux_dir = os.path.join(project_dir, ".crux")
    bip_dir = os.path.join(crux_dir, "bip")

    # Git
    messages, hashes, files = _gather_git(project_dir, since=since)

    # Filter out already-posted commits
    unposted: list[dict] = []
    for h, m in zip(hashes, messages):
        if not is_in_history(bip_dir, f"git:{h}"):
            unposted.append({"hash": h, "message": m})

    # Corrections
    corrections = _gather_corrections(crux_dir, since=since)

    # Knowledge
    knowledge = _gather_knowledge(crux_dir)

    # Session
    session = _gather_session(crux_dir)

    return BIPContext(
        commit_messages=messages,
        commit_hashes=hashes,
        files_changed=files,
        unposted_commits=unposted,
        corrections=corrections,
        knowledge_entries=knowledge,
        session_mode=session.get("active_mode", ""),
        session_tool=session.get("active_tool", ""),
        working_on=session.get("working_on", ""),
        key_decisions=session.get("key_decisions", []),
    )
