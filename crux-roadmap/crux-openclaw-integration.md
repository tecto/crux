# Crux OS + OpenClaw Integration: Complete Development & Messaging Strategy

**Document Status:** Strategic Framework & Implementation Guide
**Target Audience:** Engineering team, founding team, OpenClaw community
**Timeline:** 12-week delivery with phased rollout
**Last Updated:** 2026-03-05

---

## EXECUTIVE SUMMARY

OpenClaw is the fastest-growing open source project in history (250K+ GitHub stars in 60 days, surpassing React). It's a self-hosted autonomous AI agent that connects to 12+ messaging platforms and executes tasks with 5,400+ available skills. However, it has a critical vulnerability: **63% of deployments have security vulnerabilities, 820+ malicious skills exist in the marketplace, and the agent executes blindly without safety checks or learning mechanisms**.

Crux OS solves this problem through a seven-stage safety pipeline, 21 specialized modes, TDD enforcement, recursive security audits, and correction detection with organic knowledge generation.

**The integration thesis:** OpenClaw without Crux is powerful but dangerous. OpenClaw with Crux becomes safe, intelligent, and self-improving. This represents a natural extension of Crux into the autonomous agent space and a high-leverage entry point into a 250K-user community.

**Revenue model:** Crux OS skills and safety plugins for OpenClaw are distributed FREE on ClawHub. This massive distribution funnel converts OpenClaw users to Crux Vibe managed Mac Mini subscriptions ($125-$349/month). The 250K potential user base represents one of the highest-leverage marketing channels available.

---

## PART 1: DEVELOPMENT PLAN

### 1.1 Integration Architecture

The Crux OS intelligence layer sits between OpenClaw's Brain (message processing) and Execution layer (tools), providing safety, specialized reasoning, learning, and code quality enforcement.

```
┌──────────────────────────────────────────────────────────┐
│ OpenClaw Gateway                                         │
│ (WhatsApp, Slack, Telegram, Discord, iMessage, Signal) │
└────────────────────┬─────────────────────────────────────┘
                     │ User Request
                     ↓
┌──────────────────────────────────────────────────────────┐
│ OpenClaw Brain (ReAct Reasoning Loop)                   │
│ Receives: "Schedule a meeting and send an email"        │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────┐
│ CRUX OS INTELLIGENCE LAYER (NEW)                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Mode Router                                          │
│    Selects best mode from 21 specializations            │
│    → calendar-mode, email-mode, integration-mode, etc. │
│                                                          │
│ 2. Preflight Validation                                 │
│    Syntax check, resource estimation, permission scan   │
│                                                          │
│ 3. Knowledge Base Lookup                                │
│    Retrieves learned patterns, successful workflows     │
│    Context: project-level, user-level, public          │
│                                                          │
│ 4. Test-Spec Generation                                 │
│    TDD/BDD: Write tests before execution                │
│    Define expected outcomes                             │
│                                                          │
│ 5. Security Audit Loop (Recursive)                      │
│    • SSRF detection (CVE-2026-26322)                    │
│    • Auth validation (CVE-2026-26319)                   │
│    • Credential exposure scanning                       │
│    • Malicious skill detection                          │
│    • Re-audit fixes until convergence                   │
│                                                          │
│ 6. Second Opinion                                       │
│    Alternative LLM or reasoning path                    │
│    Consensus check for high-risk operations             │
│                                                          │
│ 7. Human Approval (Optional)                            │
│    For irreversible actions, send to human             │
│    Return via OpenClaw messaging interface              │
│                                                          │
│ 8. Dry Run Execution                                    │
│    Execute in sandbox, verify behavior                  │
│                                                          │
│ 9. Design Validation                                    │
│    Verify output matches spec, intent preservation      │
│    Correction detection if divergence found             │
│                                                          │
│ 10. Knowledge Generation                                │
│     Store successful pattern in knowledge base           │
│     Make available to agent for future use              │
│                                                          │
└────────────────────┬─────────────────────────────────────┘
                     │ Approved Action
                     ↓
┌──────────────────────────────────────────────────────────┐
│ OpenClaw Execution Layer                                 │
│ (Shell commands, Browser automation, File ops, APIs)    │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────────────┐
│ OpenClaw Memory (Enhanced by Crux Knowledge Base)        │
│ ~/.openclaw/ (Markdown files)                            │
│ Sync: Crux knowledge ↔ OpenClaw memory                  │
└──────────────────────────────────────────────────────────┘
```

**Key principle:** Crux never blocks OpenClaw; it advises, educates, and improves. Users can set risk tolerance levels (strict, moderate, permissive) to control intervention.

---

### 1.2 Five Integration Points (Technical Detail)

#### Integration Point 1: Crux as OpenClaw Skills (ClawHub Distribution)

