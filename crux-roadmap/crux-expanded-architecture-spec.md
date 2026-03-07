# Crux OS: Expanded Architecture Specification
## TDD/BDD Enforcement, Recursive Security Audits, and Design Modes

**Document Version:** 2.0
**Date:** 2026-03-05
**Status:** Formal Specification
**Scope:** Extends existing Crux OS architecture with three major capabilities

---

## 1. Executive Summary

This specification extends Crux OS, the self-improving AI operating system, with three major new capabilities:

1. **TDD/BDD Enforcement Gate** – A new test-specification gate (Gate 2) that enforces test-driven development before feature implementation across all build modes, with configurable strictness levels and BDD support.

2. **Recursive Security Audit Loop** – Evolution of the existing adversarial audit gate (Gate 3) into a recursive process that audits, fixes, re-audits, and converges to zero new findings, with seven independent audit categories and security knowledge base integration.

3. **Design Modes (5 new modes)** – First-class support for UI/UX design work using the same safety pipeline, knowledge base, and continuous improvement infrastructure as code work. Includes Figma API integration, CSS/Tailwind generation, and image-based mockups.

### Backward Compatibility Guarantee

All changes are **strictly additive**. The existing 15 modes and five-gate pipeline remain fully functional. Organizations can:
- Keep the pipeline at 5 gates by setting TDD enforcement to `off` and recursion iteration limit to 1
- Adopt new capabilities incrementally per project
- Use design modes only on projects that require design work
- Maintain legacy behavior indefinitely if preferred

---

## 2. Expanded Safety Pipeline

### 2.1 Pipeline Architecture

The enhanced pipeline now has **seven stages** (with two gates optional):

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CRUX OS ENHANCED SAFETY PIPELINE                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Stage 1: PREFLIGHT                                                │
│  ├─ Parse input, validate context                                 │
│  ├─ Check knowledge base consistency                              │
│  ├─ Load project security policy                                 │
│  └─ Risk classification (Low/Medium/High/Critical)               │
│         ↓                                                          │
│  Stage 2: TEST SPECIFICATION [NEW - Gate 2]                     │
│  ├─ For build modes ONLY (build-py, build-ex, design-*)        │
│  ├─ Plan mode: generate test spec (what, how, edge cases)      │
│  ├─ Test mode: write test files (unit, integration, e2e)       │
│  ├─ Correction loop: tests → fix → tests until GREEN            │
│  └─ Conditional: Can be set to `off` for legacy behavior       │
│         ↓                                                          │
│  Stage 3: SECURITY AUDIT LOOP [NEW - Gate 3 RECURSIVE]          │
│  ├─ Initial audit: 7 categories (input, auth, data, crypto,    │
│  │                   deps, infra, business logic)               │
│  ├─ Audit → categorized findings → severity assessment         │
│  ├─ FIX LOOP:                                                    │
│  │  ├─ Critical/High findings trigger fixes                    │
│  │  ├─ Re-audit with same categorization                      │
│  │  ├─ Track convergence (zero new findings)                 │
│  │  └─ Iterate max_iterations times (default 3)              │
│  ├─ Medium findings flagged, Low/Info logged only              │
│  └─ Security knowledge base updated with all findings          │
│         ↓                                                          │
│  Stage 4: SECOND OPINION [Gate 4]                              │
│  ├─ 32B model reviews output                                   │
│  ├─ Check test coverage (if Gate 2 passed)                    │
│  ├─ Spot-check security findings (if Gate 3 recursive loop)  │
│  └─ Thumbs up or send back to stage 3                        │
│         ↓                                                          │
│  Stage 5: HUMAN APPROVAL [Gate 5]                             │
│  ├─ Human operator reviews all findings and fixes            │
│  ├─ Can approve, reject, or request modifications           │
│  └─ Approval unblocks DRY_RUN                               │
│         ↓                                                          │
│  Stage 6: DRY RUN [Existing]                                 │
│  ├─ Execute in sandbox                                       │
│  ├─ Validate behavior matches intent                         │
│  └─ Failure returns to stage 3                              │
│         ↓                                                          │
│  Stage 7: DESIGN VALIDATION [NEW - Gate 7 CONDITIONAL]       │
│  ├─ ONLY applies when design modes (design-*) are involved  │
│  ├─ Design-review mode validates design output              │
│  ├─ Check WCAG compliance, brand consistency               │
│  ├─ Validate design ↔ code handoff data                    │
│  └─ Failure returns to design mode                         │
│         ↓                                                          │
│  ✓ APPROVED FOR PRODUCTION                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Gate Application by Risk Level

| Risk Level | Gates Active | Notes |
|------------|------------|-------|
| **Low** | 1, 2* | Preflight, optional test spec. No security audit. |
| **Medium** | 1, 2, 3, 5 | Preflight, test spec, security audit, human approval. Skip second opinion. |
| **High** | 1, 2, 3, 4, 5, 6 | All gates except design validation (unless design involved). |
| **Critical** | 1, 2, 3, 4, 5, 6, 7* | All gates. Design validation mandatory if any design mode involved. |

*Gate 2 (test spec) applies only to build modes. Waived for analyst, review, explain modes.
*Gate 7 (design validation) applies only when design-* modes are invoked.

### 2.3 Pipeline Configuration Schema

```yaml
# crux-pipeline-config.yaml
pipeline:
  # Test Spec Gate (Gate 2)
  tdd_enforcement:
    enabled: true
    level: "standard"  # Options: strict, standard, relaxed, off
    apply_to_modes: [build-py, build-ex]
    coverage_minimum: 80  # percent

  # Security Audit Loop (Gate 3)
  security_audit:
    enabled: true
    max_iterations: 3
    categories:
      - input_validation
      - authentication
      - data_exposure
      - cryptography
      - dependencies
      - infrastructure
      - business_logic
    stop_on_convergence: true  # zero new findings
    fail_on_severity: [critical, high]  # blocks if found
    warn_on_severity: [medium]
    log_on_severity: [low, info]

  # Second Opinion (Gate 4)
  second_opinion:
    enabled: true
    model: "32b"  # explicit model or "auto"
    check_test_coverage: true
    check_security_spots: true

  # Design Validation (Gate 7)
  design_validation:
    enabled: true
    wcag_level: "AA"  # AA or AAA
    check_brand_consistency: true
    check_handoff_completeness: true

  # Human Approval (Gate 5) - always enabled
  human_approval:
    required_for_severity: [critical, high, medium]
    optional_for_severity: [low]

  # Dry Run (Gate 6)
  dry_run:
    sandbox: "isolated"  # isolated, container, vm
    timeout_seconds: 300
```

---

## 3. TDD/BDD Enforcement Specification

### 3.1 Test Specification Gate (Gate 2)

The test gate is a three-phase process that enforces test-first development:

#### Phase 1: Test Planning (Plan Mode Invoked)

When build-py, build-ex, or a new build mode is invoked for **feature work**:

1. **Automatic delegation to plan mode** with test-planning context
2. **Plan mode generates a test specification document** containing:
   - What must be tested (functional requirements)
   - How to test it (test strategy per component)
   - Edge cases and boundary conditions
   - Integration points and their tests
   - Performance/load testing requirements (if applicable)
   - Acceptance criteria in human-readable form

Example test specification output:
```markdown
# Test Specification: User Registration Feature

## Components Under Test
- UserRegistrationService.register()
- EmailValidator.validate()
- PasswordHasher.hash()
- UserRepository.create()
- EmailQueue.enqueue()

## Test Categories

### Unit Tests (UserRegistrationService)
- Test case: Happy path (valid email, strong password)
  - Assert: User created, email sent
  - Assertion: user.verified = false

- Edge case: Existing email
  - Assert: Raises UserExistsError

- Edge case: Weak password
  - Assert: Raises PasswordWeakError

### Integration Tests
- Test case: Full registration → email sending
  - Mocks: EmailQueue
  - Assert: Email queued with correct recipient

### E2E Tests
- Test case: User submits form, receives email, clicks verification link
  - Simulates: Browser submission, email system
  - Assert: User.verified transitions true

## Coverage Targets
- Unit: 95%+
- Integration: 80%+
- E2E: 3+ critical paths
```

#### Phase 2: Test Writing (Test Mode Invoked)

1. **Test mode receives the test specification**
2. **Test mode writes actual test files BEFORE implementation code**
3. Test files are created in project standard locations:
   - `tests/unit/test_*.py` (Python)
   - `test/unit/*.exs` (Elixir)
   - `__tests__/*.test.js` (JavaScript/TypeScript)
4. **Tests are run to confirm they fail** (red phase of TDD)
5. All tests must execute; failures are documented as intentional

