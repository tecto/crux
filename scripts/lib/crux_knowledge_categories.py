"""Extended knowledge base categories for Crux.

Supports four knowledge domains: test patterns, security findings,
design patterns, and code patterns. Each with structured entries,
search, and promotion through confidence levels.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field


CATEGORY_TEST = "test_patterns"
CATEGORY_SECURITY = "security_findings"
CATEGORY_DESIGN = "design_patterns"
CATEGORY_CODE = "code_patterns"

STATUS_PROPOSED = "proposed"
STATUS_ADOPTED = "adopted"
STATUS_CANONICAL = "canonical"

_PROMOTION_ORDER = [STATUS_PROPOSED, STATUS_ADOPTED, STATUS_CANONICAL]


# ---------------------------------------------------------------------------
# Base entry
# ---------------------------------------------------------------------------

@dataclass
class KnowledgeEntry:
    entry_id: str = ""
    category: str = ""
    title: str = ""
    confidence: float = 0.0
    status: str = STATUS_PROPOSED
    times_used: int = 0

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "category": self.category,
            "title": self.title,
            "confidence": self.confidence,
            "status": self.status,
            "times_used": self.times_used,
        }

    @classmethod
    def from_dict(cls, d: dict) -> KnowledgeEntry:
        return cls(
            entry_id=d.get("entry_id", ""),
            category=d.get("category", ""),
            title=d.get("title", ""),
            confidence=d.get("confidence", 0.0),
            status=d.get("status", STATUS_PROPOSED),
            times_used=d.get("times_used", 0),
        )


# ---------------------------------------------------------------------------
# Specialized entries
# ---------------------------------------------------------------------------

@dataclass
class TestPatternEntry(KnowledgeEntry):
    applies_to: list[str] = field(default_factory=list)
    test_code: str = ""
    prevented_bugs: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.category = CATEGORY_TEST

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["applies_to"] = list(self.applies_to)
        d["test_code"] = self.test_code
        d["prevented_bugs"] = list(self.prevented_bugs)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> TestPatternEntry:
        return cls(
            entry_id=d.get("entry_id", ""),
            title=d.get("title", ""),
            confidence=d.get("confidence", 0.0),
            status=d.get("status", STATUS_PROPOSED),
            times_used=d.get("times_used", 0),
            applies_to=list(d.get("applies_to", [])),
            test_code=d.get("test_code", ""),
            prevented_bugs=list(d.get("prevented_bugs", [])),
        )


@dataclass
class SecurityPatternEntry(KnowledgeEntry):
    vulnerability_type: str = ""
    cwe: str = ""
    owasp: str = ""
    regex_pattern: str = ""
    remediation: str = ""

    def __post_init__(self):
        self.category = CATEGORY_SECURITY

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["vulnerability_type"] = self.vulnerability_type
        d["cwe"] = self.cwe
        d["owasp"] = self.owasp
        d["regex_pattern"] = self.regex_pattern
        d["remediation"] = self.remediation
        return d

    @classmethod
    def from_dict(cls, d: dict) -> SecurityPatternEntry:
        return cls(
            entry_id=d.get("entry_id", ""),
            title=d.get("title", ""),
            confidence=d.get("confidence", 0.0),
            status=d.get("status", STATUS_PROPOSED),
            times_used=d.get("times_used", 0),
            vulnerability_type=d.get("vulnerability_type", ""),
            cwe=d.get("cwe", ""),
            owasp=d.get("owasp", ""),
            regex_pattern=d.get("regex_pattern", ""),
            remediation=d.get("remediation", ""),
        )


@dataclass
class DesignPatternEntry(KnowledgeEntry):
    component: str = ""
    property_name: str = ""
    preferred_value: str = ""
    wcag_compliance: str = ""

    def __post_init__(self):
        self.category = CATEGORY_DESIGN

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["component"] = self.component
        d["property_name"] = self.property_name
        d["preferred_value"] = self.preferred_value
        d["wcag_compliance"] = self.wcag_compliance
        return d

    @classmethod
    def from_dict(cls, d: dict) -> DesignPatternEntry:
        return cls(
            entry_id=d.get("entry_id", ""),
            title=d.get("title", ""),
            confidence=d.get("confidence", 0.0),
            status=d.get("status", STATUS_PROPOSED),
            times_used=d.get("times_used", 0),
            component=d.get("component", ""),
            property_name=d.get("property_name", ""),
            preferred_value=d.get("preferred_value", ""),
            wcag_compliance=d.get("wcag_compliance", ""),
        )


# ---------------------------------------------------------------------------
# KnowledgeStore
# ---------------------------------------------------------------------------

class KnowledgeStore:
    """In-memory knowledge store with JSON persistence."""

    def __init__(self, store_dir: str):
        self.store_dir = store_dir
        self.entries: dict[str, KnowledgeEntry] = {}

    def add(self, entry: KnowledgeEntry) -> None:
        self.entries[entry.entry_id] = entry

    def get(self, entry_id: str) -> KnowledgeEntry | None:
        return self.entries.get(entry_id)

    def remove(self, entry_id: str) -> None:
        self.entries.pop(entry_id, None)

    def count(self) -> int:
        return len(self.entries)

    def search(
        self,
        category: str | None = None,
        query: str | None = None,
    ) -> list[KnowledgeEntry]:
        results = list(self.entries.values())
        if category:
            results = [e for e in results if e.category == category]
        if query:
            q = query.lower()
            results = [e for e in results if q in e.title.lower()]
        return results

    def save(self) -> None:
        os.makedirs(self.store_dir, exist_ok=True)
        data = {eid: e.to_dict() for eid, e in self.entries.items()}
        path = os.path.join(self.store_dir, "knowledge_store.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        path = os.path.join(self.store_dir, "knowledge_store.json")
        try:
            with open(path) as f:
                data = json.load(f)
            self.entries = {
                eid: KnowledgeEntry.from_dict(edata)
                for eid, edata in data.items()
            }
        except (FileNotFoundError, json.JSONDecodeError):
            pass


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def _short_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def create_test_pattern(
    title: str,
    applies_to: list[str],
    test_code: str,
    prevented_bugs: list[str] | None = None,
) -> TestPatternEntry:
    return TestPatternEntry(
        entry_id=_short_id("tp"),
        title=title,
        applies_to=list(applies_to),
        test_code=test_code,
        prevented_bugs=list(prevented_bugs) if prevented_bugs else [],
    )


def create_security_pattern(
    title: str,
    vulnerability_type: str,
    cwe: str,
    remediation: str,
    owasp: str = "",
    regex_pattern: str = "",
) -> SecurityPatternEntry:
    return SecurityPatternEntry(
        entry_id=_short_id("sp"),
        title=title,
        vulnerability_type=vulnerability_type,
        cwe=cwe,
        owasp=owasp,
        regex_pattern=regex_pattern,
        remediation=remediation,
    )


def create_design_pattern(
    title: str,
    component: str,
    property_name: str,
    preferred_value: str,
    wcag_compliance: str = "",
) -> DesignPatternEntry:
    return DesignPatternEntry(
        entry_id=_short_id("dp"),
        title=title,
        component=component,
        property_name=property_name,
        preferred_value=preferred_value,
        wcag_compliance=wcag_compliance,
    )


# ---------------------------------------------------------------------------
# Search and promote
# ---------------------------------------------------------------------------

def search_patterns(
    store: KnowledgeStore,
    category: str | None = None,
    query: str | None = None,
) -> list[KnowledgeEntry]:
    """Search patterns across the knowledge store."""
    return store.search(category=category, query=query)


def promote_pattern(store: KnowledgeStore, entry_id: str) -> dict:
    """Promote a pattern to the next status level."""
    entry = store.get(entry_id)
    if entry is None:
        return {"promoted": False, "error": f"Entry '{entry_id}' not found"}

    idx = _PROMOTION_ORDER.index(entry.status) if entry.status in _PROMOTION_ORDER else -1
    if idx >= len(_PROMOTION_ORDER) - 1:
        return {"promoted": False, "error": f"Already at highest status: {entry.status}"}

    entry.status = _PROMOTION_ORDER[idx + 1]
    return {"promoted": True, "new_status": entry.status}
