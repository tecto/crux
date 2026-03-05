# Crux Development Plan: Complete Knowledge Transfer

**Document Purpose**: This is the COMPLETE knowledge transfer from a months-long design session. It contains every design decision, research finding, and implementation detail needed for Claude Code to build remaining components with full understanding.

**Target Audience**: Claude Code (or any AI assistant building Crux components) with no prior context beyond a basic CLAUDE.md file.

**Last Updated**: 2026-03-05

---

## Project Vision and Philosophy

### What is Crux?

Crux is a self-improving AI operating system — not tied to any specific LLM or agentic tool. It wraps any LLM (Ollama local models, Anthropic API, OpenAI API) and any agentic coding tool (OpenCode, Aider, Claude Code) to maximize effectiveness.

**Core Principle**: Everything the AI does must be enforced by code, not by instructions. Prompts drift. Infrastructure doesn't.

### Design Philosophy

1. **Guardrails Are Infrastructure, Not Suggestions**: The five-gate script execution pipeline, token budgets, tool tier hierarchy, and risk classification are hard constraints enforced by plugins and custom tools. The model cannot talk itself out of them.

2. **Narration Over Silence**: Always show what you're doing and why. Bryan got frustrated when AI was doing background research with no visible output. Every action gets narrated.

3. **Mode-Driven Architecture**: A single "general-purpose" system prompt produces drift and confusion. 15 specialized modes, each optimized for a domain, with hard constraints on tool access per mode.

4. **Scripts Are First-Class Citizens**: The AI doesn't directly modify files. Everything flows through scripts in `.opencode/scripts/`. Scripts are templated, validated, tested, and can be promoted to reusable library status.

5. **Knowledge Is Organic**: The system doesn't rely on a manually-curated knowledge base. Corrections are automatically detected, patterns are clustered, knowledge entries are generated from session data, and promotion happens through automated pipelines.

6. **Everything Is Observable**: Session logging is aggressive and granular. 100% interaction history. JSONL append-only format survives truncation. Crash recovery from exact point. Auto-resume when reopening projects.

### User Context

- **Primary User**: Bryan
- **Primary Languages**: Python (locally), Elixir/Phoenix/Ash/PostgreSQL (web apps)
- **Hardware**: MacBook Pro M1 Max, 64GB RAM
- **Local Setup**: Ollama installed
- **Organization**: `trinsiklabs` GitHub organization
- **Workflow**: All edits flow as PRs from the `tecto` fork
- **Primary Model (Initial)**: Qwen3 32B via Ollama
- **Primary Tool**: OpenCode CLI

---

## Complete Design History

This section walks through every major design decision chronologically, capturing the reasoning, research, and context for each.

### 1. Model Selection: Qwen3 32B as the Foundation

**Problem**: Need a local model with strong reasoning, code capability, and acceptable latency on MacBook Pro M1 Max.

