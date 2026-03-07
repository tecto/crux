"""Tests for crux_cross_domain.py — cross-domain knowledge flows."""

import json
import os

import pytest

from scripts.lib.crux_knowledge_categories import (
    KnowledgeStore,
    create_test_pattern,
    create_security_pattern,
    create_design_pattern,
    CATEGORY_TEST,
    CATEGORY_SECURITY,
    CATEGORY_DESIGN,
)
from scripts.lib.crux_cross_domain import (
    security_to_test_pattern,
    testing_to_design_pattern as _testing_to_design_pattern,
    design_to_security_pattern,
    cross_domain_sync,
)
from scripts.lib.crux_security_audit import SecurityFinding
from scripts.lib.crux_design_validation import ValidationFinding


# ---------------------------------------------------------------------------
# security_to_test_pattern
# ---------------------------------------------------------------------------

class TestSecurityToTestPattern:
    def test_creates_test_pattern(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        finding = SecurityFinding(
            finding_id="sec-001",
            category="input_validation",
            severity="high",
            title="SQL Injection in search",
            description="f-string interpolation in SQL",
            file_path="app/search.py",
            line_range=[10, 15],
            remediation="Use parameterized queries",
            cwe="CWE-89",
        )
        entry = security_to_test_pattern(finding, store)
        assert entry.category == CATEGORY_TEST
        assert "sql injection" in entry.title.lower()
        assert entry.entry_id in store.entries

    def test_adds_applies_to(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        finding = SecurityFinding(
            finding_id="sec-002",
            category="authentication",
            severity="critical",
            title="Auth bypass",
            description="Missing auth check",
            file_path="auth.py",
            line_range=[],
            remediation="Add auth",
        )
        entry = security_to_test_pattern(finding, store)
        assert "authentication" in entry.applies_to


# ---------------------------------------------------------------------------
# testing_to_design_pattern
# ---------------------------------------------------------------------------

class TestTestingToDesignPattern:
    def test_creates_design_pattern(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        entry = _testing_to_design_pattern(
            component="Button",
            property_name="min_size",
            preferred_value="48x48px",
            reason="Touch target too small on mobile",
            store=store,
        )
        assert entry.category == CATEGORY_DESIGN
        assert entry.component == "Button"
        assert entry.entry_id in store.entries

    def test_sets_preferred_value(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        entry = _testing_to_design_pattern(
            component="Input",
            property_name="border_color",
            preferred_value="#3B82F6",
            reason="Focus state not visible",
            store=store,
        )
        assert entry.preferred_value == "#3B82F6"


# ---------------------------------------------------------------------------
# design_to_security_pattern
# ---------------------------------------------------------------------------

class TestDesignToSecurityPattern:
    def test_creates_security_pattern(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        finding = ValidationFinding(
            finding_id="dv-001",
            category="wcag",
            severity="critical",
            title="Contrast violation",
            description="3.2:1 ratio below 4.5:1",
            element="LoginButton",
            remediation="Darken text",
        )
        entry = design_to_security_pattern(finding, store)
        assert entry.category == CATEGORY_SECURITY
        assert "contrast" in entry.title.lower() or "wcag" in entry.vulnerability_type.lower()
        assert entry.entry_id in store.entries

    def test_maps_category(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        finding = ValidationFinding(
            finding_id="dv-002",
            category="touch_target",
            severity="high",
            title="Small touch target",
            description="32x32 below minimum",
            element="CloseBtn",
            remediation="Increase size",
        )
        entry = design_to_security_pattern(finding, store)
        assert entry.vulnerability_type == "accessibility"


# ---------------------------------------------------------------------------
# cross_domain_sync
# ---------------------------------------------------------------------------

class TestCrossDomainSync:
    def test_syncs_security_findings_to_test(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        security_findings = [
            SecurityFinding(
                finding_id="sec-001", category="input_validation",
                severity="high", title="SQLi", description="d",
                file_path="f", line_range=[], remediation="r",
            ),
        ]
        result = cross_domain_sync(
            store=store,
            security_findings=security_findings,
        )
        assert result["test_patterns_created"] == 1
        test_entries = store.search(category=CATEGORY_TEST)
        assert len(test_entries) == 1

    def test_syncs_design_findings_to_security(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        design_findings = [
            ValidationFinding(
                finding_id="dv-001", category="wcag", severity="critical",
                title="Low contrast", description="d", element="e", remediation="r",
            ),
        ]
        result = cross_domain_sync(
            store=store,
            design_findings=design_findings,
        )
        assert result["security_patterns_created"] == 1

    def test_syncs_both(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        security_findings = [
            SecurityFinding(
                finding_id="sec-001", category="auth",
                severity="high", title="Auth bypass", description="d",
                file_path="f", line_range=[], remediation="r",
            ),
        ]
        design_findings = [
            ValidationFinding(
                finding_id="dv-001", category="wcag", severity="critical",
                title="Contrast", description="d", element="e", remediation="r",
            ),
        ]
        result = cross_domain_sync(
            store=store,
            security_findings=security_findings,
            design_findings=design_findings,
        )
        assert result["test_patterns_created"] == 1
        assert result["security_patterns_created"] == 1

    def test_syncs_test_design_updates(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        updates = [
            {
                "component": "Button",
                "property_name": "min_size",
                "preferred_value": "48x48px",
                "reason": "Touch target too small",
            },
        ]
        result = cross_domain_sync(
            store=store,
            test_design_updates=updates,
        )
        assert result["design_patterns_created"] == 1
        design_entries = store.search(category=CATEGORY_DESIGN)
        assert len(design_entries) == 1

    def test_empty_inputs(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        result = cross_domain_sync(store=store)
        assert result["test_patterns_created"] == 0
        assert result["security_patterns_created"] == 0
        assert result["design_patterns_created"] == 0
