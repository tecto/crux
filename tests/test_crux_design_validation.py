"""Tests for crux_design_validation.py — design validation gate engine."""

import json
import os

import pytest

from scripts.lib.crux_design_validation import (
    ContrastResult,
    ValidationFinding,
    DesignValidationState,
    check_contrast_ratio,
    validate_touch_targets,
    validate_wcag_level,
    start_validation,
    record_validation_findings,
    check_validation_status,
    validation_summary,
    VALIDATION_PASS,
    VALIDATION_FAIL,
    VALIDATION_WARNING,
)


# ---------------------------------------------------------------------------
# ContrastResult
# ---------------------------------------------------------------------------

class TestContrastResult:
    def test_create(self):
        r = ContrastResult(
            foreground="#000000",
            background="#FFFFFF",
            ratio=21.0,
            passes_aa=True,
            passes_aaa=True,
        )
        assert r.ratio == 21.0
        assert r.passes_aa is True

    def test_to_dict(self):
        r = ContrastResult(
            foreground="#333",
            background="#FFF",
            ratio=12.6,
            passes_aa=True,
            passes_aaa=True,
        )
        d = r.to_dict()
        assert d["ratio"] == 12.6

    def test_from_dict(self):
        d = {"foreground": "#000", "background": "#FFF", "ratio": 21.0,
             "passes_aa": True, "passes_aaa": True}
        r = ContrastResult.from_dict(d)
        assert r.ratio == 21.0

    def test_from_dict_defaults(self):
        r = ContrastResult.from_dict({})
        assert r.ratio == 0.0
        assert r.passes_aa is False


# ---------------------------------------------------------------------------
# ValidationFinding
# ---------------------------------------------------------------------------

class TestValidationFinding:
    def test_create(self):
        f = ValidationFinding(
            finding_id="dv-001",
            category="wcag",
            severity="critical",
            title="Insufficient contrast",
            description="Text contrast 2.1:1 below 4.5:1",
            element="LoginButton",
            remediation="Darken text color",
        )
        assert f.finding_id == "dv-001"
        assert f.severity == "critical"

    def test_to_dict(self):
        f = ValidationFinding(
            finding_id="dv-002",
            category="touch_target",
            severity="high",
            title="Small button",
            description="32x32px below 44x44px minimum",
            element="CloseBtn",
            remediation="Increase to 44px",
        )
        d = f.to_dict()
        assert d["category"] == "touch_target"

    def test_from_dict(self):
        d = {
            "finding_id": "dv-003",
            "category": "brand",
            "severity": "medium",
            "title": "Wrong color",
            "description": "Uses #blue instead of brand blue",
            "element": "Header",
            "remediation": "Use brand color",
        }
        f = ValidationFinding.from_dict(d)
        assert f.category == "brand"

    def test_from_dict_defaults(self):
        f = ValidationFinding.from_dict({})
        assert f.finding_id == ""
        assert f.resolved is False

    def test_is_blocking(self):
        f = ValidationFinding(
            finding_id="x", category="wcag", severity="critical",
            title="t", description="d", element="e", remediation="r",
        )
        assert f.is_blocking() is True

    def test_medium_not_blocking(self):
        f = ValidationFinding(
            finding_id="x", category="wcag", severity="medium",
            title="t", description="d", element="e", remediation="r",
        )
        assert f.is_blocking() is False

    def test_resolved_not_blocking(self):
        f = ValidationFinding(
            finding_id="x", category="wcag", severity="critical",
            title="t", description="d", element="e", remediation="r",
            resolved=True,
        )
        assert f.is_blocking() is False


# ---------------------------------------------------------------------------
# DesignValidationState
# ---------------------------------------------------------------------------

