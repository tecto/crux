# BUILD_PLAN_016: Agentic Coding — Autonomous Multi-Step Task Execution

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** SHOULD-CLOSE
**Competitive Gap:** Claude Code has agentic coding — the AI plans, executes multi-step tasks, uses tools autonomously. Crux has modes and tools but no autonomous execution engine.
**Goal:** Crux MCP server can receive a high-level goal and autonomously break it into steps, execute each step using available tools, and report results. Works across any connected AI tool.

**Covers:** Agentic coding, plan mode, architect mode, extended thinking, composer

## Architecture

```
Agent receives: "add OAuth2 login flow"
    │
    ▼
crux_plan(goal) → structured plan with steps
    │
    ▼
For each step:
    crux_execute_step(step) → uses available tools
    crux_validate_step(step, result) → check correctness
    │
    ▼
crux_report(results) → summary of all steps
```

## Phase 1: Plan Generation

- [ ] 1.1 MCP tool: `plan_task(goal)` — break a goal into numbered steps with dependencies
- [ ] 1.2 Each step has: description, tools_needed, files_likely, risk_level
- [ ] 1.3 Store plan in `.crux/plans/active.json`
- [ ] 1.4 MCP tool: `get_plan()` — read current plan
- [ ] 1.5 Tests

## Phase 2: Step Execution Tracking

- [ ] 2.1 MCP tool: `start_step(step_number)` — mark step in progress
- [ ] 2.2 MCP tool: `complete_step(step_number, result)` — mark done with outcome
- [ ] 2.3 MCP tool: `skip_step(step_number, reason)` — skip with justification
- [ ] 2.4 Auto-advance: when step completes, suggest next step
- [ ] 2.5 Tests

## Phase 3: Extended Thinking Integration

- [ ] 3.1 For complex steps, route to think-enabled mode (temperature 0.6, reasoning)
- [ ] 3.2 `think_about(problem)` MCP tool — triggers deep reasoning without executing
- [ ] 3.3 Result stored in plan as "reasoning" field
- [ ] 3.4 Tests

## Convergence Criteria
- Plan generation from natural language goals
- Step-by-step execution tracking
- Extended thinking for complex decisions
- Two consecutive clean audit passes
