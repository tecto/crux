"""Cross-domain knowledge flows for Crux.

Bidirectional knowledge transfer between security, testing, and design domains:
- Security findings become test patterns
- Test failures inform design patterns
- Design validation findings feed security knowledge
"""

from __future__ import annotations

from scripts.lib.crux_knowledge_categories import (
    KnowledgeStore,
    TestPatternEntry,
    SecurityPatternEntry,
    DesignPatternEntry,
    create_test_pattern,
    create_security_pattern,
    create_design_pattern,
)
from scripts.lib.crux_security_audit import SecurityFinding
from scripts.lib.crux_design_validation import ValidationFinding


def security_to_test_pattern(
    finding: SecurityFinding,
    store: KnowledgeStore,
) -> TestPatternEntry:
    """Convert a security finding into a test pattern.

    When a vulnerability is found, we create a test pattern so future
    test generation includes checks for the same class of vulnerability.
    """
    entry = create_test_pattern(
        title=f"Test for: {finding.title}",
        applies_to=[finding.category],
        test_code=f"# Regression test for {finding.finding_id}: {finding.title}\n"
                  f"# Remediation: {finding.remediation}",
        prevented_bugs=[finding.finding_id],
    )
    store.add(entry)
    return entry


def testing_to_design_pattern(
    component: str,
    property_name: str,
    preferred_value: str,
    reason: str,
    store: KnowledgeStore,
) -> DesignPatternEntry:
    """Convert a test failure insight into a design pattern.

    When UI tests fail due to design issues (e.g., touch targets too small),
    we create a design pattern so future design generation avoids the issue.
    """
    entry = create_design_pattern(
        title=f"{component}: {property_name} ({reason})",
        component=component,
        property_name=property_name,
        preferred_value=preferred_value,
    )
    store.add(entry)
    return entry


def design_to_security_pattern(
    finding: ValidationFinding,
    store: KnowledgeStore,
) -> SecurityPatternEntry:
    """Convert a design validation finding into a security pattern.

    WCAG violations and accessibility issues are tracked as security-adjacent
    patterns so future security audits also check for them.
    """
    entry = create_security_pattern(
        title=f"Accessibility: {finding.title}",
        vulnerability_type="accessibility",
        cwe="",
        remediation=finding.remediation,
    )
    store.add(entry)
    return entry


def cross_domain_sync(
    store: KnowledgeStore,
    security_findings: list[SecurityFinding] | None = None,
    design_findings: list[ValidationFinding] | None = None,
    test_design_updates: list[dict] | None = None,
) -> dict:
    """Perform all cross-domain knowledge transfers in one operation.

    Args:
        store: Knowledge store to update.
        security_findings: Security findings to convert to test patterns.
        design_findings: Design findings to convert to security patterns.
        test_design_updates: Test failure insights to convert to design patterns.
            Each dict has: component, property_name, preferred_value, reason.
    """
    test_created = 0
    security_created = 0
    design_created = 0

    if security_findings:
        for finding in security_findings:
            security_to_test_pattern(finding, store)
            test_created += 1

    if design_findings:
        for finding in design_findings:
            design_to_security_pattern(finding, store)
            security_created += 1

    if test_design_updates:
        for update in test_design_updates:
            testing_to_design_pattern(
                component=update["component"],
                property_name=update["property_name"],
                preferred_value=update["preferred_value"],
                reason=update["reason"],
                store=store,
            )
            design_created += 1

    return {
        "test_patterns_created": test_created,
        "security_patterns_created": security_created,
        "design_patterns_created": design_created,
    }