class TestDesignValidationState:
    def test_defaults(self):
        state = DesignValidationState()
        assert state.wcag_level == "AA"
        assert state.findings == []
        assert state.passed is False

    def test_to_dict(self):
        state = DesignValidationState(wcag_level="AAA")
        d = state.to_dict()
        assert d["wcag_level"] == "AAA"

    def test_from_dict(self):
        d = {"wcag_level": "A", "findings": [], "passed": True,
             "check_brand": True, "check_handoff": True}
        state = DesignValidationState.from_dict(d)
        assert state.wcag_level == "A"
        assert state.passed is True

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "dv.json")
        state = DesignValidationState(wcag_level="AAA")
        state.save(path)
        loaded = DesignValidationState.load(path)
        assert loaded.wcag_level == "AAA"

    def test_load_missing(self, tmp_path):
        path = str(tmp_path / "missing.json")
        loaded = DesignValidationState.load(path)
        assert loaded.wcag_level == "AA"

    def test_load_corrupt(self, tmp_path):
        path = str(tmp_path / "bad.json")
        with open(path, "w") as f:
            f.write("bad")
        loaded = DesignValidationState.load(path)
        assert loaded.wcag_level == "AA"

    def test_roundtrip(self):
        state = DesignValidationState(
            wcag_level="AAA",
            check_brand=False,
        )
        s2 = DesignValidationState.from_dict(state.to_dict())
        assert s2.to_dict() == state.to_dict()


# ---------------------------------------------------------------------------
# check_contrast_ratio
# ---------------------------------------------------------------------------

class TestCheckContrastRatio:
    def test_black_on_white(self):
        result = check_contrast_ratio("#000000", "#FFFFFF")
        assert result.ratio == 21.0
        assert result.passes_aa is True
        assert result.passes_aaa is True

    def test_white_on_white(self):
        result = check_contrast_ratio("#FFFFFF", "#FFFFFF")
        assert result.ratio == 1.0
        assert result.passes_aa is False
        assert result.passes_aaa is False

    def test_medium_contrast(self):
        result = check_contrast_ratio("#767676", "#FFFFFF")
        assert result.passes_aa is True
        assert result.passes_aaa is False

    def test_shorthand_hex(self):
        result = check_contrast_ratio("#000", "#FFF")
        assert result.ratio == 21.0


# ---------------------------------------------------------------------------
# validate_touch_targets
# ---------------------------------------------------------------------------

class TestValidateTouchTargets:
    def test_valid_targets(self):
        elements = {"Button": (48, 48), "Link": (44, 44)}
        findings = validate_touch_targets(elements)
        assert len(findings) == 0

    def test_small_targets(self):
        elements = {"SmallBtn": (32, 32)}
        findings = validate_touch_targets(elements)
        assert len(findings) == 1
        assert findings[0].element == "SmallBtn"
        assert findings[0].severity == "high"

    def test_mixed_targets(self):
        elements = {"Good": (48, 48), "Bad": (30, 20)}
        findings = validate_touch_targets(elements)
        assert len(findings) == 1

    def test_empty_elements(self):
        findings = validate_touch_targets({})
        assert findings == []

    def test_minimum_boundary(self):
        elements = {"Exact": (44, 44)}
        findings = validate_touch_targets(elements)
        assert len(findings) == 0

    def test_one_dimension_small(self):
        elements = {"Narrow": (44, 30)}
        findings = validate_touch_targets(elements)
        assert len(findings) == 1


# ---------------------------------------------------------------------------
# validate_wcag_level
# ---------------------------------------------------------------------------

class TestValidateWcagLevel:
    def test_aa_with_sufficient_contrast(self):
        contrast_results = [
            ContrastResult(foreground="#000", background="#FFF",
                          ratio=21.0, passes_aa=True, passes_aaa=True),
        ]
        findings = validate_wcag_level("AA", contrast_results)
        assert len(findings) == 0

    def test_aa_with_insufficient_contrast(self):
        contrast_results = [
            ContrastResult(foreground="#CCC", background="#FFF",
                          ratio=1.6, passes_aa=False, passes_aaa=False),
        ]
        findings = validate_wcag_level("AA", contrast_results)
        assert len(findings) == 1
        assert findings[0].severity == "critical"

    def test_aaa_with_aa_only(self):
        contrast_results = [
            ContrastResult(foreground="#767676", background="#FFF",
                          ratio=4.54, passes_aa=True, passes_aaa=False),
        ]
        findings = validate_wcag_level("AAA", contrast_results)
        assert len(findings) == 1
        assert findings[0].severity == "critical"

    def test_empty_results(self):
        findings = validate_wcag_level("AA", [])
        assert findings == []


