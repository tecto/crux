"""Tests for crux_knowledge_categories.py — extended knowledge base categories."""

import json
import os

import pytest

from scripts.lib.crux_knowledge_categories import (
    KnowledgeEntry,
    TestPatternEntry,
    SecurityPatternEntry,
    DesignPatternEntry,
    KnowledgeStore,
    create_test_pattern,
    create_security_pattern,
    create_design_pattern,
    search_patterns,
    promote_pattern,
    CATEGORY_TEST,
    CATEGORY_SECURITY,
    CATEGORY_DESIGN,
    CATEGORY_CODE,
    STATUS_PROPOSED,
    STATUS_ADOPTED,
    STATUS_CANONICAL,
)


# ---------------------------------------------------------------------------
# KnowledgeEntry
# ---------------------------------------------------------------------------

class TestKnowledgeEntry:
    def test_create(self):
        e = KnowledgeEntry(
            entry_id="pat-001",
            category=CATEGORY_TEST,
            title="Concurrent duplicate check",
            confidence=0.85,
        )
        assert e.entry_id == "pat-001"
        assert e.status == STATUS_PROPOSED

    def test_to_dict(self):
        e = KnowledgeEntry(entry_id="x", category=CATEGORY_SECURITY, title="t")
        d = e.to_dict()
        assert d["entry_id"] == "x"
        assert d["category"] == "security_findings"

    def test_from_dict(self):
        d = {"entry_id": "x", "category": "test_patterns", "title": "t",
             "confidence": 0.9, "status": "adopted", "times_used": 5}
        e = KnowledgeEntry.from_dict(d)
        assert e.confidence == 0.9
        assert e.status == "adopted"
        assert e.times_used == 5

    def test_from_dict_defaults(self):
        e = KnowledgeEntry.from_dict({})
        assert e.entry_id == ""
        assert e.confidence == 0.0
        assert e.status == STATUS_PROPOSED

    def test_roundtrip(self):
        e = KnowledgeEntry(
            entry_id="p1", category=CATEGORY_CODE, title="Pattern",
            confidence=0.95, status=STATUS_CANONICAL, times_used=100,
        )
        e2 = KnowledgeEntry.from_dict(e.to_dict())
        assert e2.to_dict() == e.to_dict()


# ---------------------------------------------------------------------------
# TestPatternEntry
# ---------------------------------------------------------------------------

class TestTestPatternEntry:
    def test_create(self):
        tp = TestPatternEntry(
            entry_id="tp-001",
            title="Race condition test",
            applies_to=["registration", "creation"],
            test_code="def test_concurrent...",
            prevented_bugs=["bug-001"],
        )
        assert tp.category == CATEGORY_TEST
        assert len(tp.applies_to) == 2

    def test_to_dict(self):
        tp = TestPatternEntry(entry_id="tp", title="t", applies_to=["x"],
                             test_code="code", prevented_bugs=[])
        d = tp.to_dict()
        assert d["applies_to"] == ["x"]
        assert d["test_code"] == "code"

    def test_from_dict(self):
        d = {"entry_id": "tp", "title": "t", "applies_to": ["a"],
             "test_code": "c", "prevented_bugs": ["b1"], "confidence": 0.8}
        tp = TestPatternEntry.from_dict(d)
        assert tp.applies_to == ["a"]
        assert tp.prevented_bugs == ["b1"]

    def test_from_dict_defaults(self):
        tp = TestPatternEntry.from_dict({})
        assert tp.applies_to == []
        assert tp.test_code == ""


# ---------------------------------------------------------------------------
# SecurityPatternEntry
# ---------------------------------------------------------------------------

class TestSecurityPatternEntry:
    def test_create(self):
        sp = SecurityPatternEntry(
            entry_id="sp-001",
            title="SQL injection via f-string",
            vulnerability_type="input_validation",
            cwe="CWE-89",
            owasp="A03:2021",
            regex_pattern=r"f['\"].*{.*}",
            remediation="Use parameterized queries",
        )
        assert sp.category == CATEGORY_SECURITY
        assert sp.cwe == "CWE-89"

    def test_to_dict(self):
        sp = SecurityPatternEntry(
            entry_id="sp", title="t",
            vulnerability_type="auth", cwe="CWE-1", owasp="A1",
            regex_pattern="pat", remediation="fix",
        )
        d = sp.to_dict()
        assert d["vulnerability_type"] == "auth"
        assert d["cwe"] == "CWE-1"

    def test_from_dict(self):
        d = {"entry_id": "sp", "title": "t", "vulnerability_type": "auth",
             "cwe": "CWE-89", "owasp": "A03", "regex_pattern": "p",
             "remediation": "r", "confidence": 0.99}
        sp = SecurityPatternEntry.from_dict(d)
        assert sp.owasp == "A03"

    def test_from_dict_defaults(self):
        sp = SecurityPatternEntry.from_dict({})
        assert sp.vulnerability_type == ""
        assert sp.cwe == ""


# ---------------------------------------------------------------------------
# DesignPatternEntry
# ---------------------------------------------------------------------------

class TestDesignPatternEntry:
    def test_create(self):
        dp = DesignPatternEntry(
            entry_id="dp-001",
            title="Primary button color",
            component="Button",
            property_name="background_color",
            preferred_value="#0B66F0",
            wcag_compliance="AAA",
        )
        assert dp.category == CATEGORY_DESIGN
        assert dp.component == "Button"

    def test_to_dict(self):
        dp = DesignPatternEntry(
            entry_id="dp", title="t", component="C",
            property_name="p", preferred_value="v", wcag_compliance="AA",
        )
        d = dp.to_dict()
        assert d["component"] == "C"
        assert d["wcag_compliance"] == "AA"

    def test_from_dict(self):
        d = {"entry_id": "dp", "title": "t", "component": "Input",
             "property_name": "border", "preferred_value": "#ccc",
             "wcag_compliance": "AA", "confidence": 0.7}
        dp = DesignPatternEntry.from_dict(d)
        assert dp.component == "Input"

    def test_from_dict_defaults(self):
        dp = DesignPatternEntry.from_dict({})
        assert dp.component == ""
        assert dp.wcag_compliance == ""