**Research**:
- Qwen3.5-32B doesn't exist. Qwen3.5 has 27B and 35B-A3B variants. The "32B" is from the older Qwen3 family.
- Qwen3.5 GGUFs are broken in Ollama (GitHub issue #14586 — context window problems and response quality degradation).
- Qwen3 32B is stable, well-tested in Ollama, and handles 32K context windows reliably.
- Alternatives considered:
  - Llama-3.1 405B: Too large, won't fit on 64GB without compromises.
  - Mistral Large: Good but slightly weaker reasoning than Qwen3 32B.
  - Deepseek Coder: Good for code but weaker on general reasoning and psychology tasks.

**Decision**: Qwen3 32B as primary model. Qwen3-Coder 30B as code-specialized alternative for build modes when needed.

**Why This Matters**: Model selection cascades through everything — context window design, sampling parameters, thinking mode availability, quantization strategy. Switching models requires re-tuning multiple systems.

### 2. Context Window Configuration: Explicit num_ctx Setting

**Problem**: Ollama defaults to 4096 token context window regardless of model capability. Qwen3 32B supports up to 128K.

**Discovery**: The default isn't a performance choice — it's a conservative safety default. Ollama documentation is sparse on this.

**Research Findings**:
- 4096 tokens: Can hold ~4 interactions + 2KB of code. Insufficient for any real work.
- 16K: ~15 interactions + 10KB code. Workable for simple tasks, tight for multi-file refactoring.
- 32K: ~30 interactions + 25KB code. Comfortable for most workflows. Fits on 64GB with room to spare.
- 64K: ~60 interactions + 50KB code. Optimal for complex refactoring, documentation work.
- 128K: Very rare to need. Takes up 60+GB if using Q8_0 quantization.

**Memory Impact** (Q8_0, the highest practical quality on 64GB):
- Base weights: ~34GB
- 4K context: 4GB inference overhead = 38GB total
- 32K context: 6GB inference overhead = 40GB total (still workable with 30GB free)
- 64K context: 10GB inference overhead = 44GB total (tight, requires app management)
- 128K context: 16GB inference overhead = 50GB total (requires closing most apps)

**Decision**: 32K as default. Configurable to 16K (faster), 64K (more breathing room), or 128K (rare, explicit choice).

**Implementation**: Must be set via `num_ctx` in Modelfile, not via default configuration.

### 3. System Prompt Architecture: Three-Layer Design to Combat Context Rot

**Problem**: As inputs grow, model performance degrades (context rot). System prompt overhead eats into the working window.

**Research on Context Rot**:
- After 30% of context is filled with prior conversation, model coherence drops measurably.
- Adding more instruction tokens to fight drift makes it worse — you've used more of the working context.
- Solution: Minimal system prompt, mode-specific directions injected at conversation start, no instruction bloat.

**Initial Consideration**: LiteLLM Router — a meta-prompt that analyzes the task and selects a micro-prompt variant. Rejected because:
- Adds latency (extra LLM call to route)
- Requires the LLM to introspect on the task (adds tokens)
- Doesn't actually save tokens if the base router prompt is complex

**Selected Design**: Three-layer architecture:

**Layer 1: Lean Core (Modelfile, ~50 tokens)**
- Baked into the model's system role
- Global behavioral rules (numbered lists, narration, directness)
- Meta-rule: "Modes are specialized. Follow the active mode prompt."
- Never changes between interactions

**Layer 2: Mode Prompts (per-mode, ~120-155 tokens)**
- Loaded only when mode is active
- Persona, domain-specific rules, tool access constraints
- Only one mode loaded at any time

**Layer 3: Optional LiteLLM Router (rejected)**
- Decided against because it adds complexity without saving tokens

**Token Math**:
- Lean Core: ~50 tokens
- Active Mode: ~120-155 tokens
- Total System Overhead: ~170-205 tokens
- 32K context: 32,000 tokens total
- Available for Work: 31,795+ tokens = **99.4% of window**
- Conclusion: System overhead is negligible.

**Why This Matters**: Lean overhead means the model has maximum working context and minimal instruction drift.

### 4. Mode Design Process: 15 Specialized Modes, Each Researched Individually

**The Process** (applied to each of 15 modes):
1. Research best practices and patterns for the domain
2. Design initial prompt based on research (always positive framing, ~120-155 tokens)
3. Present to Bryan with research explanation and draft prompt
4. Bryan reviews and adjusts based on preferences
5. Lock in and move to next mode

Each mode's decision was deliberate. No shortcuts, no generic "here are some modes you might want." Every mode was approved individually.

**The 15 Modes** (built in this order):

#### Core Coding Modes (4)

**Mode 1: build-py** (Python development)
- Python-specific idioms, frameworks (FastAPI, Django, Pytest)
- Always uses virtual environments and type hints
- Approach: Pragmatic, test-driven, focus on readability
- Tool constraints: Can write/edit files directly, can create scripts

**Mode 2: build-ex** (Elixir development)
- Elixir/Phoenix-specific patterns
- **Key Discovery**: "Ash First" principle. Official Ash Framework has LLM guidance with `usage_rules` tool. Must align with that.
- Approach: Functional paradigm first, immutability emphasis, leverage pattern matching
- Tool constraints: Can write/edit files directly, can create scripts
- Context: This was split from a generic "build" mode because Elixir idioms are too different from Python

**Mode 3: build-docker** (Containerization)
- Docker Compose, infrastructure-as-code preference
- Context: Split from generic sysadmin because Docker specialists need different mental models than general sysadmins
- Tool constraints: Can modify configs, write Docker files, cannot directly deploy to production

**Mode 4: debug** (Troubleshooting and investigation)
- Hypothesis-driven debugging, minimal reproduction, root cause analysis
- Uses thinking mode (complex reasoning required)
- Tool constraints: Read-heavy, can create diagnostic scripts
- Approach: Socratic method — help user discover the issue, not just fix symptoms

#### Architecture and Planning (3)

**Mode 5: plan** (Software architecture)
- System design, refactoring strategy, API design
- Token-constrained (tight budget — thinking is expensive, time is limited in planning sessions)
- Uses thinking mode
- Tool constraints: Read-only on code, cannot execute scripts, can create diagrams/docs
- Approach: Always ask clarifying questions before proposing architecture

**Mode 6: infra-architect** (Deployment, CI/CD, migration planning)
- Infrastructure-as-code, cloud strategy, cost tradeoffs
- Context: Split from generic plan mode because deployment decisions are fundamentally different from software architecture
- Uses thinking mode
- Tool constraints: Can review configs, cannot modify production systems
- Approach: Always present multiple options with cost/risk analysis

**Mode 7: strategist** (High-level decision-making, roadmap planning)
- Business context, prioritization, stakeholder impact
- Uses thinking mode
- Tool constraints: Cannot execute any changes, analysis only
- Approach: Always show the tradeoff matrix

#### Specialized Technical (3)

**Mode 8: docker** (Container operations and troubleshooting)
- Docker-specific debugging, compose configuration, image optimization
- Approach: Container-first thinking, immutability of images
- Tool constraints: Can write Docker files, cannot deploy to production
- Context: Separated from sysadmin because Docker has unique affordances and failure modes

**Mode 9: mac** (macOS-specific operations)
- Homebrew paths, launchd, BSD vs GNU tool differences, System Integrity Protection
- Critical Details:
  - `/usr/local/bin` vs `/opt/homebrew/bin` (M1 Mac vs Intel)
  - `sed -i ''` on macOS vs `sed -i` on Linux
  - `ps aux` formatting differences
  - LaunchAgent vs LaunchDaemon context
- Tool constraints: Can modify system configs within user scope, cannot modify system files
- Context: Split from generic sysadmin because macOS-specific patterns are critical

**Mode 10: review** (Code review and quality assessment)
- Critical feedback, maintainability analysis, testing gaps
- Uses thinking mode
- Tool constraints: Read-only (cannot modify code)
- Approach: Constructive but direct, focus on impact not style
- Prompt Detail: "Your job is to find problems and explain why they matter. Be specific. Don't cushion the feedback."

#### Creative and Communication (2)

**Mode 11: writer** (Technical writing, documentation, communication)
- Clarity, audience awareness, example-driven
- **Anti-patterns researched** (EQ-bench Slop Score for detecting AI writing):
  - Banned words: "delve," "tapestry," "landscape," "realm," "furthermore," "moreover"
  - Banned patterns: "not just X, but Y" construction (AI-marker for false binary)
  - Banned hedging: "it's worth noting," "interestingly," "arguably"
- Tone: Professional but warm. Clear over clever.
- Tool constraints: Can read code and docs, write documentation files
- Approach: Write for the reader, not for the archive

**Mode 12: analyst** (Data analysis, pattern recognition, research)
- Hypothesis-driven, evidence-based reasoning
- Tool constraints: Can read data, create summaries, write findings
- Approach: Always distinguish correlation from causation, always state confidence level

#### Psychological and Domain Expertise (3)

**Mode 13: psych** (Psychological support and emotional processing)
- **Deep Integration**: Researched frameworks deliberately chosen for effectiveness
  - **ACT (Acceptance and Commitment Therapy)**: Bryan's explicit choice — "ACT is CBT improved"
  - **Attachment Theory v4** (Thais Gibson research):
    - Four styles: secure, anxious, dismissive-avoidant, fearful-avoidant
    - Core wounds and subconscious beliefs underlying each
    - Earned secure attachment pathway
  - **Jungian Shadow Work**:
    - Projections as mirrors
    - Triggers as invitations to integration
  - **Somatic Awareness**:
    - Where emotions live in the body
    - The body stores what the mind avoids
    - Interoceptive awareness practices
- Approach: Socratic-first, gentle but don't cushion truth. If self-harm mentioned, encourage professional help immediately.
- Tool constraints: Read-only, cannot take actions
- Critical Note: This is a specialized counseling mode, not a substitute for therapy

**Mode 14: legal** (Legal reasoning, contract analysis, compliance)
- Precise language, precedent awareness, risk identification
- Uses thinking mode
- Tool constraints: Read-only, can write summaries
- Approach: Always flag ambiguities, always recommend professional legal review
- Limitation: AI legal analysis is not legal advice

**Mode 15: explain** (Teaching and clarification)
- Breaking down complexity, finding analogies, scaffolding understanding
- Approach: Meet learner where they are, check comprehension iteratively
- Tool constraints: Can read code and docs, write explanations and examples
- No thinking mode (explanation is best with lower temperature, more direct language)

**Why Each Mode Exists**: Every mode represents a genuinely distinct context — different tools, different constraints, different reasoning styles, different success metrics. A single "general" mode would produce inconsistent, often contradictory behavior.

### 5. Psych Mode Deep Dive: Integration of Therapeutic Frameworks

**Why This Matters**: Psych mode is the most complex because it integrates multiple therapeutic frameworks that must work together without contradiction.

**Chosen Framework: ACT (Acceptance and Commitment Therapy)**

Bryan explicitly requested ACT over CBT with reasoning: "ACT is CBT improved." The distinction matters:
- **CBT** focuses on changing thought content (thoughts → emotions → behavior)
- **ACT** focuses on changing relationship to thoughts (acceptance of thoughts + values-aligned action)
- For someone with intrusive thoughts or rumination, ACT is more effective because it doesn't require "winning" against your own mind

**Integrated Attachment Theory v4** (Thais Gibson's framework)

Four attachment styles with core wounds and subconscious beliefs:

| Style | Core Wound | Subconscious Belief | Earned Secure Path |
|-------|-----------|-------------------|-------------------|
| **Secure** | None (or processed) | "I am worthy. Others are trustworthy." | Reference frame for others |
| **Anxious** | Unpredictable caregiver | "I am unworthy. Others will leave." | Develop independent worth, practice tolerating alone time |
| **Dismissive-Avoidant** | Intrusive/enmeshed caregiver | "I am independent. Others are burdensome." | Practice vulnerability, tolerate need for connection |
| **Fearful-Avoidant** | Abusive/chaotic caregiver | "I am unworthy AND others are dangerous." | Hardest path — requires both anxiety and avoidant work |

**Application**: Psych mode asks gentle questions to help user identify their style, understand the wound, and notice when they're operating from the wound vs. the secure adult.

**Integrated Jungian Shadow Work**

- **Projections**: What we dislike in others often reflects what we dislike (or hide) in ourselves
- **Triggers as Invitations**: Strong emotional reactions signal integration work
- **Shadow Acceptance**: The goal isn't to become "all light" but to integrate the shadow parts consciously

**Application**: "That person's behavior really bothered you. What about it? Is there something in you that you recognize there?"

**Somatic Awareness Component**

- **Body Stores What Mind Avoids**: Tension, numbness, restlessness often indicate suppressed emotion
- **Interoception**: Teaching the skill of noticing what's happening in the body
- **Anchor to Nervous System**: ACT + somatic work = better regulation

**Application**: "Notice where you feel that in your body. What's the quality of the sensation? Not to fix it, just to know it's there."

**Prompt Approach**:
- Socratic: Ask more than tell
- Gentle: Not coddling, but not harsh either
- Direct: Truth without softening
- Safety-focused: If self-harm mentioned, immediately suggest professional help ("This sounds like something to bring to a therapist or counselor.")

### 6. Build Mode Split: Python vs. Elixir Are Fundamentally Different

**Problem**: Initial design had one "build" mode. Quickly became obvious it was insufficient.

**Key Discovery**: Different language paradigms require different reasoning:
- **Python**: Imperative, mutable, OOP-friendly, library ecosystem massive, test with pytest
- **Elixir**: Functional, immutable, pattern-matching first, concurrency with processes, test with ExUnit

**Critical Finding**: Ash Framework (official Elixir web framework) publishes LLM guidance with a `usage_rules` tool. This MUST be integrated into build-ex mode. Cannot ignore official framework guidance.

**Decision**: Split into build-py and build-ex.

**build-py Specifics**:
- Always propose virtual environments (`venv` or `poetry`)
- Type hints by default (PEP 484)
- Testing: pytest with fixtures
- Approach: Pragmatic, test-driven, focus on readability

**build-ex Specifics**:
- "Ash First" principle — use Ash for web apps, not manual Ecto
- Pattern matching everywhere
- Immutability mindset
- Approach: Functional paradigm first, leverage Elixir's strengths
- Tool Access: Must include Ash Framework LLM guidance when available

### 7. Sysadmin Split: Mac vs. Docker Are Separate Domains

**Problem**: One "sysadmin" mode tried to handle both macOS operations and container operations. Conflicting mental models.

**Key Differences**:

**Mac (macOS system operations)**:
- Uses Homebrew for package management
- Paths differ by architecture (M1 `/opt/homebrew/bin` vs Intel `/usr/local/bin`)
- System Integrity Protection (SIP) constraints
- `sed -i ''` (BSD sed, not GNU)
- LaunchAgent/LaunchDaemon for services
- User must be aware of file permissions and privacy settings

**Docker (container operations)**:
- Ephemeral, immutable images
- No package manager needed (everything in Dockerfile)
- Multi-stage builds for optimization
- Docker Compose for orchestration
- No SIP, no user auth, different mental model entirely

**Decision**: Split into mac and docker as separate modes.

### 8. Plan Split: Software Architecture vs. Infrastructure Deployment

**Problem**: One "plan" mode mixed two fundamentally different types of planning.

**Software Architecture Planning**:
- API design, module organization, data flow
- Thinking about code structure and interfaces
- Long-term maintainability

**Infrastructure Deployment Planning**:
- Cloud provider selection, cost optimization, CI/CD strategy
- Migration planning, disaster recovery
- Hardware constraints and scaling strategy

**Key Difference**: Different expertise, different constraints, different metrics. Architecture planning focuses on code quality. Infrastructure planning focuses on operations and cost.

**Decision**: Split into plan (software architecture) and infra-architect (deployment, CI/CD, migration).

**tool constraints differ**:
- plan: Read-only on code, analysis only
- infra-architect: Can review configs, cannot modify production systems

### 9. Writer Mode Anti-Patterns: Research-Backed AI Writing Detection

**Problem**: Need to identify and eliminate LLM-specific writing patterns that degrade quality.

**Research Source**: EQ-bench Slop Score — metrics for detecting AI writing

**Banned Words/Phrases** (strongly associated with AI):
- "delve" (especially "delve into")
- "tapestry"
- "landscape"
- "realm"
- "furthermore" (use "also" or "additionally")
- "moreover"
- "in this day and age"
- "needless to say"

**Banned Patterns**:
- "not just X, but Y" — false binary often used by AI to sound sophisticated
- Excessive hedging: "it's worth noting," "interestingly," "arguably," "one could say"
- Oxford comma overuse in casual writing
- Overly complex sentences that could be simple

**Tone Guidelines**:
- Professional but warm
- Clear over clever
- Short sentences trump long ones
- Jargon only when necessary
- Examples before abstractions

### 10. Scripts-First Architecture: Everything Through Templates

**The Core Principle** (from Bryan): The LLM should do EVERYTHING through scripts, never directly modify files.

**Why This Matters**:
- Auditability: Every change is logged
- Reversibility: Scripts can be reviewed before running
- Testing: Scripts can have dry-run mode
- Promotion: Good scripts become library functions

**Script Template** (mandatory structure):

```bash
#!/bin/bash

####################
# Script Name
# Risk Level: [low|medium|high]
# Created: [timestamp]
# Status: [session|library]
# Description: [what this does and why]
####################

set -euo pipefail

# Configuration
DRY_RUN="${DRY_RUN:-false}"

# Main logic
main() {
  # Implementation
  true
}

# Only run if not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
```

**Key Features**:
- Header section with risk classification, status, creation date
- `set -euo pipefail` for safety
- DRY_RUN support (at least for medium/high risk)
- Explicit main() function
- Can be sourced as a library

**Risk Classification**:
- **Low**: Read-only operations, no tests required
- **Medium**: File modifications, config changes, DRY_RUN required, runs without approval
- **High**: Deployment, database changes, deletions, production changes, TDD required, explicit approval required

**Workflow**:
1. LLM generates script in `.opencode/scripts/session/`
2. Script runs through validation pipeline (section 11)
3. If medium risk: runs after DRY_RUN succeeds
4. If high risk: human must approve, then runs after DRY_RUN
5. If script is good: `/promote` moves to `.opencode/scripts/lib/` for reuse
6. Old scripts auto-archive to `.opencode/scripts/archive/`

**Why This Architecture Matters**: Scripts are the enforcement boundary. The system can validate scripts before execution. Direct file modifications cannot be validated.

### 11. Risk Classification and Script Validation

**Risk Levels** (and what they mean):

**Low Risk**:
- Read-only operations (grep, find, cat, stat)
- Non-destructive queries
- No tests required
- Runs immediately without approval
- Examples: listing files, analyzing code, generating reports

**Medium Risk**:
- File modifications (create, edit, delete)
- Configuration changes
- Temporary data changes
- DRY_RUN required (must support `DRY_RUN=true` to show what would happen)
- Can run without explicit human approval (but DRY_RUN output is shown)
- Examples: refactoring, adding files, updating configs

**High Risk**:
- Production deployments
- Database schema changes
- Destructive operations (rm, delete, truncate)
- Data loss possible if wrong
- TDD required (tests written first, then script)
- Explicit human approval required before execution
- Examples: deploy to production, drop database, delete user data

**Pre-Flight Validation** (runs before any execution):

Deterministic shell function checks:
1. Risk classification matches behavior (if script says "low" but contains `rm`, reject)
2. DRY_RUN support exists for medium+ risk (script must check `$DRY_RUN` and handle it)
3. Template compliance (header present, set -euo pipefail, main function)
4. Path containment (writes only within project dir or `.opencode/scripts/`)
5. Multi-file writes require transaction scripts (HARD REQUIREMENT)

**Transaction Script Pattern** (for coordinated multi-file changes):

```bash
# Bad: separate scripts for each file
./create_module.sh
./update_domain.sh
./write_migration.sh

# Good: transaction script coordinates them
./add_resource.sh user_profile
  # runs: create_user_profile_module
  # then: update_user_domain
  # then: write_migration
  # then: update_router
  # with rollback on any failure
```

### 12. Session Logging: Aggressively Granular, JSONL Format

**Requirement** (from Bryan): "Aggressively granular logging. 100% session history. Crash recovery from exact point. Auto-resume when reopening project."

**Implementation Format**: JSONL (JSON Lines) — each line is a separate JSON object

**Why JSONL**:
- Append-only survives truncation (corrupt last line, everything else intact)
- Queryable (grep JSON, no need to parse entire file)
- Streaming-friendly (new sessions read from exact position)
- Machine-readable (plugins can query structure)

**What Gets Logged** (every interaction):

```json
{
  "timestamp": "2026-03-05T14:32:15Z",
  "type": "user_message",
  "content": "help me debug this error",
  "mode": "debug",
  "tokens_used": 1240
}

{
  "timestamp": "2026-03-05T14:32:18Z",
  "type": "model_response",
  "content": "Let me first understand the error...",
  "mode": "debug",
  "tokens_used": 892,
  "thinking_active": true
}

{
  "timestamp": "2026-03-05T14:32:22Z",
  "type": "tool_call",
  "tool": "grep",
  "args": {"pattern": "error", "path": "app.py"},
  "status": "success",
  "result_tokens": 450
}

{
  "timestamp": "2026-03-05T14:32:25Z",
  "type": "correction",
  "detected_by": "correction-detector",
  "pattern": "model_missed_requirement",
  "evidence": "user said 'no' to proposed solution"
}

{
  "timestamp": "2026-03-05T14:35:00Z",
  "type": "session_checkpoint",
  "messages_since_last": 5,
  "total_tokens": 12450,
  "mode": "debug"
}
```

**Checkpoint Strategy** (every 5 interactions):
- Store compressed session state
- Last checkpoint is recovery point if session crashes
- Checkpoint includes: mode, active handoff context, recent knowledge lookups, script status

**Crash Recovery**:
- Session restarts from last checkpoint
- Plugin reads checkpoint, loads context
- User sees: "Recovered from checkpoint at 14:35. Continue with: [summarized context]"
- Auto-resume mode is automatic (no need to ask)

**Why This Matters**: Every crash is survivable. Every session is auditable. Learning from corrections requires this granularity.

### 13. Global Behavioral Rules: Enforced in Modelfile

**These rules are GLOBAL** across all sessions and modes (overridden only by mode-specific rules):

**Rule 1: Always Use Numbered Lists**
- When presenting options, questions, or alternatives, use numbered lists, never bullets
- Numbered lists encourage sequential thinking
- Makes it easier for user to reference: "I prefer option 2"
- Applies everywhere (questions, options, steps, lists of findings)

**Rule 2: Sequential Presentation**
- When Bryan says "let's talk through" or "discuss one at a time," present each item individually
- Wait for confirmation on each item before moving to next
- Don't dump all options at once if sequential processing requested
- Confirmation threshold: explicit "yes," "next," "continue," or similar

**Rule 3: Narrate Everything**
- Always narrate what you're doing and why
- Before taking action, briefly state your plan
- During multi-step work, provide status updates
- Never work silently (this was explicit frustration point from Bryan)
- Examples of good narration:
  - "I'm going to search the codebase for all references to this function."
  - "Found 5 references. Now checking which are in production code vs. tests."
  - "Ready to refactor. First step will be creating the new module..."

**Rule 4: Be Direct, Match Response Length to Complexity**
- Simple questions deserve short answers
- Complex topics deserve thorough exploration
- Avoid padding short answers with unnecessary elaboration
- Avoid oversimplifying complex topics to be brief
- Match tone to urgency: emergency debugging is different from architectural discussion

**Why These Rules Are Global**: They shape interaction quality across all contexts. No mode should violate them (though modes can add to them).

---

## The 17 Recommendations: Evidence-Based System Optimization

After the initial 15-mode architecture was designed and locked in, a deep analysis of LLM performance, error patterns, and token efficiency produced 17 specific recommendations to maximize system effectiveness. All 17 were approved and are baked into the rebuild.

### Recommendation 1: Mode-Specific Sampling Parameters

**Problem**: Ollama defaults (temp 0.7, top_p 0.9, top_k 40) are one-size-fits-all. Qwen team published specific recommendations, which are different.

**Research**:
- Qwen team official guidance distinguishes between thinking and non-thinking modes
- Thinking mode (complex reasoning): temp 0.6, top_p 0.95, top_k 20
  - Lower temp → more focused, less random exploration
  - Higher top_p → more diverse but still coherent completions
  - Lower top_k → focus on more likely tokens
- Non-thinking mode (generation): temp 0.7, top_p 0.8, top_k 20
  - Slightly higher diversity than thinking
  - Lower top_p than thinking (more focused)

**Important Warning** (from Qwen team):
- Greedy decoding (temp 0) causes "performance degradation and endless repetitions"
- Never use temp 0 — it breaks Qwen3

**Solution**: Two Modelfile variants:
- `crux-think`: Applied to thinking modes (debug, plan, infra-architect, review, legal, strategist, psych)
- `crux-chat`: Applied to non-thinking modes (build-py, build-ex, writer, analyst, mac, docker, explain)

**Implementation Note**: These parameters must be in the Modelfile, not in OpenCode config (the plugin system can override per-mode, but defaults should be correct in model definition).

### Recommendation 2: Think/No-Think Routing via LLM Prefixes

**Problem**: Qwen3 32B has a built-in thinking mode (accessible via `/think` and `/no_think` prefixes), but it's not being used strategically.

**Research Finding**: Think mode adds latency but produces measurably better quality on reasoning tasks. Quality improvement justifies latency cost for appropriate tasks.

**Solution**: think-router plugin (uses `chat.message` hook) to automatically prepend directive based on active mode.

**Think Modes** (prepend `/think`):
- debug (complex root cause analysis)
- plan (architectural decision making)
- infra-architect (infrastructure planning with multiple tradeoffs)
- review (code review requires reasoning about impact)
- legal (legal analysis requires careful reasoning)
- strategist (high-level decisions)
- psych (psychological reasoning)

**No-Think Modes** (prepend `/no_think`):
- build-py (code generation, lower latency preferred)
- build-ex (code generation, lower latency preferred)
- writer (creative writing, think mode makes prose stiff)
- analyst (analysis, but not reasoning-intensive)
- mac (system operations, straightforward)
- docker (system operations, straightforward)
- explain (teaching, clarity preferred over deep reasoning)

**Neutral**:
- ai-infra (user controls thinking per interaction)

**Why This Matters**: Automatic routing means thinking is used when it helps, not wasted when it doesn't. Removes decision burden from user.

### Recommendation 3: Compaction Model — Qwen3 8B as Lightweight Summarizer

**Problem**: OpenCode auto-compacts at 95% of context window capacity. Without a configured smallModel, it either uses the main 32B (slow, wasteful, defeats the purpose) or doesn't compact (session dies when context fills).

**Solution**: Pull `qwen3:8b` (8 billion parameters) as the compaction model.

**Why 8B**:
- Fast (inference ~5x faster than 32B)
- Capable enough to understand code and session context
- Small enough to run simultaneously with 32B (total ~38GB, leaving room for inference overhead)
- Same tokenizer as 32B (no translation layer needed)

**Enhanced Compaction** (via `experimental.session.compacting` hook):
- Don't just summarize the conversation generically
- Inject domain-specific instructions: "Preserve script names exactly, preserve mode context, preserve recent project state, preserve knowledge lookups"
- Result: compacted session retains operational details, not just semantic gist

**Why This Matters**: Sessions can run indefinitely without degradation. No need to manually restart or clear context.

### Recommendation 4: Project Context Injection via PROJECT.md

**Problem**: Model starts every session blind to the codebase. Must rediscover: directory structure, tech stack, key files, naming conventions, recent changes.

**Solution**: `/init-project` command generates PROJECT.md with:

```markdown
# Project: example-app

## Tech Stack
- Language: Python
- Framework: FastAPI
- Database: PostgreSQL
- Testing: pytest

## Directory Structure
```
example-app/
├── app/
│   ├── main.py
│   ├── models/
│   ├── schemas/
│   └── routes/
├── tests/
├── migrations/
└── requirements.txt
```

## Key Files
- app/main.py — entry point, middleware setup
- app/models/ — SQLAlchemy models
- tests/ — test suite

## Naming Conventions
- Models: PascalCase (User, BlogPost)
- Routes: kebab-case (/api/users, /api/blog-posts)
- Functions: snake_case
- Constants: UPPER_SNAKE_CASE

## Recent Changes (tracked per session)
- Added User model
- Refactored auth middleware
- Wrote comprehensive test suite for routes
```

**Combined with Session Logging**: Session wind-down updates PROJECT.md with file-touch patterns so the next session knows which files are hot.

**Key Detail**: All scripted. The AI reads PROJECT.md, never writes it. Only `/init-project` and automation scripts can update it.

**Why This Matters**: Model has codebase context on session startup. No rediscovery phase.

### Recommendation 5: Feedback Loop — Automatic Correction Extraction

**Problem**: No mechanism to learn from corrections between sessions. If user corrects the same misunderstanding 5 times across 5 projects, system never learns.

**Solution**: Two-part system:

**Part 1: Real-Time Correction Detection** (correction-detector plugin)
- Uses `message.updated` hook to watch every message pair (user + model response)
- Detects correction patterns:
  - **Negation language**: "no," "wrong," "I said," "don't," "not what I asked"
  - **Retry pattern**: Same tool called again with different parameters
  - **Self-correction language**: "sorry," "let me fix," "I misunderstood"
- Writes structured reflections to JSONL

```json
{
  "timestamp": "2026-03-05T14:32:30Z",
  "type": "correction",
  "detected_pattern": "negation_language",
  "evidence": "user said 'no, use docker-compose instead'",
  "context": "model proposed kubernetes",
  "mode": "docker"
}
```

**Part 2: Batch Pattern Extraction** (extract-corrections.sh)
- Runs at session end or manually via `/analyze-corrections`
- Scans JSONL for correction patterns
- Clusters by similarity: 3 corrections about "missing environment variables" cluster together
- Generates knowledge entry candidate

```markdown
## Knowledge Entry: Environment Variables in Docker Compose

**Problem**: Model frequently forgets to set environment variables in docker-compose.yml

**Pattern**: User corrects by saying "add the env vars from .env file"

**Solution**: When docker-compose is being generated, always ask: "What environment variables need to be set?" and include an env_file reference.

**Confidence**: 3 sessions, 5 instances
```

**Why This Matters**: System learns from patterns without manual curation. Knowledge comes from real session data.

### Recommendation 6: MCP Servers + Five-Tier Tool Hierarchy

**Problem**: Tool reliability varies wildly. Raw bash can fail silently, succeed incorrectly, or have subtle platform differences. No strategy for tool selection.

**Solution**: Five-Tier Tool Hierarchy (enforced by tool-enforcer plugin):

**Tier 0: LSP (Language Server Protocol)**
- Deterministic code intelligence
- Jump to definition, find references, type information
- Configured: pyright for Python, elixir-ls for Elixir
- Lazy-loaded (no cost until used)
- Used by: debug, review, plan modes
- Why: Far more accurate than grep for understanding code structure

**Tier 1: Custom Tools** (built in JavaScript within OpenCode)
- Schema-validated inputs
- Atomic operations
- Deterministic, testable
- Examples: `run_script`, `lookup_knowledge`, `suggest_handoff`
- Used for: Core system operations that must be reliable

**Tier 2: MCP Servers** (open standard, external processes)
- Protocol-enforced external access
- Examples: GitHub MCP, filesystem MCP, browser MCP
- Reliability: High (protocol enforced)
- Used for: Cloud services, standard operations

**Tier 3: Library Scripts** (tested, versioned in `.opencode/scripts/lib/`)
- Pre-tested, versioned
- Used for: Common operations that have been proven safe
- Examples: `backup_database.sh`, `run_tests.sh`

**Tier 4: New Scripts** (templated, audited via five-gate pipeline)
- Generated by model, validated before use
- Used for: One-off operations, experimental automation
- Auditability: High (every script logged)

**Tier 5: Raw Bash** (minimal, logged, read-only only)
- Fallback for operations that don't fit tiers 0-4
- CONSTRAINT: Read-only only (cannot modify files)
- Examples: `ls`, `grep`, `find` (information gathering only)
- Why: Bash has platform differences, can fail silently

**Tool Enforcer Plugin** (uses `tool.execute.before` hook):
- Intercepts tool calls
- Checks which tier the tool belongs to
- **Hard constraints**: Read-only modes physically cannot call tier 4/5 (violation = rejected)
- Analytics: Track tier usage per mode
- Self-tightening: High tier 5 usage in a mode → flag for custom tool creation

**Why This Matters**: Reliability increases as tier increases. The system routes to highest reliable tier.

### Recommendation 7: LSP Integration for Code Intelligence

**Problem**: Searching code with grep is slow and error-prone. Model can't reliably distinguish between imports, comments, and actual code using text patterns alone.

**Solution**: Configure LSP servers for deterministic code intelligence.

**Setup**:
- **Python**: pyright (fast, accurate, understands Python's dynamic features well enough)
- **Elixir**: elixir-ls (standard, included with most Elixir installations)
- **Lazy-loaded**: No resource cost until first usage

**Capabilities**:
- Jump to definition (find where a function/class is defined)
- Find references (find all uses of a function)
- Type information (understand what type a variable is)
- Hover documentation (see docstrings without opening files)

**Usage Pattern** (in debug mode):
- User: "The error is in the transform_data function"
- Model: Use LSP to jump to definition, understand parameters and return type
- Model: Check all call sites with find references
- Model: Understand the context immediately, no need to search

**Why This Matters**: LSP answers structural questions quickly and accurately. Much better than text search.

### Recommendation 8: Token Budget Enforcement via Plugin

**Problem**: No guardrails on token spend per interaction. A runaway loop (grep → read → process → grep again) can burn the entire context window in one interaction.

**Solution**: token-budget plugin using `tool.execute.before` hook.

**Budget Tiers**:

**Tight Budget Modes** (warning at 70% of interaction budget, enforced ceiling at 90%):
- plan (expensive thinking mode, time is limited)
- review (expensive thinking mode)
- strategist (expensive thinking mode)
- legal (expensive thinking mode)
- psych (expensive thinking mode, limited by need for depth)

Budget: 4000 tokens per interaction

**Generous Budget Modes** (warning at 80%, ceiling at 95%):
- build-py (code generation can need lots of context)
- build-ex (code generation can need lots of context)
- debug (deep investigation needed)
- docker (infrastructure troubleshooting)

Budget: 8000 tokens per interaction

**Default Modes** (warning at 75%):
- writer, analyst, explain, mac, ai-infra

Budget: 6000 tokens per interaction

**Tool Output Token Limiting** (automatic):
- grep results capped at 1000 tokens (show first 1000, indicate truncation)
- file reads capped at 2000 tokens (show beginning and end, indicate middle truncation)
- output summaries still provided ("Found 50 matches, showing first 15")

**Implementation Detail**: Budget counter increments with every tool call. Display:
- "Token budget: 2340 / 4000 remaining" at every response
- When approaching threshold: "Approaching token budget. Recommend switching modes or starting new session."

**Read-Only Hard Constraint** (via tool-enforcer):
- plan, review, explain modes physically cannot call write/edit tools
- Violation = rejected before execution
- Not a prompt constraint, a code constraint

**Why This Matters**: Long interactions remain coherent. Runaway loops are prevented.

### Recommendation 9: Hardware-Aware Quantization Strategy

**Problem**: On 64GB RAM, quantization choice is non-obvious. Q4_K_M (~20GB) wastes quality headroom. Q8_0 (~34GB) fits with 30GB free but leaves no margin. No guidance on what to use.

**Solution**: Setup script calculates optimal quantization based on available memory.

**Quantization Options**:

| Quant | Size | Quality Loss | Available RAM Needed | When to Use |
|-------|------|--------------|----------------------|-------------|
| Q2_K | ~8GB | 15-20% | ~20GB (with inference) | Absolute fallback only |
| Q4_K_M | ~20GB | 3-8% | ~28GB | Tight on space, acceptable quality |
| Q5_K_M | ~25GB | 1-2% | ~35GB | Better quality, still fits |
| Q8_0 | ~34GB | <1% | ~42GB (tight) | Best quality if memory available |
| FP16 | ~68GB | none | 80GB+ | Won't fit on 64GB |

**Setup Script Logic**:

```
Available RAM: 30GB free
Optimal: Q8_0 needs 42GB total (inference) = not available
Next Option: Q5_K_M needs 35GB total = not available
Falls to: Q4_K_M needs 28GB total = FITS
Recommendation: Q4_K_M with 2GB margin

Or suggest: "Free up memory for better quality"
Or suggest: "Accept quality loss, use Q4_K_M"
```

**Bryan's Requirements**:
- Don't just recommend a quant, recommend the ideal
- Show what's consuming memory if optimal doesn't fit
- Let user decide: close apps for best quality, or proceed with fallback
- Never auto-decide (user makes the call on quality/memory tradeoff)

**Post-Setup Model Selection**:
- Primary model at optimal quant
- Fallback model at lower quant (for if memory fills)
- Explicit switching available via `/models`

**Why This Matters**: Model quality is the single highest impact on system performance. Running the best practical quant is worth optimizing for.

### Recommendation 10: Multi-Model Availability — Don't Pick One, Keep Options

**Problem**: Current design settles on one model at setup time. New models emerge, use cases evolve, sometimes you need a different tool.

**Solution**: Pull multiple model variants, register them, switch between them flexibly.

**Models to Maintain**:

1. **Primary Production Model**: Qwen3 32B Q8_0 (or highest quant that fits)
   - Assigned to: all modes by default
   - Thinking/no-think routing applies

2. **Lightweight Fallback**: Qwen3 32B Q4_K_M
   - Assigned to: none (on-demand)
   - Use when: memory pressure, speed needed, quality acceptable
   - Switch to via: `/models` → select Q4_K_M variant

3. **Compaction Model**: Qwen3 8B
   - Assigned to: internal compaction only
   - Not available for manual use
   - Runs alongside 32B

4. **Code Specialist**: Qwen3-Coder 30B (optional, if fits)
   - Assigned to: none (on-demand assignment)
   - Thinking mode, Q4_K_M quant
   - Use when: pure code work, specialty reasoning
   - Switch to via: `/models` → assign to build-py and build-ex

5. **Vision Exploration**: QVQ-72B-Preview (optional, Q4_K_M, ~42-45GB)
   - Assigned to: none
   - Exploration tier — needs apps closed when loaded
   - Use case: debugging UI layouts, visual analysis
   - Future: if usage patterns emerge, propose creating visual mode

**Model Registry** (at `~/.config/opencode/models/registry.json`):

```json
{
  "primary": {
    "name": "qwen3:32b",
    "quant": "Q8_0",
    "size_gb": 34,
    "assigned_modes": "all",
    "performance": {
      "reasoning": 9.2,
      "coding": 8.9,
      "speed": 7.5
    }
  },
  "fallback": {
    "name": "qwen3:32b-q4",
    "quant": "Q4_K_M",
    "size_gb": 20,
    "assigned_modes": "none",
    "performance": {
      "reasoning": 8.8,
      "coding": 8.5,
      "speed": 9.1
    }
  },
  "compaction": {
    "name": "qwen3:8b",
    "quant": "Q8_0",
    "size_gb": 9,
    "assigned_modes": "internal",
    "performance": {
      "reasoning": 7.2,
      "coding": 7.0,
      "speed": 9.5
    }
  }
}
```

**Key Detail**: Think/no-think routing is automatic per mode, but model switching is user-directed (cost of being wrong is too high to automate).

**Why This Matters**: Flexibility to match tool to task. Research new models without breaking production. Graceful fallback when needed.

### Recommendation 11: Five-Gate Script Execution Pipeline

**Problem**: Scripts are powerful but dangerous. Need a validation and safety architecture that prevents accidents without being annoying.

**Solution**: Five-gate pipeline (implemented in `run_script` custom tool):

```
Script Generation by Model
    ↓
GATE 1: Pre-Flight Validation (deterministic checks)
    ↓
GATE 2: 8B Adversarial Audit (different model, red-team)
    ↓
GATE 3: 32B Second-Opinion Audit (high-risk only)
    ↓
GATE 4: Human Approval (high-risk only)
    ↓
GATE 5: DRY_RUN (for medium+ risk)
    ↓
Execution
```

**Key Detail**: All gates run inside the `run_script` tool. The main model calls `run_script`, and `run_script` internally handles all gates. Main model never sees audit logic, can't reason about it, can't talk itself out of it. **Hard infrastructure boundary.**

#### Gate 1: Pre-Flight Validation

Deterministic shell function (always runs):

```bash
preflight_check() {
  local script="$1"

  # Check 1: Risk classification matches behavior
  risk=$(grep "Risk Level:" "$script" | cut -d: -f2 | xargs)

  if [[ "$risk" == "low" ]] && grep -q "rm\|delete\|drop" "$script"; then
    echo "ERROR: Script classified as 'low' but contains destructive operations"
    return 1
  fi

  # Check 2: DRY_RUN support for medium+ risk
  if [[ "$risk" == "medium" || "$risk" == "high" ]]; then
    if ! grep -q "DRY_RUN" "$script"; then
      echo "ERROR: Medium/high risk script must support DRY_RUN"
      return 1
    fi
  fi

  # Check 3: Template compliance
  if ! grep -q "set -euo pipefail" "$script"; then
    echo "ERROR: Missing 'set -euo pipefail' safety clause"
    return 1
  fi

  # Check 4: Path containment (no writes outside project)
  if grep -q "> /" "$script" || grep -q ">> /" "$script"; then
    echo "ERROR: Writes to root filesystem detected"
    return 1
  fi

  # Check 5: Multi-file writes require transaction pattern
  file_write_count=$(grep -c "^>" "$script" || true)
  if [[ $file_write_count -gt 1 ]] && ! grep -q "transaction" "$script"; then
    echo "ERROR: Multi-file script must be transaction pattern"
    return 1
  fi

  return 0
}
```

**Exit on Failure**: If pre-flight fails, script never runs. Model gets error and must fix the script.

#### Gate 2: 8B Adversarial Audit

Runs using the 8B model (different from 32B author, prevents self-enhancement bias):

```
Prompt (to 8B model):
---
You are a security auditor. Your job is to find every way this script could cause:
- Data loss
- Data corruption
- Unintended side effects
- Scope creep beyond its stated purpose

Assume the script is WRONG until proven safe.

List every concern you find. If you find NONE, respond with exactly: PASS

Script:
[script content]
---
```

**Key Instructions for 8B**:
- Be paranoid
- Find every possible failure mode
- Categorize: data loss vs. corruption vs. side effects vs. scope creep
- If auditor finds concerns, main model must review and address them

**Output** (auditor's response):
- If "PASS": proceed to gate 3
- If concerns found: report to main model, which must revise script, then re-run

#### Gate 3: 32B Second-Opinion Audit (High-Risk Only)

Only for scripts classified as "high" risk. Uses different persona:

```
Prompt (to 32B model in "review" mode):
---
A security audit was performed on this script. The auditor passed it (PASS).

However, as the second opinion for a HIGH-RISK operation, perform your own review.

Do NOT repeat the first audit. Look for:
1. Missing error handling (what if a command fails mid-way?)
2. Race conditions (what if two instances run simultaneously?)
3. Recovery strategy (how would we undo this if needed?)
4. Monitoring (does it report success/failure clearly?)

If you find concerns, list them. Otherwise: PASS

Script:
[script content]
---
```

**Output**:
- If "PASS": proceed to gate 4
- If concerns found: report to main model for revision

#### Gate 4: Human Approval (High-Risk Only)

For high-risk scripts, show to user:

```
High-Risk Script Ready for Approval

Name: deploy_to_production.sh
Risk: HIGH (production deployment)

Pre-flight: PASS
8B Audit: PASS
32B Audit: PASS

Description:
[script description]

Preview (first 20 lines):
[script preview]

Approve? (yes/no)
```

User must explicitly type "yes" to proceed.

#### Gate 5: DRY_RUN (Medium+ Risk)

Before actual execution, show what would happen:

```bash
echo "=== DRY_RUN OUTPUT ==="
DRY_RUN=true bash deploy_to_production.sh
echo "=== END DRY_RUN ==="
```

Output shows:
- Files that would be created/modified
- Commands that would be run
- Environment variables that would be set

User sees the preview. If satisfied, script runs for real.

#### Summary of Gate Outcomes

- **Low Risk Script**: Gate 1 → Execute
- **Medium Risk Script**: Gate 1 → Gate 2 (8B) → Gate 5 (DRY_RUN) → Execute
- **High Risk Script**: Gate 1 → Gate 2 (8B) → Gate 3 (32B) → Gate 4 (Human) → Gate 5 (DRY_RUN) → Execute

**Why This Matters**: Automated safety layer. Catches most problems before user approval. User approval is informed, not rubber-stamp.

### Recommendation 12: Mode Handoff Mechanism with Context Transfer

**Problem**: Modes are siloed. Switching modes loses all context. User must re-explain everything. Expensive in tokens and time.

**Solution**: `suggest_handoff` custom tool enables context-aware mode switching.

**Workflow**:

1. Model recognizes need to switch modes
2. Model calls `suggest_handoff` with:
   - Target mode
   - Compressed summary of relevant context
   - Expected return mode (to return to original mode after handoff)

3. Tool writes handoff context to `.opencode/handoff-context.md`:
```markdown
# Handoff Context

**From**: build-py
**To**: debug
**Return-To**: build-py

## Problem Summary
- User reported: "My FastAPI endpoint is returning 500 errors"
- Current file: app/routes/users.py line 45
- Error: TimeoutError when connecting to database
- Context: Added new async pool management yesterday

## Relevant Code
[compressed code snippet]

## Previous Steps Attempted
1. Checked database connection string (looks correct)
2. Verified database is running

## Next Steps (debug mode should focus on)
1. Check actual timeout values in pool configuration
2. Verify concurrent connection limits
```

4. Plugin switches mode (user approves)
5. New mode reads handoff-context, prepends to session
6. When returning to build-py, model can reference the context: "Based on the debug analysis..."

**Common Handoff Adjacencies** (pre-configured as suggestions):
- build-py ↔ debug (write code, debug failures, write code again)
- build-ex ↔ plan (write code, step back for architecture, write code)
- plan ↔ infra-architect (software design, infrastructure implications)
- strategist ↔ legal (strategic decision, legal implications)
- build-py/build-ex ↔ review (write code, review it, write code)

**Why This Matters**: Context loss was a major pain point. Handoff mechanism keeps context alive across mode switches.

### Recommendation 13: Organic Knowledge Base — Automated Learning

**Problem**: No offline knowledge base. Model re-discovers the same things every session. Valuable learnings are lost between projects.

**Solution**: Three-layer organic knowledge system.

#### Layer 1: Error Resolution Cache

At session end, script `extract-corrections.sh` scans JSONL for problem-solution pairs:

```json
[Session logs contain...]
{
  "timestamp": "2026-03-05T14:32:30Z",
  "type": "error",
  "message": "ModuleNotFoundError: No module named 'redis'"
}
{
  "timestamp": "2026-03-05T14:32:35Z",
  "type": "model_response",
  "content": "Let me install redis-py... pip install redis"
}
{
  "timestamp": "2026-03-05T14:32:40Z",
  "type": "user_message",
  "content": "That fixed it, thanks"
}

[Extraction produces...]
Problem: "ModuleNotFoundError: No module named 'redis'"
Solution: "pip install redis (via pip install redis)"
Mode: build-py
Confidence: 1 (first instance)
```

Stored in `.opencode/knowledge/build-py/` automatically.

#### Layer 2: Correction Aggregator

After 3 corrections about the same topic:

```
Correction 1: User corrects missing redis import (session 1)
Correction 2: User corrects missing redis configuration (session 2)
Correction 3: User corrects redis connection error (session 3)

Detection: Same topic, 3 instances
Action: Generate knowledge entry candidate
```

Generated entry:

```markdown
# Knowledge: Redis Setup in Python Projects

**Pattern**: Model frequently makes mistakes around redis setup

**Mistakes Detected**:
1. Forgetting to install redis-py
2. Forgetting to configure Redis in environment
3. Using wrong connection parameters

**Solution**:
When setting up Redis:
1. Always check if redis-py is in requirements.txt
2. Always ask about configuration: host, port, database number
3. Always include timeout and retry configuration
4. Test connection immediately after setup

**Tags**: redis, python, setup, dependencies
**Mode**: build-py
**Confidence**: 3 instances, 100%
```

Entry goes to `.opencode/knowledge/build-py/redis-setup.md` and is flagged for review.

#### Layer 3: Doc Ingestion on Init

When `/init-project` is called, checks if baseline knowledge exists for detected frameworks:

```
Detected frameworks:
- FastAPI (detected in requirements.txt)
- PostgreSQL (detected in docker-compose.yml)
- pytest (detected in requirements.txt)

Checking baseline knowledge:
- ~/.config/opencode/knowledge/shared/fastapi/ (exists)
- ~/.config/opencode/knowledge/shared/postgresql/ (exists)
- ~/.config/opencode/knowledge/shared/pytest/ (exists)

All frameworks covered, knowledge available.
```

If baseline doesn't exist (new framework):
- Query HuggingFace for framework documentation
- Compress and store as baseline knowledge
- Log that new knowledge was ingested

#### Organic Promotion

Knowledge entries exist in 2+ projects → automatically flagged as promotion candidate:

```
Candidates for Promotion:
1. redis-setup.md (in 2 projects)
2. docker-env-vars.md (in 3 projects)
3. ast-parsing.md (in 1 project, not ready)
```

Promotion candidate appears in daily digest: "You have 2 knowledge entries ready for promotion." User approves → moves to `~/.config/opencode/knowledge/` (user-level) → all projects benefit.

Further promotion: User-level → community repo (with provenance metadata).

**Key Requirement** (Bryan's): These must be organically created and maintained. No manual interface. System creates them from session data, promotes them automatically, only asks for approval at promotion boundaries.

**Why This Matters**: Institutional memory emerges naturally from usage. Knowledge becomes increasingly valuable over time without manual effort.

### Recommendation 14: Transaction Scripts for Coordinated Multi-File Changes

**Problem**: Scripts-first architecture has a blind spot. Adding an Ash resource = create module + update domain + write migration + update router + add LiveView. If any step fails, you're in a broken intermediate state.

**Solution**: Transaction script pattern.

#### Pattern Structure

```bash
#!/bin/bash

####################
# Add Ash Resource (Transaction)
# Risk: HIGH
# Status: session
# Description: Add new resource to Ash domain (atomic)
####################

set -euo pipefail

DRY_RUN="${DRY_RUN:-false}"

# Transaction declaration
TRANSACTION_STEPS=(
  "create_resource_module"
  "update_domain_file"
  "write_migration"
  "update_router"
  "add_live_view"
)

create_resource_module() {
  local module_name="$1"
  # generate module code
}

update_domain_file() {
  # update domain to include new resource
}

write_migration() {
  # generate migration file
}

update_router() {
  # update router to include new routes
}

add_live_view() {
  # generate LiveView module
}

main() {
  local resource_name="$1"

  # Run each step in order
  for step in "${TRANSACTION_STEPS[@]}"; do
    if ! $step "$resource_name"; then
      echo "Transaction failed at: $step"
      echo "Rolling back..."
      rollback
      return 1
    fi
  done

  # All steps succeeded, commit
  if [[ "$DRY_RUN" != "true" ]]; then
    git add .
    git commit -m "Add $resource_name resource"
  fi
}

rollback() {
  # Reverse changes in reverse order
  echo "Transaction rolled back"
  git checkout .
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
```

#### Key Features

- Declares steps upfront (declaration + implementation separation)
- Runs each step, checks exit code
- Rollbacks in reverse on failure
- Git commit only after all steps succeed
- DRY_RUN support (shows what would happen, no actual execution)

#### Enforcement

**Pre-flight validator**: If a script writes to multiple unrelated files, it MUST be a transaction script (hard requirement, not suggestion).

```bash
# Bad: separate scripts (will be rejected)
./create_user_module.sh
./update_domain.sh
./write_migration.sh

# Good: transaction script (will be accepted)
./add_resource.sh user
```

**Why This Matters**: Multi-file changes are atomic. No broken intermediate states. Rollback on failure.

### Recommendation 15: Daily Analytics + Digest

**Problem**: No visibility into system performance. Which modes are working well? Where do corrections cluster? What's the bottleneck?

**Solution**: Two parts:

#### Part 1: Automatic Analytics Collection

On first session of each day, system generates analytics from yesterday's sessions:

**Metrics Tracked**:
- Mode usage distribution (% time in each mode)
- Tier usage per mode (which tool tiers are used most)
- Correction frequency per mode (corrections per interaction)
- Session length before compaction (context utilization)
- Handoff patterns (which modes handoff to which)
- Script promotion rate (how many session scripts became library scripts)
- Knowledge entry creation (how many new entries)
- Tool effectiveness (which tools produce most useful results)

**Daily Digest Output**:

```markdown
# Daily Digest — March 5, 2026

## Activity Summary
- Sessions: 3
- Total interactions: 47
- Modes used: build-py, debug, review, plan

## Mode Breakdown
1. build-py: 65% of time
2. debug: 20% of time
3. review: 10% of time
4. plan: 5% of time

## Quality Metrics
- Correction rate (build-py): 2% ↓ from 5% (IMPROVED)
- Correction rate (debug): 8% (stable)
- Average session length: 18 interactions (up from 15)

## Tool Tier Distribution
- Tier 0 (LSP): 12% (python type info)
- Tier 1 (Custom): 45% (run_script, lookup_knowledge)
- Tier 2 (MCP): 8% (filesystem)
- Tier 3 (Library): 20% (test runner)
- Tier 4 (New): 15% (session scripts)
- Tier 5 (Bash): 0% (good!)

## Knowledge Ready for Review
- redis-setup.md (appears in 2 projects, ready for promotion)
- docker-env-vars.md (appears in 3 projects, ready for promotion)

## Anomalies
- build-py correction rate dropped significantly (why?)
- Review mode used less than usual (expected, lighter week?)

## Escalations (None — system healthy)
```

#### Part 2: Session Startup Display

On session start, digest is shown:

```
Good morning. You have:
- 2 knowledge entries ready for promotion
- build-py correction rate improved 60%
- 1 script promoted to library yesterday
```

#### Part 3: Escalation After Inaction

If a recommendation appears in 3 consecutive daily digests without action:

```
Day 1 Digest: "redis-setup.md ready for promotion"
Day 2 Digest: "redis-setup.md ready for promotion" (escalated to notice)
Day 3 Digest: "redis-setup.md ready for promotion" (escalated to session-start message)

Session Start (Day 4):
⚠️  ESCALATION: redis-setup.md has been waiting 3 days for review.
Cost of delay: Missing opportunity to share learning across projects.
Action: Promote now? (yes/no)
```

**Why This Matters**: Data-driven insights into what's working. Escalation prevents good ideas from getting stuck.

### Recommendation 16: Explicit GPU Layer Offload

**Problem**: Ollama may silently fall back to partial CPU inference if GPU memory isn't sufficient. Silent degradation is worse than loud failure.

**Solution**: Set `num_gpu` in Modelfile to force full Metal offload.

**In Modelfile**:
```
FROM qwen3:32b
PARAMETER num_gpu 64
PARAMETER num_ctx 32768
```

**What num_gpu 64 means**:
- Force all 64 layers onto GPU (Metal on Mac)
- Fail loudly if insufficient VRAM
- No silent fallback to partial CPU

**Error Message** (if GPU offload fails):
```
ERROR: Insufficient GPU memory for full model offload.
Available: 28GB
Required: 34GB (Q8_0) + 6GB (inference) = 40GB
Options:
1. Free up memory: Close apps (estimated 8GB available)
2. Use lower quantization: Q4_K_M (requires 28GB)
3. Reduce context window: num_ctx 16384 (requires 38GB)
```

**Why This Matters**: No silent quality degradation. User knows exactly what's happening.

### Recommendation 17: Graceful Degradation with Cloud Fallback

**Problem**: Local 32B model has a capability ceiling. Some tasks just require more power.

**Solution**: When daily digest detects sustained high correction rate for a mode/task type, flag as capability ceiling (not a prompt problem). Suggest cloud API fallback.

#### Detection

```
Analytics show:
- build-ex mode: 15% correction rate (high)
- Pattern: Complex refactoring scenarios
- Across: 3 sessions, 12 instances

Analysis: Not random errors. Specific task type.

Conclusion: Capability ceiling (task complexity exceeds model capacity)
```

#### Suggestion

Display in digest:

```
⚠️  Capability Ceiling Detected

Mode: build-ex
Task Type: Complex Elixir refactoring
Correction Rate: 15% (expected: <3%)

Analysis: Your local Qwen3 32B is struggling with complex refactoring patterns.
Recommendation: Use cloud API for this specific task type.

Cost Analysis:
- Estimated usage: 3-4 refactoring tasks per week
- Cost per task: ~$0.05 (Claude 3.5 Sonnet)
- Weekly cost: $0.15-$0.20
- Monthly cost: $0.60-$0.80

Recommendation: Enable cloud fallback for build-ex mode.
```

#### Implementation

OpenCode supports multiple providers — configure as priority:

1. Ollama (local, free)
2. Claude API (fallback for specific modes)
3. OpenAI API (optional additional fallback)

When build-ex mode detects capability ceiling:
- Switch to Claude API
- Continue session seamlessly
- Log cost and result
- Report in next digest: "1 cloud API call this week. Would it make sense to enable permanently?"

**Why This Matters**: Perfect is the enemy of done. Sometimes cloud is the right tool. System tells you when and why.

---

## Additional Requirements Beyond the 17

These are critical requirements that emerged during design but aren't part of the 17 core recommendations.

### Max Narration Mode

Bryan got frustrated when AI was doing background research with no visible output. This is a **global rule in the Modelfile**:

**Modelfile System Prompt Must Include**:
```
Always narrate what you are doing and why. Before taking action,
briefly state your plan. During multi-step work, provide status updates.
Never work silently.
```

**Where This Appears** (must be consistent everywhere):
1. Modelfile system prompt (Lean Core layer)
2. AGENTS.md (global rules file)
3. Each mode prompt (reinforced in mode-specific guidance)

**Examples of Good Narration**:
- "I'm going to search for all uses of the deprecated function to understand scope."
- "Found 15 uses. Now I'll check which are in active code paths vs. tests."
- "Ready to refactor. First step: create new function with updated signature. Second step: update all call sites."

**Why This Matters**: User has visibility. No surprise complexity later.

### Model Registry and Auto-Evaluation

Bryan doesn't want to manually discover, evaluate, or configure models. The system should be pro-active.

#### Registry Maintenance

Maintain at `~/.config/opencode/models/registry.json`:

```json
{
  "last_updated": "2026-03-05T12:00:00Z",
  "models": [
    {
      "id": "qwen3:32b",
      "source": "ollama",
      "quant": "Q8_0",
      "size_gb": 34,
      "available": true,
      "performance": {
        "reasoning": 9.2,
        "coding": 8.9,
        "speed_tokens_per_second": 12
      },
      "last_evaluated": "2026-02-28",
      "evaluation_results": {
        "correction_rate_build_py": 0.02,
        "correction_rate_debug": 0.08
      }
    }
  ]
}
```

#### Auto-Update

Daily background script (threshold-triggered, not scheduled):

1. Query Ollama library for new releases
2. Query HuggingFace for trending models
3. Identify models that fit criteria (open source, <40GB Q4_K_M, released <6 months ago)
4. Add candidates to registry with status: "available, unevaluated"

#### Auto-Evaluation

When new model added:

```
Found: Qwen3.5 35B-A3B
Status: Unevaluated

Evaluating against existing correction scenarios...
- Running build-ex corrections (12 scenarios)
- Running build-py corrections (15 scenarios)
- Running debug scenarios (8 scenarios)

Results:
- Qwen3 32B current: 9/12 build-ex corrections avoided
- Qwen3.5 35B: 11/12 build-ex corrections avoided (+18% improvement)

Next evaluation: Compare speed, memory, reasoning quality
Recommendation: Evaluate for assignment to build-ex mode
```

#### Presentation (with Evidence)

Daily digest shows model evaluation results:

```
Model Evaluation Complete: Qwen3.5 35B-A3B

Performance vs. Current (Qwen3 32B):
- Reasoning: +8% (measured on 20 planning scenarios)
- Code quality: +12% (measured on 35 build-ex scenarios)
- Speed: -15% (12 → 10 tokens/sec)
- Memory: Fits (35GB with Q4_K_M)

Evidence (recent corrections):
✓ Correctly handled type annotations (failed 2x with current model)
✓ Correctly structured Ash resources (failed 1x with current model)
✗ Slower response time (noticeable in interactive mode)

Recommendation: Worth trying as fallback for complex build-ex tasks
```

#### Cost-Benefit for Commercial Models

When considering commercial models (Claude, GPT-4):

```
Claude Opus Evaluation for build-ex Mode

Your actual usage (last 30 days):
- build-ex sessions: 8
- Avg tokens per session: 12,000

Monthly cost projection (Claude Opus @ $15/MTok):
- 8 sessions × 12K tokens = 96K tokens/month
- 96K tokens × $0.000015 = $1.44/month

Benefit: Your build-ex correction rate drops from 8% to 2%
(measured on 50-scenario evaluation)

Verdict: Low cost, high benefit. Enable as assigned model for build-ex?
```

#### Post-Deployment Monitoring

After new model assigned, system tracks:

```
Qwen3.5 35B assigned to build-ex (deployed 5 days ago)

Correction rate: 3% (vs. 8% with Qwen3 32B)
Average response time: 9.2 sec (vs. 7.1 sec with 32B)
User satisfaction: High (no complaints, 1 praise)

Verdict: Deployment successful. Improvement held up in production.
```

**Key Principle**: System never asks user to make evaluation decisions. It makes the data-driven calls and surfaces results.

### QVQ-72B-Preview: Vision-Language Exploration

Optional expansion tier. QVQ-72B-Preview is a vision-language model.

**Setup**:
- Pull at Q4_K_M (~42-45GB)
- Marked as "exploration tier" (not production)
- Available for on-demand use via `/models`
- Loading requires closing apps (needs 40GB+ free)

**Use Cases**:
- Debugging UI layouts (screenshot → analysis)
- Reading complex diagrams
- OCR for handwritten notes
- Visual data analysis

**Monitoring for Mode Creation**:
If usage patterns emerge (e.g., frequently used for debugging UI layouts):
- Log usage
- Suggest new mode: `visual` or `debug-ui`
- Run approval process with Bryan
- Create mode if approved

### Continuous Background Processing (Threshold-Triggered)

Bryan rejected cron jobs AND session-based triggers. Sessions don't have clean boundaries — you fall asleep, you keep going, you crash, you restart.

**Solution**: Threshold-triggered async processing.

**Triggers**:
- Queue reaches 10 items (corrections, promotion candidates, errors)
- OR 50 interactions since last processing
- OR token usage crosses 5K increment
- OR explicitly triggered via `/process`

**Implementation**:
- Plugin maintains in-memory queue
- Spawns background async processing when threshold fires
- Processing never blocks active session
- Results surfaced in next session startup

### Three-Tier Scope + Public Repo

Knowledge and artifacts have three scope levels with promotion flowing upward:

**Project Level** (`.opencode/` in repo)
- Project-specific knowledge and tools
- Private to this project
- Created by model during sessions
- Promoted to user level when general enough

**User Level** (`~/.config/opencode/`)
- Shared across all projects
- User's personal knowledge base, tools, preferences
- Created through promotion from project level
- Promoted to public repo when valuable for community

**Public Repo** (`trinsiklabs/crux`)
- Shared with community
- Carries provenance metadata (created by whom, in which project, how many sessions, correction history)
- Bidirectional learning: can accept community contributions
- Privacy boundary: no session logs, code, or project structure leave the machine

### Self-Improvement Across All Five Levels

#### Level 1: Interaction (Real-Time)

Correction detection via plugin. Structured reflections stay in active context.

#### Level 2: Continuous Processing (Threshold-Triggered)

Background processor triggered by thresholds:
- Clusters corrections by similarity
- Analyzes tool usage patterns
- Scores mode effectiveness

#### Level 3: Cross-Session (Pattern Convergence)

Automatic detection of:
- Same correction 3+ sessions = systemic gap
- Workflow fingerprinting (repeated sequences → transaction script candidates)
- Mode drift detection (mode used for out-of-scope work → new mode candidate)

#### Level 4: Cross-Project (User-Level Aggregator)

User-level aggregator watches all projects:
- Same correction in multiple repos = mode-level weakness
- Mode prompt optimization triggered by accumulated evidence
- Aggregated analytics (which modes are performing best across projects)

#### Level 5: Ecosystem (Bidirectional)

- Publish proven artifacts with provenance
- Accept community contributions through staging (`~/.config/opencode/community/`)
- Anonymized correction patterns (opt-in) enable community-wide mode optimization

### Mode Creation Pipeline: Data-Driven Mode Proposal

When mode drift detection reveals a gap:

**Trigger**: Same out-of-scope interaction detected 5+ times across sessions

**Process**:

1. `/propose-mode` fires
2. Evidence presented (clustered interactions, frequency, use case)
3. Generate draft spec using mode template
4. Run adversarial audit on spec
5. **Critically**: Bryan reviews CONVERSATIONALLY, not as rubber stamp

**Conversational Review** (numbered decision points):

```
Mode Proposal: visual

Evidence:
- 7 instances of "can you look at this screenshot?"
- 5 instances in build-py, 2 in debug
- User trying to debug UI layout issues
- Current modes don't have visual analysis tools

Draft Spec:
- Name: visual
- Scope: Analyze images, screenshots, diagrams
- Tools: LSP (NO — not applicable), Custom (image analysis), MCP (vision API)
- Persona: Design-aware code reviewer

Review Questions:
1. Does this scope feel right? (image analysis, screenshots, diagrams)
   Or would you broaden it to: visual design, UI/UX feedback, accessibility?
2. Which LSP tools should be available? (pyright for Python code in images?)
3. Should it have thinking mode? (reasoning about design implications)
4. Integration: Build new vision mode OR expand existing debug mode?

Please confirm each point.
```

Bryan iterates:

```
User: "Broaden to visual design + UI/UX feedback. Don't need LSP.
Yes to thinking mode for design implications. Create new mode."

System: "Locked in. Creating visual mode with thinking, no LSP.

visual mode created:
- `.opencode/modes/visual.md` — prompt
- `.opencode/knowledge/visual/` — knowledge directory
- Registered in opencode.json
- Starting to accumulate learning
```

### Promotion Candidate Notifications

Bryan won't remember to check queues. System must interrupt with urgency:

**Session Startup** (every session):
```
You have 7 knowledge entries ready for review.
```

**After 3 Days Ignored** (escalation):
```
⚠️  ESCALATION: 5 knowledge entries have been waiting 3+ days for promotion.
Cost of delay: Missing opportunity to share learning across projects.
Action: Review candidates? (yes/no)
```

Explicit escalation forces decision.

---

## Implementation Priority: Dependency-Driven Sequencing

Build in this order. Dependencies flow downward (lower items depend on upper items).

### Phase 1: Core Infrastructure (Everything depends on these)

**1.1 preflight-validator.sh**
- Deterministic pre-flight checks (risk classification, template compliance, path containment)
- Blocks invalid scripts before execution
- Dependency: none
- Purpose: Safety foundation

**1.2 run_script.js (Custom Tool)**
- Implements five-gate pipeline (preflight → 8B audit → 32B audit → human approval → DRY_RUN)
- Core execution guardrail
- Dependency: preflight-validator.sh
- Purpose: Script safety and auditability

**1.3 session-logger.js (Plugin)**
- Verify/fix against actual OpenCode `message.updated` hook API
- Log every interaction to JSONL
- Dependency: none (but needed for all learning)
- Purpose: Session observability and recovery

**1.4 correction-detector.js (Plugin)**
- Real-time correction pattern detection
- Detects: negation language, retry patterns, self-correction language
- Dependency: session-logger.js (reads messages)
- Purpose: Learning signal extraction

### Phase 2: Knowledge and Learning Engine (Builds on Phase 1)

**2.1 extract-corrections.sh**
- Scans JSONL for correction patterns
- Clusters similar corrections
- Generates knowledge entry candidates
- Dependency: session-logger.js (reads logs)
- Purpose: Bulk pattern analysis

**2.2 lookup_knowledge.js (Custom Tool)**
- Mode-scoped knowledge retrieval from project + user + shared levels
- Invoked by model during interactions
- Dependency: directory structure (project `.opencode/knowledge/`, user `~/.config/opencode/knowledge/`)
- Purpose: Knowledge access

**2.3 update-project-context.sh**
- Generate and maintain PROJECT.md
- Extract directory tree, tech stack, recent changes
- Runs at project init and session end
- Dependency: none
- Purpose: Project context provision

**2.4 promote-knowledge.sh**
- Move knowledge entries from project to user level
- Promote to public repo with provenance
- User approval required
- Dependency: knowledge entries exist in promotion queues
- Purpose: Knowledge promotion

**2.5 generate-digest.sh**
- Daily analytics aggregation
- Extract metrics from logs and session state
- Generate daily digest
- Dependency: session-logger.js, analytics data files
- Purpose: Daily intelligence

### Phase 3: Workflow Tools (Improves daily usage, builds on Phase 1)

**3.1 promote_script.js (Custom Tool)**
- Atomic script promotion from session to library
- Move `.opencode/scripts/session/foo.sh` → `.opencode/scripts/lib/foo.sh`
- Update registry, archive old version
- Dependency: script must exist and pass validation
- Purpose: Script lifecycle management

**3.2 list_scripts.js (Custom Tool)**
- Library script discovery
- Show available scripts, descriptions, usage
- Allow invocation by name
- Dependency: lib scripts exist
- Purpose: Script reuse enablement

**3.3 suggest_handoff.js (Custom Tool)**
- Mode handoff with context transfer
- Write handoff context, switch mode
- Return mode capability
- Dependency: modes must exist
- Purpose: Context preservation across mode switches

**3.4 project_context.js (Custom Tool)**
- Read and serve PROJECT.md
- Return relevant file paths, tech stack, key info
- Used by model for context
- Dependency: update-project-context.sh has run
- Purpose: Codebase context provision

### Phase 4: Enforcement and Safety (Hardens the system, builds on Phase 1-2)

**4.1 compaction-hook.js (Plugin)**
- Fire before context compaction
- Inject domain-specific instructions to 8B compaction model
- Preserve script names, mode context, project state
- Dependency: session-logger.js (context to preserve)
- Purpose: Informed context compaction

**4.2 token-budget.js (Plugin)**
- Token spend enforcement per interaction
- Uses `tool.execute.before` hook
- Hard constraints on read-only modes (cannot call write tools)
- Dependency: none
- Purpose: Token efficiency and safety

**4.3 tool-enforcer.js (Plugin)**
- Tier hierarchy enforcement
- Reject tool calls that violate tier constraints
- Analytics on tier usage per mode
- Dependency: tool definitions
- Purpose: Tool reliability guarantee

### Phase 5: Model Intelligence (Optimizes model selection, builds on Phase 1-3)

**5.1 manage_models.js (Custom Tool)**
- Registry queries
- Pull new models, configure, evaluate
- Model switching
- Dependency: `~/.config/opencode/models/registry.json` exists
- Purpose: Model flexibility

**5.2 Model Registry Auto-Update Script**
- Query Ollama library and HuggingFace
- Identify new models, add to registry
- Threshold-triggered (not scheduled)
- Dependency: registry.json exists
- Purpose: Model discovery

**5.3 Model Auto-Evaluation Pipeline**
- Evaluate new models against correction scenarios
- Compare performance vs. current model
- Report results
- Dependency: correction scenarios exist (from Phase 2)
- Purpose: Data-driven model selection

### Phase 6: Mode Prompt Audit (Can happen anytime after Phase 1)

**6.1 Audit all 15 modes** for:
- Positive framing (do X not don't do Y)
- Prime positions (critical rules at beginning and end)
- Length target (120-155 tokens)

**6.2 Synchronize** setup.sh mode prompts with standalone mode files

### Phase 7: Documentation (After everything else works)

**7.1 Architecture deep-dive docs**
- System design rationale
- Component interactions
- Data flow diagrams

**7.2 Individual system documentation**
- Tool hierarchy explanation
- Safety pipeline documentation
- Plugin hook reference

---

## Research Findings That Inform Implementation

These findings are the evidence base for design decisions. Keep them in mind during implementation.

### Prompt Engineering Research

1. **Positive Instructions > Negative Instructions**
   - Positive: "Always use type hints in Python" (strongly biases toward type hints)
   - Negative: "Don't forget type hints" (only weakly reduces probability of missing them)
   - **Implementation**: All mode prompts use positive framing. Never "don't do X," always "do Y."

2. **Simple Task-Relevant Personas > Elaborate Backstories**
   - Good: "You are a security-focused code reviewer"
   - Bad: "You are a senior engineer with 20 years at Google, passionate about clean code, mentors juniors..." (fictional detail = bias drift)
   - **Implementation**: Mode personas are census-style descriptions, not backstories.

3. **Instruction Placement Matters**
   - Prime positions: beginning and end of system prompt
   - Middle position: 40% less effective
   - **Implementation**: Critical rules (narration, numbered lists) in first 50 tokens and last 30 tokens of system prompt.

4. **Optimal System Prompt Length: 150-200 Words**
   - Current modes: ~120-155 tokens (90-115 words)
   - Room to add specificity without degradation
   - **Implementation**: Keep mode prompts within target range. Additional specificity goes in optional knowledge lookups, not in system prompt.

### OpenCode Plugin Hook System (Actual API)

Available hooks in OpenCode (verified against actual hook system):

- `chat.message` — mutate user messages before agent processing
- `chat.params` — modify LLM parameters (temperature, topP, topK)
- `experimental.chat.system.transform` — mutate system prompt array
- `experimental.chat.messages.transform` — mutate full message history
- `tool.definition` — mutate tool descriptions and schemas
- `tool.execute.before` — intercept tool calls before execution
- `tool.execute.after` — react to tool results
- `session.created` — session start
- `message.updated` — react to messages
- `session.idle` — session becomes idle
- `experimental.session.compacting` — fire before context compaction

**Important Limitations**:
- MCP tool calls don't trigger tool.execute.before/after
- Subagent tool calls don't trigger tool.execute.before
- System prompt mutations must be implemented carefully (order matters)

### OpenCode Context Management

- Auto-compaction triggers at 95% of context capacity
- Uses specialized "compaction agent" to summarize
- Token Budget system keeps "Head" and "Tail" of tool output, prunes middle
- Provider-specific prompt caching available (if using Claude API)

### LLM-as-Judge Biases (When Using 8B to Audit 32B)

1. **Self-Enhancement Bias** (5-7% boost when evaluating own outputs)
   - **Mitigation**: Using different model (8B) to audit a different model's (32B) output avoids this
   - **Implementation**: 8B always audits 32B scripts, never vice versa

2. **Position Bias** (~40% inconsistency in ordering)
   - **Relevance**: Not relevant for single-script audit
   - **Would matter for**: Multi-option comparisons

3. **Verbosity Bias** (~15% inflation for longer responses)
   - **Mitigation**: Explicit "PASS or list concerns" instruction (closes open-ended response)
   - **Implementation**: 8B audit prompt ends with "Respond with PASS or list your concerns. Nothing else."

### DSPy for Mode Optimization (Future Enhancement)

DSPy can optimize prompts programmatically:
- Works with local models via Ollama
- Uses metric functions to measure output quality
- Iteratively refines prompts
- Relevant optimizers: MIPROv2 (generates instructions + few-shot examples), COPRO (coordinate ascent)

**Applicability**: Could be used for automated mode prompt optimization at Level 4 (cross-project aggregation), but current approach is scripted analytics + human review. Worth revisiting after 2-3 months of operation.

---

## File Locations Reference

This section documents where files are created and their purposes.

### User-Level Configuration (`~/.config/opencode/`)

These files persist across all projects. Created by setup script.

```
~/.config/opencode/
├── opencode.json                    # OpenCode configuration
├── AGENTS.md                        # Global behavioral rules
├── modes/                           # Mode prompt files
│   ├── build-py.md
│   ├── build-ex.md
│   ├── build-docker.md
│   ├── debug.md
│   ├── plan.md
│   ├── infra-architect.md
│   ├── strategist.md
│   ├── docker.md
│   ├── mac.md
│   ├── review.md
│   ├── writer.md
│   ├── analyst.md
│   ├── psych.md
│   ├── legal.md
│   └── explain.md
├── plugins/                         # Plugin JavaScript files
│   ├── think-router.js
│   ├── session-logger.js
│   ├── correction-detector.js
│   ├── compaction-hook.js
│   ├── token-budget.js
│   └── tool-enforcer.js
├── tools/                           # Custom tool JavaScript files
│   ├── run_script.js
│   ├── lookup_knowledge.js
│   ├── suggest_handoff.js
│   ├── promote_script.js
│   ├── list_scripts.js
│   ├── project_context.js
│   └── manage_models.js
├── commands/                        # Command markdown files
│   ├── init-project.md
│   ├── stats.md
│   └── [others]
├── knowledge/                       # User-level knowledge base (shared across projects)
│   ├── shared/
│   │   ├── fastapi/
│   │   ├── postgresql/
│   │   ├── pytest/
│   │   └── [frameworks]
│   ├── build-py/
│   ├── build-ex/
│   ├── docker/
│   └── [mode-specific]
├── models/
│   └── registry.json                # Model registry with evaluations
├── analytics/                       # Analytics data files
│   ├── daily/
│   ├── weekly/
│   └── monthly/
└── setup-state/                     # Setup script state tracking
    └── [setup flags and configs]
```

### Ollama Models (`~/.ollama/models/`)

Modelfile variants created by setup:

```
~/.ollama/models/
├── crux-think                       # Qwen3 32B with thinking parameters
├── crux-chat                        # Qwen3 32B with non-thinking parameters
├── qwen3:32b                        # Base model (auto-downloaded)
├── qwen3:8b                         # Compaction model (auto-downloaded)
└── [other models as configured]
```

### Project-Level Files (`.opencode/` in repo)

Created by `/init-project`. Private to each project.

```
.opencode/
├── scripts/
│   ├── session/                     # Current session scripts
│   │   ├── script1.sh
│   │   ├── script2.sh
│   │   └── [transient scripts]
│   ├── lib/                         # Promoted reusable scripts
│   │   ├── backup_database.sh
│   │   ├── run_tests.sh
│   │   └── [proven scripts]
│   └── archive/                     # Auto-archived scripts
│       └── [old session scripts]
├── knowledge/                       # Project-specific knowledge
│   ├── redis-setup.md
│   ├── docker-env-vars.md
│   └── [project discoveries]
├── logs/                            # Session logs (JSONL format)
│   ├── 2026-03-05.jsonl
│   ├── 2026-03-04.jsonl
│   └── [daily logs]
├── tools/                           # Project-specific custom tools
│   └── [as needed]
├── AGENTS.md                        # Project-specific behavioral rules
└── PROJECT.md                       # Project context (auto-generated and maintained)
```

### Handoff Context (Temporary)

Created during mode handoff:

```
.opencode/
└── handoff-context.md               # Temporary, cleared after handoff
```

### Checkpoint Files (During Session)

Created by session-logger plugin at checkpoints:

```
.opencode/
└── checkpoint.json                  # Last checkpoint (in memory, for crash recovery)
```

---

## Summary: The Crux Thesis

Crux is built on the principle that **infrastructure enforces what prompts cannot**. Prompts drift. Code doesn't.

### Core Convictions

1. **Mode Architecture**: 15 specialized modes are more effective than one general-purpose system
2. **Scripts-First**: Everything through templated, validated scripts. No direct file modification.
3. **Learning Is Organic**: The system learns from correction patterns, not manual curation
4. **Safety Is Infrastructure**: Five-gate execution pipeline, token budgets, tool tiers, risk classification
5. **Observability Is Built-In**: 100% session logging, 100% session recovery, automatic analytics
6. **Context Rot Is Addressable**: Lean system prompt (3 layers), compaction with domain awareness, knowledge injection
7. **Multi-Model Is Better Than One**: Primary + fallback + compaction + exploration models, data-driven selection
8. **Narration Over Silence**: Always show what you're doing. No background work.

### The Implementation Roadmap

**Phase 1** (Core Infrastructure): Validation, execution pipeline, logging, correction detection. Foundation for everything else.

**Phase 2** (Learning Engine): Knowledge extraction, lookup, promotion. System becomes self-improving.

**Phase 3** (Workflow Tools): Scripting utilities, handoff mechanism, project context. Daily usability improves.

**Phase 4** (Enforcement): Safety and efficiency layers. Reliability hardens.

**Phase 5** (Model Intelligence): Registry, auto-evaluation, fallback routing. System becomes multi-model.

**Phase 6** (Cleanup): Mode audits, sync, documentation.

**Phase 7** (Documentation): Architecture docs, system reference.

### Success Metrics

- **Correction rate trends down over time** (learning is working)
- **Session length increases before compaction** (broader context window used effectively)
- **Script promotion rate increases** (session scripts becoming library scripts faster)
- **Mode usage distribution stabilizes** (modes are reaching appropriate usage levels)
- **Token efficiency improves** (same work in fewer tokens)
- **User happiness with system increases** (narration, handoff, knowledge improve experience)

### The North Star

Crux is a self-improving AI operating system where:
- **Everything is auditable** (100% logging)
- **Nothing is hidden** (max narration)
- **Learning is automatic** (organic knowledge)
- **Safety is enforced** (infrastructure constraints)
- **Quality improves over time** (correction-driven optimization)

---

## End of Document

This document represents the complete knowledge transfer from the design session. Every design decision, research finding, and nuance is captured here.

For Claude Code building remaining components: Use this document as your source of truth. Cross-reference section numbers when decisions affect multiple areas. The 17 recommendations are the core optimization strategy. The implementation priority section shows dependencies.

**Questions?** Search this document for keywords. Every major system is explained with rationale, not just spec.

**Ready to build?** Start with Phase 1. Nothing else can be built until the core infrastructure exists.

Good luck.