Example test mode output (pytest):
```python
# tests/unit/test_user_registration.py
import pytest
from app.services.user_registration import UserRegistrationService
from app.models import User
from app.exceptions import UserExistsError, PasswordWeakError

class TestUserRegistrationService:

    def test_register_valid_user(self, user_service, user_repo):
        """Happy path: user created with valid email and strong password"""
        result = user_service.register(
            email="user@example.com",
            password="SecurePass123!"
        )
        assert result.user_id is not None
        assert user_repo.get_by_email("user@example.com") is not None
        assert result.user.verified is False

    def test_register_existing_email_raises_error(self, user_service, user_repo):
        """Edge case: duplicate email raises UserExistsError"""
        user_repo.create(email="taken@example.com", password_hash="hash")

        with pytest.raises(UserExistsError):
            user_service.register(
                email="taken@example.com",
                password="SecurePass123!"
            )

    def test_register_weak_password_raises_error(self, user_service):
        """Edge case: weak password raises PasswordWeakError"""
        with pytest.raises(PasswordWeakError):
            user_service.register(
                email="user@example.com",
                password="weak"
            )
```

#### Phase 3: Implementation and Correction Loop

1. **Build mode (build-py/build-ex) writes implementation code** to pass the test suite
2. **Tests run automatically after implementation**
3. **Correction loop**: If any tests fail:
   - Build mode analyzes failures
   - Updates implementation (or tests if spec was wrong)
   - Re-runs tests
   - Loops until all tests pass (green phase)
4. **All tests must be green before Gate 2 completes**

### 3.2 TDD Enforcement Levels

#### `strict`
- **All tests must be written first** (red phase confirmed)
- **All tests must pass** before proceeding to Gate 3
- **No exceptions or skips allowed**
- Code coverage minimum enforced per build mode
- Blocks entire pipeline if any test skipped

#### `standard` (default)
- **Unit tests must be written first**
- **Integration/E2E tests** can follow implementation (within same build session)
- **All tests must eventually pass** before Gate 3
- Code coverage minimum: 80% of touched code
- Allows pragmatic fast iteration

#### `relaxed`
- **Tests can be written alongside implementation**
- **Some manual acceptance testing allowed** alongside automated tests
- Code coverage minimum: 60%
- Suitable for prototypes and exploratory work

#### `off`
- **Legacy behavior**: No test specification gate
- Pipeline runs with original 5 gates
- Backward compatibility mode

### 3.3 BDD/Gherkin Integration

For user-facing features, the test mode can generate Gherkin specifications that translate to executable tests:

```gherkin
# features/user_registration.feature
Feature: User Registration
  As a new user
  I want to create an account
  So that I can access the platform

  Scenario: Successful registration with valid credentials
    Given the registration page is open
    When I enter email "user@example.com"
    And I enter password "SecurePass123!"
    And I click the register button
    Then my account should be created
    And I should receive a verification email
    And I should be redirected to the verification page

  Scenario: Registration fails with duplicate email
    Given an account already exists for "taken@example.com"
    When I try to register with email "taken@example.com"
    Then I should see the error "Email already registered"
    And no new account should be created

  Scenario: Registration fails with weak password
    When I enter email "user@example.com"
    And I enter password "weak"
    And I click the register button
    Then I should see an error about password strength
```

These translate to step definitions:
```python
# features/steps/registration_steps.py
from behave import given, when, then

@when('I enter email "{email}"')
def step_enter_email(context, email):
    context.browser.fill_email_field(email)

@when('I enter password "{password}"')
def step_enter_password(context, password):
    context.browser.fill_password_field(password)

@when('I click the register button')
def step_click_register(context):
    context.browser.click_register_button()

@then('my account should be created')
def step_account_created(context):
    assert context.user_service.get_by_email(context.email) is not None
```

### 3.4 Coverage Tracking System

The test mode maintains a coverage database:

```json
{
  "project_id": "myapp",
  "coverage_summary": {
    "overall_percent": 84.5,
    "unit_percent": 92.3,
    "integration_percent": 78.9,
    "e2e_percent": 65.0,
    "by_mode": {
      "build-py": 89.2,
      "build-ex": 81.5
    },
    "untested_lines": 287,
    "critical_untested_paths": [
      "payment_processing.py:1204-1250",
      "email_service.py:567-589"
    ]
  },
  "test_history": [
    {
      "timestamp": "2026-03-05T14:22:10Z",
      "mode": "build-py",
      "feature": "user_registration",
      "tests_written": 12,
      "tests_passed": 12,
      "coverage_delta": "+3.2%"
    }
  ]
}
```

### 3.5 Test Knowledge Integration

When tests fail in production (i.e., a bug escapes), the correction detection system:

1. Identifies that a bug occurred
2. Generates the missing test case that would have caught it
3. Adds this test to the **test knowledge base**
4. Future test generation (for similar features) automatically includes similar edge case tests

Example flow:
```
Production Bug Detected: User registration with duplicate email succeeds
    ↓
Correction Detection: This should have been caught by existing test suite
    ↓
Generate Missing Test: Test for race condition in UserRepository.create()
    ↓
Add to Knowledge Base: {
      "test_pattern": "concurrent_duplicate_check",
      "applies_to": ["registration", "creation", "unique_constraint"],
      "confidence": 0.95
    }
    ↓
Future Test Generation: When writing tests for "account creation",
    system suggests concurrent duplicate test cases
```

### 3.6 Test Mode Definition

Following the Crux mode template (150-200 words, positive instructions, first/last position rules):

```markdown
## Mode: test

**Purpose:** Write test-first code ensuring quality through comprehensive test coverage. Generate test specifications, test files (unit, integration, E2E), and execute test suites to validate implementation against requirements.

**Primary Actions:**
1. Analyze requirements and generate test specification (what, how, edge cases)
2. Write test files in project-standard locations (pytest, ExUnit, Jest, Playwright, Cypress)
3. Run tests and validate RED phase (tests fail before implementation)
4. Accept implementation code and run full test suites
5. Implement correction loops until all tests pass (GREEN phase)
6. Track test coverage and generate coverage reports
7. Generate Gherkin BDD specs for user-facing features
8. Update test knowledge base with patterns that catch real bugs

**Scope:** Test file writing, test execution, coverage analysis, BDD specification, test knowledge management. Does NOT write implementation code; delegates to build-py/build-ex after tests are written.

**Tools:** pytest, pytest-cov, ExUnit, Jest, Playwright, Cypress, Behave, Cucumber. Can invoke build-py/build-ex for implementation work after test RED phase confirmed.

**First:** Always confirm test specification with requirements before writing test code.
**Last:** Verify all tests pass GREEN before returning control to build mode for implementation.

**Safety:** Tests serve as executable specifications. Comprehensive coverage reduces security surface. Regression tests prevent bugs from recurring.
```

---

## 4. Recursive Security Audit Loop Specification

### 4.1 Security Audit Loop Architecture

The security audit gate evolves from a single-pass review into a recursive process:

```
┌─────────────────────────────────────────────────┐
│     SECURITY AUDIT LOOP (Gate 3 - RECURSIVE)   │
├─────────────────────────────────────────────────┤
│                                                  │
│  INPUT: Generated code from Stage 2 (or Stage 1 for non-build modes)
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  AUDIT ITERATION N                       │  │
│  ├──────────────────────────────────────────┤  │
│  │                                          │  │
│  │  Category 1: Input Validation            │  │
│  │  ├─ SQL injection patterns               │  │
│  │  ├─ XSS vulnerabilities                  │  │
│  │  ├─ Command injection                    │  │
│  │  └─ Path traversal                       │  │
│  │                                          │  │
│  │  Category 2: Authentication & Authz      │  │
│  │  ├─ Session management                   │  │
│  │  ├─ Token handling (JWT, OAuth)          │  │
│  │  ├─ RBAC implementation                  │  │
│  │  └─ Privilege escalation paths           │  │
│  │                                          │  │
│  │  Category 3: Data Exposure               │  │
│  │  ├─ Secrets in logs                      │  │
│  │  ├─ Error message leakage                │  │
│  │  ├─ PII handling in memory               │  │
│  │  └─ Debug code in production             │  │
│  │                                          │  │
│  │  Category 4: Cryptography                │  │
│  │  ├─ Key management                       │  │
│  │  ├─ Algorithm selection                  │  │
│  │  ├─ Entropy generation                   │  │
│  │  └─ Initialization vectors               │  │
│  │                                          │  │
│  │  Category 5: Dependency Vulnerabilities  │  │
│  │  ├─ Known CVEs in dependencies           │  │
│  │  ├─ Deprecated package versions          │  │
│  │  ├─ Version pinning compliance           │  │
│  │  └─ Supply chain risks                   │  │
│  │                                          │  │
│  │  Category 6: Infrastructure Security     │  │
│  │  ├─ Network exposure (ports, endpoints)  │  │
│  │  ├─ Container security (escape vectors) │  │
│  │  ├─ Privilege escalation                 │  │
│  │  └─ Cloud IAM configuration              │  │
│  │                                          │  │
│  │  Category 7: Business Logic              │  │
│  │  ├─ Race conditions (TOCTOU)             │  │
│  │  ├─ Idempotency violations               │  │
│  │  ├─ Financial calculation errors         │  │
│  │  └─ State machine invariants             │  │
│  │                                          │  │
│  └──────────────────────────────────────────┘  │
│         ↓                                       │
│  GENERATE FINDINGS (structured, categorized)   │
│         ↓                                       │
│  ASSESS SEVERITY (critical/high/medium/low)   │
│         ↓                                       │
│  FILTER BY POLICY:                            │
│  ├─ Critical/High → MUST FIX (blocks)         │
│  ├─ Medium → REVIEW (flags, doesn't block)   │
│  └─ Low/Info → LOG (informational only)      │
│         ↓                                       │
│  ANY CRITICAL/HIGH FINDINGS?                  │
│  │                                            │
│  ├─ YES → Build mode writes fixes            │
│  │         ↓                                  │
│  │    NEW AUDIT ITERATION N+1                │
│  │         ↓                                  │
│  │    CONVERGENCE CHECK:                     │
│  │    • Same findings as iteration N?        │
│  │      → Still fixing, continue             │
│  │    • ZERO new findings? (converged)       │
│  │      → Proceed to Stage 4 (second opinion) │
│  │    • Max iterations hit (default 3)?      │
│  │      → Human review required              │
│  │                                            │
│  └─ NO → Proceed to Stage 4 (second opinion)  │
│                                                │
└─────────────────────────────────────────────────┘
```