# ---------------------------------------------------------------------------
# start_validation
# ---------------------------------------------------------------------------

class TestStartValidation:
    def test_starts(self, tmp_path):
        path = str(tmp_path / "dv.json")
        state = start_validation(wcag_level="AA", validation_file=path)
        assert state.wcag_level == "AA"
        assert os.path.exists(path)

    def test_custom_options(self, tmp_path):
        path = str(tmp_path / "dv.json")
        state = start_validation(
            wcag_level="AAA",
            check_brand=False,
            check_handoff=False,
            validation_file=path,
        )
        assert state.wcag_level == "AAA"
        assert state.check_brand is False


# ---------------------------------------------------------------------------
# record_validation_findings
# ---------------------------------------------------------------------------

class TestRecordValidationFindings:
    def test_records(self, tmp_path):
        path = str(tmp_path / "dv.json")
        start_validation(validation_file=path)
        findings = [
            ValidationFinding(
                finding_id="dv-001", category="wcag", severity="critical",
                title="Low contrast", description="d", element="e", remediation="r",
            ),
        ]
        state = record_validation_findings(findings, validation_file=path)
        assert len(state.findings) == 1
        assert state.passed is False

    def test_passes_with_no_blocking(self, tmp_path):
        path = str(tmp_path / "dv.json")
        start_validation(validation_file=path)
        findings = [
            ValidationFinding(
                finding_id="dv-001", category="brand", severity="low",
                title="Minor", description="d", element="e", remediation="r",
            ),
        ]
        state = record_validation_findings(findings, validation_file=path)
        assert state.passed is True

    def test_empty_findings_passes(self, tmp_path):
        path = str(tmp_path / "dv.json")
        start_validation(validation_file=path)
        state = record_validation_findings([], validation_file=path)
        assert state.passed is True


# ---------------------------------------------------------------------------
# check_validation_status
# ---------------------------------------------------------------------------

class TestCheckValidationStatus:
    def test_not_started(self, tmp_path):
        path = str(tmp_path / "missing.json")
        status = check_validation_status(path)
        assert status["started"] is False

    def test_in_progress(self, tmp_path):
        path = str(tmp_path / "dv.json")
        start_validation(validation_file=path)
        status = check_validation_status(path)
        assert status["started"] is True
        assert status["passed"] is False

    def test_passed(self, tmp_path):
        path = str(tmp_path / "dv.json")
        start_validation(validation_file=path)
        record_validation_findings([], validation_file=path)
        status = check_validation_status(path)
        assert status["passed"] is True


# ---------------------------------------------------------------------------
# validation_summary
# ---------------------------------------------------------------------------

class TestValidationSummary:
    def test_empty(self, tmp_path):
        path = str(tmp_path / "dv.json")
        start_validation(validation_file=path)
        summary = validation_summary(path)
        assert summary["total_findings"] == 0
        assert summary["status"] == VALIDATION_PASS

    def test_with_blocking(self, tmp_path):
        path = str(tmp_path / "dv.json")
        start_validation(validation_file=path)
        findings = [
            ValidationFinding(
                finding_id="dv-001", category="wcag", severity="critical",
                title="t", description="d", element="e", remediation="r",
            ),
        ]
        record_validation_findings(findings, validation_file=path)
        summary = validation_summary(path)
        assert summary["total_findings"] == 1
        assert summary["blocking_count"] == 1
        assert summary["status"] == VALIDATION_FAIL

    def test_with_warnings_only(self, tmp_path):
        path = str(tmp_path / "dv.json")
        start_validation(validation_file=path)
        findings = [
            ValidationFinding(
                finding_id="dv-001", category="brand", severity="medium",
                title="t", description="d", element="e", remediation="r",
            ),
        ]
        record_validation_findings(findings, validation_file=path)
        summary = validation_summary(path)
        assert summary["status"] == VALIDATION_WARNING

    def test_not_started(self, tmp_path):
        path = str(tmp_path / "missing.json")
        summary = validation_summary(path)
        assert summary["total_findings"] == 0
