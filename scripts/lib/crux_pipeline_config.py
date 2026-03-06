"""Pipeline configuration system for Crux.

Manages the 7-gate enhanced safety pipeline configuration:
Gate 1: Preflight, Gate 2: TDD/BDD, Gate 3: Security Audit,
Gate 4: Second Opinion, Gate 5: Human Approval, Gate 6: Dry Run,
Gate 7: Design Validation.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


VALID_TDD_LEVELS = ["strict", "standard", "relaxed", "off"]
VALID_RISK_LEVELS = ["low", "medium", "high", "critical"]
VALID_SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]
VALID_SANDBOX_TYPES = ["isolated", "container", "vm"]
VALID_WCAG_LEVELS = ["A", "AA", "AAA"]
VALID_SECURITY_CATEGORIES = [
    "input_validation",
    "authentication",
    "data_exposure",
    "cryptography",
    "dependencies",
    "infrastructure",
    "business_logic",
]

DESIGN_MODES = [
    "design-ui",
    "design-review",
    "design-system",
    "design-responsive",
    "design-accessibility",
]


# ---------------------------------------------------------------------------
# Sub-configs
# ---------------------------------------------------------------------------

@dataclass
class TddConfig:
    enabled: bool = True
    level: str = "standard"
    apply_to_modes: list[str] = field(default_factory=lambda: ["build-py", "build-ex"])
    coverage_minimum: int = 80
    coverage_minimum_strict: int = 95
    max_correction_iterations: int = 10
    bdd_enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "level": self.level,
            "apply_to_modes": list(self.apply_to_modes),
            "coverage_minimum": self.coverage_minimum,
            "coverage_minimum_strict": self.coverage_minimum_strict,
            "max_correction_iterations": self.max_correction_iterations,
            "bdd_enabled": self.bdd_enabled,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TddConfig:
        return cls(
            enabled=d.get("enabled", True),
            level=d.get("level", "standard"),
            apply_to_modes=list(d.get("apply_to_modes", ["build-py", "build-ex"])),
            coverage_minimum=d.get("coverage_minimum", 80),
            coverage_minimum_strict=d.get("coverage_minimum_strict", 95),
            max_correction_iterations=d.get("max_correction_iterations", 10),
            bdd_enabled=d.get("bdd_enabled", True),
        )


@dataclass
class SecurityAuditConfig:
    enabled: bool = True
    max_iterations: int = 3
    stop_on_convergence: bool = True
    categories: list[str] = field(default_factory=lambda: list(VALID_SECURITY_CATEGORIES))
    fail_on_severity: list[str] = field(default_factory=lambda: ["critical", "high"])
    warn_on_severity: list[str] = field(default_factory=lambda: ["medium"])
    log_on_severity: list[str] = field(default_factory=lambda: ["low", "info"])

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "max_iterations": self.max_iterations,
            "stop_on_convergence": self.stop_on_convergence,
            "categories": list(self.categories),
            "fail_on_severity": list(self.fail_on_severity),
            "warn_on_severity": list(self.warn_on_severity),
            "log_on_severity": list(self.log_on_severity),
        }

    @classmethod
    def from_dict(cls, d: dict) -> SecurityAuditConfig:
        return cls(
            enabled=d.get("enabled", True),
            max_iterations=d.get("max_iterations", 3),
            stop_on_convergence=d.get("stop_on_convergence", True),
            categories=list(d.get("categories", VALID_SECURITY_CATEGORIES)),
            fail_on_severity=list(d.get("fail_on_severity", ["critical", "high"])),
            warn_on_severity=list(d.get("warn_on_severity", ["medium"])),
            log_on_severity=list(d.get("log_on_severity", ["low", "info"])),
        )


@dataclass
class SecondOpinionConfig:
    enabled: bool = True
    model: str = "auto"
    check_test_coverage: bool = True
    check_security_findings: bool = True

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "model": self.model,
            "check_test_coverage": self.check_test_coverage,
            "check_security_findings": self.check_security_findings,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SecondOpinionConfig:
        return cls(
            enabled=d.get("enabled", True),
            model=d.get("model", "auto"),
            check_test_coverage=d.get("check_test_coverage", True),
            check_security_findings=d.get("check_security_findings", True),
        )


@dataclass
class HumanApprovalConfig:
    enabled: bool = True
    required_for_severity: list[str] = field(
        default_factory=lambda: ["critical", "high", "medium"]
    )

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "required_for_severity": list(self.required_for_severity),
        }

    @classmethod
    def from_dict(cls, d: dict) -> HumanApprovalConfig:
        return cls(
            enabled=d.get("enabled", True),
            required_for_severity=list(
                d.get("required_for_severity", ["critical", "high", "medium"])
            ),
        )


@dataclass
class DryRunConfig:
    enabled: bool = True
    sandbox_type: str = "container"
    timeout_seconds: int = 300

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "sandbox_type": self.sandbox_type,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DryRunConfig:
        return cls(
            enabled=d.get("enabled", True),
            sandbox_type=d.get("sandbox_type", "container"),
            timeout_seconds=d.get("timeout_seconds", 300),
        )


@dataclass
class DesignValidationConfig:
    enabled: bool = True
    wcag_level: str = "AA"
    check_brand_consistency: bool = True
    check_handoff_completeness: bool = True

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "wcag_level": self.wcag_level,
            "check_brand_consistency": self.check_brand_consistency,
            "check_handoff_completeness": self.check_handoff_completeness,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DesignValidationConfig:
        return cls(
            enabled=d.get("enabled", True),
            wcag_level=d.get("wcag_level", "AA"),
            check_brand_consistency=d.get("check_brand_consistency", True),
            check_handoff_completeness=d.get("check_handoff_completeness", True),
        )


@dataclass
class KnowledgeBaseConfig:
    enabled: bool = True
    categories: list[str] = field(
        default_factory=lambda: [
            "test_patterns",
            "security_findings",
            "design_patterns",
            "code_patterns",
        ]
    )
    auto_promote_patterns: bool = True
    cross_project_learning: bool = True

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "categories": list(self.categories),
            "auto_promote_patterns": self.auto_promote_patterns,
            "cross_project_learning": self.cross_project_learning,
        }

    @classmethod
    def from_dict(cls, d: dict) -> KnowledgeBaseConfig:
        return cls(
            enabled=d.get("enabled", True),
            categories=list(
                d.get(
                    "categories",
                    ["test_patterns", "security_findings", "design_patterns", "code_patterns"],
                )
            ),
            auto_promote_patterns=d.get("auto_promote_patterns", True),
            cross_project_learning=d.get("cross_project_learning", True),
        )


# ---------------------------------------------------------------------------
# Top-level PipelineConfig
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    version: str = "2.0"
    environment: str = "production"
    tdd: TddConfig = field(default_factory=TddConfig)
    security_audit: SecurityAuditConfig = field(default_factory=SecurityAuditConfig)
    second_opinion: SecondOpinionConfig = field(default_factory=SecondOpinionConfig)
    human_approval: HumanApprovalConfig = field(default_factory=HumanApprovalConfig)
    dry_run: DryRunConfig = field(default_factory=DryRunConfig)
    design_validation: DesignValidationConfig = field(default_factory=DesignValidationConfig)
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)

    def to_dict(self) -> dict:
        return {
            "metadata": {
                "version": self.version,
                "environment": self.environment,
            },
            "pipeline": {
                "tdd_enforcement": self.tdd.to_dict(),
                "security_audit": self.security_audit.to_dict(),
                "second_opinion": self.second_opinion.to_dict(),
                "human_approval": self.human_approval.to_dict(),
                "dry_run": self.dry_run.to_dict(),
                "design_validation": self.design_validation.to_dict(),
            },
            "knowledge_base": self.knowledge_base.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> PipelineConfig:
        meta = d.get("metadata", {})
        pipeline = d.get("pipeline", {})
        return cls(
            version=meta.get("version", "2.0"),
            environment=meta.get("environment", "production"),
            tdd=TddConfig.from_dict(pipeline.get("tdd_enforcement", {})),
            security_audit=SecurityAuditConfig.from_dict(pipeline.get("security_audit", {})),
            second_opinion=SecondOpinionConfig.from_dict(pipeline.get("second_opinion", {})),
            human_approval=HumanApprovalConfig.from_dict(pipeline.get("human_approval", {})),
            dry_run=DryRunConfig.from_dict(pipeline.get("dry_run", {})),
            design_validation=DesignValidationConfig.from_dict(
                pipeline.get("design_validation", {})
            ),
            knowledge_base=KnowledgeBaseConfig.from_dict(d.get("knowledge_base", {})),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def default_config() -> PipelineConfig:
    """Return a fresh default pipeline configuration."""
    return PipelineConfig()


def save_pipeline_config(config: PipelineConfig, path: str) -> None:
    """Persist pipeline config to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)