### 4.2 Finding Schema (JSON)

Every security finding is a structured object:

```json
{
  "finding_id": "sec-2026-0342",
  "iteration": 2,
  "category": "input_validation",
  "severity": "high",
  "title": "SQL Injection in user search endpoint",
  "description": "User input is concatenated directly into SQL query without parameterization",
  "cwe": "CWE-89",
  "owasp": "A03:2021 Injection",
  "file_path": "app/services/user_search.py",
  "line_range": [45, 52],
  "code_snippet": "query = f'SELECT * FROM users WHERE name LIKE {search_term}'",
  "vulnerable_pattern": "f-string SQL interpolation",
  "attack_scenario": "Attacker submits search_term = \"'; DROP TABLE users; --\" to delete all user records",
  "remediation": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE name LIKE ?', (search_term,))",
  "confidence": 0.98,
  "false_positive_probability": 0.02,
  "previous_findings": {
    "found_in_iteration": 1,
    "was_fixed": false,
    "fix_attempt_details": "Developer comment suggests awareness but not fixed"
  },
  "knowledge_base_ref": "pattern:sql_injection:f_string_concat",
  "automated_fix_available": false,
  "manual_effort_hours": 0.5,
  "priority_score": 9.2
}
```

### 4.3 Severity Classification

```
Critical (MUST FIX - blocks pipeline)
├─ Remote code execution
├─ Complete authentication bypass
├─ Full database dump/modification
├─ Complete infrastructure compromise
└─ Loss of all user data

High (MUST FIX - blocks pipeline)
├─ Privilege escalation
├─ Significant data exposure (>100 records)
├─ Denial of service
├─ Significant integrity violation
└─ Breaks core security properties

Medium (REVIEW - flags but doesn't block)
├─ Limited data exposure (10-100 records)
├─ Session fixation
├─ Weak cryptography (but functional)
├─ Missing rate limiting
└─ Incomplete input validation

Low (LOG only - informational)
├─ Theoretical vulnerabilities
├─ Defense in depth suggestions
├─ Code quality security improvements
└─ Future-proofing recommendations

Info (LOG only)
├─ Best practice deviations (not security)
├─ Documentation suggestions
└─ Process improvements
```

### 4.4 Resolution Tracking

The security audit loop tracks all fixes:

```json
{
  "finding_id": "sec-2026-0342",
  "resolution_history": [
    {
      "iteration": 1,
      "status": "open",
      "assigned_to": "build-py",
      "suggested_fix": "Use parameterized queries"
    },
    {
      "iteration": 2,
      "status": "in_progress",
      "assigned_to": "build-py",
      "fix_code": "cursor.execute('SELECT * FROM users WHERE name LIKE ?', (search_term,))",
      "fix_attempt_timestamp": "2026-03-05T14:35:22Z"
    },
    {
      "iteration": 3,
      "status": "fixed",
      "fix_verified": true,
      "re_audit_result": "finding_not_detected",
      "fix_verification_timestamp": "2026-03-05T14:37:45Z"
    }
  ]
}
```

### 4.5 Security Knowledge Base Integration

Every finding feeds the knowledge base, improving future audits:

```json
{
  "knowledge_entry": {
    "id": "pattern:sql_injection:f_string_concat",
    "pattern_type": "vulnerability",
    "category": "input_validation",
    "languages": ["python"],
    "detected_times": 47,
    "fixed_times": 47,
    "current_projects_with_issue": [],
    "confidence": 0.99,
    "regex_detection": "query\\s*=\\s*f['\\\"].*{.*}",
    "remediation": "Replace with parameterized queries (cursor.execute with ? placeholders)",
    "owasp": "A03:2021 Injection",
    "cwe": ["CWE-89"],
    "severity": "high",
    "first_seen": "2025-10-13T08:12:34Z",
    "last_seen": "2026-03-05T14:35:22Z",
    "example_fixes": [
      {
        "language": "python",
        "vulnerable": "cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')",
        "fixed": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
      }
    ]
  }
}
```

Over time, the security mode learns from patterns:
- Detects similar vulnerabilities faster
- Suggests more accurate fixes
- Reduces false positive rate through machine learning
- Identifies attack patterns specific to the project

### 4.6 Convergence Logic

The audit loop terminates under these conditions:

```python
class SecurityAuditLoop:
    def __init__(self, max_iterations=3, convergence_window=1):
        self.max_iterations = max_iterations
        self.convergence_window = convergence_window
        self.findings_history = []
        self.iteration = 0

    def should_continue(self):
        """Determines if audit loop should continue"""
        self.iteration += 1

        # Condition 1: Hit max iterations
        if self.iteration > self.max_iterations:
            return "max_iterations_reached"

        # Get critical/high findings from latest audit
        latest_findings = self.findings_history[-1] if self.findings_history else []
        critical_high = [f for f in latest_findings
                        if f.severity in ["critical", "high"]]

        # Condition 2: No critical/high findings remain
        if not critical_high:
            return "convergence_achieved"

        # Condition 3: Same critical/high findings persisting across iterations
        if len(self.findings_history) > self.convergence_window:
            prev_critical_high = [f for f in self.findings_history[-2]
                                 if f.severity in ["critical", "high"]]
            if set(f.finding_id for f in prev_critical_high) == \
               set(f.finding_id for f in critical_high):
                return "fix_stalled"  # Human intervention needed

        # Condition 4: Zero new findings (convergence)
        if len(self.findings_history) > 1:
            prev_findings_set = {f.finding_id for f in self.findings_history[-2]}
            curr_findings_set = {f.finding_id for f in self.findings_history[-1]}
            if not (curr_findings_set - prev_findings_set):  # no new findings
                return "convergence_achieved"

        return "continue_auditing"

    def escape_hatch(self, human_override=False, reason=None):
        """Human can force exit the loop"""
        if human_override:
            return {
                "exit_type": "human_override",
                "reason": reason,
                "blocking_findings": [f for f in self.findings_history[-1]
                                     if f.severity in ["critical", "high"]],
                "requires_acknowledgment": True
            }
```

### 4.7 Maximum Iteration Configuration

```yaml
# In crux-pipeline-config.yaml
security_audit:
  max_iterations: 3  # default
  # Typical progression:
  # - Iteration 1: Find all vulnerabilities, complexity emerges
  # - Iteration 2: Fix high-priority issues, new low-priority found
  # - Iteration 3: Final cleanup, convergence usually achieved

  escape_hatch:
    enabled: true  # humans can override
    requires_security_approval: true
    reason_required: true
```

### 4.8 Security Mode Definition

Following the Crux mode template:

```markdown
## Mode: security

**Purpose:** Identify, categorize, and remediate security vulnerabilities through adversarial analysis. Recursively audit code and infrastructure for exploitable weaknesses across seven security domains.

**Primary Actions:**
1. Audit code across seven security categories (input, auth, data, crypto, dependencies, infrastructure, business logic)
2. Identify vulnerabilities with OWASP/CWE classification
3. Assign severity (critical/high/medium/low/info)
4. Document attack scenarios and impact
5. Suggest remediation for critical/high findings
6. Re-audit after fixes to verify resolution
7. Feed security patterns into knowledge base
8. Track convergence toward zero new findings

**Scope:** Static analysis, dependency scanning, threat modeling, vulnerability assessment. DOES NOT fix code directly; identifies and suggests fixes, which build modes implement.

**Tools:** Bandit, Safety, OWASP Dependency-Check, Semgrep, custom regex patterns from knowledge base. Integrates with security knowledge base for pattern detection.

**Adversarial Mindset:** Think like an attacker. Consider exploitation paths, race conditions, privilege escalation, data leakage, cryptographic weaknesses.

**First:** Parse code and load relevant security patterns from knowledge base for language/framework.
**Last:** Confirm convergence (zero new findings) before releasing audit results to Stage 4.

**Distinct from Review Mode:** Review is broader (correctness, design, maintainability). Security is focused solely on exploitable vulnerabilities.
```

---

## 5. Design Modes Specification

### 5.1 Design Modes Overview

