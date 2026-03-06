"""Recursive security audit loop engine for Crux.

Manages Gate 3 of the enhanced safety pipeline: multi-category auditing,
finding tracking, convergence detection, and resolution management.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"
SEVERITY_INFO = "info"

BLOCKING_SEVERITIES = {SEVERITY_CRITICAL, SEVERITY_HIGH}

ALL_CATEGORIES = [
    "input_validation",
    "authentication",
    "data_exposure",
    "cryptography",
    "dependencies",
    "infrastructure",
    "business_logic",
]

CONVERGENCE_ACHIEVED = "convergence_achieved"
CONVERGENCE_CONTINUE = "continue"
CONVERGENCE_MAX_ITERATIONS = "max_iterations_reached"
CONVERGENCE_STALLED = "fix_stalled"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SecurityFinding:
    finding_id: str = ""
    category: str = ""
    severity: str = ""
    title: str = ""
    description: str = ""
    file_path: str = ""
    line_range: list[int] = field(default_factory=list)
    remediation: str = ""
    cwe: str = ""
    owasp: str = ""
    resolved: bool = False

    def is_blocking(self) -> bool:
        """Return True if this finding blocks the pipeline."""
        return self.severity in BLOCKING_SEVERITIES and not self.resolved

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_range": list(self.line_range),
            "remediation": self.remediation,
            "cwe": self.cwe,
            "owasp": self.owasp,
            "resolved": self.resolved,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SecurityFinding:
        return cls(
            finding_id=d.get("finding_id", ""),
            category=d.get("category", ""),
            severity=d.get("severity", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            file_path=d.get("file_path", ""),
            line_range=list(d.get("line_range", [])),
            remediation=d.get("remediation", ""),
            cwe=d.get("cwe", ""),
            owasp=d.get("owasp", ""),
            resolved=d.get("resolved", False),
        )


@dataclass
class AuditIteration:
    iteration: int = 0
    findings: list[SecurityFinding] = field(default_factory=list)
    new_finding_count: int = 0
    fixed_count: int = 0

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "findings": [f.to_dict() for f in self.findings],
            "new_finding_count": self.new_finding_count,
            "fixed_count": self.fixed_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> AuditIteration:
        return cls(
            iteration=d.get("iteration", 0),
            findings=[SecurityFinding.from_dict(f) for f in d.get("findings", [])],
            new_finding_count=d.get("new_finding_count", 0),
            fixed_count=d.get("fixed_count", 0),
        )


@dataclass
class SecurityAuditState:
    max_iterations: int = 3
    current_iteration: int = 0
    iterations: list[AuditIteration] = field(default_factory=list)
    convergence_status: str = ""
    categories: list[str] = field(default_factory=lambda: list(ALL_CATEGORIES))
    passed: bool = False

    def to_dict(self) -> dict:
        return {
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "iterations": [it.to_dict() for it in self.iterations],
            "convergence_status": self.convergence_status,
            "categories": list(self.categories),
            "passed": self.passed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SecurityAuditState:
        return cls(
            max_iterations=d.get("max_iterations", 3),
            current_iteration=d.get("current_iteration", 0),
            iterations=[AuditIteration.from_dict(it) for it in d.get("iterations", [])],
            convergence_status=d.get("convergence_status", ""),
            categories=list(d.get("categories", ALL_CATEGORIES)),
            passed=d.get("passed", False),
        )

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> SecurityAuditState:
        try:
            with open(path) as f:
                return cls.from_dict(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()


# ---------------------------------------------------------------------------
# Audit operations
# ---------------------------------------------------------------------------

def start_audit(
    max_iterations: int = 3,
    categories: list[str] | None = None,
    audit_file: str = "",
) -> SecurityAuditState:
    """Initialize a new security audit loop."""
    state = SecurityAuditState(
        max_iterations=max_iterations,
        categories=list(categories) if categories else list(ALL_CATEGORIES),
    )
    if audit_file:
        state.save(audit_file)
    return state


def record_findings(
    findings: list[SecurityFinding],
    audit_file: str,
) -> SecurityAuditState:
    """Record findings from an audit iteration."""
    state = SecurityAuditState.load(audit_file)
    state.current_iteration += 1

    # Determine which findings are new vs seen before
    prev_ids: set[str] = set()
    if state.iterations:
        prev_ids = {f.finding_id for f in state.iterations[-1].findings}

    new_count = sum(1 for f in findings if f.finding_id not in prev_ids)

    iteration = AuditIteration(
        iteration=state.current_iteration,
        findings=list(findings),
        new_finding_count=new_count,
        fixed_count=0,
    )
    state.iterations.append(iteration)
    state.convergence_status = _compute_convergence(state)
    state.save(audit_file)
    return state


def record_fixes(
    fixed_finding_ids: list[str],
    audit_file: str,
) -> SecurityAuditState:
    """Mark findings as resolved in the latest iteration."""
    state = SecurityAuditState.load(audit_file)

    if not state.iterations:
        state.save(audit_file)
        return state

    latest = state.iterations[-1]
    fixed_set = set(fixed_finding_ids)
    for finding in latest.findings:
        if finding.finding_id in fixed_set:
            finding.resolved = True
            latest.fixed_count += 1

    state.save(audit_file)
    return state


def check_convergence(audit_file: str) -> str:
    """Check whether the audit loop has converged."""
    state = SecurityAuditState.load(audit_file)
    return _compute_convergence(state)


def _compute_convergence(state: SecurityAuditState) -> str:
    """Internal convergence logic."""
    if not state.iterations:
        return CONVERGENCE_CONTINUE

    # Check max iterations
    if state.current_iteration >= state.max_iterations:
        return CONVERGENCE_MAX_ITERATIONS

    latest = state.iterations[-1]
    blocking = [f for f in latest.findings if f.is_blocking()]

    # No blocking findings = converged
    if not blocking:
        return CONVERGENCE_ACHIEVED

    # Check if stalled (same blocking findings across last 2 iterations)
    if len(state.iterations) >= 2:
        prev = state.iterations[-2]
        prev_blocking_ids = {f.finding_id for f in prev.findings if f.is_blocking()}
        curr_blocking_ids = {f.finding_id for f in blocking}
        if prev_blocking_ids == curr_blocking_ids:
            return CONVERGENCE_STALLED

    return CONVERGENCE_CONTINUE


def get_blocking_findings(audit_file: str) -> list[SecurityFinding]:
    """Get all unresolved critical/high findings from the latest iteration."""
    state = SecurityAuditState.load(audit_file)
    if not state.iterations:
        return []
    return [f for f in state.iterations[-1].findings if f.is_blocking()]


def resolve_finding(finding_id: str, audit_file: str) -> dict:
    """Resolve a single finding by ID."""
    state = SecurityAuditState.load(audit_file)

    if not state.iterations:
        return {"resolved": False, "finding_id": finding_id, "error": "No iterations"}

    for finding in state.iterations[-1].findings:
        if finding.finding_id == finding_id:
            finding.resolved = True
            state.save(audit_file)
            return {"resolved": True, "finding_id": finding_id}

    return {"resolved": False, "finding_id": finding_id, "error": "Finding not found"}


def audit_summary(audit_file: str) -> dict:
    """Generate a summary of the audit state."""
    state = SecurityAuditState.load(audit_file)

    if not state.iterations:
        return {
            "total_iterations": 0,
            "total_findings": 0,
            "blocking_count": 0,
            "by_severity": {},
            "convergence": _compute_convergence(state),
            "passed": state.passed,
        }

    latest = state.iterations[-1]
    by_severity: dict[str, int] = {}
    for f in latest.findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1

    blocking = [f for f in latest.findings if f.is_blocking()]

    return {
        "total_iterations": state.current_iteration,
        "total_findings": len(latest.findings),
        "blocking_count": len(blocking),
        "by_severity": by_severity,
        "convergence": _compute_convergence(state),
        "passed": state.passed,
    }