def load_pipeline_config(path: str) -> PipelineConfig:
    """Load pipeline config from a JSON file, or return defaults if missing/corrupt."""
    try:
        with open(path) as f:
            return PipelineConfig.from_dict(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return default_config()


def gates_for_risk_level(risk_level: str, config: PipelineConfig) -> list[int]:
    """Return active gate numbers for a given risk level.

    Gate mapping:
    1=Preflight, 2=TDD, 3=Security Audit, 4=Second Opinion,
    5=Human Approval, 6=Dry Run, 7=Design Validation.
    """
    gates = [1]  # Preflight always active

    if config.tdd.enabled:
        if risk_level in ("medium", "high", "critical", "unknown"):
            gates.append(2)
        elif risk_level == "low":
            gates.append(2)  # optional but included when enabled

    if risk_level in ("medium", "high", "critical", "unknown"):
        if config.security_audit.enabled:
            gates.append(3)

    if risk_level in ("high", "critical", "unknown"):
        if config.second_opinion.enabled:
            gates.append(4)

    if risk_level in ("medium", "high", "critical", "unknown"):
        if config.human_approval.enabled:
            gates.append(5)

    if risk_level in ("high", "critical", "unknown"):
        if config.dry_run.enabled:
            gates.append(6)

    if risk_level in ("critical", "unknown"):
        if config.design_validation.enabled:
            gates.append(7)

    return sorted(gates)


def gates_for_mode(
    mode: str,
    risk_level: str,
    config: PipelineConfig,
) -> list[int]:
    """Return active gate numbers filtered by mode context.

    TDD gate (2) only applies to modes in tdd.apply_to_modes.
    Design gate (7) only applies to design-* modes.
    """
    gates = gates_for_risk_level(risk_level, config)

    # TDD gate only for configured build modes
    if 2 in gates and mode not in config.tdd.apply_to_modes:
        gates.remove(2)

    # Design validation only for design modes
    is_design = mode.startswith("design-")
    if 7 in gates and not is_design:
        gates.remove(7)

    # Design modes always get gate 7 if enabled (even at non-critical risk)
    if is_design and config.design_validation.enabled and 7 not in gates:
        gates.append(7)
        gates.sort()

    return gates
