"""Tests for crux_design_handoff.py — design-to-code handoff system."""

import json
import os

import pytest

from scripts.lib.crux_design_handoff import (
    DesignToken,
    ComponentNode,
    InteractionSpec,
    AccessibilitySpec,
    DesignHandoff,
    create_handoff,
    save_handoff,
    load_handoff,
    render_handoff_markdown,
)


# ---------------------------------------------------------------------------
# DesignToken
# ---------------------------------------------------------------------------

class TestDesignToken:
    def test_create(self):
        token = DesignToken(name="color.primary", value="#3B82F6", category="color")
        assert token.name == "color.primary"
        assert token.value == "#3B82F6"
        assert token.category == "color"

    def test_to_dict(self):
        token = DesignToken(name="spacing.md", value="16px", category="spacing")
        d = token.to_dict()
        assert d["name"] == "spacing.md"
        assert d["value"] == "16px"

    def test_from_dict(self):
        d = {"name": "font.body", "value": "14px", "category": "typography"}
        token = DesignToken.from_dict(d)
        assert token.category == "typography"

    def test_from_dict_defaults(self):
        token = DesignToken.from_dict({})
        assert token.name == ""
        assert token.category == ""

    def test_roundtrip(self):
        token = DesignToken(name="shadow.sm", value="0 1px 2px rgba(0,0,0,0.05)", category="shadow")
        t2 = DesignToken.from_dict(token.to_dict())
        assert t2.to_dict() == token.to_dict()


# ---------------------------------------------------------------------------
# ComponentNode
# ---------------------------------------------------------------------------

class TestComponentNode:
    def test_create(self):
        node = ComponentNode(
            name="EmailField",
            component_type="TextField",
            props={"label": "Email", "type": "email"},
        )
        assert node.name == "EmailField"
        assert node.component_type == "TextField"

    def test_with_children(self):
        child = ComponentNode(name="Label", component_type="Text", props={})
        parent = ComponentNode(
            name="FormGroup", component_type="Container",
            props={}, children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].name == "Label"

    def test_to_dict(self):
        child = ComponentNode(name="Input", component_type="TextInput", props={"type": "text"})
        parent = ComponentNode(
            name="Field", component_type="FormField",
            props={"required": True}, children=[child],
        )
        d = parent.to_dict()
        assert d["name"] == "Field"
        assert len(d["children"]) == 1

    def test_from_dict(self):
        d = {
            "name": "Button",
            "component_type": "Button",
            "props": {"variant": "primary"},
            "children": [],
        }
        node = ComponentNode.from_dict(d)
        assert node.props["variant"] == "primary"

    def test_from_dict_nested(self):
        d = {
            "name": "Form",
            "component_type": "Form",
            "props": {},
            "children": [
                {"name": "Email", "component_type": "Input", "props": {}, "children": []},
            ],
        }
        node = ComponentNode.from_dict(d)
        assert len(node.children) == 1
        assert node.children[0].name == "Email"

    def test_from_dict_defaults(self):
        node = ComponentNode.from_dict({})
        assert node.name == ""
        assert node.children == []


# ---------------------------------------------------------------------------
# InteractionSpec
# ---------------------------------------------------------------------------

class TestInteractionSpec:
    def test_create(self):
        spec = InteractionSpec(
            element="SubmitButton",
            states={"hover": "bg-blue-600", "active": "scale(0.98)", "loading": "spinner"},
        )
        assert spec.element == "SubmitButton"
        assert "hover" in spec.states

    def test_to_dict(self):
        spec = InteractionSpec(element="Input", states={"focus": "blue ring"})
        d = spec.to_dict()
        assert d["element"] == "Input"

    def test_from_dict(self):
        d = {"element": "Link", "states": {"hover": "underline"}}
        spec = InteractionSpec.from_dict(d)
        assert spec.states["hover"] == "underline"

    def test_from_dict_defaults(self):
        spec = InteractionSpec.from_dict({})
        assert spec.element == ""
        assert spec.states == {}


# ---------------------------------------------------------------------------
# AccessibilitySpec
# ---------------------------------------------------------------------------

class TestAccessibilitySpec:
    def test_create(self):
        spec = AccessibilitySpec(
            wcag_level="AA",
            contrast_ratios={"primary_on_white": 8.6},
            keyboard_order=["email", "password", "submit"],
            aria_attributes={"email": {"aria-required": "true"}},
        )
        assert spec.wcag_level == "AA"
        assert spec.contrast_ratios["primary_on_white"] == 8.6

    def test_to_dict(self):
        spec = AccessibilitySpec(
            wcag_level="AAA",
            contrast_ratios={},
            keyboard_order=[],
            aria_attributes={},
        )
        d = spec.to_dict()
        assert d["wcag_level"] == "AAA"

    def test_from_dict(self):
        d = {
            "wcag_level": "AA",
            "contrast_ratios": {"text": 4.5},
            "keyboard_order": ["input1"],
            "aria_attributes": {},
        }
        spec = AccessibilitySpec.from_dict(d)
        assert spec.contrast_ratios["text"] == 4.5

    def test_from_dict_defaults(self):
        spec = AccessibilitySpec.from_dict({})
        assert spec.wcag_level == "AA"
        assert spec.keyboard_order == []


# ---------------------------------------------------------------------------
# DesignHandoff
# ---------------------------------------------------------------------------

