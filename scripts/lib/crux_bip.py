"""Build-in-public state, config, and history management.

Manages `.crux/bip/` — the infrastructure for continuous shipping updates.
Tracks post history, cooldowns, trigger counters, and Typefully config.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_HIGH_SIGNAL_EVENTS = [
    "test_green",
    "new_mcp_tool",
    "git_tag",
    "pr_merge",
    "crux_switch",
    "crux_adopt",
    "knowledge_promoted",
    "correction_detected",
]

DEFAULT_NEVER_WORDS = [
    "Revolutionary",
    "Game-changing",
    "Excited to announce",
    "I'm thrilled",
    "Delighted to share",
    "Proud to announce",
]


@dataclass
class BIPConfig:
    social_set_id: int = 0
    api_key_path: str = ".crux/bip/typefully.key"
    commit_threshold: int = 4
    token_threshold: int = 50000
    interaction_threshold: int = 30
    cooldown_minutes: int = 15
    target_posts_per_hour: int = 1
    quiet_hours: list[int] | None = None
    high_signal_events: list[str] = field(default_factory=lambda: list(DEFAULT_HIGH_SIGNAL_EVENTS))
    platforms: list[str] = field(default_factory=lambda: ["x"])
    never_words: list[str] = field(default_factory=lambda: list(DEFAULT_NEVER_WORDS))
    voice_style: str = "all lowercase except proper nouns"
    voice_tone: str = "technical, direct, no hype, builder energy"


def save_config(config: BIPConfig, bip_dir: str) -> None:
    os.makedirs(bip_dir, exist_ok=True)
    with open(os.path.join(bip_dir, "config.json"), "w") as f:
        json.dump(asdict(config), f, indent=2)


def load_config(bip_dir: str) -> BIPConfig:
    path = os.path.join(bip_dir, "config.json")
    if not os.path.exists(path):
        return BIPConfig()
    try:
        with open(path) as f:
            data = json.load(f)
        return BIPConfig(**{k: v for k, v in data.items() if k in BIPConfig.__dataclass_fields__})
    except (json.JSONDecodeError, OSError, TypeError):
        return BIPConfig()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class BIPState:
    last_queued_at: str | None = None
    last_queued_id: int | None = None
    commits_since_last_post: int = 0
    tokens_since_last_post: int = 0
    interactions_since_last_post: int = 0
    posts_today: int = 0
    posts_this_hour: int = 0


def save_state(state: BIPState, bip_dir: str) -> None:
    os.makedirs(bip_dir, exist_ok=True)
    with open(os.path.join(bip_dir, "state.json"), "w") as f:
        json.dump(asdict(state), f, indent=2)


def load_state(bip_dir: str) -> BIPState:
    path = os.path.join(bip_dir, "state.json")
    if not os.path.exists(path):
        return BIPState()
    try:
        with open(path) as f:
            data = json.load(f)
        return BIPState(**{k: v for k, v in data.items() if k in BIPState.__dataclass_fields__})
    except (json.JSONDecodeError, OSError, TypeError):
        return BIPState()


def reset_counters(bip_dir: str) -> None:
    state = load_state(bip_dir)
    state.commits_since_last_post = 0
    state.tokens_since_last_post = 0
    state.interactions_since_last_post = 0
    save_state(state, bip_dir)


def increment_counter(bip_dir: str, field_name: str, amount: int = 1) -> None:
    state = load_state(bip_dir)
    current = getattr(state, field_name, 0)
    setattr(state, field_name, current + amount)
    save_state(state, bip_dir)


# ---------------------------------------------------------------------------
# Cooldown
# ---------------------------------------------------------------------------

def check_cooldown(bip_dir: str, cooldown_minutes: int = 15) -> bool:
    """Return True if cooldown has elapsed (ok to post)."""
    state = load_state(bip_dir)
    if not state.last_queued_at:
        return True
    try:
        last = datetime.fromisoformat(state.last_queued_at)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - last) >= timedelta(minutes=cooldown_minutes)
    except (ValueError, TypeError):
        return True


# ---------------------------------------------------------------------------
# History / dedup
# ---------------------------------------------------------------------------

def load_history(bip_dir: str) -> list[dict]:
    path = os.path.join(bip_dir, "history.jsonl")
    if not os.path.exists(path):
        return []
    entries: list[dict] = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries


def record_history(bip_dir: str, source_key: str, draft_preview: str) -> None:
    os.makedirs(bip_dir, exist_ok=True)
    entry = {
        "source_key": source_key,
        "draft_preview": draft_preview[:200],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(bip_dir, "history.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def is_in_history(bip_dir: str, source_key: str) -> bool:
    history = load_history(bip_dir)
    return any(h.get("source_key") == source_key for h in history)