**Objective:** Package Crux modes as installable skills in ClawHub (OpenClaw's 5,400+ skill marketplace).

**Format:** OpenClaw skills are Markdown files with YAML frontmatter, identical to Crux mode format. Each skill becomes independently installable.

**Implementation:**

```markdown
# SKILL.md for crux-build-python

---
name: crux-build-python
version: 1.0.0
author: Crux OS
license: MIT
description: Build, test, and validate Python projects with TDD enforcement and security scanning
tags: [python, build, tdd, security, crux]
category: development
prerequisites:
  - python >= 3.9
  - pytest
  - mypy
dependencies:
  - crux-security-audit
  - crux-knowledge-base
---

## Overview

This skill enforces test-driven development for Python projects:
1. Scans project for existing tests
2. Generates test specifications for changes
3. Runs security audit (SAST, dependency scanning)
4. Executes TDD pipeline before code deployment
5. Stores successful patterns in knowledge base

## Usage

```
user: "Build a new API endpoint for user authentication"

skill: This will:
1. Generate pytest specs for authentication logic
2. Run security audit for auth vulnerabilities
3. Build with TDD enforcement
4. Store successful auth pattern in knowledge
```

## Configuration

```yaml
test_framework: pytest
security_tools:
  - bandit
  - safety
  - semgrep
tdd_enforcement: strict  # strict | moderate | permissive
```

## Implementation (TypeScript in OpenClaw context)

```typescript
export async function cruxBuildPython(context: SkillContext) {
  const project = context.projectPath;

  // 1. Detect existing tests
  const tests = await detectTests(project);

  // 2. Generate test specifications
  const spec = await generateTestSpec(context.userRequest, tests);

  // 3. Run security audit
  const audit = await runSecurityAudit(project, {
    tools: ['bandit', 'safety', 'semgrep']
  });

  if (audit.failures.length > 0) {
    // Recursive security audit loop
    const fixes = await generateSecurityFixes(audit.failures);
    await applyFixes(project, fixes);
    const reaudit = await runSecurityAudit(project);
    if (reaudit.failures.length > 0) {
      return { success: false, reason: 'Security audit convergence failed' };
    }
  }

  // 4. Execute TDD pipeline
  const testResult = await runTests(spec);
  if (!testResult.passed) {
    // Generate fixes and retry
    const fixes = await generateTestFixes(testResult.failures);
    await applyFixes(project, fixes);
    return await runTests(spec); // Retry
  }

  // 5. Store in knowledge base
  await storeKnowledgePattern({
    pattern: 'python-auth-build',
    spec: spec,
    result: testResult,
    timestamp: Date.now()
  });

  return { success: true, tests: testResult };
}
```

**Skill Install Command:**
```bash
clawhub install crux-build-python
clawhub install crux-review-code
clawhub install crux-security-audit
clawhub install crux-vault  # Secret management
clawhub install crux-os     # Meta-skill installing all 21 modes
```

**Distribution Strategy:**
- Publish crux-build-python, crux-review, crux-security-audit first (Phase 1)
- All skills marked "crux-verified" with security badge
- Include in official Crux documentation: "Install Crux for OpenClaw"
- Weekly blog post: "New Crux skill available on ClawHub"

---

#### Integration Point 2: Crux Safety Pipeline as OpenClaw Gateway Plugin

**Objective:** Build TypeScript/JavaScript plugin that hooks into OpenClaw's Gateway and intercepts all tool calls before execution.

**Architecture:** The plugin sits in OpenClaw's tool execution pipeline, applying the seven-gate safety check before any action runs.

**Plugin Code Structure:**

```typescript
// crux-safety-gateway.ts
// Installs into OpenClaw's tool middleware chain

import { Tool, ToolCall, ToolResult, Gateway } from '@openclaw/types';
import { CruxSafetyPipeline } from './pipeline';
import { CruxSecurityAudit } from './security';
import { CruxKnowledgeBase } from './knowledge';

interface SafetyConfig {
  riskTolerance: 'strict' | 'moderate' | 'permissive';
  requireHumanApprovalFor: string[]; // ['delete', 'network', 'auth']
  enableSecurityAudit: boolean;
  enableDryRun: boolean;
  enableTDD: boolean;
}

export class CruxSafetyGateway {
  private config: SafetyConfig;
  private pipeline: CruxSafetyPipeline;
  private audit: CruxSecurityAudit;
  private knowledge: CruxKnowledgeBase;

  constructor(config: SafetyConfig) {
    this.config = config;
    this.pipeline = new CruxSafetyPipeline(config);
    this.audit = new CruxSecurityAudit();
    this.knowledge = new CruxKnowledgeBase();
  }

  /**
   * Intercept all tool calls before execution
   * Returns: { allow: boolean, modifiedCall?: ToolCall, reason: string }
   */
  async validateToolCall(call: ToolCall, context: ExecutionContext) {
    const result = {
      allow: false,
      modifiedCall: call,
      reason: '',
      appliedGates: []
    };

    // Gate 1: Preflight Validation
    const preflightCheck = await this.pipeline.preflight(call);
    if (!preflightCheck.valid) {
      result.reason = `Preflight failed: ${preflightCheck.error}`;
      result.appliedGates.push('preflight');
      return result;
    }
    result.appliedGates.push('preflight');

    // Gate 2: Syntax & Format Check
    const syntaxCheck = await this.validateSyntax(call);
    if (!syntaxCheck.valid) {
      result.reason = `Syntax error: ${syntaxCheck.error}`;
      result.appliedGates.push('syntax');
      return result;
    }
    result.appliedGates.push('syntax');

    // Gate 3: Security Audit (Recursive)
    const securityResult = await this.audit.auditToolCall(call, {
      checkFor: ['ssrf', 'rce', 'auth_bypass', 'credential_leak'],
      recurseOnFail: true,
      maxIterations: 3
    });

    if (!securityResult.safe && this.config.riskTolerance === 'strict') {
      result.reason = `Security risk detected: ${securityResult.risks.map(r => r.type).join(', ')}`;
      result.appliedGates.push('security-audit');

      // Attempt auto-fix
      if (securityResult.suggestedFix) {
        result.modifiedCall = securityResult.suggestedFix;
        result.reason += ` (auto-fixed: ${securityResult.fixDescription})`;
        result.appliedGates.push('security-audit-fix');
      } else {
        return result;
      }
    }
    result.appliedGates.push('security-audit');

    // Gate 4: Second Opinion (Alternative reasoning)
    if (this.config.riskTolerance === 'strict') {
      const secondOpinion = await this.pipeline.secondOpinion(call);
      if (!secondOpinion.agree) {
        result.reason = `Second opinion disagreed: ${secondOpinion.reason}`;
        result.appliedGates.push('second-opinion');
        return result;
      }
      result.appliedGates.push('second-opinion');
    }

    // Gate 5: Human Approval (if needed)
    if (this.requiresHumanApproval(call, this.config)) {
      result.reason = 'Awaiting human approval';
      result.appliedGates.push('human-approval-pending');
      // Queue for human review, return pending
      return { ...result, allow: false, requiresApproval: true };
    }

    // Gate 6: Dry Run
    if (this.config.enableDryRun && this.isDangerous(call)) {
      const dryRun = await this.executeDryRun(call, context);
      if (!dryRun.successful) {
        result.reason = `Dry run failed: ${dryRun.error}`;
        result.appliedGates.push('dry-run');
        return result;
      }
      result.appliedGates.push('dry-run');
    }

    // Gate 7: TDD Validation (if code generation)
    if (this.config.enableTDD && this.isCodeGeneration(call)) {
      const tddResult = await this.pipeline.validateTDD(call);
      if (!tddResult.valid) {
        result.reason = `TDD validation failed: ${tddResult.error}`;
        result.appliedGates.push('tdd-validation');
        return result;
      }
      result.appliedGates.push('tdd-validation');
    }

    // All gates passed
    result.allow = true;
    result.reason = 'All gates passed';

    // Gate 8: Store in knowledge base for future use
    await this.knowledge.storeSuccessfulPattern({
      toolCall: call,
      context: context,
      appliedGates: result.appliedGates,
      timestamp: Date.now()
    });

    return result;
  }

  private requiresHumanApproval(call: ToolCall, config: SafetyConfig): boolean {
    const dangerousTools = ['shell', 'delete', 'modify_auth', 'network_call'];
    const requiredApproval = config.requireHumanApprovalFor;
    return dangerousTools.some(tool =>
      call.tool.includes(tool) || requiredApproval.includes(call.tool)
    );
  }

  private isDangerous(call: ToolCall): boolean {
    return ['shell', 'delete', 'modify_auth', 'send_email'].includes(call.tool);
  }

  private isCodeGeneration(call: ToolCall): boolean {
    return ['write_file', 'create_function', 'build'].includes(call.tool);
  }

  private async executeDryRun(call: ToolCall, context: ExecutionContext) {
    // Clone context to sandbox
    const sandbox = await context.createSandbox();
    try {
      const result = await this.executeInSandbox(call, sandbox);
      return { successful: true, result };
    } catch (error) {
      return { successful: false, error: error.message };
    }
  }

  private async validateSyntax(call: ToolCall) {
    try {
      // Basic syntax validation
      if (call.arguments && typeof call.arguments === 'string') {
        JSON.parse(call.arguments);
      }
      return { valid: true };
    } catch (error) {
      return { valid: false, error: error.message };
    }
  }
}

// Plugin registration for OpenClaw
export function registerCruxSafetyPlugin(gateway: Gateway, config: SafetyConfig) {
  const plugin = new CruxSafetyGateway(config);

  gateway.use(async (call: ToolCall, context: ExecutionContext, next) => {
    const validation = await plugin.validateToolCall(call, context);

    if (!validation.allow) {
      console.warn(`[Crux Safety] Blocked: ${validation.reason}`);
      console.warn(`[Crux Safety] Applied gates: ${validation.appliedGates.join(' → ')}`);

      if (validation.requiresApproval) {
        // Send to human for approval via OpenClaw messaging
        await context.requestHumanApproval(call, validation.reason);
        return; // Wait for human response
      }

      throw new Error(`Crux Safety: ${validation.reason}`);
    }

    if (validation.modifiedCall !== call) {
      console.log(`[Crux Safety] Modified call: ${validation.reason}`);
      call = validation.modifiedCall;
    }

    return next(call);
  });
}

// Installation: Add to OpenClaw config.yaml
/*
plugins:
  - name: crux-safety-gateway
    version: 1.0.0
    config:
      riskTolerance: moderate
      requireHumanApprovalFor: [delete, modify_auth, send_email]
      enableSecurityAudit: true
      enableDryRun: true
      enableTDD: true
*/
```

**Installation Steps:**
```bash
# 1. Install npm package
npm install @crux-os/safety-gateway

# 2. Add to OpenClaw config.yaml
echo "
plugins:
  - name: crux-safety-gateway
    version: 1.0.0
    config:
      riskTolerance: moderate
      enableSecurityAudit: true
      enableDryRun: false
      enableTDD: true
" >> ~/.openclaw/config.yaml

# 3. Restart OpenClaw
openclaw restart
```

**What this solves:**
- Blocks CVE-2026-26322 (SSRF) automatically
- Detects CVE-2026-26319 (missing auth)
- Prevents credential exposure in plaintext
- Validates all code before execution
- Provides audit trail of all blocked actions

---

#### Integration Point 3: Crux Knowledge Base as OpenClaw Memory Extension

**Objective:** Bidirectional sync between Crux's tiered knowledge base and OpenClaw's memory system.

**OpenClaw memory format:**
```
~/.openclaw/
├── memories.md          # Main memory file
├── patterns/           # Successful workflows
│   ├── auth-pattern.md
│   ├── api-pattern.md
│   └── file-ops-pattern.md
└── mistakes/           # Correction log for learning
    ├── failed-shell-1.md
    └── failed-api-1.md
```

**Crux knowledge base format:**
```
~/.crux/
├── knowledge/
│   ├── project/        # Project-specific (private)
│   │   └── myproject/
│   │       ├── successful-builds.md
│   │       └── auth-failures.md
│   ├── user/           # User-level (private)
│   │   ├── preferred-patterns.md
│   │   └── common-mistakes.md
│   └── public/         # Shareable patterns
│       ├── python-best-practices.md
│       └── security-patterns.md
```

**Sync Mechanism:**

```typescript
// crux-knowledge-sync.ts
// Runs as OpenClaw scheduled task

import { OpenClawMemory } from '@openclaw/memory';
import { CruxKnowledgeBase } from '@crux-os/knowledge';

export class KnowledgeSync {
  private openclaw: OpenClawMemory;
  private crux: CruxKnowledgeBase;

  async syncOpenClawTooCrux() {
    // Read OpenClaw's memory
    const memories = await this.openclaw.readMemories();
    const patterns = await this.openclaw.readPatterns();
    const mistakes = await this.openclaw.readMistakes();

    // Write to Crux knowledge base (user-level, private)
    for (const pattern of patterns) {
      await this.crux.storePattern({
        source: 'openclaw',
        level: 'user',
        content: pattern,
        tags: ['openclaw-learned'],
        timestamp: Date.now()
      });
    }

    // Store correction patterns from mistakes
    for (const mistake of mistakes) {
      const correction = await generateCorrection(mistake);
      await this.crux.storeCorrection({
        source: 'openclaw',
        level: 'user',
        mistakePattern: mistake,
        correctionPattern: correction,
        tags: ['openclaw-correction'],
        timestamp: Date.now()
      });
    }
  }

  async syncCruxToOpenClaw() {
    // Read user-level Crux knowledge
    const knowledge = await this.crux.getKnowledge('user');

    // Write successful patterns to OpenClaw memory
    for (const pattern of knowledge.patterns) {
      await this.openclaw.storePattern({
        source: 'crux',
        content: pattern,
        metadata: {
          cruxMode: pattern.mode,
          successRate: pattern.metrics.successRate,
          lastUsed: pattern.metrics.lastUsed
        }
      });
    }

    // Write correction patterns
    for (const correction of knowledge.corrections) {
      await this.openclaw.storeCorrection({
        source: 'crux',
        content: correction
      });
    }
  }

  async continuousSync() {
    // Run every 5 minutes or on task completion
    setInterval(async () => {
      await this.syncOpenClawTooCrux();
      await this.syncCruxToOpenClaw();
    }, 5 * 60 * 1000);
  }
}

// Enable in OpenClaw config
/*
tasks:
  - name: crux-knowledge-sync
    schedule: "*/5 * * * *"  # Every 5 minutes
    action: crux-knowledge-sync
*/
```

**What this enables:**
- OpenClaw learns from Crux's patterns (if same user has run Crux elsewhere)
- Crux learns from OpenClaw's trial-and-error (correction detection)
- Patterns are private to the user, project, or public (tiered)
- Agent gets smarter every time it completes a task

---

#### Integration Point 4: Crux MCP Server for OpenClaw

**Objective:** Expose Crux modes, safety checks, and knowledge base as Model Context Protocol (MCP) server that OpenClaw can call.

**MCP allows:** Any tool (OpenClaw, Claude directly, other agents) to call Crux capabilities via standard protocol.

**Architecture:**

```typescript
// crux-mcp-server.ts
// MCP server exposing Crux capabilities

import { Server, Tool, CallToolRequest } from '@modelcontextprotocol/sdk/types';

export class CruxMCPServer {
  private server: Server;
  private modes: CruxMode[];
  private knowledge: CruxKnowledgeBase;
  private safety: CruxSafetyPipeline;

  constructor() {
    this.server = new Server();
    this.setupTools();
  }

  private setupTools() {
    // Tool 1: Mode Router
    this.server.addTool({
      name: 'crux-select-mode',
      description: 'Analyze user request and select best Crux mode (specialist)',
      inputSchema: {
        type: 'object',
        properties: {
          userRequest: {
            type: 'string',
            description: 'The user request to analyze'
          },
          context: {
            type: 'object',
            description: 'Optional context (available tools, project type, etc.)'
          }
        },
        required: ['userRequest']
      },
      handler: async (request: CallToolRequest) => {
        const { userRequest, context } = request.params;
        const selectedMode = await this.selectMode(userRequest, context);
        return {
          mode: selectedMode.name,
          confidence: selectedMode.confidence,
          rationale: selectedMode.rationale,
          parameters: selectedMode.suggestedParameters
        };
      }
    });

    // Tool 2: Security Audit
    this.server.addTool({
      name: 'crux-security-audit',
      description: 'Audit proposed action for security risks and generate fixes',
      inputSchema: {
        type: 'object',
        properties: {
          action: {
            type: 'string',
            description: 'The action/code to audit'
          },
          actionType: {
            type: 'string',
            enum: ['shell', 'api_call', 'file_operation', 'code_generation'],
            description: 'Type of action'
          },
          riskLevel: {
            type: 'string',
            enum: ['high', 'medium', 'low'],
            description: 'Target risk level'
          }
        },
        required: ['action', 'actionType']
      },
      handler: async (request: CallToolRequest) => {
        const { action, actionType, riskLevel } = request.params;
        const audit = await this.safety.audit(action, actionType);
        return {
          safe: audit.safe,
          risks: audit.risks,
          suggestedFix: audit.suggestedFix,
          confidence: audit.confidence
        };
      }
    });

    // Tool 3: Query Knowledge Base
    this.server.addTool({
      name: 'crux-query-knowledge',
      description: 'Query learned patterns and successful workflows',
      inputSchema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'What pattern are you looking for?'
          },
          scope: {
            type: 'string',
            enum: ['project', 'user', 'public'],
            description: 'Knowledge scope to search'
          }
        },
        required: ['query']
      },
      handler: async (request: CallToolRequest) => {
        const { query, scope } = request.params;
        const results = await this.knowledge.search(query, scope || 'user');
        return {
          found: results.length > 0,
          patterns: results.slice(0, 5),
          totalMatches: results.length
        };
      }
    });

    // Tool 4: Store Knowledge
    this.server.addTool({
      name: 'crux-store-pattern',
      description: 'Store a successful pattern for future use',
      inputSchema: {
        type: 'object',
        properties: {
          patternName: {
            type: 'string',
            description: 'Name for this pattern'
          },
          description: {
            type: 'string',
            description: 'What does this pattern do?'
          },
          code: {
            type: 'string',
            description: 'The code/approach'
          },
          scope: {
            type: 'string',
            enum: ['project', 'user', 'public'],
            description: 'Who should have access?'
          }
        },
        required: ['patternName', 'description', 'code']
      },
      handler: async (request: CallToolRequest) => {
        const { patternName, description, code, scope } = request.params;
        await this.knowledge.store({
          name: patternName,
          description: description,
          content: code,
          scope: scope || 'user',
          tags: ['mcp-stored'],
          timestamp: Date.now()
        });
        return { stored: true, pattern: patternName };
      }
    });

    // Tool 5: TDD Specification
    this.server.addTool({
      name: 'crux-generate-tdd-spec',
      description: 'Generate test specifications before implementation',
      inputSchema: {
        type: 'object',
        properties: {
          requirement: {
            type: 'string',
            description: 'What needs to be built?'
          },
          language: {
            type: 'string',
            description: 'Programming language',
            default: 'python'
          }
        },
        required: ['requirement']
      },
      handler: async (request: CallToolRequest) => {
        const { requirement, language } = request.params;
        const spec = await this.safety.generateTDDSpec(requirement, language);
        return {
          tests: spec.tests,
          expectedBehavior: spec.expectedBehavior,
          edgeCases: spec.edgeCases
        };
      }
    });
  }

  private async selectMode(userRequest: string, context?: any) {
    // Analyze request and return best mode with parameters
    // Uses mode definitions and context awareness
    return {
      name: 'code-review-mode',
      confidence: 0.92,
      rationale: 'Request mentions reviewing code quality and patterns',
      suggestedParameters: { detail_level: 'deep', focus: 'security' }
    };
  }

  async start(port: number = 3001) {
    await this.server.start(port);
    console.log(`Crux MCP Server running on port ${port}`);
  }
}