class TestDesignHandoff:
    def test_create(self):
        handoff = DesignHandoff(
            feature_name="Registration Form",
            component_tree=ComponentNode(name="Root", component_type="Container", props={}),
            tokens=[DesignToken(name="color.primary", value="#3B82F6", category="color")],
            interactions=[InteractionSpec(element="Button", states={"hover": "dark"})],
            accessibility=AccessibilitySpec(wcag_level="AA", contrast_ratios={}, keyboard_order=[], aria_attributes={}),
            breakpoints={"mobile": "0-640px", "desktop": "1025px+"},
        )
        assert handoff.feature_name == "Registration Form"
        assert len(handoff.tokens) == 1

    def test_to_dict(self):
        handoff = DesignHandoff(
            feature_name="Login",
            component_tree=ComponentNode(name="R", component_type="C", props={}),
            tokens=[],
            interactions=[],
            accessibility=AccessibilitySpec(wcag_level="AA", contrast_ratios={}, keyboard_order=[], aria_attributes={}),
            breakpoints={},
        )
        d = handoff.to_dict()
        assert d["feature_name"] == "Login"
        assert "component_tree" in d
        assert "accessibility" in d

    def test_from_dict(self):
        d = {
            "feature_name": "Search",
            "component_tree": {"name": "Root", "component_type": "Div", "props": {}, "children": []},
            "tokens": [{"name": "c", "value": "v", "category": "x"}],
            "interactions": [],
            "accessibility": {"wcag_level": "AAA", "contrast_ratios": {}, "keyboard_order": [], "aria_attributes": {}},
            "breakpoints": {"mobile": "0-640px"},
        }
        handoff = DesignHandoff.from_dict(d)
        assert handoff.feature_name == "Search"
        assert len(handoff.tokens) == 1
        assert handoff.accessibility.wcag_level == "AAA"

    def test_from_dict_defaults(self):
        handoff = DesignHandoff.from_dict({})
        assert handoff.feature_name == ""
        assert handoff.tokens == []

    def test_roundtrip(self):
        handoff = DesignHandoff(
            feature_name="Profile",
            component_tree=ComponentNode(
                name="Form", component_type="Form", props={"action": "/profile"},
                children=[ComponentNode(name="Name", component_type="Input", props={})],
            ),
            tokens=[DesignToken(name="c.primary", value="#000", category="color")],
            interactions=[InteractionSpec(element="Save", states={"hover": "dark"})],
            accessibility=AccessibilitySpec(
                wcag_level="AA",
                contrast_ratios={"text": 4.5},
                keyboard_order=["name", "save"],
                aria_attributes={"name": {"aria-label": "Full name"}},
            ),
            breakpoints={"mobile": "0-640", "desktop": "1025+"},
        )
        h2 = DesignHandoff.from_dict(handoff.to_dict())
        assert h2.to_dict() == handoff.to_dict()


# ---------------------------------------------------------------------------
# create_handoff
# ---------------------------------------------------------------------------

class TestCreateHandoff:
    def test_creates_with_minimal_args(self):
        handoff = create_handoff(feature_name="Signup")
        assert handoff.feature_name == "Signup"
        assert handoff.component_tree.name == "Root"
        assert handoff.accessibility.wcag_level == "AA"

    def test_creates_with_full_args(self):
        tree = ComponentNode(name="Form", component_type="Form", props={})
        tokens = [DesignToken(name="c", value="v", category="color")]
        handoff = create_handoff(
            feature_name="Login",
            component_tree=tree,
            tokens=tokens,
            wcag_level="AAA",
        )
        assert handoff.component_tree.name == "Form"
        assert len(handoff.tokens) == 1
        assert handoff.accessibility.wcag_level == "AAA"


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "handoff.json")
        handoff = create_handoff(feature_name="Test")
        save_handoff(handoff, path)

        loaded = load_handoff(path)
        assert loaded.feature_name == "Test"

    def test_load_missing_returns_empty(self, tmp_path):
        path = str(tmp_path / "missing.json")
        loaded = load_handoff(path)
        assert loaded.feature_name == ""

    def test_load_corrupt_returns_empty(self, tmp_path):
        path = str(tmp_path / "bad.json")
        with open(path, "w") as f:
            f.write("not json")
        loaded = load_handoff(path)
        assert loaded.feature_name == ""

    def test_save_creates_dirs(self, tmp_path):
        path = str(tmp_path / "sub" / "handoff.json")
        save_handoff(create_handoff(feature_name="X"), path)
        assert os.path.exists(path)


# ---------------------------------------------------------------------------
# render_handoff_markdown
# ---------------------------------------------------------------------------

class TestRenderHandoffMarkdown:
    def test_renders_feature_name(self):
        handoff = create_handoff(feature_name="User Registration")
        md = render_handoff_markdown(handoff)
        assert "# Design Handoff: User Registration" in md

    def test_renders_tokens(self):
        handoff = create_handoff(
            feature_name="Login",
            tokens=[DesignToken(name="color.primary", value="#3B82F6", category="color")],
        )
        md = render_handoff_markdown(handoff)
        assert "color.primary" in md
        assert "#3B82F6" in md

    def test_renders_component_tree(self):
        tree = ComponentNode(
            name="Form", component_type="Form", props={},
            children=[ComponentNode(name="Email", component_type="Input", props={})],
        )
        handoff = create_handoff(feature_name="F", component_tree=tree)
        md = render_handoff_markdown(handoff)
        assert "Form" in md
        assert "Email" in md

    def test_renders_accessibility(self):
        handoff = create_handoff(feature_name="F", wcag_level="AAA")
        md = render_handoff_markdown(handoff)
        assert "AAA" in md

    def test_renders_breakpoints(self):
        handoff = create_handoff(feature_name="F")
        handoff.breakpoints = {"mobile": "0-640px"}
        md = render_handoff_markdown(handoff)
        assert "mobile" in md

    def test_renders_interactions(self):
        handoff = create_handoff(feature_name="F")
        handoff.interactions = [InteractionSpec(element="Button", states={"hover": "bg-dark"})]
        md = render_handoff_markdown(handoff)
        assert "Button" in md
        assert "hover" in md
