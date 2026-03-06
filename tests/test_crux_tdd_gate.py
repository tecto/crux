"""Tests for crux_tdd_gate.py — TDD/BDD enforcement gate engine."""

import json
import os

import pytest

from scripts.lib.crux_tdd_gate import (
    TestSpec,
    TestPhase,
    TddGateState,
    create_test_spec,
    start_tdd_gate,
    record_red_phase,
    record_green_phase,
    check_tdd_gate_status,
    get_coverage_for_gate,
    TDD_PHASE_PLAN,
    TDD_PHASE_RED,
    TDD_PHASE_GREEN,
    TDD_PHASE_COMPLETE,
    TDD_PHASE_SKIPPED,
)


# ---------------------------------------------------------------------------
# TestSpec
# ---------------------------------------------------------------------------

class TestTestSpec:
    def test_create(self):
        spec = TestSpec(
            feature="user_registration",
            components=["UserService", "EmailValidator"],
            test_categories={"unit": ["happy path", "edge cases"]},
            edge_cases=["duplicate email", "weak password"],
            coverage_target=80,
        )
        assert spec.feature == "user_registration"
        assert len(spec.components) == 2
        assert "unit" in spec.test_categories
        assert len(spec.edge_cases) == 2
        assert spec.coverage_target == 80

    def test_to_dict(self):
        spec = TestSpec(
            feature="login",
            components=["AuthService"],
            test_categories={"unit": ["auth flow"]},
            edge_cases=["expired token"],
            coverage_target=90,
        )
        d = spec.to_dict()
        assert d["feature"] == "login"
        assert d["components"] == ["AuthService"]
        assert d["coverage_target"] == 90

    def test_from_dict(self):
        d = {
            "feature": "login",
            "components": ["AuthService"],
            "test_categories": {"unit": ["auth"]},
            "edge_cases": ["expired"],
            "coverage_target": 95,
        }
        spec = TestSpec.from_dict(d)
        assert spec.feature == "login"
        assert spec.coverage_target == 95

    def test_from_dict_defaults(self):
        spec = TestSpec.from_dict({})
        assert spec.feature == ""
        assert spec.components == []
        assert spec.coverage_target == 80

    def test_roundtrip(self):
        spec = TestSpec(
            feature="search",
            components=["SearchEngine"],
            test_categories={"integration": ["api calls"]},
            edge_cases=["empty query"],
            coverage_target=85,
        )
        spec2 = TestSpec.from_dict(spec.to_dict())
        assert spec2.to_dict() == spec.to_dict()


# ---------------------------------------------------------------------------
# TestPhase
# ---------------------------------------------------------------------------

class TestTestPhase:
    def test_create(self):
        phase = TestPhase(
            phase=TDD_PHASE_RED,
            tests_written=5,
            tests_passing=0,
            tests_failing=5,
            test_files=["tests/test_user.py"],
        )
        assert phase.phase == TDD_PHASE_RED
        assert phase.tests_written == 5
        assert phase.tests_passing == 0

    def test_to_dict(self):
        phase = TestPhase(
            phase=TDD_PHASE_GREEN,
            tests_written=5,
            tests_passing=5,
            tests_failing=0,
            test_files=["tests/test_user.py"],
        )
        d = phase.to_dict()
        assert d["phase"] == "green"
        assert d["tests_passing"] == 5

    def test_from_dict(self):
        d = {
            "phase": "red",
            "tests_written": 3,
            "tests_passing": 0,
            "tests_failing": 3,
            "test_files": ["test_a.py"],
        }
        phase = TestPhase.from_dict(d)
        assert phase.phase == "red"
        assert phase.tests_failing == 3

    def test_from_dict_defaults(self):
        phase = TestPhase.from_dict({})
        assert phase.phase == "plan"
        assert phase.tests_written == 0
        assert phase.test_files == []


# ---------------------------------------------------------------------------
# TddGateState
# ---------------------------------------------------------------------------