Crux OS gains first-class support for design work through five new modes that integrate with the safety pipeline, knowledge base, and correction detection:

| Mode | Purpose | Outputs |
|------|---------|---------|
| **design-ui** | Generate UI implementations across three backends | Figma files, HTML/CSS, React components, SVG, PNG mockups |
| **design-review** | Validate designs for quality, accessibility, consistency | WCAG compliance report, brand consistency audit, cross-device validation |
| **design-system** | Create/maintain design systems and component libraries | Design tokens, component library, style guide, Figma master components |
| **design-responsive** | Specialize in responsive/adaptive layouts | Breakpoint strategies, mobile-first implementations, performance optimizations |
| **design-accessibility** | Deep WCAG expertise for inclusive design | ARIA specifications, keyboard navigation patterns, color contrast analysis, legal compliance |

### 5.2 Design-UI Mode (Three Backends)

#### Backend 1: Figma API Integration

The design-ui mode can programmatically create and modify Figma designs:

```python
# Mode: design-ui (Figma backend)
# Generates Figma API calls to create designs

from figma_api import FigmaClient

def generate_design(spec):
    """
    Args:
        spec: Design specification with components, layout, tokens
    Returns:
        Figma file with design
    """
    client = FigmaClient(api_key=FIGMA_API_KEY)

    # Create new file
    file = client.create_file(
        name="User Registration Form - Auto Generated",
        team_id=TEAM_ID
    )

    # Create component frame for input field
    input_component = client.add_component(
        file_id=file.id,
        name="TextField",
        description="Reusable text input component",
        props={
            "label": "Label text",
            "error": "false",
            "disabled": "false",
            "value": "Input text"
        }
    )

    # Create instances of component
    email_field = client.add_instance(
        file_id=file.id,
        component_id=input_component.id,
        props={"label": "Email Address"}
    )
    password_field = client.add_instance(
        file_id=file.id,
        component_id=input_component.id,
        props={"label": "Password"}
    )

    # Apply design tokens
    client.apply_typography(
        text_id=email_field.label,
        token_name="typography.body.regular"  # From design system
    )

    client.apply_color(
        shape_id=input_component.border,
        token_name="color.border.default"
    )

    return file.url
```

Output: Live Figma link to editable design file with components, design tokens, prototype interactions.

#### Backend 2: CSS/Tailwind Direct Generation

```python
# Mode: design-ui (CSS/Tailwind backend)
# Generates HTML + CSS/Tailwind directly

def generate_html_component(spec):
    """
    Args:
        spec: Component specification with layout, styling
    Returns:
        HTML + Tailwind CSS
    """
    component_html = f"""
    <div class="form-container max-w-md mx-auto p-6 bg-white rounded-lg shadow">
      <!-- Email Field -->
      <div class="mb-4">
        <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
          Email Address
        </label>
        <input
          id="email"
          type="email"
          class="w-full px-4 py-2 border-2 border-gray-300 rounded-md
                 focus:outline-none focus:border-blue-500 focus:ring-2
                 focus:ring-blue-200 transition-colors"
          placeholder="user@example.com"
          aria-label="Email address"
          aria-required="true"
        />
        <p class="text-xs text-gray-500 mt-1">We'll never share your email.</p>
      </div>

      <!-- Password Field -->
      <div class="mb-6">
        <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
          Password
        </label>
        <input
          id="password"
          type="password"
          class="w-full px-4 py-2 border-2 border-gray-300 rounded-md
                 focus:outline-none focus:border-blue-500 focus:ring-2
                 focus:ring-blue-200 transition-colors"
          placeholder="••••••••"
          aria-label="Password"
          aria-required="true"
          aria-describedby="password-strength"
        />
        <p id="password-strength" class="text-xs text-gray-500 mt-1">
          Min 8 characters, 1 uppercase, 1 number
        </p>
      </div>

      <!-- Submit Button -->
      <button class="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold
                     py-2 px-4 rounded-md transition-colors focus:outline-none
                     focus:ring-2 focus:ring-blue-300 disabled:opacity-50
                     disabled:cursor-not-allowed"
              type="submit"
              aria-label="Create account">
        Create Account
      </button>
    </div>
    """

    # Also generate CSS for custom components
    component_css = """
    /* Design tokens as CSS variables */
    :root {
      --color-primary: #3b82f6;
      --color-primary-hover: #2563eb;
      --color-border: #d1d5db;
      --spacing-unit: 0.25rem;
      --spacing-4: calc(1rem);
      --font-size-sm: 0.875rem;
      --font-weight-medium: 500;
      --radius-md: 0.375rem;
      --shadow-sm: 0 1px 2px 0 rgba(0,0,0,0.05);
    }

    .form-container {
      box-shadow: var(--shadow-sm);
    }
    """

    return {
        "html": component_html,
        "css": component_css,
        "tailwind_config": spec.get("tailwind_config", {})
    }
```

Output: Production-ready HTML + CSS files with accessibility features (ARIA labels, semantic HTML, focus states).

#### Backend 3: Image Generation Models

```python
# Mode: design-ui (Image generation backend)
# Creates mockups via DALL-E, Stable Diffusion

def generate_mockup_image(spec):
    """
    Args:
        spec: Design specification with context, style direction
    Returns:
        PNG mockup image
    """
    import anthropic

    client = anthropic.Anthropic()

    prompt = f"""
    Create a professional UI mockup for a {spec['feature_name']} feature.

    Requirements:
    - Brand colors: {spec['brand_colors']}
    - Layout: {spec['layout_type']}
    - Key elements: {', '.join(spec['elements'])}
    - Style: {spec['design_style']}

    The mockup should show:
    1. How the UI looks at desktop size
    2. Clear typography and spacing
    3. Professional polish
    4. All interactive elements clearly labeled
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )

    # Note: Real implementation would use Stable Diffusion API or DALL-E
    # This demonstrates the architecture
    return {
        "mockup_description": response.content[0].text,
        "backend": "stable_diffusion",
        "generated_at": datetime.now().isoformat()
    }
```

Output: PNG/JPG mockup images suitable for early design validation and stakeholder review.

### 5.3 Design-Review Mode

```markdown
## Mode: design-review

**Purpose:** Validate designs for quality, accessibility, consistency, and brand compliance. Provide structured feedback on visual hierarchy, usability patterns, and WCAG conformance.

**Primary Actions:**
1. Audit design against WCAG 2.1 AA accessibility guidelines
2. Check color contrast ratios (4.5:1 for normal text, 3:1 for large text)
3. Validate brand guideline compliance from project knowledge base
4. Check cross-browser/cross-device consistency
5. Assess responsive breakpoint strategy
6. Review interactive element sizing (mobile touch targets)
7. Evaluate visual hierarchy and information architecture
8. Check for cognitive accessibility (clear labels, consistent patterns)
9. Generate accessibility report (WCAG level achieved)
10. Feed design patterns into knowledge base for continuous improvement

**Scope:** Design file analysis (Figma, Sketch), HTML/CSS review, mockup evaluation. Works with outputs from design-ui mode.

**Tools:** Figma API, custom WCAG checking, axe-core integration, contrast analyzer. Loads brand guidelines from project knowledge base.

**First:** Load design specification and brand guidelines.
**Last:** Produce accessibility audit with pass/fail status and remediation suggestions.

**Severity Levels:** Critical (WCAG AA violations), High (design inconsistencies), Medium (brand deviations), Low (optimization suggestions).

**Integration with Safety Pipeline:** Runs through adapted safety pipeline with accessibility audit replacing security audit.
```

### 5.4 Design-System Mode

```markdown
## Mode: design-system

**Purpose:** Create and maintain design system assets including design tokens, component libraries, and style guides. Ensure consistency across projects and evolve design practices.

**Primary Actions:**
1. Define design tokens: colors, typography, spacing, shadows, shadows, animations
2. Generate token files in multiple formats (JSON, CSS variables, Tailwind config)
3. Create component library documentation
4. Generate Figma master components with design token integration
5. Build style guide (living documentation)
6. Version design tokens and track evolution
7. Detect inconsistencies in existing designs
8. Promote design patterns to all projects via knowledge base
9. Cross-reference components with build-py/build-ex component implementations
10. Generate automated accessibility audit templates for components

**Scope:** Design token generation, component documentation, style guide creation, design asset versioning.

**Tools:** Figma API, design token standards (Design Tokens Community Group), CSS variable generation, JSON schema validation.

**First:** Audit existing designs to extract design tokens.
**Last:** Generate design token files, Figma components, and style guide documentation.

**Knowledge Base Integration:** Successful component patterns are promoted to all projects. Teams can fork and customize.
```

### 5.5 Design-Responsive Mode

