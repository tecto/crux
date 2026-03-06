"""TDD/BDD enforcement gate engine for Crux.

Manages Gate 2 of the enhanced safety pipeline: test specification,
red/green phase tracking, coverage enforcement, and correction loops.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


TDD_PHASE_PLAN = "plan"
TDD_PHASE_RED = "red"
TDD_PHASE_GREEN = "green"
TDD_PHASE_COMPLETE = "complete"
TDD_PHASE_SKIPPED = "skipped"

_COVERAGE_BY_LEVEL = {
    "strict": 95,
    "standard": 80,
    "relaxed": 60,
    "off": 0,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TestSpec:
    feature: str = ""
    components: list[str] = field(default_factory=list)
    test_categories: dict[str, list[str]] = field(default_factory=dict)
    edge_cases: list[str] = field(default_factory=list)
    coverage_target: int = 80

    def to_dict(self) -> dict:
        return {
            "feature": self.feature,
            "components": list(self.components),
            "test_categories": {k: list(v) for k, v in self.test_categories.items()},
            "edge_cases": list(self.edge_cases),
            "coverage_target": self.coverage_target,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TestSpec:
        return cls(
            feature=d.get("feature", ""),
            components=list(d.get("components", [])),
            test_categories={k: list(v) for k, v in d.get("test_categories", {}).items()},
            edge_cases=list(d.get("edge_cases", [])),
            coverage_target=d.get("coverage_target", 80),
        )


@dataclass
class TestPhase:
    phase: str = TDD_PHASE_PLAN
    tests_written: int = 0
    tests_passing: int = 0
    tests_failing: int = 0
    test_files: list[str] = field(default_factory=list)
    coverage_percent: float = 0.0

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "tests_written": self.tests_written,
            "tests_passing": self.tests_passing,
            "tests_failing": self.tests_failing,
            "test_files": list(self.test_files),
            "coverage_percent": self.coverage_percent,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TestPhase:
        return cls(
            phase=d.get("phase", TDD_PHASE_PLAN),
            tests_written=d.get("tests_written", 0),
            tests_passing=d.get("tests_passing", 0),
            tests_failing=d.get("tests_failing", 0),
            test_files=list(d.get("test_files", [])),
            coverage_percent=d.get("coverage_percent", 0.0),
        )


@dataclass
class TddGateState:
    mode: str = ""
    enforcement_level: str = "standard"
    spec: TestSpec | None = None
    current_phase: TestPhase | None = None
    phases: list[TestPhase] = field(default_factory=list)
    iteration: int = 0
    passed: bool = False

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "enforcement_level": self.enforcement_level,
            "spec": self.spec.to_dict() if self.spec else None,
            "current_phase": self.current_phase.to_dict() if self.current_phase else None,
            "phases": [p.to_dict() for p in self.phases],
            "iteration": self.iteration,
            "passed": self.passed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TddGateState:
        spec_data = d.get("spec")
        phase_data = d.get("current_phase")
        return cls(
            mode=d.get("mode", ""),
            enforcement_level=d.get("enforcement_level", "standard"),
            spec=TestSpec.from_dict(spec_data) if spec_data else None,
            current_phase=TestPhase.from_dict(phase_data) if phase_data else None,
            phases=[TestPhase.from_dict(p) for p in d.get("phases", [])],
            iteration=d.get("iteration", 0),
            passed=d.get("passed", False),
        )

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> TddGateState:
        try:
            with open(path) as f:
                return cls.from_dict(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()


# ---------------------------------------------------------------------------
# Gate operations
# ---------------------------------------------------------------------------

def create_test_spec(
    feature: str,
    components: list[str],
    edge_cases: list[str],
    coverage_target: int = 80,
) -> TestSpec:
    """Create a test specification for a feature."""
    test_categories: dict[str, list[str]] = {}
    if components:
        test_categories["unit"] = [f"Test {c}" for c in components]
    return TestSpec(
        feature=feature,
        components=list(components),
        test_categories=test_categories,
        edge_cases=list(edge_cases),
        coverage_target=coverage_target,
    )


def start_tdd_gate(
    mode: str,
    enforcement_level: str,
    feature: str,
    components: list[str],
    edge_cases: list[str],
    gate_file: str,
    coverage_target: int = 80,
) -> TddGateState:
    """Initialize the TDD gate for a feature build."""
    spec = create_test_spec(feature, components, edge_cases, coverage_target)

    if enforcement_level == "off":
        phase = TestPhase(phase=TDD_PHASE_SKIPPED)
        state = TddGateState(
            mode=mode,
            enforcement_level=enforcement_level,
            spec=spec,
            current_phase=phase,
            phases=[phase],
            passed=True,
        )
    else:
        phase = TestPhase(phase=TDD_PHASE_PLAN)
        state = TddGateState(
            mode=mode,
            enforcement_level=enforcement_level,
            spec=spec,
            current_phase=phase,
            phases=[phase],
        )

    state.save(gate_file)
    return state


def record_red_phase(
    tests_written: int,
    tests_failing: int,
    test_files: list[str],
    gate_file: str,
) -> TddGateState:
    """Record that tests have been written and are failing (red phase)."""
    state = TddGateState.load(gate_file)
    phase = TestPhase(
        phase=TDD_PHASE_RED,
        tests_written=tests_written,
        tests_passing=0,
        tests_failing=tests_failing,
        test_files=list(test_files),
    )
    state.current_phase = phase
    state.phases.append(phase)
    state.iteration += 1
    state.save(gate_file)
    return state


def record_green_phase(
    tests_passing: int,
    tests_failing: int,
    coverage_percent: float,
    gate_file: str,
) -> TddGateState:
    """Record test results after implementation (green phase attempt)."""
    state = TddGateState.load(gate_file)

    all_passing = tests_failing == 0
    required_coverage = get_coverage_for_gate(state.enforcement_level)
    meets_coverage = coverage_percent >= required_coverage

    if all_passing and meets_coverage:
        phase_name = TDD_PHASE_COMPLETE
        state.passed = True
    else:
        phase_name = TDD_PHASE_GREEN

    phase = TestPhase(
        phase=phase_name,
        tests_written=tests_passing + tests_failing,
        tests_passing=tests_passing,
        tests_failing=tests_failing,
        coverage_percent=coverage_percent,
    )
    state.current_phase = phase
    state.phases.append(phase)
    state.save(gate_file)
    return state


def check_tdd_gate_status(gate_file: str) -> dict:
    """Check the current status of the TDD gate."""
    state = TddGateState.load(gate_file)

    if not state.mode:
        return {"started": False, "passed": False, "current_phase": None}

    return {
        "started": True,
        "passed": state.passed,
        "current_phase": state.current_phase.phase if state.current_phase else None,
        "iteration": state.iteration,
        "mode": state.mode,
        "enforcement_level": state.enforcement_level,
    }


def get_coverage_for_gate(
    enforcement_level: str,
    coverage_minimum: int | None = None,
) -> int:
    """Get required coverage percentage for a TDD enforcement level."""
    if coverage_minimum is not None:
        return coverage_minimum
    return _COVERAGE_BY_LEVEL.get(enforcement_level, 80)
