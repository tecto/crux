"""Design-to-code handoff system for Crux.

Generates structured handoff documents that bridge design modes
(design-ui, design-system, etc.) and build modes (build-py, build-ex).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DesignToken:
    name: str = ""
    value: str = ""
    category: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "category": self.category}

    @classmethod
    def from_dict(cls, d: dict) -> DesignToken:
        return cls(
            name=d.get("name", ""),
            value=d.get("value", ""),
            category=d.get("category", ""),
        )


@dataclass
class ComponentNode:
    name: str = ""
    component_type: str = ""
    props: dict = field(default_factory=dict)
    children: list[ComponentNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "component_type": self.component_type,
            "props": dict(self.props),
            "children": [c.to_dict() for c in self.children],
        }

    @classmethod
    def from_dict(cls, d: dict) -> ComponentNode:
        return cls(
            name=d.get("name", ""),
            component_type=d.get("component_type", ""),
            props=dict(d.get("props", {})),
            children=[cls.from_dict(c) for c in d.get("children", [])],
        )


@dataclass
class InteractionSpec:
    element: str = ""
    states: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"element": self.element, "states": dict(self.states)}

    @classmethod
    def from_dict(cls, d: dict) -> InteractionSpec:
        return cls(
            element=d.get("element", ""),
            states=dict(d.get("states", {})),
        )


@dataclass
class AccessibilitySpec:
    wcag_level: str = "AA"
    contrast_ratios: dict[str, float] = field(default_factory=dict)
    keyboard_order: list[str] = field(default_factory=list)
    aria_attributes: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "wcag_level": self.wcag_level,
            "contrast_ratios": dict(self.contrast_ratios),
            "keyboard_order": list(self.keyboard_order),
            "aria_attributes": {k: dict(v) for k, v in self.aria_attributes.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> AccessibilitySpec:
        return cls(
            wcag_level=d.get("wcag_level", "AA"),
            contrast_ratios=dict(d.get("contrast_ratios", {})),
            keyboard_order=list(d.get("keyboard_order", [])),
            aria_attributes={k: dict(v) for k, v in d.get("aria_attributes", {}).items()},
        )


@dataclass
class DesignHandoff:
    feature_name: str = ""
    component_tree: ComponentNode = field(default_factory=ComponentNode)
    tokens: list[DesignToken] = field(default_factory=list)
    interactions: list[InteractionSpec] = field(default_factory=list)
    accessibility: AccessibilitySpec = field(default_factory=AccessibilitySpec)
    breakpoints: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "feature_name": self.feature_name,
            "component_tree": self.component_tree.to_dict(),
            "tokens": [t.to_dict() for t in self.tokens],
            "interactions": [i.to_dict() for i in self.interactions],
            "accessibility": self.accessibility.to_dict(),
            "breakpoints": dict(self.breakpoints),
        }

    @classmethod
    def from_dict(cls, d: dict) -> DesignHandoff:
        tree_data = d.get("component_tree")
        a11y_data = d.get("accessibility")
        return cls(
            feature_name=d.get("feature_name", ""),
            component_tree=ComponentNode.from_dict(tree_data) if tree_data else ComponentNode(),
            tokens=[DesignToken.from_dict(t) for t in d.get("tokens", [])],
            interactions=[InteractionSpec.from_dict(i) for i in d.get("interactions", [])],
            accessibility=AccessibilitySpec.from_dict(a11y_data) if a11y_data else AccessibilitySpec(),
            breakpoints=dict(d.get("breakpoints", {})),
        )


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def create_handoff(
    feature_name: str,
    component_tree: ComponentNode | None = None,
    tokens: list[DesignToken] | None = None,
    interactions: list[InteractionSpec] | None = None,
    wcag_level: str = "AA",
    breakpoints: dict[str, str] | None = None,
) -> DesignHandoff:
    """Create a new design handoff document."""
    return DesignHandoff(
        feature_name=feature_name,
        component_tree=component_tree or ComponentNode(name="Root", component_type="Container", props={}),
        tokens=list(tokens) if tokens else [],
        interactions=list(interactions) if interactions else [],
        accessibility=AccessibilitySpec(
            wcag_level=wcag_level,
            contrast_ratios={},
            keyboard_order=[],
            aria_attributes={},
        ),
        breakpoints=dict(breakpoints) if breakpoints else {},
    )


def save_handoff(handoff: DesignHandoff, path: str) -> None:
    """Persist a design handoff to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(handoff.to_dict(), f, indent=2)


def load_handoff(path: str) -> DesignHandoff:
    """Load a design handoff from JSON."""
    try:
        with open(path) as f:
            return DesignHandoff.from_dict(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return DesignHandoff()


def render_handoff_markdown(handoff: DesignHandoff) -> str:
    """Render a design handoff as markdown for human consumption."""
    lines = [f"# Design Handoff: {handoff.feature_name}", ""]

    # Component tree
    lines.append("## Component Tree")
    lines.append("")
    _render_tree(handoff.component_tree, lines, indent=0)
    lines.append("")

    # Design tokens
    if handoff.tokens:
        lines.append("## Design Tokens")
        lines.append("")
        for token in handoff.tokens:
            lines.append(f"- **{token.name}**: `{token.value}` ({token.category})")
        lines.append("")

    # Interactions
    if handoff.interactions:
        lines.append("## Interaction Specifications")
        lines.append("")
        for interaction in handoff.interactions:
            lines.append(f"### {interaction.element}")
            for state, desc in interaction.states.items():
                lines.append(f"- **{state}**: {desc}")
            lines.append("")

    # Breakpoints
    if handoff.breakpoints:
        lines.append("## Responsive Breakpoints")
        lines.append("")
        for name, value in handoff.breakpoints.items():
            lines.append(f"- **{name}**: {value}")
        lines.append("")

    # Accessibility
    lines.append("## Accessibility")
    lines.append("")
    lines.append(f"**WCAG Level:** {handoff.accessibility.wcag_level}")
    lines.append("")

    return "\n".join(lines)


def _render_tree(node: ComponentNode, lines: list[str], indent: int) -> None:
    """Recursively render a component tree."""
    prefix = "  " * indent
    type_info = f" ({node.component_type})" if node.component_type else ""
    lines.append(f"{prefix}- {node.name}{type_info}")
    for child in node.children:
        _render_tree(child, lines, indent + 1)