```markdown
## Mode: design-responsive

**Purpose:** Specialize in responsive and adaptive layouts. Define breakpoint strategies, implement mobile-first design, and optimize for performance across device types.

**Primary Actions:**
1. Define responsive breakpoint strategy (mobile, tablet, desktop, 4K)
2. Generate CSS media queries aligned with breakpoints
3. Implement fluid typography (scales between min/max sizes)
4. Design mobile-first layouts with progressive enhancement
5. Ensure touch targets meet minimum sizes (48x48px, 44x44px minimum)
6. Validate landscape/portrait orientation handling
7. Optimize images for different device DPIs and viewport widths
8. Review lazy loading strategies
9. Test layout at different viewport sizes
10. Generate responsive design documentation

**Scope:** Responsive layout design, breakpoint strategy, mobile-first implementation, touch-friendly interactions, performance optimization.

**Tools:** CSS Grid, Flexbox, CSS custom properties, responsive image techniques (srcset, picture element), Tailwind responsive classes.

**First:** Understand target devices and network conditions.
**Last:** Validate layouts at all defined breakpoints with performance metrics.

**Performance Awareness:** Mobile-first design naturally promotes performance. Evaluates image optimization, lazy loading, and rendering efficiency.
```

### 5.6 Design-Accessibility Mode

```markdown
## Mode: design-accessibility

**Purpose:** Deep expertise in creating universally accessible designs. Ensure compliance with WCAG 2.1 AAA, Section 508, ADA, and international standards. Design for all users including those with disabilities.

**Primary Actions:**
1. Audit designs against WCAG 2.1 AAA standards (highest level)
2. Verify color contrast (minimum 4.5:1 for normal text)
3. Design keyboard navigation patterns (Tab order, focus indicators)
4. Create ARIA attribute specifications (roles, labels, descriptions)
5. Design for screen reader users (semantic HTML, meaningful alt text)
6. Review cognitive accessibility (clear language, consistent patterns, glanceability)
7. Ensure forms are properly labeled and error messages clear
8. Design for hearing impaired (captions for video, transcripts)
9. Design for motor impaired (large click targets, keyboard shortcuts, voice control)
10. Document legal compliance (ADA, Section 508, EN 301 549)
11. Generate accessibility checklist for implementation team

**Scope:** WCAG AAA compliance, inclusive design patterns, accessibility specifications, legal compliance documentation.

**Tools:** WCAG 2.1 standards, axe-core, ARIA authoring practices guide, WebAIM resources, accessibility testing frameworks.

**First:** Understand user base and accessibility requirements.
**Last:** Provide comprehensive accessibility specification that developers can implement with confidence.

**Perspective:** Design for edge cases first (users with disabilities), creating better designs for everyone.
```

### 5.7 Design ↔ Code Handoff Protocol

When design-ui generates a design, it creates a `design-handoff.md` file:

```markdown
# Design Handoff: User Registration Form

**Generated by:** design-ui mode
**Figma File:** https://figma.com/file/...
**Generated:** 2026-03-05T14:22:10Z
**Design System Version:** 2.3.0

## Component Tree

```
- Container (max-width: 448px)
  - Header
    - Heading: "Create Your Account"
    - Subheading: "Join millions of users"
  - Form
    - EmailField (component: TextField)
      - Label: "Email Address"
      - Placeholder: "user@example.com"
      - Validation: email format
    - PasswordField (component: TextField)
      - Label: "Password"
      - Type: password
      - Validation: min 8 chars, 1 uppercase, 1 number
      - Hint: "Min 8 characters, 1 uppercase, 1 number"
    - SubmitButton (component: Button)
      - Label: "Create Account"
      - Loading state: spinner
      - Success state: checkmark
  - Footer
    - Text: "Already have an account?"
    - Link: "Sign in"
```

## Design Tokens Used

```json
{
  "colors": {
    "primary": "#3B82F6",
    "primary_hover": "#2563EB",
    "text_primary": "#111827",
    "text_secondary": "#6B7280",
    "border_default": "#D1D5DB",
    "background": "#FFFFFF",
    "background_hover": "#F9FAFB"
  },
  "typography": {
    "heading_lg": {
      "font_family": "Inter",
      "font_size": "24px",
      "font_weight": 700,
      "line_height": "1.3"
    },
    "body_regular": {
      "font_family": "Inter",
      "font_size": "14px",
      "font_weight": 400,
      "line_height": "1.5"
    }
  },
  "spacing": {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px"
  }
}
```

## Responsive Breakpoints

- Mobile: 0-640px (single column, full-width)
- Tablet: 641-1024px (single column, centered)
- Desktop: 1025px+ (single column, centered with max-width)

## Interaction Specifications

### Email Field
- **Focus State:** Blue border (#3B82F6), blue ring (4px)
- **Error State:** Red border (#EF4444), error message below
- **Filled State:** Label floats above field (Material Design)

### Password Field
- **Focus State:** Same as email field
- **Error State:** Red border, error message
- **Show/Hide Toggle:** Eye icon on right (only when filled)

### Submit Button
- **Hover:** Background color #2563EB
- **Active:** Transform scale(0.98)
- **Loading:** Spinner appears, button disabled
- **Success:** Checkmark appears for 2 seconds, then navigates to next screen
- **Error:** Red error message appears below button, button re-enables

## Accessibility Requirements

**WCAG 2.1 AA Compliance:**
- [ ] Color contrast 4.5:1 (verified: primary on white = 8.6:1)
- [ ] Touch targets 44x44px minimum (verified: buttons are 48px height)
- [ ] Keyboard navigation: Tab → Email → Password → Submit → Sign In Link
- [ ] Focus indicators visible on all interactive elements
- [ ] Error messages associated with form fields (aria-describedby)
- [ ] Form labels properly connected with aria-label or <label>
- [ ] Semantic HTML: <form>, <label>, <input>, <button>

**ARIA Attributes:**
```html
<form aria-label="User registration form">
  <input
    id="email"
    type="email"
    aria-label="Email address"
    aria-required="true"
    aria-invalid="false"
    aria-describedby="email-error"
  />
  <div id="email-error" role="alert" aria-live="polite">
    <!-- Error message appears here -->
  </div>
</form>
```

## Implementation Notes

- Design tokens are defined in: `src/design/tokens.json`
- Component implementations: `src/components/TextField.tsx`, `src/components/Button.tsx`
- Responsive behavior: Tailwind breakpoints defined in `tailwind.config.js`
- Test fixtures available in `design-handoff.fixtures.json`

## Sign-Off

**Designer:** Sarah Chen
**Review Status:** Approved by design-review mode (WCAG AA, brand consistency ✓)
**Implementation Ready:** Yes
**Last Updated:** 2026-03-05T14:30:22Z
```

When build-py or build-ex receives this handoff, they:
1. Parse the component tree and design tokens
2. Cross-reference with existing component implementations
3. Use design tokens to configure CSS/Tailwind
4. Implement interactions matching specifications
5. Apply ARIA attributes from accessibility section
6. Write tests with design specifications as acceptance criteria

### 5.8 Design Knowledge Base Integration

When developers report "that button color doesn't match the design" or "the spacing looks wrong", the correction detection system:

1. Identifies the design divergence
2. Extracts the component and property that deviated
3. Adds to **design knowledge base** as a learned preference
4. Future design generation uses this feedback

Example flow:
```
Correction Detected: "Update button color from #2563EB to #0B66F0 - looks better"
    ↓
Extract: {
  "component": "Button",
  "property": "hover_color",
  "original": "#2563EB",
  "corrected": "#0B66F0",
  "reason": "better contrast and visibility",
  "confidence": 0.85
}
    ↓
Add to Design Knowledge Base: {
  "design_preference": {
    "applies_to": ["Button"],
    "property": "hover_color",
    "preferred_value": "#0B66F0",
    "times_corrected": 3,
    "times_correct_first": 12,
    "adoption_rate": 0.8,
    "context": "primary actions in registration flow"
  }
}
    ↓
Future Design Generation: When design-ui generates buttons,
    system suggests hover_color = #0B66F0 based on project history
```

### 5.9 Design Safety Pipeline Adaptation

Design modes go through the safety pipeline with adaptations:

```
Preflight → Test Spec* → Security Audit* → Second Opinion → Human Approval → Dry Run → Design Validation
                  ↑                            ↑
         *Optional for design modes    *Accessibility audit
                                        instead of security
```

**Test Spec for design:** Tests validate visual regression (design output matches spec). Can be visual regression tests using pixel comparison or Figma API verification.

**Accessibility Audit for design:** Replaces security audit. Checks WCAG compliance, contrast ratios, keyboard navigation, screen reader compatibility.

---

## 6. Expanded Mode Registry

### Complete Mode Table

