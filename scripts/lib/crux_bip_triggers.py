"""Trigger evaluation for build-in-public draft generation.

Checks commit counts, interaction counts, token counts, high-signal events,
and cooldown gates to decide whether a BIP draft should be generated.
"""

from __future__ import annotations

from dataclasses import dataclass

from scripts.lib.crux_bip import (
    load_config,
    load_state,
    check_cooldown,
)


@dataclass
class TriggerResult:
    should_trigger: bool
    reason: str


def evaluate_triggers(
    bip_dir: str,
    event: str | None = None,
    force: bool = False,
) -> TriggerResult:
    """Evaluate whether a BIP draft should be generated.

    Args:
        bip_dir: Path to .crux/bip/
        event: Optional high-signal event name (e.g. "test_green")
        force: Bypass cooldown and thresholds

    Returns:
        TriggerResult with should_trigger and reason.
    """
    config = load_config(bip_dir)
    state = load_state(bip_dir)

    # Force bypasses everything
    if force:
        return TriggerResult(should_trigger=True, reason="Force bypass")

    # Cooldown gate (hard floor) — checked before any trigger
    cooldown_ok = check_cooldown(bip_dir, cooldown_minutes=config.cooldown_minutes)

    # High-signal event
    if event:
        if event not in config.high_signal_events:
            return TriggerResult(should_trigger=False, reason=f"Unknown event: {event}")
        if not cooldown_ok:
            return TriggerResult(should_trigger=False, reason=f"Event {event} blocked by cooldown")
        return TriggerResult(should_trigger=True, reason=f"High-signal event: {event}")

    # Threshold checks (only if cooldown allows)
    if not cooldown_ok:
        return TriggerResult(should_trigger=False, reason="Cooldown not elapsed")

    # Commit threshold
    if state.commits_since_last_post >= config.commit_threshold:
        return TriggerResult(
            should_trigger=True,
            reason=f"Commit threshold met: {state.commits_since_last_post} >= {config.commit_threshold}",
        )

    # Interaction threshold
    if state.interactions_since_last_post >= config.interaction_threshold:
        return TriggerResult(
            should_trigger=True,
            reason=f"Interaction threshold met: {state.interactions_since_last_post} >= {config.interaction_threshold}",
        )

    # Token threshold
    if state.tokens_since_last_post >= config.token_threshold:
        return TriggerResult(
            should_trigger=True,
            reason=f"Token threshold met: {state.tokens_since_last_post} >= {config.token_threshold}",
        )

    return TriggerResult(should_trigger=False, reason="No trigger threshold met")
