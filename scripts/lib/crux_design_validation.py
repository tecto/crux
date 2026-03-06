"""Design validation gate engine for Crux.

Manages Gate 7 of the enhanced safety pipeline: WCAG compliance checking,
contrast ratio validation, touch target validation, and brand consistency.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field


VALIDATION_PASS = "pass"
VALIDATION_FAIL = "fail"
VALIDATION_WARNING = "warning"

BLOCKING_SEVERITIES = {"critical", "high"}

# WCAG AA minimum contrast ratios
CONTRAST_AA_NORMAL = 4.5
CONTRAST_AA_LARGE = 3.0
CONTRAST_AAA_NORMAL = 7.0

# Minimum touch target size (px)
MIN_TOUCH_TARGET = 44


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ContrastResult:
    foreground: str = ""
    background: str = ""
    ratio: float = 0.0
    passes_aa: bool = False
    passes_aaa: bool = False

    def to_dict(self) -> dict:
        return {
            "foreground": self.foreground,
            "background": self.background,
            "ratio": self.ratio,
            "passes_aa": self.passes_aa,
            "passes_aaa": self.passes_aaa,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ContrastResult:
        return cls(
            foreground=d.get("foreground", ""),
            background=d.get("background", ""),
            ratio=d.get("ratio", 0.0),
            passes_aa=d.get("passes_aa", False),
            passes_aaa=d.get("passes_aaa", False),
        )


@dataclass
class ValidationFinding:
    finding_id: str = ""
    category: str = ""
    severity: str = ""
    title: str = ""
    description: str = ""
    element: str = ""
    remediation: str = ""
    resolved: bool = False

    def is_blocking(self) -> bool:
        return self.severity in BLOCKING_SEVERITIES and not self.resolved

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "element": self.element,
            "remediation": self.remediation,
            "resolved": self.resolved,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ValidationFinding:
        return cls(
            finding_id=d.get("finding_id", ""),
            category=d.get("category", ""),
            severity=d.get("severity", ""),
            title=d.get("title", ""),
            description=d.get("description", ""),
            element=d.get("element", ""),
            remediation=d.get("remediation", ""),
            resolved=d.get("resolved", False),
        )


@dataclass
class DesignValidationState:
    wcag_level: str = "AA"
    check_brand: bool = True
    check_handoff: bool = True
    findings: list[ValidationFinding] = field(default_factory=list)
    passed: bool = False

    def to_dict(self) -> dict:
        return {
            "wcag_level": self.wcag_level,
            "check_brand": self.check_brand,
            "check_handoff": self.check_handoff,
            "findings": [f.to_dict() for f in self.findings],
            "passed": self.passed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DesignValidationState:
        return cls(
            wcag_level=d.get("wcag_level", "AA"),
            check_brand=d.get("check_brand", True),
            check_handoff=d.get("check_handoff", True),
            findings=[ValidationFinding.from_dict(f) for f in d.get("findings", [])],
            passed=d.get("passed", False),
        )

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> DesignValidationState:
        try:
            with open(path) as f:
                return cls.from_dict(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()


# ---------------------------------------------------------------------------
# Contrast ratio calculation (WCAG 2.1 algorithm)
# ---------------------------------------------------------------------------

def _parse_hex(hex_color: str) -> tuple[int, int, int]:
    """Parse hex color string to RGB tuple."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.1."""
    def linearize(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def check_contrast_ratio(foreground: str, background: str) -> ContrastResult:
    """Calculate contrast ratio between two hex colors."""
    fg_rgb = _parse_hex(foreground)
    bg_rgb = _parse_hex(background)

    l1 = _relative_luminance(*fg_rgb)
    l2 = _relative_luminance(*bg_rgb)

    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = round((lighter + 0.05) / (darker + 0.05), 1)

    return ContrastResult(
        foreground=foreground,
        background=background,
        ratio=ratio,
        passes_aa=ratio >= CONTRAST_AA_NORMAL,
        passes_aaa=ratio >= CONTRAST_AAA_NORMAL,
    )


# ---------------------------------------------------------------------------
# Touch target validation
# ---------------------------------------------------------------------------

def validate_touch_targets(
    elements: dict[str, tuple[int, int]],
) -> list[ValidationFinding]:
    """Validate touch target sizes. elements = {name: (width, height)}."""
    findings: list[ValidationFinding] = []
    for name, (w, h) in elements.items():
        if w < MIN_TOUCH_TARGET or h < MIN_TOUCH_TARGET:
            findings.append(ValidationFinding(
                finding_id=f"touch-{name.lower()}",
                category="touch_target",
                severity="high",
                title=f"Touch target too small: {name}",
                description=f"{name} is {w}x{h}px, minimum is {MIN_TOUCH_TARGET}x{MIN_TOUCH_TARGET}px",
                element=name,
                remediation=f"Increase to at least {MIN_TOUCH_TARGET}x{MIN_TOUCH_TARGET}px",
            ))
    return findings


# ---------------------------------------------------------------------------
# WCAG level validation
# ---------------------------------------------------------------------------

def validate_wcag_level(
    wcag_level: str,
    contrast_results: list[ContrastResult],
) -> list[ValidationFinding]:
    """Validate contrast results against a WCAG level."""
    findings: list[ValidationFinding] = []

    for i, result in enumerate(contrast_results):
        passes = result.passes_aa if wcag_level in ("A", "AA") else result.passes_aaa
        if not passes:
            findings.append(ValidationFinding(
                finding_id=f"contrast-{i}",
                category="wcag",
                severity="critical",
                title=f"Contrast ratio {result.ratio}:1 fails WCAG {wcag_level}",
                description=(
                    f"{result.foreground} on {result.background} "
                    f"has ratio {result.ratio}:1"
                ),
                element=f"color-pair-{i}",
                remediation=f"Increase contrast to meet WCAG {wcag_level} requirements",
            ))

    return findings


# ---------------------------------------------------------------------------
# Gate operations
# ---------------------------------------------------------------------------

def start_validation(
    wcag_level: str = "AA",
    check_brand: bool = True,
    check_handoff: bool = True,
    validation_file: str = "",
) -> DesignValidationState:
    """Initialize a design validation gate."""
    state = DesignValidationState(
        wcag_level=wcag_level,
        check_brand=check_brand,
        check_handoff=check_handoff,
    )
    if validation_file:
        state.save(validation_file)
    return state


def record_validation_findings(
    findings: list[ValidationFinding],
    validation_file: str,
) -> DesignValidationState:
    """Record validation findings and determine pass/fail."""
    state = DesignValidationState.load(validation_file)
    state.findings.extend(findings)

    blocking = [f for f in state.findings if f.is_blocking()]
    state.passed = len(blocking) == 0

    state.save(validation_file)
    return state


def check_validation_status(validation_file: str) -> dict:
    """Check status of design validation gate."""
    state = DesignValidationState.load(validation_file)

    if not state.findings and not state.passed:
        # Check if file exists to distinguish not-started from empty
        if not os.path.exists(validation_file):
            return {"started": False, "passed": False}

    return {
        "started": True,
        "passed": state.passed,
        "finding_count": len(state.findings),
        "blocking_count": len([f for f in state.findings if f.is_blocking()]),
    }


def validation_summary(validation_file: str) -> dict:
    """Generate a summary of design validation results."""
    state = DesignValidationState.load(validation_file)

    blocking = [f for f in state.findings if f.is_blocking()]
    warnings = [f for f in state.findings
                if f.severity in ("medium",) and not f.resolved]

    if blocking:
        status = VALIDATION_FAIL
    elif warnings:
        status = VALIDATION_WARNING
    else:
        status = VALIDATION_PASS

    by_category: dict[str, int] = {}
    for f in state.findings:
        by_category[f.category] = by_category.get(f.category, 0) + 1

    return {
        "total_findings": len(state.findings),
        "blocking_count": len(blocking),
        "warning_count": len(warnings),
        "by_category": by_category,
        "status": status,
        "passed": state.passed,
    }