| # | Mode Name | Category | Purpose | Tools | Safety Gates | New? |
|---|-----------|----------|---------|-------|--------------|------|
| 1 | build-py | Build | Write Python implementation | pytest, LSP | 1,2,3,4,5,6 | — |
| 2 | build-ex | Build | Write Elixir implementation | ExUnit, LSP | 1,2,3,4,5,6 | — |
| 3 | plan | Planning | Create project/feature plans | markdown | 1,5 | — |
| 4 | infra-architect | Infrastructure | Design cloud/container architecture | Terraform, Docker | 1,3,4,5,6 | — |
| 5 | review | QA | Review code for quality/correctness | LSP | 1,3,4,5 | — |
| 6 | debug | Development | Debug and fix issues | debugger tools | 1,3,4,5,6 | — |
| 7 | explain | Documentation | Write documentation | markdown | 1 | — |
| 8 | analyst | Data | Analyze data and generate insights | pandas, SQL | 1,5 | — |
| 9 | writer | Content | Write content for users | markdown | 1 | — |
| 10 | psych | UX | User psychology and behavior analysis | design specs | 1,5 | — |
| 11 | legal | Compliance | Legal review and contract work | markdown | 1,4,5 | — |
| 12 | strategist | Strategy | Strategic planning and business logic | markdown | 1,5 | — |
| 13 | ai-infra | ML/AI | AI/ML infrastructure and training | PyTorch, TF | 1,3,4,5,6 | — |
| 14 | mac | Automation | macOS automation and scripting | shell, AppleScript | 1,5,6 | — |
| 15 | docker | Container | Docker/container configuration | Docker, K8s | 1,3,4,5,6 | — |
| 16 | **test** | **Testing** | **Test-first development** | **pytest, Jest, Playwright** | **1,2,3,4,5,6** | **✓ NEW** |
| 17 | **security** | **QA/Security** | **Vulnerability identification** | **Bandit, Safety, Semgrep** | **1,3,4,5** | **✓ NEW** |
| 18 | **design-ui** | **Design** | **UI implementation (3 backends)** | **Figma API, Tailwind, image gen** | **1,2,4,5,6,7** | **✓ NEW** |
| 19 | **design-review** | **Design QA** | **Design accessibility/consistency** | **axe-core, Figma API** | **1,3*,4,5,7** | **✓ NEW** |
| 20 | **design-system** | **Design** | **Design system/tokens** | **Figma API, token generation** | **1,5** | **✓ NEW** |
| 21 | **design-responsive** | **Design** | **Responsive/adaptive layouts** | **CSS, Tailwind, responsive testing** | **1,2,5** | **✓ NEW** |
| 22 | **design-accessibility** | **Design** | **WCAG/inclusive design** | **axe-core, ARIA specs** | **1,3*,4,5,7** | **✓ NEW** |

*Gate 3 for design modes is accessibility audit, not security audit.

### Mode Handoff Compatibility Matrix

```
FROM MODE          → TO MODE              HANDOFF DATA
─────────────────────────────────────────────────────────────────
plan               → build-py/build-ex    feature spec, test plan
build-py/build-ex  → review              code, tests, coverage
build-py/build-ex  → test                implementation awaiting tests
test               → build-py/build-ex    test spec, failing test cases
security           → build-py/build-ex    vulnerability report, fixes
design-ui          → build-py/build-ex    design-handoff.md (component tree, tokens, specs)
design-review      → design-ui            accessibility feedback, fixes needed
design-review      → design-system        component/pattern recommendations
design-responsive  → build-py/build-ex    responsive specs, breakpoint strategy
design-accessibility → build-py/build-ex  ARIA specs, accessibility checklist
review             → debug               issues found, test cases
debug              → test                regression test needed
```

### Tool Access Matrix

| Mode | LSP | Bash | File I/O | Figma API | Design Tokens | PyTest | Security Tools | Image Gen |
|------|-----|------|----------|-----------|---------------|--------|----------------|-----------|
| build-py | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | — |
| build-ex | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | — |
| test | — | ✓ | ✓ | — | — | ✓ | — | — |
| security | — | ✓ | ✓ | — | — | — | ✓ | — |
| design-ui | — | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |
| design-review | — | ✓ | ✓ | ✓ | — | — | — | — |
| design-system | — | ✓ | ✓ | ✓ | ✓ | — | — | — |
| design-responsive | — | ✓ | ✓ | — | ✓ | ✓ | — | — |
| design-accessibility | — | ✓ | ✓ | ✓ | — | — | ✓ | — |
| review | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| plan | — | — | ✓ | — | — | — | — | — |

---

## 7. Knowledge Base Extensions

### 7.1 New Knowledge Categories

The knowledge base gains three new domains:

#### Test Patterns Knowledge Base

```json
{
  "category": "test_patterns",
  "entries": [
    {
      "id": "pattern:registration:concurrent_duplicate",
      "applies_to": ["registration", "user_creation", "account_setup"],
      "pattern_type": "edge_case",
      "description": "Race condition when multiple users register with same email simultaneously",
      "detection_frequency": 3,
      "severity": "high",
      "test_code": [
        {
          "language": "python",
          "framework": "pytest",
          "example": "def test_concurrent_duplicate_email_registration..."
        }
      ],
      "prevents_bugs": [
        "users.2026.0152",
        "users.2025.0234"
      ],
      "confidence": 0.98,
      "last_used": "2026-03-05T12:34:56Z"
    }
  ]
}
```

#### Security Findings Knowledge Base

Already specified in Section 4.5. Tracks vulnerability patterns, fixes, and remediation strategies.

#### Design Patterns Knowledge Base

```json
{
  "category": "design_patterns",
  "entries": [
    {
      "id": "pattern:button:primary_color",
      "applies_to": ["Button", "CallToAction", "PrimaryAction"],
      "pattern_type": "component_style",
      "property": "background_color",
      "preferred_value": "#0B66F0",
      "alternatives": ["#3B82F6", "#2563EB"],
      "times_used": 47,
      "times_correct_first": 45,
      "adoption_rate": 0.957,
      "context": "primary actions in registration and onboarding flows",
      "contrast_ratio": 8.6,
      "wcag_compliance": "AAA",
      "last_updated": "2026-03-05T14:22:10Z"
    },
    {
      "id": "pattern:spacing:form_vertical",
      "applies_to": ["Form", "FormGroup", "FormLayout"],
      "pattern_type": "layout_spacing",
      "property": "vertical_gap",
      "preferred_value": "16px",
      "range": ["12px", "24px"],
      "rationale": "Optimal touch target spacing on mobile while maintaining visual grouping",
      "wcag_touch_target": "44x44px_minimum",
      "mobile_optimized": true,
      "projects_using": 12,
      "last_updated": "2026-03-05T10:15:22Z"
    }
  ]
}
```

### 7.2 Cross-Domain Learning

Knowledge flows bidirectionally across domains:

#### Security → Testing
When a security finding is resolved, the resolution becomes a test pattern:

```
Security Finding: SQL injection in user search
    ↓
Resolution: Use parameterized queries
    ↓
Add to Test Patterns Knowledge Base:
{
  "pattern": "parameterized_query_validation",
  "applies_to": ["search", "query_building", "database_access"],
  "test_code": "Test that verifies parameterized query prevents injection"
}
    ↓
Future Test Generation: When writing tests for "product search" feature,
    system automatically includes parameterized query validation tests
```

#### Testing → Design
When tests fail in UI, design patterns are updated:

```
Test Failure: Button click not responding
    ↓
Root Cause: Touch target too small on mobile
    ↓
Update Design Pattern Knowledge:
{
  "pattern": "button_touch_target",
  "minimum_size": "48x48px",
  "failure_count": 3,
  "severity": "high"
}
    ↓
Future Design Generation: design-ui and design-responsive
    modes always specify minimum 48x48px button touch targets
```

#### Design → Security
When accessibility audit finds WCAG violations, security mode is updated:

```
Design Review Finding: Color contrast 3.2:1 (needs 4.5:1)
    ↓
Severity: Medium accessibility issue
    ↓
Update Security Knowledge:
{
  "vulnerability": "wcag_contrast_violation",
  "category": "accessibility",
  "severity": "medium",
  "pattern": "button_color_insufficient_contrast"
}
    ↓
Future Security Audits: system flags insufficient contrast
    as a medium severity finding
```

### 7.3 Knowledge Promotion Paths

Patterns graduate through confidence levels:

```
PROPOSED (newly detected, confidence < 0.7)
    ↓ (confirmed in 3+ projects, confidence > 0.9)
ADOPTED (standard practice across organization)
    ↓ (used in 20+ projects, zero regressions)
CANONICAL (best practice, taught to new team members)
    ↓ (stable for 1+ year, industry standard)
LEGACY (replaced by better pattern, archived for reference)
```

---

## 8. Impact on Existing Modes

### 8.1 Review Mode Changes

**Before:**
- Reviews code for correctness, design, maintainability
- Checks security alongside other concerns

**After:**
- Reviews code for correctness, design, maintainability
- **Delegates security to `security` mode** (focuses only on vulnerabilities)
- Can focus on architectural decisions, performance, maintainability
- Receives security findings from security mode as input
- Simpler, more focused reviews

### 8.2 Build Mode Changes (build-py, build-ex)

**Before:**
- Receives plan/feature spec
- Writes code
- Proceeds to review gate

**After:**
- Receives plan/feature spec + test spec from `plan` mode
- **Receives test files from `test` mode** (tests written first)
- Writes implementation code to pass tests (TDD green phase)
- Correction loop: if tests fail, fixes code until GREEN
- Once all tests pass, proceeds to security audit
- Can still use existing build tools and patterns

### 8.3 Plan Mode Changes

**Before:**
- Creates feature plans with specifications

