"""Tests for crux_bip_triggers.py — trigger evaluation for build-in-public."""

import json
import os
from datetime import datetime, timezone, timedelta

import pytest

from scripts.lib.crux_bip import BIPConfig, BIPState, save_config, save_state
from scripts.lib.crux_bip_triggers import evaluate_triggers, TriggerResult


@pytest.fixture
def bip_dir(tmp_path):
    d = tmp_path / ".crux" / "bip"
    d.mkdir(parents=True)
    (d / "drafts").mkdir()
    save_config(BIPConfig(), str(d))
    save_state(BIPState(), str(d))
    return str(d)


# ---------------------------------------------------------------------------
# Commit threshold
# ---------------------------------------------------------------------------

class TestCommitThreshold:
    def test_triggers_when_threshold_met(self, bip_dir):
        save_state(BIPState(commits_since_last_post=5), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is True
        assert "commit" in result.reason.lower()

    def test_does_not_trigger_below_threshold(self, bip_dir):
        save_state(BIPState(commits_since_last_post=2), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is False

    def test_respects_custom_threshold(self, bip_dir):
        save_config(BIPConfig(commit_threshold=10), bip_dir)
        save_state(BIPState(commits_since_last_post=8), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is False

        save_state(BIPState(commits_since_last_post=10), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is True


# ---------------------------------------------------------------------------
# Interaction threshold
# ---------------------------------------------------------------------------

class TestInteractionThreshold:
    def test_triggers_on_interaction_count(self, bip_dir):
        save_state(BIPState(interactions_since_last_post=35), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is True
        assert "interaction" in result.reason.lower()

    def test_does_not_trigger_below_interaction_threshold(self, bip_dir):
        save_state(BIPState(interactions_since_last_post=10), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is False


# ---------------------------------------------------------------------------
# Token threshold
# ---------------------------------------------------------------------------

class TestTokenThreshold:
    def test_triggers_on_token_count(self, bip_dir):
        save_state(BIPState(tokens_since_last_post=60000), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is True
        assert "token" in result.reason.lower()

    def test_does_not_trigger_below_token_threshold(self, bip_dir):
        save_state(BIPState(tokens_since_last_post=10000), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is False


# ---------------------------------------------------------------------------
# Cooldown gate
# ---------------------------------------------------------------------------

class TestCooldownGate:
    def test_cooldown_blocks_trigger(self, bip_dir):
        now = datetime.now(timezone.utc).isoformat()
        save_state(BIPState(
            commits_since_last_post=10,
            last_queued_at=now,
        ), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is False
        assert "cooldown" in result.reason.lower()

    def test_cooldown_elapsed_allows_trigger(self, bip_dir):
        old = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
        save_state(BIPState(
            commits_since_last_post=10,
            last_queued_at=old,
        ), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is True

    def test_no_previous_post_no_cooldown(self, bip_dir):
        save_state(BIPState(commits_since_last_post=5), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is True


# ---------------------------------------------------------------------------
# Force bypass
# ---------------------------------------------------------------------------

class TestForceBypass:
    def test_force_bypasses_cooldown(self, bip_dir):
        now = datetime.now(timezone.utc).isoformat()
        save_state(BIPState(
            commits_since_last_post=10,
            last_queued_at=now,
        ), bip_dir)
        result = evaluate_triggers(bip_dir, force=True)
        assert result.should_trigger is True
        assert "force" in result.reason.lower()

    def test_force_bypasses_thresholds(self, bip_dir):
        save_state(BIPState(commits_since_last_post=0), bip_dir)
        result = evaluate_triggers(bip_dir, force=True)
        assert result.should_trigger is True


# ---------------------------------------------------------------------------
# High-signal events
# ---------------------------------------------------------------------------

class TestHighSignalEvents:
    def test_event_triggers(self, bip_dir):
        result = evaluate_triggers(bip_dir, event="test_green")
        assert result.should_trigger is True
        assert "test_green" in result.reason

    def test_unknown_event_does_not_trigger(self, bip_dir):
        result = evaluate_triggers(bip_dir, event="unknown_event")
        assert result.should_trigger is False

    def test_event_blocked_by_cooldown(self, bip_dir):
        now = datetime.now(timezone.utc).isoformat()
        save_state(BIPState(last_queued_at=now), bip_dir)
        result = evaluate_triggers(bip_dir, event="test_green")
        assert result.should_trigger is False

    def test_event_with_force_bypasses_cooldown(self, bip_dir):
        now = datetime.now(timezone.utc).isoformat()
        save_state(BIPState(last_queued_at=now), bip_dir)
        result = evaluate_triggers(bip_dir, event="test_green", force=True)
        assert result.should_trigger is True


# ---------------------------------------------------------------------------
# Multiple triggers
# ---------------------------------------------------------------------------

class TestMultipleTriggers:
    def test_first_matching_trigger_wins(self, bip_dir):
        save_state(BIPState(
            commits_since_last_post=10,
            interactions_since_last_post=50,
        ), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is True
        # Should mention commit (checked first)
        assert "commit" in result.reason.lower()

    def test_no_triggers_met(self, bip_dir):
        save_state(BIPState(), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert result.should_trigger is False
        assert "no trigger" in result.reason.lower()


# ---------------------------------------------------------------------------
# TriggerResult
# ---------------------------------------------------------------------------

class TestTriggerResult:
    def test_result_fields(self, bip_dir):
        save_state(BIPState(commits_since_last_post=5), bip_dir)
        result = evaluate_triggers(bip_dir)
        assert isinstance(result, TriggerResult)
        assert isinstance(result.should_trigger, bool)
        assert isinstance(result.reason, str)