class TestTddGateState:
    def test_create_default(self):
        state = TddGateState()
        assert state.mode == ""
        assert state.enforcement_level == "standard"
        assert state.spec is None
        assert state.current_phase is None
        assert state.phases == []
        assert state.iteration == 0
        assert state.passed is False

    def test_to_dict(self):
        state = TddGateState(mode="build-py", enforcement_level="strict")
        d = state.to_dict()
        assert d["mode"] == "build-py"
        assert d["enforcement_level"] == "strict"
        assert d["spec"] is None
        assert d["phases"] == []

    def test_to_dict_with_spec(self):
        spec = TestSpec(feature="f", components=[], test_categories={}, edge_cases=[], coverage_target=80)
        state = TddGateState(mode="build-py", spec=spec)
        d = state.to_dict()
        assert d["spec"]["feature"] == "f"

    def test_from_dict(self):
        d = {
            "mode": "build-py",
            "enforcement_level": "relaxed",
            "spec": {"feature": "login", "components": [], "test_categories": {}, "edge_cases": [], "coverage_target": 90},
            "phases": [],
            "iteration": 2,
            "passed": True,
        }
        state = TddGateState.from_dict(d)
        assert state.mode == "build-py"
        assert state.enforcement_level == "relaxed"
        assert state.spec.feature == "login"
        assert state.iteration == 2
        assert state.passed is True

    def test_from_dict_empty(self):
        state = TddGateState.from_dict({})
        assert state.mode == ""
        assert state.spec is None

    def test_roundtrip(self):
        spec = TestSpec(feature="x", components=["A"], test_categories={"unit": ["a"]}, edge_cases=["b"], coverage_target=80)
        phase = TestPhase(phase="red", tests_written=3, tests_passing=0, tests_failing=3, test_files=["t.py"])
        state = TddGateState(
            mode="build-py",
            enforcement_level="strict",
            spec=spec,
            current_phase=phase,
            phases=[phase],
            iteration=1,
            passed=False,
        )
        state2 = TddGateState.from_dict(state.to_dict())
        assert state2.to_dict() == state.to_dict()

    def test_save_and_load(self, tmp_path):
        gate_file = str(tmp_path / "tdd_gate.json")
        state = TddGateState(mode="build-py", enforcement_level="standard")
        state.save(gate_file)

        loaded = TddGateState.load(gate_file)
        assert loaded.mode == "build-py"

    def test_load_missing_returns_default(self, tmp_path):
        gate_file = str(tmp_path / "nonexistent.json")
        loaded = TddGateState.load(gate_file)
        assert loaded.mode == ""

    def test_load_corrupt_returns_default(self, tmp_path):
        gate_file = str(tmp_path / "bad.json")
        with open(gate_file, "w") as f:
            f.write("not json")
        loaded = TddGateState.load(gate_file)
        assert loaded.mode == ""


# ---------------------------------------------------------------------------
# create_test_spec
# ---------------------------------------------------------------------------

class TestCreateTestSpec:
    def test_creates_spec(self):
        spec = create_test_spec(
            feature="registration",
            components=["UserService"],
            edge_cases=["duplicate email"],
            coverage_target=90,
        )
        assert spec.feature == "registration"
        assert spec.coverage_target == 90

    def test_default_coverage(self):
        spec = create_test_spec(feature="f", components=[], edge_cases=[])
        assert spec.coverage_target == 80

    def test_categories_from_components(self):
        spec = create_test_spec(
            feature="search",
            components=["SearchEngine", "QueryParser"],
            edge_cases=[],
        )
        assert "unit" in spec.test_categories
        assert len(spec.test_categories["unit"]) == 2


# ---------------------------------------------------------------------------
# start_tdd_gate
# ---------------------------------------------------------------------------