**After:**
- Creates feature plans with specifications
- **Also generates test specifications** (what to test, edge cases)
- **Also generates design plan** (if UI work needed)
- Can delegate to test mode for test file generation
- Richer, more structured planning

### 8.4 Backward Compatibility

All changes are **strictly additive**:

```yaml
# To maintain legacy behavior:
pipeline:
  tdd_enforcement:
    enabled: false  # skips test gate
    level: "off"

  security_audit:
    max_iterations: 1  # single pass (no recursion)

  design_validation:
    enabled: false  # skips design gate

result: Original 5-gate pipeline still available
```

Organizations can adopt incrementally:
- Enable TDD enforcement on new projects first
- Keep recursive security audits disabled until team is ready
- Use design modes only on projects with explicit design work
- Migrate to new capabilities at own pace

---

## 9. Configuration Schema

### Complete JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Crux OS Pipeline Configuration",
  "type": "object",
  "properties": {
    "metadata": {
      "type": "object",
      "properties": {
        "version": { "type": "string", "default": "2.0" },
        "project_name": { "type": "string" },
        "environment": { "enum": ["dev", "staging", "production"] }
      }
    },

    "pipeline": {
      "type": "object",
      "properties": {

        "preflight": {
          "type": "object",
          "description": "Gate 1: Input validation and risk classification",
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "validate_context": { "type": "boolean", "default": true },
            "check_knowledge_base": { "type": "boolean", "default": true },
            "risk_levels_enabled": {
              "type": "array",
              "items": { "enum": ["low", "medium", "high", "critical"] },
              "default": ["low", "medium", "high", "critical"]
            }
          }
        },

        "tdd_enforcement": {
          "type": "object",
          "description": "Gate 2: Test specification and test-first development",
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "level": {
              "type": "string",
              "enum": ["strict", "standard", "relaxed", "off"],
              "default": "standard",
              "description": "strict: all tests first; standard: unit tests first; relaxed: tests alongside code; off: legacy"
            },
            "apply_to_modes": {
              "type": "array",
              "items": { "type": "string" },
              "default": ["build-py", "build-ex"],
              "description": "Modes that trigger test gate"
            },
            "coverage_minimum": {
              "type": "number",
              "minimum": 0,
              "maximum": 100,
              "default": 80,
              "description": "Required code coverage percentage"
            },
            "coverage_minimum_strict": {
              "type": "number",
              "default": 95,
              "description": "For strict mode, higher minimum"
            },
            "max_correction_iterations": {
              "type": "integer",
              "minimum": 1,
              "default": 10,
              "description": "Max attempts to fix failing tests"
            },
            "bdd_enabled": {
              "type": "boolean",
              "default": true,
              "description": "Generate Gherkin BDD specs for user-facing features"
            }
          }
        },

        "security_audit": {
          "type": "object",
          "description": "Gate 3: Recursive security audit loop",
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "max_iterations": {
              "type": "integer",
              "minimum": 1,
              "default": 3,
              "description": "Maximum recursive audit passes"
            },
            "stop_on_convergence": {
              "type": "boolean",
              "default": true,
              "description": "Exit loop when zero new findings detected"
            },
            "categories": {
              "type": "array",
              "items": {
                "enum": [
                  "input_validation",
                  "authentication",
                  "data_exposure",
                  "cryptography",
                  "dependencies",
                  "infrastructure",
                  "business_logic"
                ]
              },
              "default": [
                "input_validation",
                "authentication",
                "data_exposure",
                "cryptography",
                "dependencies",
                "infrastructure",
                "business_logic"
              ],
              "description": "Security categories to audit"
            },
            "fail_on_severity": {
              "type": "array",
              "items": { "enum": ["critical", "high"] },
              "default": ["critical", "high"],
              "description": "Severity levels that block pipeline"
            },
            "warn_on_severity": {
              "type": "array",
              "items": { "enum": ["medium"] },
              "default": ["medium"],
              "description": "Severity levels that flag but don't block"
            },
            "log_on_severity": {
              "type": "array",
              "items": { "enum": ["low", "info"] },
              "default": ["low", "info"],
              "description": "Severity levels that log only"
            }
          }
        },

        "second_opinion": {
          "type": "object",
          "description": "Gate 4: Secondary review by 32B model",
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "model": {
              "type": "string",
              "default": "auto",
              "description": "Model to use or 'auto' for 32B"
            },
            "check_test_coverage": { "type": "boolean", "default": true },
            "check_security_findings": { "type": "boolean", "default": true }
          }
        },

        "human_approval": {
          "type": "object",
          "description": "Gate 5: Human operator approval",
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "required_for_severity": {
              "type": "array",
              "items": { "enum": ["critical", "high", "medium"] },
              "default": ["critical", "high", "medium"],
              "description": "Severity levels requiring human approval"
            }
          }
        },

        "dry_run": {
          "type": "object",
          "description": "Gate 6: Execute in sandbox environment",
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "sandbox_type": {
              "enum": ["isolated", "container", "vm"],
              "default": "container"
            },
            "timeout_seconds": {
              "type": "integer",
              "minimum": 30,
              "default": 300
            }
          }
        },

        "design_validation": {
          "type": "object",
          "description": "Gate 7: Design validation (conditional)",
          "properties": {
            "enabled": { "type": "boolean", "default": true },
            "apply_when": {
              "type": "string",
              "default": "design_mode_invoked",
              "description": "Only applies when design-* modes involved"
            },
            "wcag_level": {
              "enum": ["A", "AA", "AAA"],
              "default": "AA"
            },
            "check_brand_consistency": { "type": "boolean", "default": true },
            "check_handoff_completeness": { "type": "boolean", "default": true }
          }
        }
      },
      "required": ["preflight"]
    },

    "knowledge_base": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "categories": {
          "type": "array",
          "items": {
            "enum": [
              "test_patterns",
              "security_findings",
              "design_patterns",
              "code_patterns"
            ]
          },
          "default": [
            "test_patterns",
            "security_findings",
            "design_patterns",
            "code_patterns"
          ]
        },
        "auto_promote_patterns": {
          "type": "boolean",
          "default": true,
          "description": "Automatically promote patterns to canonical status when confidence high"
        },
        "cross_project_learning": {
          "type": "boolean",
          "default": true,
          "description": "Share patterns across projects"
        }
      }
    },

    "design_modes": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean", "default": true },
        "ui_backends": {
          "type": "object",
          "properties": {
            "figma": {
              "type": "object",
              "properties": {
                "enabled": { "type": "boolean", "default": true },
                "api_key": { "type": "string" },
                "team_id": { "type": "string" }
              }
            },
            "css_tailwind": {
              "type": "object",
              "properties": {
                "enabled": { "type": "boolean", "default": true },
                "tailwind_config": { "type": "object" }
              }
            },
            "image_generation": {
              "type": "object",
              "properties": {
                "enabled": { "type": "boolean", "default": false },
                "provider": {
                  "enum": ["stable_diffusion", "dall_e", "midjourney"],
                  "default": "stable_diffusion"
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Default Configuration (Standard Setup)

```yaml
# crux-config-default.yaml
metadata:
  version: "2.0"
  environment: production

pipeline:
  preflight:
    enabled: true
    validate_context: true
    check_knowledge_base: true
    risk_levels_enabled: [low, medium, high, critical]

  tdd_enforcement:
    enabled: true
    level: standard  # unit tests required first
    coverage_minimum: 80
    apply_to_modes: [build-py, build-ex]

  security_audit:
    enabled: true
    max_iterations: 3
    stop_on_convergence: true
    fail_on_severity: [critical, high]
    warn_on_severity: [medium]

  second_opinion:
    enabled: true

  human_approval:
    enabled: true
    required_for_severity: [critical, high, medium]

  dry_run:
    enabled: true

  design_validation:
    enabled: true
    wcag_level: AA

knowledge_base:
  enabled: true
  auto_promote_patterns: true
  cross_project_learning: true

design_modes:
  enabled: true
  ui_backends:
    figma:
      enabled: true
    css_tailwind:
      enabled: true
    image_generation:
      enabled: false
```

### Enterprise Configuration (Maximum Safety)

```yaml
# crux-config-enterprise.yaml
metadata:
  version: "2.0"
  environment: production

pipeline:
  preflight:
    enabled: true
    validate_context: true
    check_knowledge_base: true

  tdd_enforcement:
    enabled: true
    level: strict  # all tests first, strict coverage
    coverage_minimum: 95
    max_correction_iterations: 20

  security_audit:
    enabled: true
    max_iterations: 5
    stop_on_convergence: true
    fail_on_severity: [critical, high]
    warn_on_severity: [medium, low]

  second_opinion:
    enabled: true

  human_approval:
    enabled: true
    required_for_severity: [critical, high, medium, low]

  dry_run:
    enabled: true
    sandbox_type: vm  # strongest isolation
    timeout_seconds: 600

  design_validation:
    enabled: true
    wcag_level: AAA  # highest accessibility standard
    check_brand_consistency: true
    check_handoff_completeness: true
```

---

## 10. Crux Standalone vs. Crux Vibe Integration

### 10.1 Crux Standalone (Developer + CLI)

**Scenario:** Single developer using Crux OS locally

```
Developer → Crux CLI
  ↓
  Invokes mode (e.g., `crux build-py --feature user-registration`)
  ↓
  Crux OS Execution Pipeline (all 7 gates)
  ↓
  Knowledge Base (stored locally in project or ~/.crux/)
  ↓
  Output: Production-ready code with tests, security review, design validation
```

**Knowledge Base Scope:**
- Project knowledge (stored in `.crux/knowledge/`)
- User knowledge (stored in `~/.crux/knowledge/`)
- Public knowledge (curated patterns from ecosystem)

**Advantages:**
- Works offline
- Full control over pipeline configuration
- Knowledge stays on developer's machine
- No external dependencies

**Limitations:**
- Knowledge limited to single developer's experience
- Patterns not shared across teams
- Less powerful than distributed system

### 10.2 Crux Vibe Integration (Orchestration Layer)

**Scenario:** Organization using Crux Vibe to coordinate multiple Crux instances

```
Product Manager (Vibe UI)
  ↓ specifies feature with design & requirements
Crux Vibe Orchestrator
  ├─ Crux OS Instance 1 (Backend Developer)
  ├─ Crux OS Instance 2 (Frontend Developer)
  ├─ Crux OS Instance 3 (Designer)
  └─ Crux OS Instance 4 (QA/Security)
  ↓
  Central Knowledge Base (aggregates learning from all instances)
  ↓
  All Instances Receive Updated Knowledge
  ↓
  Future Work Benefits from Collective Learning
```

**Knowledge Sharing Flow:**

```
Crux Instance 1 finds vulnerability → Adds to central KB
    ↓
Crux Instance 2 learns pattern → Prevents similar vulnerability in its work
    ↓
Crux Instance 3 discovers design pattern → Shares across organization
    ↓
Crux Instance 4 validates tests → Suggests improvements to testing library
    ↓
Next cycle: All instances start with richer knowledge
```

**Vibe Workflow:**

1. **Feature Request Input** (Vibe UI)
   ```
   Feature: User Registration with Email Verification
   Requirements:
     - WCAG AA compliant UI
     - User management APIs
     - Email notification system
     - Rate limiting on registration
   ```

2. **Intelligent Delegation** (Vibe Orchestrator)
   ```
   → Send to plan mode (get detailed specification)
   → Send to design-ui mode (get UI design)
   → Send to build-py mode (backend implementation)
   → Send to build-ex mode (alternative implementation)
   → Send to design-review mode (validate accessibility)
   → Aggregate all outputs
   ```

3. **Cross-Instance Feedback** (Vibe)
   ```
   Designer: "The button color should be #0B66F0"
     ↓
   Stored in central KB as design preference
     ↓
   Backend developer benefits: Next feature auto-suggests this color
     ↓
   Collective learning increases
   ```

4. **Unified Knowledge Base** (Vibe)
   ```
   Central KB:
   - Test patterns (from all test runs across organization)
   - Security findings (aggregated vulnerabilities and fixes)
   - Design patterns (organization-wide design system)
   - Code patterns (best practices)
   ```

### 10.3 Key Architecture Principle

**Knowledge flows upward:**
- Crux standalone instances generate local knowledge
- Crux Vibe aggregates into organizational knowledge
- Organizational knowledge flows back down to all instances
- Result: System-wide improvement with each feature developed

**Backward Compatibility:**
- Crux can work completely standalone
- Crux can integrate with Vibe gradually
- Organizations can choose their deployment model
- All modes work identically in both contexts

---

## 11. Implementation Roadmap

### Phase 1: Test Mode (Foundation)

**Scope:** Implement test mode and test gate integration

- [ ] Create `test` mode definition
- [ ] Implement test file generation (pytest, ExUnit, Jest)
- [ ] Add test execution and coverage tracking
- [ ] Integrate test gate into pipeline (Gate 2)
- [ ] Implement correction loop (tests → fix → tests)
- [ ] Add BDD/Gherkin support
- [ ] Test with existing build modes

**Effort:** 3-4 weeks
**Dependencies:** Existing build modes

### Phase 2: Security Recursion (Robustness)

**Scope:** Implement recursive security audit loop

- [ ] Create `security` mode definition
- [ ] Implement 7-category audit system
- [ ] Add finding schema and severity classification
- [ ] Implement recursive fix loop with convergence detection
- [ ] Integrate into pipeline (Gate 3)
- [ ] Build security knowledge base integration
- [ ] Test with real vulnerability examples

**Effort:** 4-5 weeks
**Dependencies:** Phase 1 test infrastructure

### Phase 3: Design Modes (Scale)

**Scope:** Implement all 5 design modes and integrations

- [ ] Create all 5 design mode definitions
- [ ] Implement Figma API backend
- [ ] Implement CSS/Tailwind backend
- [ ] Implement image generation backend
- [ ] Create design-handoff protocol
- [ ] Implement design ↔ code integration
- [ ] Add design validation gate
- [ ] Test with real design projects

**Effort:** 6-7 weeks
**Dependencies:** Phases 1-2 complete

### Phase 4: Knowledge Base (Intelligence)

**Scope:** Implement cross-domain learning

- [ ] Extend knowledge base schema
- [ ] Add test pattern learning
- [ ] Add security pattern learning
- [ ] Add design pattern learning
- [ ] Implement cross-domain knowledge flows
- [ ] Add knowledge promotion system
- [ ] Test with multi-domain workflows

**Effort:** 3-4 weeks
**Dependencies:** Phases 1-3 complete

### Phase 5: Vibe Integration (Scale)

**Scope:** Integrate with Crux Vibe orchestration layer

- [ ] Design central knowledge base architecture
- [ ] Implement knowledge sync protocol
- [ ] Add multi-instance coordination
- [ ] Implement feedback aggregation
- [ ] Test with distributed team scenario

**Effort:** 4-5 weeks
**Dependencies:** All phases complete

---

## 12. Validation & Testing

### Test Coverage for New Features

```
✓ TDD Enforcement Gate
  ✓ Test spec generation
  ✓ Test file writing
  ✓ Test execution and failure detection
  ✓ Correction loops
  ✓ Coverage calculation
  ✓ BDD spec generation

✓ Recursive Security Audit
  ✓ Category-by-category auditing
  ✓ Finding schema validation
  ✓ Severity classification
  ✓ Fix suggestion generation
  ✓ Re-audit after fixes
  ✓ Convergence detection
  ✓ Knowledge base integration

✓ Design Modes
  ✓ Design-UI with 3 backends (Figma, CSS, image gen)
  ✓ Design-Review WCAG validation
  ✓ Design-System token generation
  ✓ Design-Responsive breakpoint strategy
  ✓ Design-Accessibility ARIA specs
  ✓ Design-handoff protocol
  ✓ Design ↔ code integration
```

### Backward Compatibility Testing

All existing modes and workflows must function identically:

```
✓ Legacy 5-gate pipeline still functional
✓ Existing 15 modes unchanged
✓ Configuration defaults preserve legacy behavior
✓ Knowledge base compatible with existing tools
✓ Handoff protocol extended, not replaced
```

---

## 13. Glossary & Definitions

| Term | Definition |
|------|-----------|
| **Gate** | A stage in the safety pipeline where code/design must meet criteria before proceeding |
| **TDD** | Test-Driven Development: write tests first, then code to pass tests |
| **BDD** | Behavior-Driven Development: write human-readable specifications that translate to tests |
| **Convergence** | Audit process reaches stability when zero new findings detected in consecutive passes |
| **Severity** | Classification of vulnerability/issue: critical, high, medium, low, info |
| **Handoff** | Transfer of context and specifications from one mode to another |
| **Knowledge Base** | Organizational repository of patterns, vulnerabilities, design preferences |
| **Design Token** | Named value representing design system property (color, spacing, typography) |
| **WCAG** | Web Content Accessibility Guidelines (A, AA, or AAA levels) |
| **Crux Vibe** | Orchestration layer above Crux OS for team coordination |
| **Correction Detection** | System's ability to detect when output diverges from intent and update knowledge |

---

## 14. Conclusion

This specification extends Crux OS with three major capabilities that maintain full backward compatibility while dramatically increasing quality assurance, security rigor, and design capability.

**Key Guarantees:**
- Strict additive changes: nothing removed, nothing replaced
- Backward compatible: legacy behavior always available
- Incremental adoption: can enable features per project
- Unified architecture: test, security, and design use same pipeline
- Knowledge integration: learning flows across all domains

**Benefits:**
- **TDD enforcement** ensures comprehensive test coverage from day one
- **Recursive security audits** achieve convergence toward zero exploitable vulnerabilities
- **Design modes** bring UI/UX into first-class development workflow
- **Knowledge base** enables organizational learning and pattern reuse
- **Crux Vibe integration** amplifies benefits across teams

The expanded Crux OS becomes a comprehensive platform for building secure, well-tested, beautifully designed software with continuous organizational learning.

---

**Document Version:** 2.0
**Status:** Formal Specification
**Last Updated:** 2026-03-05
**Maintainer:** Crux OS Architecture Team