// Usage in OpenClaw
/*
# In openclaw config:
mcp_servers:
  crux:
    url: "http://localhost:3001"
    tools:
      - crux-select-mode
      - crux-security-audit
      - crux-query-knowledge
      - crux-store-pattern
      - crux-generate-tdd-spec

# OpenClaw calls Crux MCP for:
user: "Review this code for security issues"
openclaw: "Calling crux-select-mode to determine best approach..."
        "Selected: code-review-mode (92% confidence)"
        "Calling crux-security-audit with selected parameters..."
*/
```

**Benefits:**
- Works with any OpenClaw instance, no special integration needed
- Also works with Claude API directly: `use_mcp_tool("crux-security-audit")`
- Future: Other agents can call Crux capabilities
- Separation of concerns: Crux remains independent service

---

#### Integration Point 5: Heartbeat Scheduler for Continuous Processing

**Objective:** Leverage OpenClaw's Heartbeat (cron-style autonomous scheduler) to trigger Crux's continuous improvement cycles.

**What happens:**
```
OpenClaw Heartbeat triggers every 5 minutes:
├─ Check if agent idle (no active tasks)
├─ If idle, run Crux continuous processing:
│  ├─ Analyze recent patterns (last 100 actions)
│  ├─ Detect successful patterns and store in knowledge base
│  ├─ Detect failure patterns (corrections) and store
│  ├─ Run recursive security audit on stored patterns
│  ├─ Generate summary of learned behaviors
│  └─ Queue summary for delivery via OpenClaw messaging
└─ Send daily digest: "Your agent learned X new patterns today"
```

**Implementation:**

```typescript
// crux-heartbeat-processor.ts
// Runs on OpenClaw Heartbeat

import { Heartbeat, TaskLog } from '@openclaw/types';
import { CruxKnowledgeBase } from '@crux-os/knowledge';

export class CruxHeartbeatProcessor {
  private knowledge: CruxKnowledgeBase;

  async processHeartbeat(heartbeat: Heartbeat) {
    // Only run if agent is idle
    if (heartbeat.activeTaskCount > 0) return;

    console.log('[Crux Heartbeat] Starting continuous improvement cycle');

    // 1. Analyze recent task logs
    const recentLogs = await this.getRecentTaskLogs(100);

    // 2. Extract successful patterns
    const successPatterns = recentLogs
      .filter(log => log.status === 'success')
      .map(log => ({
        action: log.action,
        parameters: log.parameters,
        outcome: log.outcome,
        duration: log.duration
      }));

    // 3. Analyze failure patterns (corrections)
    const failurePatterns = recentLogs
      .filter(log => log.status === 'failed' || log.status === 'corrected');

    // 4. Store patterns
    for (const pattern of successPatterns) {
      // Group similar patterns
      const patternType = await this.classifyPattern(pattern);
      const existingPattern = await this.knowledge.findSimilar(patternType);

      if (existingPattern) {
        // Enhance existing pattern
        await this.knowledge.updatePattern(existingPattern.id, {
          lastUsed: Date.now(),
          successCount: existingPattern.successCount + 1
        });
      } else {
        // Store new pattern
        await this.knowledge.store({
          name: `${patternType}-${Date.now()}`,
          type: patternType,
          content: pattern,
          scope: 'user',
          tags: ['heartbeat-learned']
        });
      }
    }

    // 5. Process corrections (learn from failures)
    for (const failure of failurePatterns) {
      const correction = await this.generateCorrection(failure);
      await this.knowledge.storeCorrection({
        failurePattern: failure.action,
        correctionPattern: correction,
        timestamp: Date.now()
      });
    }

    // 6. Run recursive security audit on new patterns
    const newPatterns = await this.knowledge.getRecent(10);
    for (const pattern of newPatterns) {
      const audit = await this.runSecurityAudit(pattern);
      if (!audit.safe) {
        await this.knowledge.markAsRisky(pattern.id, audit.risks);
      }
    }

    // 7. Generate summary
    const summary = {
      patternsLearned: successPatterns.length,
      correctionsApplied: failurePatterns.length,
      riskIssuesFound: newPatterns.filter(p => p.risky).length,
      timestamp: Date.now()
    };

    // 8. Send summary via OpenClaw messaging
    await this.sendDailyDigest(summary);

    console.log('[Crux Heartbeat] Continuous improvement cycle complete');
  }

  private async getRecentTaskLogs(limit: number = 100) {
    // Read from ~/.openclaw/activity.log
    return await this.readActivityLog(limit);
  }

  private async classifyPattern(pattern: any): Promise<string> {
    // Analyze pattern and classify: auth, api, file-ops, shell, etc.
    return 'code-operation';
  }

  private async generateCorrection(failure: any) {
    // Use LLM to generate correction from failure
    return {
      successfulApproach: 'Use alternative method',
      explanation: 'Original approach failed due to timeout'
    };
  }

  private async runSecurityAudit(pattern: any) {
    // Security audit of pattern content
    return {
      safe: true,
      risks: []
    };
  }

  private async sendDailyDigest(summary: any) {
    // Use OpenClaw's messaging to send digest
    // User gets message: "Your agent learned 12 new patterns today. 2 security issues detected and fixed."
  }
}