class TestStartTddGate:
    def test_starts_gate(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        state = start_tdd_gate(
            mode="build-py",
            enforcement_level="standard",
            feature="registration",
            components=["UserService"],
            edge_cases=["dup email"],
            gate_file=gate_file,
        )
        assert state.mode == "build-py"
        assert state.spec.feature == "registration"
        assert state.current_phase.phase == TDD_PHASE_PLAN
        assert state.passed is False
        assert os.path.exists(gate_file)

    def test_skipped_when_off(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        state = start_tdd_gate(
            mode="build-py",
            enforcement_level="off",
            feature="anything",
            components=[],
            edge_cases=[],
            gate_file=gate_file,
        )
        assert state.passed is True
        assert state.current_phase.phase == TDD_PHASE_SKIPPED

    def test_persists_to_file(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py",
            enforcement_level="standard",
            feature="f",
            components=[],
            edge_cases=[],
            gate_file=gate_file,
        )
        loaded = TddGateState.load(gate_file)
        assert loaded.spec.feature == "f"


# ---------------------------------------------------------------------------
# record_red_phase
# ---------------------------------------------------------------------------

class TestRecordRedPhase:
    def test_records_red(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py", enforcement_level="standard",
            feature="f", components=[], edge_cases=[], gate_file=gate_file,
        )
        state = record_red_phase(
            tests_written=5,
            tests_failing=5,
            test_files=["tests/test_f.py"],
            gate_file=gate_file,
        )
        assert state.current_phase.phase == TDD_PHASE_RED
        assert state.current_phase.tests_written == 5
        assert state.current_phase.tests_failing == 5
        assert state.current_phase.tests_passing == 0

    def test_records_to_phases_list(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py", enforcement_level="standard",
            feature="f", components=[], edge_cases=[], gate_file=gate_file,
        )
        state = record_red_phase(
            tests_written=3, tests_failing=3,
            test_files=["t.py"], gate_file=gate_file,
        )
        assert len(state.phases) == 2  # plan + red

    def test_increments_iteration(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py", enforcement_level="standard",
            feature="f", components=[], edge_cases=[], gate_file=gate_file,
        )
        state = record_red_phase(
            tests_written=3, tests_failing=3,
            test_files=["t.py"], gate_file=gate_file,
        )
        assert state.iteration == 1


# ---------------------------------------------------------------------------
# record_green_phase
# ---------------------------------------------------------------------------

class TestRecordGreenPhase:
    def _setup_to_red(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py", enforcement_level="standard",
            feature="f", components=["C"], edge_cases=[], gate_file=gate_file,
        )
        record_red_phase(
            tests_written=5, tests_failing=5,
            test_files=["t.py"], gate_file=gate_file,
        )
        return gate_file

    def test_all_passing_completes(self, tmp_path):
        gate_file = self._setup_to_red(tmp_path)
        state = record_green_phase(
            tests_passing=5, tests_failing=0,
            coverage_percent=90.0, gate_file=gate_file,
        )
        assert state.current_phase.phase == TDD_PHASE_COMPLETE
        assert state.passed is True

    def test_some_failing_stays_green(self, tmp_path):
        gate_file = self._setup_to_red(tmp_path)
        state = record_green_phase(
            tests_passing=3, tests_failing=2,
            coverage_percent=60.0, gate_file=gate_file,
        )
        assert state.current_phase.phase == TDD_PHASE_GREEN
        assert state.passed is False

    def test_low_coverage_in_strict_fails(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py", enforcement_level="strict",
            feature="f", components=["C"], edge_cases=[], gate_file=gate_file,
        )
        record_red_phase(
            tests_written=5, tests_failing=5,
            test_files=["t.py"], gate_file=gate_file,
        )
        state = record_green_phase(
            tests_passing=5, tests_failing=0,
            coverage_percent=80.0, gate_file=gate_file,
        )
        # strict requires 95%
        assert state.passed is False
        assert state.current_phase.phase == TDD_PHASE_GREEN

    def test_high_coverage_in_strict_passes(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py", enforcement_level="strict",
            feature="f", components=["C"], edge_cases=[], gate_file=gate_file,
        )
        record_red_phase(
            tests_written=5, tests_failing=5,
            test_files=["t.py"], gate_file=gate_file,
        )
        state = record_green_phase(
            tests_passing=5, tests_failing=0,
            coverage_percent=96.0, gate_file=gate_file,
        )
        assert state.passed is True

    def test_records_to_phases_list(self, tmp_path):
        gate_file = self._setup_to_red(tmp_path)
        state = record_green_phase(
            tests_passing=5, tests_failing=0,
            coverage_percent=90.0, gate_file=gate_file,
        )
        assert len(state.phases) == 3  # plan + red + green/complete


# ---------------------------------------------------------------------------
# check_tdd_gate_status
# ---------------------------------------------------------------------------

class TestCheckTddGateStatus:
    def test_not_started(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        status = check_tdd_gate_status(gate_file)
        assert status["started"] is False
        assert status["passed"] is False

    def test_in_progress(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py", enforcement_level="standard",
            feature="f", components=[], edge_cases=[], gate_file=gate_file,
        )
        status = check_tdd_gate_status(gate_file)
        assert status["started"] is True
        assert status["passed"] is False
        assert status["current_phase"] == TDD_PHASE_PLAN

    def test_completed(self, tmp_path):
        gate_file = str(tmp_path / "tdd.json")
        start_tdd_gate(
            mode="build-py", enforcement_level="standard",
            feature="f", components=["C"], edge_cases=[], gate_file=gate_file,
        )
        record_red_phase(
            tests_written=3, tests_failing=3,
            test_files=["t.py"], gate_file=gate_file,
        )
        record_green_phase(
            tests_passing=3, tests_failing=0,
            coverage_percent=90.0, gate_file=gate_file,
        )
        status = check_tdd_gate_status(gate_file)
        assert status["passed"] is True
        assert status["current_phase"] == TDD_PHASE_COMPLETE


# ---------------------------------------------------------------------------
# get_coverage_for_gate
# ---------------------------------------------------------------------------

class TestGetCoverageForGate:
    def test_standard_level(self):
        required = get_coverage_for_gate("standard")
        assert required == 80

    def test_strict_level(self):
        required = get_coverage_for_gate("strict")
        assert required == 95

    def test_relaxed_level(self):
        required = get_coverage_for_gate("relaxed")
        assert required == 60

    def test_off_level(self):
        required = get_coverage_for_gate("off")
        assert required == 0

    def test_custom_overrides(self):
        required = get_coverage_for_gate("standard", coverage_minimum=90)
        assert required == 90
