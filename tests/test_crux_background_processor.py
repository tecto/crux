"""Tests for crux_background_processor.py — threshold-triggered continuous learning."""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from scripts.lib.crux_init import init_project, init_user
from scripts.lib.crux_background_processor import (
    ProcessorConfig,
    check_thresholds,
    should_process,
    run_processors,
    get_processor_status,
)


@pytest.fixture
def env(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    init_user(home=str(home))
    init_project(project_dir=str(project))
    return {"home": str(home), "project": str(project)}


def _write_corrections(project_dir, count):
    corr_dir = os.path.join(project_dir, ".crux", "corrections")
    os.makedirs(corr_dir, exist_ok=True)
    with open(os.path.join(corr_dir, "corrections.jsonl"), "w") as f:
        for i in range(count):
            f.write(json.dumps({
                "original": f"bad{i}", "corrected": f"good{i}",
                "category": "style", "mode": "build-py",
                "timestamp": "2026-03-06T01:00:00Z",
            }) + "\n")


def _write_interactions(project_dir, count):
    log_dir = os.path.join(project_dir, ".crux", "analytics", "interactions")
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(os.path.join(log_dir, f"{today}.jsonl"), "w") as f:
        for i in range(count):
            f.write(json.dumps({
                "timestamp": "2026-03-06T01:00:00Z",
                "tool_name": "Bash", "tool_input": {},
            }) + "\n")


def _set_last_digest(project_dir, hours_ago):
    state_dir = os.path.join(project_dir, ".crux", "analytics")
    os.makedirs(state_dir, exist_ok=True)
    ts = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = {"last_digest": ts, "last_corrections": ts, "last_mode_audit": ts}
    with open(os.path.join(state_dir, "processor_state.json"), "w") as f:
        json.dump(state, f)


# ---------------------------------------------------------------------------
# ProcessorConfig
# ---------------------------------------------------------------------------

class TestProcessorConfig:
    def test_default_values(self):
        cfg = ProcessorConfig()
        assert cfg.correction_queue_size == 10
        assert cfg.interaction_count == 50
        assert cfg.digest_age_hours == 24

    def test_custom_values(self):
        cfg = ProcessorConfig(correction_queue_size=5, interaction_count=20, digest_age_hours=12)
        assert cfg.correction_queue_size == 5


# ---------------------------------------------------------------------------
# check_thresholds
# ---------------------------------------------------------------------------

class TestCheckThresholds:
    def test_no_data_nothing_exceeded(self, env):
        result = check_thresholds(env["project"], env["home"])
        assert result["corrections_exceeded"] is False
        assert result["interactions_exceeded"] is False
        assert result["digest_stale"] is False

    def test_corrections_exceeded(self, env):
        _write_corrections(env["project"], 15)
        result = check_thresholds(env["project"], env["home"])
        assert result["corrections_exceeded"] is True
        assert result["correction_count"] == 15

    def test_corrections_below_threshold(self, env):
        _write_corrections(env["project"], 5)
        result = check_thresholds(env["project"], env["home"])
        assert result["corrections_exceeded"] is False

    def test_interactions_exceeded(self, env):
        _write_interactions(env["project"], 60)
        result = check_thresholds(env["project"], env["home"])
        assert result["interactions_exceeded"] is True

    def test_interactions_below_threshold(self, env):
        _write_interactions(env["project"], 30)
        result = check_thresholds(env["project"], env["home"])
        assert result["interactions_exceeded"] is False

    def test_digest_stale(self, env):
        _set_last_digest(env["project"], 30)
        _write_interactions(env["project"], 5)  # need some data
        result = check_thresholds(env["project"], env["home"])
        assert result["digest_stale"] is True

    def test_digest_fresh(self, env):
        _set_last_digest(env["project"], 2)
        result = check_thresholds(env["project"], env["home"])
        assert result["digest_stale"] is False

    def test_custom_config(self, env):
        _write_corrections(env["project"], 3)
        cfg = ProcessorConfig(correction_queue_size=2)
        result = check_thresholds(env["project"], env["home"], config=cfg)
        assert result["corrections_exceeded"] is True


# ---------------------------------------------------------------------------
# should_process
# ---------------------------------------------------------------------------

class TestShouldProcess:
    def test_false_when_no_data(self, env):
        assert should_process(env["project"], env["home"]) is False

    def test_true_when_corrections_exceeded(self, env):
        _write_corrections(env["project"], 15)
        assert should_process(env["project"], env["home"]) is True

    def test_true_when_interactions_exceeded(self, env):
        _write_interactions(env["project"], 60)
        assert should_process(env["project"], env["home"]) is True


# ---------------------------------------------------------------------------
# run_processors
# ---------------------------------------------------------------------------

class TestRunProcessors:
    def test_runs_and_returns_result(self, env):
        _write_corrections(env["project"], 15)
        _write_interactions(env["project"], 60)
        result = run_processors(env["project"], env["home"])
        assert result["success"] is True
        assert isinstance(result["processors_run"], list)
        assert len(result["processors_run"]) > 0

    def test_updates_processor_state(self, env):
        _write_corrections(env["project"], 15)
        run_processors(env["project"], env["home"])
        state_path = os.path.join(env["project"], ".crux", "analytics", "processor_state.json")
        assert os.path.exists(state_path)
        with open(state_path) as f:
            state = json.load(f)
        assert "last_corrections" in state

    def test_skips_when_nothing_due(self, env):
        result = run_processors(env["project"], env["home"])
        assert result["success"] is True
        assert len(result["processors_run"]) == 0

    def test_idempotent(self, env):
        _write_corrections(env["project"], 15)
        run_processors(env["project"], env["home"])
        # Running again immediately should find nothing to do since state was updated
        result2 = run_processors(env["project"], env["home"])
        assert result2["success"] is True

    def test_runs_digest_when_stale(self, env):
        _set_last_digest(env["project"], 30)
        _write_interactions(env["project"], 10)
        result = run_processors(env["project"], env["home"])
        assert "digest" in [p["name"] for p in result["processors_run"]]


# ---------------------------------------------------------------------------
# get_processor_status
# ---------------------------------------------------------------------------

class TestGetProcessorStatus:
    def test_returns_status_dict(self, env):
        status = get_processor_status(env["project"])
        assert isinstance(status, dict)
        assert "last_digest" in status
        assert "last_corrections" in status
        assert "last_mode_audit" in status

    def test_returns_never_when_no_state(self, env):
        status = get_processor_status(env["project"])
        assert status["last_digest"] == "never"

    def test_returns_timestamps_after_run(self, env):
        _write_corrections(env["project"], 15)
        run_processors(env["project"], env["home"])
        status = get_processor_status(env["project"])
        assert status["last_corrections"] != "never"


class TestEdgeCases:
    def test_bad_timestamp_in_processor_state(self, env):
        """_hours_since should return inf for bad timestamps."""
        state_dir = os.path.join(env["project"], ".crux", "analytics")
        os.makedirs(state_dir, exist_ok=True)
        state = {"last_digest": "not-a-timestamp"}
        with open(os.path.join(state_dir, "processor_state.json"), "w") as f:
            json.dump(state, f)
        _write_interactions(env["project"], 5)  # need data for digest_stale
        result = check_thresholds(env["project"], env["home"])
        # Bad timestamp = treated as infinitely old = stale
        assert result["digest_stale"] is True

    def test_correction_extraction_error_handled(self, env, monkeypatch):
        _write_corrections(env["project"], 15)
        import scripts.lib.crux_background_processor as bp
        original_check = bp.check_thresholds

        # Monkeypatch extract_corrections to raise
        import scripts.lib.extract_corrections as ec
        monkeypatch.setattr(ec, "extract_corrections", lambda **kw: (_ for _ in ()).throw(RuntimeError("boom")))

        result = run_processors(env["project"], env["home"])
        corr = next(p for p in result["processors_run"] if p["name"] == "corrections")
        assert corr["status"] == "error"
        assert "boom" in corr["error"]

    def test_mode_audit_error_handled(self, env, monkeypatch):
        _write_corrections(env["project"], 15)
        import scripts.lib.audit_modes as am
        monkeypatch.setattr(am, "audit_all_modes", lambda **kw: (_ for _ in ()).throw(RuntimeError("audit fail")))

        result = run_processors(env["project"], env["home"])
        audit = next(p for p in result["processors_run"] if p["name"] == "mode_audit")
        assert audit["status"] == "error"

    def test_digest_error_handled(self, env, monkeypatch):
        _write_interactions(env["project"], 60)
        import scripts.lib.generate_digest as gd
        monkeypatch.setattr(gd, "generate_digest", lambda **kw: (_ for _ in ()).throw(RuntimeError("digest fail")))

        result = run_processors(env["project"], env["home"])
        digest = next(p for p in result["processors_run"] if p["name"] == "digest")
        assert digest["status"] == "error"
