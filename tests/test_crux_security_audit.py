"""Tests for crux_security_audit.py — recursive security audit loop engine."""

import json
import os

import pytest

from scripts.lib.crux_security_audit import (
    SecurityFinding,
    AuditIteration,
    SecurityAuditState,
    start_audit,
    record_findings,
    record_fixes,
    check_convergence,
    get_blocking_findings,
    resolve_finding,
    audit_summary,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
    SEVERITY_INFO,
    ALL_CATEGORIES,
    CONVERGENCE_ACHIEVED,
    CONVERGENCE_CONTINUE,
    CONVERGENCE_MAX_ITERATIONS,
    CONVERGENCE_STALLED,
)


# ---------------------------------------------------------------------------
# SecurityFinding
# ---------------------------------------------------------------------------

class TestSecurityFinding:
    def test_create(self):
        f = SecurityFinding(
            finding_id="sec-001",
            category="input_validation",
            severity="high",
            title="SQL Injection",
            description="User input concatenated into SQL",
            file_path="app/db.py",
            line_range=[10, 15],
            remediation="Use parameterized queries",
        )
        assert f.finding_id == "sec-001"
        assert f.severity == "high"

    def test_to_dict(self):
        f = SecurityFinding(
            finding_id="sec-001",
            category="input_validation",
            severity="critical",
            title="RCE",
            description="Command injection",
            file_path="app/run.py",
            line_range=[1, 5],
            remediation="Sanitize input",
        )
        d = f.to_dict()
        assert d["finding_id"] == "sec-001"
        assert d["severity"] == "critical"
        assert d["line_range"] == [1, 5]

    def test_from_dict(self):
        d = {
            "finding_id": "sec-002",
            "category": "authentication",
            "severity": "medium",
            "title": "Weak session",
            "description": "Session not invalidated",
            "file_path": "auth.py",
            "line_range": [20, 25],
            "remediation": "Invalidate on logout",
            "cwe": "CWE-613",
            "owasp": "A07:2021",
        }
        f = SecurityFinding.from_dict(d)
        assert f.finding_id == "sec-002"
        assert f.cwe == "CWE-613"
        assert f.owasp == "A07:2021"

    def test_from_dict_defaults(self):
        f = SecurityFinding.from_dict({})
        assert f.finding_id == ""
        assert f.cwe == ""
        assert f.owasp == ""
        assert f.resolved is False

    def test_roundtrip(self):
        f = SecurityFinding(
            finding_id="sec-003",
            category="data_exposure",
            severity="low",
            title="Debug log",
            description="Sensitive data in logs",
            file_path="log.py",
            line_range=[100, 105],
            remediation="Remove from logs",
            cwe="CWE-532",
            owasp="A09:2021",
        )
        f2 = SecurityFinding.from_dict(f.to_dict())
        assert f2.to_dict() == f.to_dict()

    def test_is_blocking_critical(self):
        f = SecurityFinding(
            finding_id="x", category="input_validation",
            severity="critical", title="t", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        assert f.is_blocking() is True

    def test_is_blocking_high(self):
        f = SecurityFinding(
            finding_id="x", category="input_validation",
            severity="high", title="t", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        assert f.is_blocking() is True

    def test_not_blocking_medium(self):
        f = SecurityFinding(
            finding_id="x", category="input_validation",
            severity="medium", title="t", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        assert f.is_blocking() is False

    def test_resolved_not_blocking(self):
        f = SecurityFinding(
            finding_id="x", category="input_validation",
            severity="critical", title="t", description="d",
            file_path="f", line_range=[], remediation="r",
            resolved=True,
        )
        assert f.is_blocking() is False


# ---------------------------------------------------------------------------
# AuditIteration
# ---------------------------------------------------------------------------

class TestAuditIteration:
    def test_create(self):
        it = AuditIteration(
            iteration=1,
            findings=[],
            new_finding_count=0,
            fixed_count=0,
        )
        assert it.iteration == 1
        assert it.findings == []

    def test_to_dict(self):
        finding = SecurityFinding(
            finding_id="s1", category="authentication",
            severity="high", title="t", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        it = AuditIteration(
            iteration=1, findings=[finding],
            new_finding_count=1, fixed_count=0,
        )
        d = it.to_dict()
        assert d["iteration"] == 1
        assert len(d["findings"]) == 1
        assert d["new_finding_count"] == 1

    def test_from_dict(self):
        d = {
            "iteration": 2,
            "findings": [{"finding_id": "s1", "category": "x", "severity": "low",
                         "title": "t", "description": "d", "file_path": "f",
                         "line_range": [], "remediation": "r"}],
            "new_finding_count": 0,
            "fixed_count": 1,
        }
        it = AuditIteration.from_dict(d)
        assert it.iteration == 2
        assert len(it.findings) == 1
        assert it.fixed_count == 1


# ---------------------------------------------------------------------------
# SecurityAuditState
# ---------------------------------------------------------------------------

class TestSecurityAuditState:
    def test_create_default(self):
        state = SecurityAuditState()
        assert state.max_iterations == 3
        assert state.current_iteration == 0
        assert state.iterations == []
        assert state.convergence_status == ""
        assert state.passed is False

    def test_to_dict(self):
        state = SecurityAuditState(max_iterations=5)
        d = state.to_dict()
        assert d["max_iterations"] == 5
        assert d["iterations"] == []

    def test_from_dict(self):
        d = {
            "max_iterations": 2,
            "current_iteration": 1,
            "iterations": [],
            "convergence_status": "continue",
            "categories": ["input_validation"],
            "passed": False,
        }
        state = SecurityAuditState.from_dict(d)
        assert state.max_iterations == 2
        assert state.categories == ["input_validation"]

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "audit.json")
        state = SecurityAuditState(max_iterations=5)
        state.save(path)
        loaded = SecurityAuditState.load(path)
        assert loaded.max_iterations == 5

    def test_load_missing_returns_default(self, tmp_path):
        path = str(tmp_path / "missing.json")
        loaded = SecurityAuditState.load(path)
        assert loaded.max_iterations == 3

    def test_load_corrupt_returns_default(self, tmp_path):
        path = str(tmp_path / "bad.json")
        with open(path, "w") as f:
            f.write("{bad json")
        loaded = SecurityAuditState.load(path)
        assert loaded.max_iterations == 3

    def test_roundtrip(self):
        state = SecurityAuditState(
            max_iterations=5,
            categories=["input_validation", "authentication"],
        )
        state2 = SecurityAuditState.from_dict(state.to_dict())
        assert state2.to_dict() == state.to_dict()


# ---------------------------------------------------------------------------
# start_audit
# ---------------------------------------------------------------------------

class TestStartAudit:
    def test_starts_audit(self, tmp_path):
        path = str(tmp_path / "audit.json")
        state = start_audit(
            max_iterations=3,
            categories=["input_validation", "authentication"],
            audit_file=path,
        )
        assert state.max_iterations == 3
        assert state.current_iteration == 0
        assert len(state.categories) == 2
        assert os.path.exists(path)

    def test_default_categories(self, tmp_path):
        path = str(tmp_path / "audit.json")
        state = start_audit(audit_file=path)
        assert state.categories == list(ALL_CATEGORIES)


# ---------------------------------------------------------------------------
# record_findings
# ---------------------------------------------------------------------------

class TestRecordFindings:
    def test_records_first_iteration(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        findings = [
            SecurityFinding(
                finding_id="sec-001", category="input_validation",
                severity="high", title="SQLi", description="d",
                file_path="f", line_range=[], remediation="r",
            ),
            SecurityFinding(
                finding_id="sec-002", category="authentication",
                severity="medium", title="Weak auth", description="d",
                file_path="f", line_range=[], remediation="r",
            ),
        ]
        state = record_findings(findings, audit_file=path)
        assert state.current_iteration == 1
        assert len(state.iterations) == 1
        assert state.iterations[0].new_finding_count == 2

    def test_records_second_iteration(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)

        # Second iteration — same finding persists
        f1_again = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        state = record_findings([f1_again], audit_file=path)
        assert state.current_iteration == 2
        assert len(state.iterations) == 2
        assert state.iterations[1].new_finding_count == 0  # not new


# ---------------------------------------------------------------------------
# record_fixes
# ---------------------------------------------------------------------------

class TestRecordFixes:
    def test_marks_resolved(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)

        state = record_fixes(["sec-001"], audit_file=path)
        latest = state.iterations[-1]
        resolved = [f for f in latest.findings if f.resolved]
        assert len(resolved) == 1

    def test_unknown_finding_ignored(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)
        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)
        state = record_fixes(["nonexistent"], audit_file=path)
        resolved = [f for f in state.iterations[-1].findings if f.resolved]
        assert len(resolved) == 0

    def test_no_iterations_noop(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)
        state = record_fixes(["sec-001"], audit_file=path)
        assert state.iterations == []


# ---------------------------------------------------------------------------
# check_convergence
# ---------------------------------------------------------------------------

class TestCheckConvergence:
    def test_no_iterations_returns_continue(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)
        result = check_convergence(audit_file=path)
        assert result == CONVERGENCE_CONTINUE

    def test_no_blocking_findings_converged(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="low", title="Minor", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)
        result = check_convergence(audit_file=path)
        assert result == CONVERGENCE_ACHIEVED

    def test_blocking_findings_continue(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="critical", title="RCE", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)
        result = check_convergence(audit_file=path)
        assert result == CONVERGENCE_CONTINUE

    def test_max_iterations_reached(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(max_iterations=2, audit_file=path)

        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="critical", title="RCE", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)
        record_findings([f1], audit_file=path)
        result = check_convergence(audit_file=path)
        assert result == CONVERGENCE_MAX_ITERATIONS

    def test_stalled_same_findings(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(max_iterations=5, audit_file=path)

        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)
        record_findings([f1], audit_file=path)
        # Same blocking finding in both iterations = stalled
        result = check_convergence(audit_file=path)
        assert result == CONVERGENCE_STALLED

    def test_zero_new_findings_converged(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)
        record_fixes(["sec-001"], audit_file=path)

        f1_resolved = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
            resolved=True,
        )
        record_findings([f1_resolved], audit_file=path)
        result = check_convergence(audit_file=path)
        assert result == CONVERGENCE_ACHIEVED


# ---------------------------------------------------------------------------
# get_blocking_findings
# ---------------------------------------------------------------------------

class TestGetBlockingFindings:
    def test_returns_critical_and_high(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        findings = [
            SecurityFinding(finding_id="s1", category="x", severity="critical",
                          title="t", description="d", file_path="f",
                          line_range=[], remediation="r"),
            SecurityFinding(finding_id="s2", category="x", severity="high",
                          title="t", description="d", file_path="f",
                          line_range=[], remediation="r"),
            SecurityFinding(finding_id="s3", category="x", severity="medium",
                          title="t", description="d", file_path="f",
                          line_range=[], remediation="r"),
        ]
        record_findings(findings, audit_file=path)
        blocking = get_blocking_findings(audit_file=path)
        assert len(blocking) == 2
        ids = {f.finding_id for f in blocking}
        assert ids == {"s1", "s2"}

    def test_no_iterations_returns_empty(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)
        blocking = get_blocking_findings(audit_file=path)
        assert blocking == []


# ---------------------------------------------------------------------------
# resolve_finding
# ---------------------------------------------------------------------------

class TestResolveFinding:
    def test_resolves_by_id(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)
        result = resolve_finding("sec-001", audit_file=path)
        assert result["resolved"] is True
        assert result["finding_id"] == "sec-001"

    def test_resolve_nonexistent(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)
        f1 = SecurityFinding(
            finding_id="sec-001", category="input_validation",
            severity="high", title="SQLi", description="d",
            file_path="f", line_range=[], remediation="r",
        )
        record_findings([f1], audit_file=path)
        result = resolve_finding("nonexistent", audit_file=path)
        assert result["resolved"] is False

    def test_resolve_no_iterations(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)
        result = resolve_finding("sec-001", audit_file=path)
        assert result["resolved"] is False
        assert "No iterations" in result["error"]


# ---------------------------------------------------------------------------
# audit_summary
# ---------------------------------------------------------------------------

class TestAuditSummary:
    def test_empty_audit(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)
        summary = audit_summary(audit_file=path)
        assert summary["total_iterations"] == 0
        assert summary["total_findings"] == 0
        assert summary["blocking_count"] == 0

    def test_with_findings(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)

        findings = [
            SecurityFinding(finding_id="s1", category="x", severity="critical",
                          title="t", description="d", file_path="f",
                          line_range=[], remediation="r"),
            SecurityFinding(finding_id="s2", category="x", severity="low",
                          title="t", description="d", file_path="f",
                          line_range=[], remediation="r"),
        ]
        record_findings(findings, audit_file=path)
        summary = audit_summary(audit_file=path)
        assert summary["total_iterations"] == 1
        assert summary["total_findings"] == 2
        assert summary["blocking_count"] == 1
        assert summary["by_severity"]["critical"] == 1
        assert summary["by_severity"]["low"] == 1

    def test_convergence_status(self, tmp_path):
        path = str(tmp_path / "audit.json")
        start_audit(audit_file=path)
        f1 = SecurityFinding(finding_id="s1", category="x", severity="low",
                            title="t", description="d", file_path="f",
                            line_range=[], remediation="r")
        record_findings([f1], audit_file=path)
        summary = audit_summary(audit_file=path)
        assert summary["convergence"] == CONVERGENCE_ACHIEVED