// Register with OpenClaw Heartbeat
/*
In config.yaml:
heartbeat:
  processors:
    - name: crux-continuous-improvement
      interval: "*/5 * * * *"
      handler: crux-heartbeat-processor
*/
```

**What this enables:**
- Agent learns autonomously during idle time
- No user intervention needed
- Patterns improve over time (self-improvement)
- Users get daily digest of learned behaviors
- Security scanning happens in background

---

### 1.3 What Crux Solves for OpenClaw: Complete Mapping

This table shows how each Crux component addresses OpenClaw's documented vulnerabilities:

| OpenClaw Weakness | Impact | Crux Solution | Implementation | Phase |
|---|---|---|---|---|
| **Security Vulnerabilities** | 63% of deployments have exploitable flaws | Recursive security audit loop (preflight → audit → fix → re-audit → convergence) | crux-safety-gateway plugin + security-audit-mode | 2 |
| **SSRF Attack Vector** | CVE-2026-26322 allows arbitrary network requests | SSRF detector in security audit gate | Scan all network calls for metadata server patterns, AWS credential endpoints | 2 |
| **Missing Authentication** | CVE-2026-26319 bypasses API auth | Auth validator in preflight + second-opinion gate | Verify API calls include auth headers, check credential presence | 2 |
| **Exposed Instance** | 135K instances publicly accessible | Security audit identifies and fixes exposure patterns | Detect public port bindings, suggest firewall rules, auto-remediate | 3 |
| **Malicious Marketplace Skills** | 820+ skills contain malware/backdoors | Skill auditor mode + ClawHub scanner | Review skill code before execution, static analysis, sandboxed test-run | 3 |
| **Blind Execution** | Agent executes LLM suggestions without verification | Scripts-first architecture + dry-run gate | All code changes reviewed and tested before applied | 2 |
| **No Safety Pipeline** | No gates between reasoning and execution | Seven-gate safety pipeline (preflight → syntax → security → opinion → approval → dry-run → validation) | crux-safety-gateway plugin | 2 |
| **No Code Review** | Generated code deployed directly | Review mode (code-review-mode) + TDD enforcement | Static analysis, security review, test coverage validation before deployment | 2 |
| **No Learning** | Agent makes same mistakes repeatedly | Correction detection + knowledge base | Every failure stored as correction pattern, agent learns from mistakes | 3 |
| **No Testing Enforcement** | Generated code untested before deployment | TDD/BDD gate + test-spec-mode | Generate tests first, verify code meets spec before execution | 2 |
| **Plaintext Secrets** | API keys and credentials stored unencrypted in ~/.openclaw/ | Crux vault mode + encrypted knowledge store | Encrypt sensitive data at rest, rotate credentials, mask in logs | 3 |
| **General-Purpose Agent** | Poor performance in specialized domains (not a calendar expert, not an API specialist) | 21 specialized modes | Mode router selects optimal specialist for each task (calendar-mode, email-mode, api-integration-mode, etc.) | 3 |
| **No Code Correction** | Errors in generated code not caught or fixed | Correction detection with recursive validation | Run generated code in sandbox, detect divergence from spec, auto-fix, re-validate | 3 |
| **No Continuous Improvement** | No way to improve agent capability over time | Five-level continuous self-improvement + knowledge generation | Heartbeat processor learns from each task, stores patterns, builds knowledge base | 5 |

---

### 1.4 Development Phases: 12-Week Timeline

#### Phase 1: Proof of Concept (Weeks 1-2)

**Goal:** Demonstrate Crux-OpenClaw integration with three essential skills on ClawHub.

**Deliverables:**
1. Three Crux modes packaged as OpenClaw skills (SKILL.md format)
   - `crux-build-python`: TDD enforcement + security scanning for Python projects
   - `crux-review`: Code review with security focus
   - `crux-security-audit`: Vulnerability scanning (SAST, dependency check, pattern analysis)

2. Published to ClawHub (official marketplace)
3. Installation documentation
4. Blog post: "Introducing Crux for OpenClaw"
5. Community announcement on r/LocalLLaMA, OpenClaw GitHub

**Success metrics:**
- 3 skills published and installable
- 100+ ClawHub installs
- 50+ GitHub stars on crux-openclaw repository

**Tasks:**
```
Week 1:
- [ ] Package crux-build-python as SKILL.md
  - Implement TDD runner (use Crux's existing code)
  - Wire in pytest, mypy, bandit
  - Test locally with OpenClaw instance
- [ ] Package crux-review as SKILL.md
  - Implement code review flow
  - Test with sample projects
- [ ] Package crux-security-audit as SKILL.md
  - Implement SAST + dependency scanning
  - Test detection of CVE patterns

Week 2:
- [ ] Publish all three to ClawHub
- [ ] Create OpenClaw + Crux installation guide
- [ ] Write blog post
- [ ] Post to r/LocalLLaMA, OpenClaw GitHub Discussions
- [ ] Tag @steipete (OpenClaw creator) in announcement
```

---

#### Phase 2: Safety Plugin (Weeks 3-4)

**Goal:** Build crux-safety-gateway plugin that hooks into OpenClaw's execution pipeline.

**Deliverables:**
1. TypeScript plugin: `crux-safety-gateway`
   - Implements five critical gates (preflight, security, second-opinion, dry-run, validation)
   - Intercepts all tool calls before execution
   - Configurable risk tolerance (strict, moderate, permissive)

2. Configuration guide (risk tolerance levels)
3. Testing suite (unit + integration tests)
4. Documentation for operators

**Success metrics:**
- Plugin blocks known vulnerabilities (simulate CVE-2026-26322, CVE-2026-26319)
- 50+ installations
- Integration with Ollama-based OpenClaw instances

**Tasks:**
```
Week 3:
- [ ] Build crux-safety-gateway TypeScript plugin
  - Implement preflight gate (syntax, permissions, resources)
  - Implement security audit gate (SSRF, RCE, auth bypass detection)
  - Implement second-opinion gate (alternative reasoning path)
  - Implement dry-run gate (sandboxed execution)
  - Implement validation gate (output matches spec)
- [ ] Write unit tests for each gate
- [ ] Test against sample exploits (SSRF, plaintext secrets)

Week 4:
- [ ] Package plugin for npm/yarn
- [ ] Write installation guide
- [ ] Create configuration documentation
- [ ] Test end-to-end with OpenClaw + Ollama
- [ ] Blog post: "OpenClaw + Crux Security Plugin: Block Vulnerabilities Automatically"
- [ ] Publish to npm and OpenClaw plugin registry
```

---

#### Phase 3: Full Integration (Weeks 5-8)

**Goal:** Complete integration across all five points (skills, safety plugin, knowledge base, MCP, heartbeat).

**Deliverables:**
1. All 21 Crux modes packaged as OpenClaw skills
2. Knowledge base ↔ OpenClaw memory bidirectional sync
3. Crux MCP server (tools: mode-select, security-audit, query-knowledge, store-pattern, tdd-spec)
4. Heartbeat processor for continuous learning
5. Complete documentation and examples

**Success metrics:**
- 21 skills published to ClawHub
- 500+ total installations
- Knowledge sync working bidirectionally
- Heartbeat learning demonstrated (agent learns from past tasks)

**Tasks:**
```
Week 5-6: Remaining 18 Crux modes as skills
- [ ] Package each mode as SKILL.md
  - calendar-mode, email-mode, integration-mode, etc.
  - Test locally before publishing
- [ ] Publish to ClawHub in batches
- [ ] Create "awesome-crux-for-openclaw" guide

Week 6-7: Knowledge base integration
- [ ] Build knowledge sync module (OpenClaw ↔ Crux)
  - Read OpenClaw memories (patterns, mistakes)
  - Write to Crux knowledge base (user-level)
  - Bidirectional sync
- [ ] Test sync with sample workflows
- [ ] Add knowledge store capability to OpenClaw skills

Week 7-8: MCP server + Heartbeat
- [ ] Build Crux MCP server
  - Expose: mode-select, security-audit, query-knowledge, store-pattern, tdd-spec
  - Test with OpenClaw client
- [ ] Build Heartbeat processor
  - Analyze task logs
  - Extract patterns
  - Store in knowledge base
  - Send daily digest
- [ ] End-to-end integration test
  - User runs task on OpenClaw
  - OpenClaw calls Crux for mode selection
  - Crux safety plugin validates execution
  - Success pattern stored in knowledge base
  - Heartbeat processes and improves pattern
  - Daily digest delivered
```

---

#### Phase 4: Crux Vibe + OpenClaw Bundle (Weeks 9-12)

**Goal:** Pre-configured Mac Mini image bundling OpenClaw + Crux OS + Ollama, ready for one-command deployment.

**Deliverables:**
1. Mac Mini disk image with full stack
   - OpenClaw (latest)
   - Crux OS (with all 21 modes)
   - Ollama (with recommended models)
   - Messaging integrations pre-configured (WhatsApp, Slack, Telegram, etc.)

2. Setup script (one-command installation)
3. Configuration guide
4. Crux Vibe integration (sold as premium tier)

**Success metrics:**
- Mac Mini image published and documented
- 50+ Crux Vibe subscribers (Tier B or C)
- Average monthly revenue: $6,250 (50 × $125) or more

**Tasks:**
```
Week 9-10: Mac Mini image building
- [ ] Create base Mac Mini image (macOS, security baseline)
- [ ] Install OpenClaw + dependencies
- [ ] Install Crux OS + all 21 modes
- [ ] Install Ollama + recommended models
  - mistral-7b (fast, general)
  - neural-chat (faster, good for agents)
  - openchat (efficient, good for local)
- [ ] Pre-configure messaging integrations
  - WhatsApp webhook ready
  - Slack OAuth template
  - Telegram bot template
  - Discord webhook ready
- [ ] Test full stack end-to-end

Week 10-11: Setup automation + Crux Vibe integration
- [ ] Build setup script (one-command installation)
  - Auto-discover Mac Mini hardware
  - Auto-configure Ollama resources
  - Auto-setup messaging with guided steps
  - Auto-enroll in Crux Vibe tier
- [ ] Document all setup options
- [ ] Create video tutorials
- [ ] Integrate with Crux Vibe payment/billing

Week 11-12: Launch + marketing
- [ ] Publish Mac Mini image to Crux Vibe platform
- [ ] Launch Tier B (Colocated, $125/month) and Tier C (Managed, $349/month)
- [ ] Create landing page
- [ ] Write launch announcement
- [ ] Reach out to OpenClaw community (GitHub, r/LocalLLaMA, Discord)
```

---

#### Phase 5: Ecosystem & Governance (Ongoing)

**Ongoing initiatives:**
1. Community Crux skills for OpenClaw
   - Bounty program: $100-500 per skill
   - Vetting and publishing process

2. Crux-audited skill badge program
   - Run security audit on all ClawHub skills
   - Award "Crux-verified" badge to safe skills
   - Publish weekly audit reports

3. Vulnerability disclosure partnership with OpenClaw foundation
   - Share security findings responsibly
   - Collaborate on security improvements
   - Joint security advisory program

4. Knowledge base marketplace
   - Users can share successful patterns across projects
   - "Pattern marketplace" in Crux Vibe
   - Revenue share with pattern authors

---

### 1.5 Technical Specifications & Code Examples

#### Specification 1: OpenClaw Skill Format (Crux Modes)

Every Crux mode becomes an installable SKILL.md file:

```markdown
---
name: crux-code-review-mode
version: 1.2.0
author: Crux OS
license: MIT
description: >
  Deep code review with security focus, performance analysis, and design validation.
  Uses static analysis, security scanning, and knowledge-based patterns to identify issues.
category: development
tags: [review, security, quality, testing]
dependencies:
  - python >= 3.9
  - nodejs >= 16
prerequisites:
  - semgrep
  - bandit
  - mypy
keywords:
  - code review
  - security
  - quality assurance
  - design review
difficulty: intermediate
estimatedDuration: 300  # seconds per review
---

# Crux Code Review Mode

## Overview

This mode performs comprehensive code reviews combining static analysis, security scanning, architectural assessment, and knowledge-based pattern matching.

## Features

- **Security Analysis**: SAST, dependency vulnerabilities, auth patterns
- **Performance**: Algorithmic complexity, memory usage patterns
- **Design Review**: Architecture, SOLID principles, design patterns
- **Testing**: Coverage analysis, test quality assessment
- **Knowledge-Based**: Compares against learned successful patterns

## Usage

User request to OpenClaw: "Review my Python authentication module"

This skill will:
1. Load the module code
2. Run semantic analysis (semgrep) - security patterns
3. Run static checks (bandit, mypy) - type safety
4. Query knowledge base for similar successful auth patterns
5. Generate comprehensive review with:
   - Security findings (critical/high/medium/low)
   - Performance issues and suggestions
   - Design feedback
   - Comparison to best practices
   - Test coverage assessment
6. Store review pattern in knowledge base for future reference

## Configuration

```yaml
review_tools:
  - semgrep          # Pattern matching (includes security rules)
  - bandit           # Python security
  - mypy             # Type checking
  - pylint           # Code style
  - pytest --cov     # Coverage

security_level: high  # Filter issues: high | medium | low | all
include_design_review: true
include_performance_analysis: true
compare_to_patterns: true
```

## Example Output

```
REVIEW SUMMARY: auth_module.py
================================

Security Findings:
  [CRITICAL] SQL injection risk in query builder (line 42)
    Risk: User input not parameterized
    Fix: Use parameterized queries
    Pattern: crux-safe-sql-pattern

  [HIGH] Hardcoded API key in config (line 15)
    Risk: Credential exposure
    Fix: Use environment variables
    Pattern: crux-vault-integration-pattern

Performance Issues:
  [MEDIUM] N+1 query in user fetch loop (line 78)
    Impact: O(n) queries for n users
    Fix: Use JOIN or batch fetch
    Pattern: crux-efficient-db-pattern

Design Feedback:
  [SUGGESTION] Consider decorator pattern for auth checks
    Benefit: More composable, easier to test
    Example: See crux-decorator-auth-pattern

Test Coverage:
  Current: 67% (acceptable)
  Recommended: 90%+ for auth code
  Missing: Edge cases (expired tokens, malformed input)

Knowledge Base Matches:
  Similar successful patterns found:
  - crux-jwt-auth-pattern (98% match)
  - crux-password-hashing-pattern (92% match)
  - crux-session-management-pattern (85% match)

RECOMMENDATION: Fix critical/high findings before merge
```

## Implementation (JavaScript/TypeScript)

```typescript
export async function reviewCode(context: SkillContext) {
  const code = await context.readFile(context.params.filePath);

  // Run security analysis
  const security = await runSemgrep(code, {
    rules: 'p/security-audit'
  });

  // Run static checks
  const style = await runPylint(code);
  const types = await runMypy(code);

  // Query knowledge base
  const patterns = await context.knowledge.search(
    `${detectLanguage(code)} best practices`,
    'public'
  );

  // Generate review
  const review = {
    security: security.issues,
    performance: analyzePerformance(code),
    design: analyzeDesign(code, patterns),
    coverage: await analyzeCoverage(code),
    recommendations: generateRecommendations(security, patterns)
  };

  // Store review pattern
  await context.knowledge.storePattern({
    name: `review-${Date.now()}`,
    type: 'code-review',
    code: code,
    findings: review,
    timestamp: Date.now()
  });

  return review;
}
```

---

#### Specification 2: Plugin Format (crux-safety-gateway)

TypeScript plugin that integrates with OpenClaw's middleware system:

```typescript
// Package: @crux-os/safety-gateway
// Installation: npm install @crux-os/safety-gateway

import type { Plugin, ToolCall, ExecutionContext } from '@openclaw/types';

export interface SafetyGatewayConfig {
  // Risk tolerance for automated blocking
  riskTolerance: 'strict' | 'moderate' | 'permissive';

  // Tools requiring human approval
  requireHumanApprovalFor: string[];

  // Gate enablement
  gates: {
    preflight: boolean;
    securityAudit: boolean;
    secondOpinion: boolean;
    humanApproval: boolean;
    dryRun: boolean;
    validation: boolean;
  };

  // Security scanning
  security: {
    enableSSRFDetection: boolean;
    enableAuthValidation: boolean;
    enableCredentialLeakDetection: boolean;
    maxRecursiveAuditIterations: number;
  };
}

export const DEFAULT_CONFIG: SafetyGatewayConfig = {
  riskTolerance: 'moderate',
  requireHumanApprovalFor: ['delete', 'modify_auth', 'send_email'],
  gates: {
    preflight: true,
    securityAudit: true,
    secondOpinion: false,
    humanApproval: true,
    dryRun: true,
    validation: true
  },
  security: {
    enableSSRFDetection: true,
    enableAuthValidation: true,
    enableCredentialLeakDetection: true,
    maxRecursiveAuditIterations: 3
  }
};

export const plugin: Plugin = {
  name: 'crux-safety-gateway',
  version: '1.0.0',

  onToolCall: async (
    call: ToolCall,
    context: ExecutionContext,
    config: SafetyGatewayConfig = DEFAULT_CONFIG
  ) => {
    console.log(`[Crux] Validating tool call: ${call.tool}`);

    const validation = await validateToolCall(call, context, config);

    if (!validation.allowed) {
      console.warn(`[Crux] BLOCKED: ${validation.reason}`);
      console.warn(`[Crux] Gates: ${validation.gates.join(' → ')}`);

      if (validation.requiresApproval) {
        // Queue for human review
        await context.requestApproval(call, validation.reason);
        return { blocked: true, requiresApproval: true };
      }

      throw new Error(`Crux Safety: ${validation.reason}`);
    }

    console.log(`[Crux] ALLOWED: All gates passed`);
    return { blocked: false, modifiedCall: validation.modifiedCall };
  }
};

async function validateToolCall(
  call: ToolCall,
  context: ExecutionContext,
  config: SafetyGatewayConfig
) {
  const gates = [];
  let allowed = true;
  let reason = '';
  let modifiedCall = call;

  // Gate 1: Preflight
  if (config.gates.preflight) {
    const result = validatePreflight(call);
    gates.push('preflight');
    if (!result.valid) {
      allowed = false;
      reason = result.error;
      return { allowed, gates, reason, modifiedCall: call };
    }
  }

  // Gate 2: Security Audit
  if (config.gates.securityAudit) {
    const audit = await performSecurityAudit(call, config);
    gates.push('security-audit');

    if (!audit.safe) {
      if (audit.suggestedFix && config.riskTolerance !== 'strict') {
        modifiedCall = audit.suggestedFix;
        gates.push('security-fix-applied');
      } else {
        allowed = false;
        reason = `Security risk: ${audit.risks.join(', ')}`;
        return { allowed, gates, reason, modifiedCall: call };
      }
    }
  }

  // Gate 3: Human Approval
  if (config.gates.humanApproval && requiresApproval(call, config)) {
    gates.push('human-approval');
    return {
      allowed: false,
      gates,
      reason: 'Awaiting human approval',
      requiresApproval: true,
      modifiedCall
    };
  }

  return { allowed: true, gates, reason: 'All gates passed', modifiedCall };
}

function performSecurityAudit(call: ToolCall, config: SafetyGatewayConfig) {
  const risks = [];

  // SSRF detection
  if (config.security.enableSSRFDetection && isNetworkCall(call)) {
    if (containsMetadataPatterns(call.arguments)) {
      risks.push('SSRF: Metadata server access attempt');
    }
  }

  // Credential leak detection
  if (config.security.enableCredentialLeakDetection) {
    if (containsSecrets(call.arguments)) {
      risks.push('Credential exposure: Secrets in command');
    }
  }

  return {
    safe: risks.length === 0,
    risks,
    suggestedFix: generateSecurityFix(call, risks)
  };
}
```

---

### 1.6 The OpenClaw Security Opportunity: Strategic Entry Point

OpenClaw's security crisis is Crux's highest-leverage market entry point. Here's why:

**The Numbers:**
- 250K+ OpenClaw users (and growing)
- 63% have security vulnerabilities
- 135K exposed instances
- 820+ malicious skills in marketplace
- Massive security awareness opportunity

**Crux's Strategic Positioning:**
1. **Free safety plugin** → Immediate adoption across OpenClaw community
2. **Solves documented problems** → Security fixes CVE-2026-26322, CVE-2026-26319, credential exposure
3. **Low friction** → Install one skill/plugin, get protection
4. **Network effect** → Every protected instance is a marketing win

**The Funnel:**
```
1. User hears about OpenClaw security issues
2. User discovers "Crux makes OpenClaw safe"
3. User installs crux-safety-gateway (free)
4. User loves the safety, stability, and learning
5. User wants more: managed Mac Mini, all features
6. User subscribes to Crux Vibe ($125-349/month)
```

**Why This Works:**
- OpenClaw community is security-conscious (self-hosted, cautious)
- Crux's solution directly addresses their pain (safety pipeline)
- Free distribution builds massive user base
- Conversion to paid tiers happens naturally (want more protection + convenience)

**Execution:**
1. **Week 1:** Launch crux-safety-gateway as free plugin (Phase 1)
2. **Messaging:** "Make your OpenClaw safe with Crux's seven-gate safety pipeline"
3. **Channels:** r/LocalLLaMA, OpenClaw GitHub, OpenClaw Discord, HackerNews
4. **Content:** Security audit reports, vulnerability demonstrations, comparison articles
5. **Results:** 5K+ installations → 1-2% convert to Crux Vibe → $62,500-125,000/month revenue at scale

---

## PART 2: WEBSITE MESSAGING & MARKETING STRATEGY

### 2.1 Website Copy: Crux + OpenClaw Landing Section

#### Primary Headline Options

**Option A (Safety-focused):**
```
OpenClaw is Powerful. Crux Makes It Safe.
```
Subheading: "Your autonomous AI agent, protected by a seven-gate safety pipeline and learned from 5,000+ successful workflows."

**Option B (Capability-focused):**
```
From General Agent to 21 Specialists
```
Subheading: "OpenClaw + Crux turns your single AI into a team of experts, each optimized for their domain."

**Option C (Security-focused, direct):**
```
63% of OpenClaw Deployments Have Security Vulnerabilities.
Fix Yours in One Command.
```
Subheading: "Crux's safety pipeline blocks malicious skills, detects SSRF attacks, and prevents credential exposure—automatically."

**Option D (Empowerment-focused):**
```
Your OpenClaw Agent Just Got Smarter
```
Subheading: "Learn from every task. Improve with every attempt. Understand your agent's decisions."

---

#### Primary Copy (2-3 paragraphs)

**Recommended approach: Combination of B + A**

```
Headline: From General Agent to 21 Specialists
Subheading: OpenClaw + Crux gives your autonomous AI both protection and expertise.

Paragraph 1:
OpenClaw is incredible — 250K developers use it to build autonomous AI agents that
connect to WhatsApp, Slack, Telegram, and Discord. But it has a problem: it's a
general-purpose agent. One model trying to do everything. Security researcher?
Calendar expert? API integrator? All handled the same way.

Crux solves this with 21 specialized modes. Instead of one agent, you get a team:
a code review specialist, a security auditor, an API integration expert, a calendar
manager. Each mode is optimized for its domain, uses the best patterns, understands
the specific risks and opportunities.

The result: Your agent is smarter, safer, and actually learns from its mistakes.

Paragraph 2:
But there's more. OpenClaw doesn't have a safety pipeline — the agent executes
whatever the LLM suggests. No checking for SSRF attacks. No credential leak detection.
No testing before deployment. 63% of OpenClaw deployments are vulnerable to known exploits.

Crux adds a seven-gate safety system between thinking and doing. Every action is validated:
• Syntax & permissions check
• Security audit (recursive, until safe)
• Alternative reasoning path (second opinion)
• Sandboxed test run (dry run)
• Outcome validation (did it work as intended?)
And then Crux learns. Every successful action becomes a pattern. Your agent improves over time.

Paragraph 3:
OpenClaw without Crux: Powerful but risky. General-purpose agent executing blind.
OpenClaw with Crux: Safe, specialized, and self-improving. This is how you run
autonomous AI in production.

Install Crux for OpenClaw → clawhub install crux-os
Get started with managed hardware → Crux Vibe ($125-349/month)
```

---

#### Feature Callouts (6-8 with icons)

```
🔐 Seven-Gate Safety Pipeline
Every action validated before execution. SSRF detection. Credential leak prevention.
No more 135K exposed instances.

🧠 21 Specialized Modes
Code review specialist. Security auditor. API expert. Calendar manager.
Each mode is a domain expert, not a generalist.

📚 Learned Patterns
Every successful task becomes a pattern. Your agent learns over time, makes better
decisions, and can explain why it chose an approach.

🔍 Recursive Security Audit
Security issues automatically detected and fixed. Audit runs until convergence.
No more 63% vulnerability rate.

✅ TDD Enforcement
Code is tested before deployment. Specifications are validated. Tests are run.
No more shipping untested code.

🛡️ Malicious Skill Detection
ClawHub skills are audited before use. Crux-verified badge means safe. 820+
malicious skills in marketplace? We catch them.

📊 Continuous Improvement
Heartbeat processor runs during idle time. Analyzes patterns. Learns from corrections.
Generates daily digest of improvements.

⚡ Works on Your Mac Mini
OpenClaw + Crux + Ollama running locally. Full sovereignty. No cloud. Full control.
Just like Crux Vibe's infrastructure — you can run your own.
```

---

#### Call-to-Action Section

```
Ready to Make OpenClaw Safe and Smart?

Option A: DIY (Free)
Install Crux for OpenClaw on your existing instance
clawhub install crux-os

Get all 21 modes, safety pipeline, knowledge base, continuous improvement.
Full open source, MIT licensed.
Perfect for engineers who want full control.

Option B: Managed (Crux Vibe)
Crux + OpenClaw pre-configured on a colocated or managed Mac Mini
Starting at $125/month (colocated) or $349/month (fully managed)

One-command setup. Automatic updates. We handle hardware, networking, backups.
Perfect for teams who want to focus on building, not operations.

Option C: Enterprise
Custom deployments, team features, priority support, security audits
Contact us for details

Choose your path →
```

---

### 2.2 Messaging Framework: Different Audiences

#### For Security-Conscious Users

**Lead with numbers:**
"63% of OpenClaw deployments have security vulnerabilities. The top three CVEs? All addressed by Crux's safety pipeline."

**Message structure:**
1. Problem: OpenClaw is powerful but exposed
2. Why it matters: Your agent has access to APIs, files, shell commands
3. Crux solution: Seven-gate safety pipeline prevents all three CVEs
4. Proof: Specific technical details (SSRF detector, auth validator, credential leak scanner)
5. CTA: "Install the free safety plugin. Protect your instance in 5 minutes."

**Tone:** Urgent but not fear-mongering. Technical. Trustworthy.

**Sample headline:** "How We Blocked CVE-2026-26322 (SSRF) in OpenClaw — Automatically"

---

#### For Power Users (Technical, want capability)

**Lead with capability:**
"21 specialized modes instead of one general agent. Your AI just became a team of experts."

**Message structure:**
1. Problem: General-purpose agents make mistakes in specialized domains
2. Solution: Crux's mode router selects the right specialist for each task
3. Benefit: Better decisions, learned patterns, self-improvement
4. Example: "You ask for a calendar event. Calendar-mode handles it (knows timezone rules, respects availability, understands recurring patterns). Not a generalist fumbling through date logic."
5. CTA: "Install Crux. See your agent's decision-making improve."

**Tone:** Technical. Capability-focused. Respect for intelligence.

**Sample headline:** "OpenClaw + 21 Specialized Modes: The Difference Between Competence and Expertise"

---

#### For Beginners

**Lead with simplicity:**
"Your personal AI on a Mac Mini. It learns. It improves. It stays safe."

**Message structure:**
1. What: OpenClaw (personal AI assistant on your computer) + Crux (makes it smart and safe)
2. Why: Control your AI. No cloud. Continuous improvement.
3. How: One command to install. Mac Mini for hardware (we recommend it).
4. What you get: Agent that handles emails, schedules, integrations. Learns your preferences. Explains its decisions.
5. CTA: "Start free. Upgrade to managed hardware when you're ready."

**Tone:** Accessible. Aspirational. Not technical.

**Sample headline:** "Your Personal AI, Running on Your Mac. Learning Every Day."

---

#### For Enterprise/Regulated (Compliance + Auditing)

**Lead with compliance:**
"Auditable, compliant AI agent operation with full safety pipeline and decision logs."

**Message structure:**
1. Problem: Autonomous AI in regulated industries (finance, healthcare, legal) needs audit trails and safety validation
2. Solution: Crux provides complete decision logging, safety gates, and correction tracking
3. Benefits: Regulatory compliance. Explainability. Correction documentation.
4. Features: Seven-gate safety pipeline with audit log. Every decision traced. Every correction documented. TDD enforcement means tested code.
5. CTA: "Contact us for enterprise deployment and compliance features."

**Tone:** Professional. Compliance-focused. Trustworthy.

**Sample headline:** "Autonomous AI for Regulated Industries: Full Safety Pipeline, Audit Trails, Compliance Ready"

---

### 2.3 Content Strategy for OpenClaw Community

#### Blog Post Series (5 posts)

**Post 1: "How We Made OpenClaw 10x Safer with Crux's Safety Pipeline"**
- Deep dive on CVE-2026-26322 (SSRF), CVE-2026-26319 (auth), credential exposure
- Show real attack scenarios
- Demonstrate Crux's gates blocking each attack
- Include video of safety pipeline in action
- CTA: Install safety plugin

**Post 2: "From General Agent to 21 Specialists: Mode-Routing for OpenClaw"**
- Explain mode routing concept
- Show side-by-side: general approach vs. specialized approach
- Example: Calendar task
  - Without Crux: Agent tries to handle timezone math, availability checking, recurring rules
  - With Crux: calendar-mode handles it (knows all the patterns)
- Performance comparison
- CTA: Install Crux, see the difference

**Post 3: "OpenClaw + Crux + Mac Mini: The Sovereign AI Stack"**
- Complete architecture diagram
- Hardware recommendations (Mac Mini M1/M2 specs)
- Software setup (OpenClaw, Crux, Ollama)
- Networking (secure, local-first)
- Messaging integrations (WhatsApp, Slack, Telegram)
- Performance benchmarks
- Cost comparison (DIY vs. Crux Vibe)
- CTA: Buy Mac Mini, follow one-command setup

**Post 4: "Why Your OpenClaw Instance Needs TDD Enforcement"**
- Problem: Generated code often untested
- Impact: Bugs reach production, agent loses trust
- Solution: Crux's TDD gate
  - Generate tests first (test-spec-mode)
  - Run tests before deployment
  - Verify outcome matches specification
- Real examples of bugs prevented
- CTA: Enable TDD enforcement in crux-safety-gateway

**Post 5: "Building a Self-Improving OpenClaw Agent with Crux Knowledge Base"**
- How Crux knowledge base works (project/user/public levels)
- How Heartbeat processor learns from every task
- How corrections become patterns
- Real example: Agent learns better auth pattern after failure
- Dashboard showing learned patterns over time
- CTA: Deploy Crux Vibe to see knowledge base in action

---

#### Reddit Strategy

**Primary subreddit: r/LocalLLaMA**
- OpenClaw discussions happen here
- High technical literacy
- Security-conscious audience

**Secondary: r/selfhosted**
- Mac Mini + OpenClaw popular
- Privacy-focused audience
- Infrastructure-interested

**Posting strategy:**

**Post format 1: Technical deep-dive**
```
Title: "I Added Crux's Safety Pipeline to My OpenClaw Instance.
        Here's What Changed (CVE Blocking, Attack Prevention, Learning)"

Content:
- Problem statement (63% vulnerability rate, exposed instances)
- How I set it up (5 minutes, 2 commands)
- What changed:
  * CVE-2026-26322 (SSRF) now blocked automatically
  * Credential leak detection prevents secret exposure
  * Agent learns from successful tasks
  * TDD enforcement validates generated code
- Metrics:
  * Before: 2 failed tasks/week, unexplained errors
  * After: 0 failed tasks (6 weeks), visible improvements
- Lessons learned
- Recommendation: Try it yourself, community seems interested

[Link to GitHub with setup guide]
```

**Post format 2: "Show HN" style**
```
Title: "Crux — Safety Pipeline and Specialized Modes for OpenClaw"

Content:
- What is it?
- Why does it matter?
- Technical details
- Results
- Try it yourself (one command)

[Link to installation guide]
```

**Post format 3: Question-based engagement**
```
Title: "OpenClaw Security: How are you protecting your instance?
        (63% have vulnerabilities according to research)"

Content:
- Share security research findings
- Ask community: What security measures do you use?
- Share Crux as one option (not the only answer)
- Engage authentically with community responses

This positions Crux as part of the conversation, not salesmanship.
```

**Posting cadence:** 1-2 posts per month, not spammy, respond authentically to all comments.

---

#### Hacker News Strategy

**Target:** Technical audience, security-focused, early adopter.

**Submission 1: Launch post**
```
Title: Crux — Safety Pipeline for OpenClaw (Make Autonomous AI Safe)

Text:
We built a safety pipeline for OpenClaw that addresses CVE-2026-26322 (SSRF),
CVE-2026-26319 (missing auth), and credential exposure. 63% of OpenClaw
deployments are vulnerable; we're making that fixable. Open source, MIT licensed.

Links:
- GitHub repo
- Installation guide
- Blog post: How we blocked these CVEs
```

**Why it matters for HN:**
- Security vulnerability with clear solution
- Open source
- Technical depth
- Community-beneficial

**Strategy:**
- Submit on Tuesday-Thursday (best timing)
- Be available for comments (HN audience appreciates responsive creators)
- Don't oversell; let the work speak
- Reference specific CVEs and vulnerabilities (HN respects technical specificity)

---

#### X/Twitter Strategy

**Thread template:**

```
THREAD: OpenClaw security is broken. 63% of deployments are vulnerable.
Here's how I fixed mine.

1/ OpenClaw is amazing — 250K developers, autonomous AI agent that connects
to messaging platforms. But it has zero safety pipeline. Agent executes blindly.

2/ CVE-2026-26322 (SSRF): No protection against metadata server attacks.
   CVE-2026-26319 (Missing auth): No auth validation on API calls.
   Credential exposure: API keys stored in plaintext.

   135K instances exposed to the internet.

3/ I tried Crux's safety pipeline. It's a 7-gate system:
   → Syntax validation
   → Security audit (recursive)
   → Second opinion (alternative reasoning)
   → Dry run (sandboxed test)
   → Outcome validation
   → Knowledge learning

   Every action validated before execution.

4/ Results after 6 weeks:
   • 0 CVE exploits (was vulnerable before)
   • 0 credential leaks
   • Agent learned 47 successful patterns
   • Generated code tested before deployment
   • Daily improvement report

5/ Setup: One command.
   clawhub install crux-os

   Open source. MIT licensed. Works on Mac Mini + Ollama.
   Took 5 minutes to install.

6/ If you run OpenClaw and care about security (you should),
try Crux. Free. Open source. Blocks the stuff that matters.

[Link to installation guide]

---

cc: @steipete (thanks for building OpenClaw)
#openclaw #crux #localllm #selfhosted #security
```

**Posting cadence:** 2-3 times per week, mix of:
- Educational threads (security lessons, architecture)
- Announcement threads (feature releases)
- Engagement threads (questions, discussions)
- Case study threads (user results)

**Engagement:** Respond to replies, retweet relevant discussions, tag OpenClaw contributors.

---

### 2.4 OpenClaw Community Engagement Plan

**Objective:** Build credibility and relationships with OpenClaw community. Position Crux as trusted partner, not competitor.

#### Phase 1: Credibility (Weeks 1-4)

**Actions:**
1. Contribute security fixes to OpenClaw core repo
   - Identify and fix security issues in main codebase
   - Submit PRs with detailed explanations
   - Show community leadership

2. File thoughtful issues
   - Not complaint posts, but constructive discovery
   - "I found a pattern in OpenClaw that could lead to SSRF attacks. Here's a real-world scenario and a proposed fix."
   - Demonstrate deep understanding

3. Participate in GitHub Discussions
   - Answer user questions about OpenClaw
   - Help with setup, troubleshooting
   - Offer Crux as one solution option (not pushy)

#### Phase 2: Partnership (Weeks 5-8)

**Actions:**
1. Offer free security audits of popular ClawHub skills
   - "We analyzed the top 20 ClawHub skills. Found 3 security issues. Here's the report."
   - No CTA, just value
   - Builds trust

2. Propose "Crux-audited" badge program to OpenClaw foundation
   - Skill authors can request security audit from Crux
   - Badge shows skill has been validated
   - Partnership benefit for OpenClaw (better marketplace security)

3. Build relationships with core contributors
   - Direct outreach (GitHub DMs, Twitter, email)
   - Share findings and insights
   - Propose collaboration on security improvements

#### Phase 3: Integration (Weeks 9-12)

**Actions:**
1. Official recommendation in OpenClaw docs
   - Get OpenClaw to link to Crux safety plugin in security section
   - Position as official recommended safety layer

2. Joint security advisory
   - OpenClaw + Crux coordinate on CVE response
   - Share vulnerability research
   - Co-authored security posts

3. ClawHub integration
   - Crux skills available directly from OpenClaw marketplace
   - Easy one-command install

#### Phase 4: Ongoing

**Recurring activities:**
- Weekly security audit reports (top 10 ClawHub skills)
- Monthly blog post on OpenClaw security trends
- Quarterly partnership updates with OpenClaw foundation
- Community presence (Discord, GitHub, Reddit, Twitter)

---

### 2.5 Revenue Model Analysis

#### Freemium Approach (Recommended)

**Free tier:**
```
OpenClaw Skills (on ClawHub):
  • crux-build-python (TDD enforcement)
  • crux-review (code review)
  • crux-security-audit (vulnerability scanning)
  • crux-vault (secret management)
  • ... all 21 modes

Safety Plugin:
  • crux-safety-gateway (basic: 3 gates)
  • Preflight validation
  • Security audit
  • Dry run

Knowledge Base:
  • Project-level storage (private to your project)
  • Up to 1,000 stored patterns

Heartbeat Learning:
  • Automatic pattern extraction
  • Daily digest (text-based)
```

**Paid tier (Crux Vibe subscription, $125-349/month):**
```
Everything in free, plus:

Safety Plugin Pro:
  • All 7 gates (including human approval, second opinion)
  • Custom risk tolerance policies
  • Team management (invite colleagues)
  • Audit log export

Knowledge Base Plus:
  • User-level sharing (across your projects)
  • Public knowledge marketplace
  • Pattern versioning and history
  • Search and discovery UI

Continuous Learning:
  • Smart pattern organization
  • Improvement metrics dashboard
  • Cross-project learning
  • Weekly strategy reports

Hardware Options:
  • Tier B: Colocated Mac Mini ($125/month)
    - Your Mac Mini in MacStadium facility
    - We manage networking, power, updates
    - You maintain full control

  • Tier C: Managed Mac Mini ($349/month)
    - We own and manage everything
    - OpenClaw + Crux pre-configured
    - Hands-off operation
    - Messaging integrations ready
    - Automatic backups

Support:
  • Community support (free)
  • Email support (Tier B)
  • Priority Slack support (Tier C)

Enterprise:
  • Custom policies
  • Team features (audit logs, approval workflows)
  • Security audit services
  • SLA guarantees
```

#### Why This Model Works

**Free distribution:**
- 250K OpenClaw users can install Crux skills instantly
- Network effect: more users = more learned patterns = better for everyone
- No friction to try
- Data: what modes are most popular? What patterns work best?

**Paid conversion funnel:**
```
Step 1: User installs free Crux skills (clawhub install crux-build-python)
Step 2: User loves the safety and learning
Step 3: User wants managed hardware (don't want to manage Mac Mini)
Step 4: User subscribes to Crux Vibe ($125-349/month)
Step 5: User invites team members (increase seat count)
```

**Revenue projection (conservative):**
- 250K OpenClaw users
- 2% adoption rate (5,000 install Crux skills)
- 1% conversion to Crux Vibe (50 subscriptions)
- Average tier: $237/month (mix of Tier B and C)
- Monthly recurring revenue: $11,850
- Annual: $142,200

**Realistic (optimistic):**
- 5% adoption (12,500 install)
- 2% conversion (250 subscriptions)
- Average: $237/month
- Monthly: $59,250
- Annual: $711,000

---

### 2.6 Integration Into Guerrilla Marketing Plan

#### New Channels

**ClawHub Marketplace**
- 5,400+ skills, millions of downloads potential
- Crux skills published and discoverable
- Integration: Users searching for "test automation" find crux-build-python
- Each skill description links to: "Full safety pipeline: install crux-os"

**OpenClaw GitHub Discussions**
- Active community (thousands of daily discussions)
- Monitor for security questions, setup help
- Propose Crux as solution option (helpfully, not pushy)

**OpenClaw Discord/Community Channels**
- Real-time engagement with users
- Answer questions, offer assistance
- Announce new Crux skills
- Share security research

**r/LocalLLaMA**
- OpenClaw discussions concentrated here
- High-quality, technical audience
- Post technical content, not just promotion

---

#### New Content Types

**Tutorial Series: OpenClaw + Crux Setup**
1. "Installing OpenClaw on Mac Mini (5 minutes)"
2. "Adding Crux Safety Pipeline (2 commands)"
3. "Configuring Messaging Integrations (WhatsApp, Slack, Telegram)"
4. "Monitoring Your Agent (Dashboard, Logs, Learning Metrics)"
5. "Scaling to a Team (Multi-user, Approval Workflows)"

Format: Blog posts + YouTube videos (clear, step-by-step)

**Security Audit Reports (Weekly)**
```
"Weekly OpenClaw Marketplace Security Report"
- Top 20 ClawHub skills analyzed
- Security findings for each
- Crux audit status (does it pass security checks?)
- Recommendations
- Published to: Blog, Reddit, Twitter

Example:
  Skill: "email-automation-pro" (4,200 installs)
  Status: ⚠️ Security Risk Found
  Issue: Hardcoded API key in main.js
  Severity: CRITICAL
  Recommendation: Update to v2.1.0 (fix released) OR use Crux vault mode
  Crux Audit: Not yet reviewed
  Action: We've notified the author
```

**Comparative Performance Posts**
- "OpenClaw with Crux vs. Without Crux: 6-Week Comparison"
- Metrics:
  - Success rate (tasks completed correctly)
  - Security incidents (CVE exploits attempted)
  - Code quality (test coverage)
  - Agent learning (patterns stored)
  - Execution speed

**Mac Mini Setup Guides**
- Complete hardware recommendations (M1 vs. M2, RAM, storage)
- Networking setup (secure, local-first)
- Ollama configuration (model selection)
- OpenClaw + Crux deployment
- Messaging integration
- Cost breakdown (hardware + Crux Vibe vs. cloud alternatives)

---

#### New Guerrilla Tactics

**Tactic 1: Free Security Audit Program**
- "We'll audit your top 3 ClawHub skills for free"
- Blog post: "3 Popular OpenClaw Skills We Audited: Security Findings"
- No CTA, just value
- Builds credibility, discovers real vulnerabilities
- Positions Crux as security leader

**Tactic 2: Security Thread Responses**
- Monitor: r/LocalLLaMA, r/selfhosted, OpenClaw GitHub, HackerNews for security posts
- When someone posts: "Is OpenClaw secure?" or "How do I protect my OpenClaw instance?"
- Respond with detailed, helpful answer
- Include Crux solution as one option
- Never pushy, always respectful

**Tactic 3: "Awesome OpenClaw Security" Repository**
- GitHub repo: awesome-openclaw-security
- List of security practices, tools, resources
- Feature Crux prominently (but alongside other approaches)
- Community contributions
- Becomes go-to resource for OpenClaw security

**Tactic 4: Skill Bounty Program**
- "$500 bounty: Write a Crux skill for [domain]"
- Examples: crux-slack-automation, crux-notion-integration, crux-airtable-sync
- Community authors get paid
- Crux gets more skills
- Users get more capabilities

**Tactic 5: Security Bug Bounty**
- "Found a security issue in OpenClaw? We'll match the OpenClaw foundation's reward."
- Shows commitment to security
- Builds credibility
- Benefits whole ecosystem

---

#### New Metrics to Track

**Awareness:**
- GitHub stars on crux-openclaw repo
- Twitter mentions of Crux + OpenClaw
- r/LocalLLaMA post upvotes/engagement
- HackerNews ranking

**Adoption:**
- ClawHub skill installs (per mode)
- crux-safety-gateway npm downloads
- MCP server deployments
- Total Crux instances running alongside OpenClaw (from telemetry)

**Conversion:**
- Free OpenClaw users who install Crux
- Crux users who subscribe to Crux Vibe
- Conversion rate (% of OpenClaw users)
- Average revenue per user (ARPU)

**Engagement:**
- GitHub Issues/PRs on crux-openclaw
- Reddit/Twitter replies to our posts
- OpenClaw GitHub Discussions participation
- Email signups (newsletter)

**Business:**
- Monthly recurring revenue (Crux Vibe subscriptions)
- Lifetime value per customer
- Customer acquisition cost
- Churn rate

---

### 2.7 How This Folds Into Guerrilla Marketing Master Plan

#### Unified Strategy

**Core message:** Crux + OpenClaw = Safe, Smart, Self-Improving AI

**Channels (in priority order):**
1. **ClawHub** (Distribution hub) — Skills published, discoverability
2. **r/LocalLLaMA** (Community hub) — Technical discussions, credibility
3. **OpenClaw GitHub** (Authority hub) — Issues, discussions, PRs, credibility
4. **Hacker News** (Awareness hub) — Technical audience, high trust
5. **Twitter/X** (Amplification) — Thread discussions, regular engagement
6. **Blog** (Thought leadership) — Long-form content, SEO
7. **YouTube** (Tutorial hub) — Setup guides, demos, explainers
8. **Direct outreach** (Relationships) — Email to creators, Discord conversations, GitHub DMs

**Execution rhythm:**
- Week 1: Publish Crux skills to ClawHub + announcement blog post
- Week 2: Submit to HackerNews, post on r/LocalLLaMA
- Week 3-4: Publish security audit report, tweet thread, GitHub discussion participation
- Week 5-6: YouTube tutorial series, email outreach to OpenClaw creators
- Week 7-8: New blog post (deep dive), Twitter engagement, Reddit follow-up
- Ongoing: Weekly security audits, daily Twitter responses, GitHub monitoring

**Content multiplication (make each piece work 10x):**
- Blog post → Twitter thread → Reddit post → YouTube thumbnail/transcript
- Security audit → Tweet → Blog post → Reddit post → HackerNews discussion
- Skill release → Demo video → Blog post → Twitter thread → Reddit announcement

---

## APPENDIX: Quick Reference

### Key Contacts & Communities
- **OpenClaw Creator:** Peter Steinberger (@steipete) on Twitter/GitHub
- **OpenClaw Discord:** https://discord.gg/openclaw (estimate URL)
- **OpenClaw GitHub:** https://github.com/steipete/openclaw
- **r/LocalLLaMA:** https://reddit.com/r/LocalLLaMA
- **OpenClaw Foundation:** Contact through GitHub

### Key Vulnerabilities to Reference
- **CVE-2026-26322:** SSRF (Server-Side Request Forgery) — metadata server access
- **CVE-2026-26319:** Missing authentication on API calls
- **"ClawJacked" vulnerability:** Malicious skill execution
- **Plaintext secrets:** API keys in ~/.openclaw/memory.md

### Key Statistics to Reference
- 250K+ GitHub stars (60 days)
- 63% of deployments have security vulnerabilities
- 135K exposed instances
- 820+ malicious skills in marketplace
- 5,400+ skills total in ClawHub

### Success Metrics (12-week targets)
- **Phase 1:** 3 skills published, 100+ installs
- **Phase 2:** Safety plugin with 50+ installations
- **Phase 3:** All 21 skills published, 500+ total installs
- **Phase 4:** Mac Mini image published, 50+ Crux Vibe subscribers ($6,250+/month MRR)
- **Overall:** 5-10% adoption rate of OpenClaw user base, $10K-60K/month recurring revenue

---

## CLOSING: Why This Works

OpenClaw represents a 250K-user market begging for safety, specialization, and learning. Crux addresses exactly these problems. By positioning Crux as the safety layer for OpenClaw (free distribution) while offering Crux Vibe as the premium experience (managed hardware + full features), we create a natural funnel:

```
Curious OpenClaw user
    ↓
Installs free Crux safety plugin (clawhub install crux-os)
    ↓
Loves the safety and learning capabilities
    ↓
Wants managed hardware (doesn't want to maintain Mac Mini)
    ↓
Subscribes to Crux Vibe ($125-349/month)
    ↓
Invites team members (increase subscription seats)
    ↓
Becomes long-term customer (LTV > $20K)
```

This is a high-leverage entry into a rapidly growing market. The 250K OpenClaw users are already self-hosting, already security-conscious, already open-source friendly. They're perfect Crux Vibe customers.

**Action items for this week:**
1. Package crux-build-python, crux-review, crux-security-audit as SKILL.md files
2. Set up ClawHub publisher account
3. Publish first three skills
4. Write announcement blog post
5. Prepare r/LocalLLaMA post

**Target:** 100+ skill installs by end of Phase 1 (2 weeks). Then compound from there.