# ---------------------------------------------------------------------------
# KnowledgeStore
# ---------------------------------------------------------------------------

class TestKnowledgeStore:
    def test_create_empty(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        assert store.entries == {}

    def test_add_entry(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        entry = KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="Test")
        store.add(entry)
        assert "e1" in store.entries

    def test_get_entry(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        entry = KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="Test")
        store.add(entry)
        result = store.get("e1")
        assert result is not None
        assert result.title == "Test"

    def test_get_missing(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        assert store.get("nonexistent") is None

    def test_search_by_category(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.add(KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="T1"))
        store.add(KnowledgeEntry(entry_id="e2", category=CATEGORY_SECURITY, title="T2"))
        store.add(KnowledgeEntry(entry_id="e3", category=CATEGORY_TEST, title="T3"))
        results = store.search(category=CATEGORY_TEST)
        assert len(results) == 2

    def test_search_by_query(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.add(KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="SQL injection test"))
        store.add(KnowledgeEntry(entry_id="e2", category=CATEGORY_TEST, title="Auth test"))
        results = store.search(query="sql")
        assert len(results) == 1

    def test_search_by_category_and_query(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.add(KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="SQL test"))
        store.add(KnowledgeEntry(entry_id="e2", category=CATEGORY_SECURITY, title="SQL pattern"))
        results = store.search(category=CATEGORY_TEST, query="sql")
        assert len(results) == 1
        assert results[0].entry_id == "e1"

    def test_save_and_load(self, tmp_path):
        store_dir = str(tmp_path / "kb")
        store = KnowledgeStore(store_dir)
        store.add(KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="Test"))
        store.save()

        store2 = KnowledgeStore(store_dir)
        store2.load()
        assert "e1" in store2.entries
        assert store2.entries["e1"].title == "Test"

    def test_load_empty_dir(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.load()
        assert store.entries == {}

    def test_remove_entry(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.add(KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="T"))
        store.remove("e1")
        assert "e1" not in store.entries

    def test_remove_missing_noop(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.remove("nonexistent")  # should not raise

    def test_count(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.add(KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="T"))
        store.add(KnowledgeEntry(entry_id="e2", category=CATEGORY_TEST, title="T"))
        assert store.count() == 2


# ---------------------------------------------------------------------------
# create_* helpers
# ---------------------------------------------------------------------------

class TestCreateHelpers:
    def test_create_test_pattern(self):
        tp = create_test_pattern(
            title="Concurrent duplicate",
            applies_to=["registration"],
            test_code="def test...",
        )
        assert tp.category == CATEGORY_TEST
        assert tp.entry_id.startswith("tp-")

    def test_create_security_pattern(self):
        sp = create_security_pattern(
            title="SQL injection",
            vulnerability_type="input_validation",
            cwe="CWE-89",
            remediation="Parameterize",
        )
        assert sp.category == CATEGORY_SECURITY
        assert sp.entry_id.startswith("sp-")

    def test_create_design_pattern(self):
        dp = create_design_pattern(
            title="Button color",
            component="Button",
            property_name="bg",
            preferred_value="#000",
        )
        assert dp.category == CATEGORY_DESIGN
        assert dp.entry_id.startswith("dp-")


# ---------------------------------------------------------------------------
# search_patterns
# ---------------------------------------------------------------------------

class TestSearchPatterns:
    def test_search_in_store(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.add(create_test_pattern(title="SQL test", applies_to=["search"], test_code="c"))
        store.add(create_security_pattern(title="SQL vuln", vulnerability_type="input", cwe="CWE-89", remediation="r"))
        results = search_patterns(store, query="sql")
        assert len(results) == 2

    def test_search_by_category(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        store.add(create_test_pattern(title="Test A", applies_to=[], test_code="c"))
        store.add(create_design_pattern(title="Design A", component="C", property_name="p", preferred_value="v"))
        results = search_patterns(store, category=CATEGORY_DESIGN)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# promote_pattern
# ---------------------------------------------------------------------------

class TestPromotePattern:
    def test_promote_proposed_to_adopted(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        entry = KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="T",
                              confidence=0.5, status=STATUS_PROPOSED)
        store.add(entry)
        result = promote_pattern(store, "e1")
        assert result["promoted"] is True
        assert store.get("e1").status == STATUS_ADOPTED

    def test_promote_adopted_to_canonical(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        entry = KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="T",
                              confidence=0.95, status=STATUS_ADOPTED)
        store.add(entry)
        result = promote_pattern(store, "e1")
        assert result["promoted"] is True
        assert store.get("e1").status == STATUS_CANONICAL

    def test_promote_canonical_stays(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        entry = KnowledgeEntry(entry_id="e1", category=CATEGORY_TEST, title="T",
                              status=STATUS_CANONICAL)
        store.add(entry)
        result = promote_pattern(store, "e1")
        assert result["promoted"] is False

    def test_promote_nonexistent(self, tmp_path):
        store = KnowledgeStore(str(tmp_path / "kb"))
        result = promote_pattern(store, "nonexistent")
        assert result["promoted"] is False
        assert "not found" in result["error"]
