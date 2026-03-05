# OpenCode Custom Tools Specification

## Overview

Custom tools are JavaScript/TypeScript modules that extend the OpenCode agent with domain-specific capabilities. They are loaded from:
- **Project-level:** `.opencode/tools/` (takes precedence)
- **Global-level:** `~/.config/opencode/tools/`

Tools are **Tier 1** in the tool hierarchy — preferred over everything except LSP (Tier 0). The model sees the tool's description and schema, decides when to invoke it, and the tool executes deterministically.

## Export Format

All custom tools must export a default object matching this structure:

```javascript
import { z } from 'zod';

export default {
  name: 'tool_name',
  description: 'What this tool does — the model reads this to decide when to use it',
  parameters: z.object({
    param1: z.string().describe('What this parameter is'),
    param2: z.boolean().optional().describe('Optional flag'),
  }),
  execute: async (params, context) => {
    // context.agent — current agent instance
    // context.sessionID — unique session identifier
    // context.directory — project root directory
    // Implementation here
    return { result: 'output shown to model' };
  }
};
```

All tools must:
1. Use **Zod** for parameter validation (zod library)
2. Provide clear descriptions for the model
3. Implement `execute` as an async function
4. Return a result object with a `result` field
5. Log important actions to the session JSONL (see logging format below)

---

## Tool 1: run_script.js

### Purpose

**THE critical tool.** All script execution flows through this. It implements the five-gate safety pipeline internally — the model calls `run_script` and the tool handles all validation, auditing, dry-run, and execution orchestration.

### Parameters

```typescript
{
  script_path: string        // Path to the script to execute (required)
  approval_override: boolean // Set true if user has already approved in conversation
                             // For high-risk scripts where the model asked the user (optional, default false)
  dry_run: boolean           // Force DRY_RUN mode even for low-risk scripts
                             // (optional, default false)
}
```

### Five-Gate Pipeline Implementation

#### Gate 1: Deterministic Pre-flight (all scripts)

Execute the `preflight-validator.sh` library script against the target script:

```javascript
const { exec } = require('child_process');
const preflight = await exec(`${context.directory}/.opencode/scripts/lib/preflight-validator.sh ${params.script_path}`);
```

The preflight validator checks (in order):
- **Header compliance:** Required fields (name, risk, created, status, description)
- **Safety pragma:** `set -euo pipefail` present
- **Risk-behavior consistency:** Script's declared risk matches its operations
  - "low" scripts cannot contain: `rm `, `DROP`, `DELETE`, `docker down`, `git push --force`, writes outside project
  - "medium"/"high" scripts must reference `DRY_RUN` in body
- **Path containment:** All write operations stay within project or `.opencode/scripts/`
- **Multi-file write detection:** Scripts writing to 2+ unrelated directories are rejected with message "Refactor into transaction script"

**On failure:** Return error with specific reason. Script does NOT proceed to Gate 2.

**On success:** Continue to Gate 2.

#### Gate 2: 8B Adversarial Audit (medium and high risk scripts)

For scripts with risk "medium" or "high":

1. Read the full script content
2. POST to Ollama API at `http://localhost:11434/api/generate`:

```json
{
  "model": "qwen3:8b",
  "prompt": "You are a security auditor. Your job is to find every way this script could cause data loss, corruption, unintended side effects, or scope creep beyond its stated purpose. Assume the script is wrong until proven safe. List every concern. If you find none, say PASS.\n\nScript:\n{full_script_text}",
  "stream": false,
  "timeout": 30000
}
```

3. Parse response:
   - If response contains "PASS" → proceed to Gate 3
   - If concerns listed → return `{ result: 'audit_concerns', concerns: [list], gate: 2 }` to the model

4. The model then:
   - Shows the user the concerns
   - Either revises the script and calls `run_script` again
   - Or asks the user for approval (which moves to Gate 4)

**Timeout handling:** If the Ollama API takes >30 seconds, log a warning and skip to Gate 3 (don't block the workflow).

**Ollama unreachable:** If the API is unreachable, skip AI gates with a warning but continue to pre-flight validation (Gate 1 always runs).

#### Gate 3: 32B Second-Opinion Audit (high risk scripts only)

For scripts with risk "high":

1. Use the `crux-think` model variant (same base model but reasoning-optimized parameters)
2. POST to the model backend with this system prompt:

```
You are an independent reviewer performing a final safety check. This script was written by another agent and has passed an initial 8B audit. Your job is to find anything the first audit missed — subtle risks, edge cases, unintended consequences, scope creep. Review this script for safety and compliance with OpenCode conventions.

If the script is safe and properly constructed, respond with: APPROVED

If you find remaining concerns, list them clearly with reasoning.
```

3. Include the script text and the concerns (if any) from Gate 2
4. Parse response:
   - If "APPROVED" → proceed to Gate 4 (human approval for high-risk)
   - If concerns listed → return to the model with combined audit results from both gates

#### Gate 4: Human Approval (high risk scripts only)

Return a message to the model formatted for user presentation:

```
This is a high-risk script that requires explicit user approval before execution.

[Full script text]

## Audit Results

### 8B Audit (Gate 2)
[concerns from Gate 2, or "PASS"]

### 32B Audit (Gate 3)
[concerns from Gate 3, or "APPROVED"]

## Risk Classification
[from header: risk level]

## Your Decision
Do you approve execution of this script? Respond "yes" to proceed or describe needed changes.
```

The model presents this to the user. If the user approves, the model calls `run_script` again with `approval_override: true`.

#### Gate 5: DRY_RUN (medium and high risk scripts)

For scripts with risk "medium" or "high":

1. Set environment variable `DRY_RUN=true`
2. Execute: `bash -e {script_path}` with DRY_RUN environment variable
3. Capture stdout and stderr
4. Return dry-run output to the model

The model then:
- Presents the dry-run results to the user
- If results look correct, calls `run_script` again (without `dry_run: true` parameter)
- If issues found, the user can revise the script

#### Final Execution

After all gates pass:

1. Execute: `bash -e {script_path}`
2. Capture stdout, stderr, and exit code
3. Log to session JSONL:
   ```json
   {
     "type": "script_execution",
     "script_path": "{path}",
     "risk_level": "{low|medium|high}",
     "gates_passed": [1, 2, 3, 4, 5],
     "exit_code": 0,
     "output_lines": 42,
     "timestamp": "2026-03-05T14:23:45Z"
   }
   ```
4. Return output to the model

### Session JSONL Logging

For every script execution, append an entry to `.opencode/logs/{session_id}.jsonl`:

```json
{
  "timestamp": "ISO8601",
  "type": "script_audit",
  "script_path": "relative/path",
  "gate": 1,
  "result": "pass|fail|concerns",
  "details": "specific reason or concern list"
}
```

Log each gate separately as it completes.

### Error Handling

- **Gate 1 fails:** Return error with specific validator output. Stop.
- **Gate 2 returns concerns:** Return concerns to model for revision or user approval.
- **Gate 3 returns concerns:** Combine with Gate 2 results and return to model.
- **Gate 4 user rejects:** Stop. User can revise script.
- **Gate 5 dry-run shows issues:** Stop. User can revise.
- **Final execution fails:** Capture exit code and stderr, return to model.

---

## Tool 2: promote_script.js

### Purpose

Atomically promote a one-off session script to the reusable library. Handles file relocation, header update, and git integration.

### Parameters

```typescript
{
  script_path: string  // Path to the session script (required)
  new_name: string     // Optional new name for the promoted script (optional)
}
```

### Behavior

**Step 1: Validation**
- Verify script exists at `script_path`
- Verify script is in `.opencode/scripts/session/` directory
  - If in `.opencode/scripts/lib/`, return error: "Script is already in library"
  - If in `.opencode/scripts/archive/`, return error: "Cannot promote archived scripts"
- Read script header and parse: name, risk, created, status, description
  - If header is malformed, return error with specific missing fields

**Step 2: Determine destination**
- If `new_name` provided, use `{new_name}`
- Otherwise use the `name` field from script header
- Destination: `.opencode/scripts/lib/{name}.sh`
- If destination file exists, return error: "Library script '{name}' already exists"

**Step 3: Update header**
- Replace `Status: one-off` with `Status: promoted`
- Add new field: `Promoted: {current_date}`
- Keep all other header fields unchanged
- Write to temporary file, verify it's valid with `preflight-validator.sh`

**Step 4: Copy to destination**
- Copy (not move) the updated script to `.opencode/scripts/lib/{name}.sh`
- Preserve file permissions

**Step 5: Git commit**
- Run: `git add .opencode/scripts/lib/{name}.sh`
- Run: `git commit -m "Promote script: {name} from session to library"`
- If git fails with "not a git repo", warn but don't fail
- If git commit fails, warn but don't fail (file is already copied)

**Step 6: Session logging**
- Append to session JSONL:
  ```json
  {
    "type": "script_promotion",
    "from_path": "{original_path}",
    "to_path": ".opencode/scripts/lib/{name}.sh",
    "status": "success|git_warning",
    "timestamp": "ISO8601"
  }
  ```

**Step 7: Return success**

```javascript
return {
  result: 'Script promoted successfully',
  promoted_path: '.opencode/scripts/lib/{name}.sh',
  status: 'success'
};
```

### Error Cases

| Scenario | Error Message |
|----------|---------------|
| Script not found | `Script not found at: {path}` |
| Not in session/ | `Only scripts in .opencode/scripts/session/ can be promoted` |
| Already in lib/ | `Script is already in library` |
| In archive/ | `Cannot promote archived scripts` |
| Destination exists | `A library script named '{name}' already exists at: {path}` |
| Header malformed | `Script header is missing required field: {field}` |
| Preflight validation fails | Return preflight validator output |

---

## Tool 3: list_scripts.js

### Purpose

Returns available library scripts with metadata. The model calls this BEFORE writing a new script to check if an existing one handles the task.

### Parameters

```typescript
{
  filter: string  // "all", "low", "medium", "high" (optional, default "all")
  search: string  // Search term for name or description (optional)
}
```

### Behavior

**Step 1: Scan locations**
- Project-level: `.opencode/scripts/lib/` (checked first)
- Global-level: `~/.config/opencode/scripts/lib/` (checked second)
- Stop at first match (project takes precedence)

**Step 2: Parse metadata**
For each `.sh` file in the selected directory:
1. Read lines until first non-comment or until after `set -euo pipefail`
2. Extract header block (lines starting with `#`):
   - `# Name: {name}`
   - `# Risk: {low|medium|high}`
   - `# Created: {YYYY-MM-DD}`
   - `# Status: {promoted|archived|deprecated}`
   - `# Description: {description}`
3. If any required field is missing, skip the script with a warning

**Step 3: Filter and search**

```javascript
let results = scripts;

if (params.filter !== 'all') {
  results = results.filter(s => s.risk === params.filter);
}

if (params.search) {
  const searchLower = params.search.toLowerCase();
  results = results.filter(s =>
    s.name.toLowerCase().includes(searchLower) ||
    s.description.toLowerCase().includes(searchLower)
  );
}
```

**Step 4: Sort and format**
- Sort by: created date (newest first)
- Format each entry:
  ```
  {name}
    Risk: {risk}
    Created: {YYYY-MM-DD}
    Description: {description}
    Path: {relative/path}
  ```

**Step 5: Return results**

```javascript
return {
  result: `Found ${results.length} scripts matching filter`,
  scripts: results,
  total_count: scripts.length
};
```

### Output Example

```
Found 3 scripts matching filter

build-project
  Risk: medium
  Created: 2025-12-15
  Description: Build the project with proper dependency resolution
  Path: .opencode/scripts/lib/build-project.sh

setup-env
  Risk: low
  Created: 2025-11-20
  Description: Initialize development environment
  Path: .opencode/scripts/lib/setup-env.sh
```

---

## Tool 4: project_context.js

### Purpose

Provides mode-scoped project context by reading and returning PROJECT.md. Keeps the model's context window efficient by serving only what's relevant.

### Parameters

```typescript
{
  section: string  // Optional: "tech_stack", "directory", "conventions", "active_context" (optional)
}
```

### Behavior

**Step 1: Locate PROJECT.md**
- Check: `{project_directory}/.opencode/PROJECT.md`
- If not found, return:
  ```javascript
  return {
    result: 'PROJECT.md not found. Run /init-project to create project context.',
    status: 'not_found'
  };
  ```

**Step 2: Parse file**
- Read full PROJECT.md
- If `section` parameter provided, extract that section using markdown heading syntax
  - Section "tech_stack" → content between `## Tech Stack` and next `##`
  - Section "directory" → content between `## Directory Structure` and next `##`
  - etc.
- If section not found, return error: `Section '{section}' not found in PROJECT.md`

**Step 3: Return content**

If full file:
```javascript
return {
  result: 'Project context loaded',
  content: fullContent,
  section: null
};
```

If specific section:
```javascript
return {
  result: `Section '${params.section}' loaded`,
  content: sectionContent,
  section: params.section
};
```

**Step 4: Content size management**
- If full PROJECT.md exceeds 500 tokens, log a warning and truncate to 500 tokens
- Preserve markdown structure (don't cut mid-heading)

### Expected PROJECT.md Structure

```markdown
# Project Context
Generated: YYYY-MM-DD HH:MM
Last session: {session-id}

## Tech Stack
Elixir 1.14, Phoenix 1.7, Ash Framework 2.x
Database: PostgreSQL 15

## Directory Structure
(tree output, depth 3)

## Key Files
- config/config.exs — Application configuration
- lib/app_web/router.ex — Route definitions

## Active Context
Branch: main
Recent commits: last 3 commit messages

## Conventions
From .formatter.exs: line_length 120
From .credo.exs: disabled checks [...]
```

### Session JSONL Logging

```json
{
  "type": "project_context_lookup",
  "section": "null|section_name",
  "content_tokens": 250,
  "timestamp": "ISO8601"
}
```

---

## Tool 5: lookup_knowledge.js

### Purpose

Mode-scoped knowledge base retrieval. Searches knowledge entries relevant to a query with automatic scope management (project → user → shared).

### Parameters

```typescript
{
  query: string  // Search query (required)
  mode: string   // Override mode scope (optional, defaults to current active mode)
}
```

### Behavior

**Step 1: Determine search scope**

Order of precedence:
1. Project-level: `{project}/.opencode/knowledge/{mode}/` (highest priority)
2. User-level: `~/.config/opencode/knowledge/{mode}/`
3. Shared: `~/.config/opencode/knowledge/shared/`

Create scope array in precedence order. Check existence before adding to array.

**Step 2: Collect files**

For each directory in scope:
- List all `.md` files
- Store with metadata: filename, directory level (project|user|shared), full path
- Maintain order by scope precedence

**Step 3: Relevance matching**

For each file:
1. Read file content
2. Extract title from first `#` heading
3. Case-insensitive substring matching:
   - If ANY word from `query` appears in title → high relevance
   - If ANY word from `query` appears in content → medium relevance
   - No match → exclude

Score matches:
```javascript
const words = params.query.toLowerCase().split(/\s+/);
const hasInTitle = words.some(w => title.toLowerCase().includes(w));
const hasInContent = words.some(w => content.toLowerCase().includes(w));

if (hasInTitle) score = 3;
else if (hasInContent) score = 1;
else score = 0;
```

**Step 4: Sort results**

Sort by:
1. Relevance score (descending)
2. Scope precedence (project > user > shared)
3. Filename (ascending)

**Step 5: Truncate output**

- Cap total content at 2000 tokens (to avoid context bloat)
- Include complete files in order until approaching 2000 tokens
- Truncate last file if it would exceed limit, append `[... content truncated]`

**Step 6: Return results**

```javascript
return {
  result: `Found ${results.length} matching entries`,
  entries: results.map(r => ({
    title: r.title,
    source: r.level, // "project" | "user" | "shared"
    path: r.path,
    excerpt: r.content.substring(0, 200) + '...'
  })),
  full_content: combinedContent,
  total_tokens: estimatedTokens
};
```

### Example Result

```
Found 2 matching entries

1. Refactoring Patterns (project-level)
   Path: .opencode/knowledge/build-ex/refactoring-patterns.md
   Excerpt: "When breaking down large functions, follow the
   composed function pattern..."

2. Code Review Guidelines (user-level)
   Path: ~/.config/opencode/knowledge/shared/code-review.md
   Excerpt: "Always check for unused variables, which
   account for 15% of bugs..."

[Full content of both entries...]
```

### Session JSONL Logging

```json
{
  "type": "knowledge_lookup",
  "query": "user query",
  "mode": "build-ex",
  "matches_found": 2,
  "scopes_checked": ["project", "user"],
  "timestamp": "ISO8601"
}
```

---

## Tool 6: suggest_handoff.js

### Purpose

Facilitates graceful cross-mode handoff with context preservation. The model invokes this when recognizing that a question/task belongs in a different mode's domain.

### Parameters

```typescript
{
  target_mode: string      // The mode to hand off to (required)
  context_summary: string  // Compressed context: what we're building, why we need
                           // the new mode, what the new mode needs to know (required)
  return_mode: string      // The mode to return to after handoff (required)
}
```

### Behavior

**Step 1: Validate modes**
- Verify `target_mode` is a recognized mode (check agent configuration)
- Verify `return_mode` is a recognized mode
- Return error if either is invalid

**Step 2: Create handoff context file**

Write to `.opencode/handoff-context.md`:

```markdown
# Handoff Context
From: {return_mode}
To: {target_mode}
Timestamp: {ISO8601}
Session: {session_id}

## Summary
{context_summary}

## Return Instruction
When this work is complete, return to {return_mode} mode.

## Files Modified
{list of files touched in current session}

## Previous Context
{last 5 lines from project context if available}
```

**Step 3: Session logging**

```json
{
  "type": "handoff_prepared",
  "from_mode": "{return_mode}",
  "to_mode": "{target_mode}",
  "context_bytes": 1250,
  "timestamp": "ISO8601"
}
```

**Step 4: Return result**

```javascript
return {
  result: 'Handoff context prepared',
  target_mode: params.target_mode,
  return_mode: params.return_mode,
  context_file: '.opencode/handoff-context.md',
  next_step: `Suggest to user: /mode ${params.target_mode}`
};
```

### Important Notes

- The tool **PREPARES** the handoff but does NOT switch modes
- The model suggests the switch to the user
- The user explicitly approves and runs `/mode {target_mode}`
- This keeps the user in control of mode transitions
- Handoff context persists until the target mode reads it

---

## Tool 7: manage_models.js

### Purpose

Interface to the model registry. Queries available models, pulls new ones, evaluates candidates, and manages mode assignments.

### Parameters

```typescript
{
  action: string      // "list" | "recommend" | "pull" | "evaluate" | "status" (required)
  model_name: string  // Model name for pull/evaluate (optional)
  mode: string        // Mode name for recommend action (optional)
}
```

### Actions

#### list

**Purpose:** Show all available and installed models with metadata

**Behavior:**
1. Read registry from `~/.config/opencode/models/registry.json`
2. For each model entry, include:
   - name
   - provider (ollama, anthropic, openai, etc.)
   - parameters (7B, 32B, etc.)
   - quantization (Q8_0, Q4_K_M, etc.)
   - status (assigned, available, not-pulled)
   - assigned_modes (if assigned)
   - strengths and weaknesses
3. Format as table or list

**Return:**
```javascript
return {
  result: `${models.length} models in registry`,
  models: models,
  statistics: {
    total_size_gb: sumOfSizes,
    assigned_modes: countOfAssignedModes,
    unassigned_available: countOfAvailable
  }
};
```

#### recommend

**Purpose:** Suggest optimal model for a given mode

**Parameters needed:**
- `mode: string` — the mode to recommend for

**Behavior:**
1. Read mode's task type from agent config (code-generation, reasoning, creative, analysis, etc.)
2. Scan registry for models with matching strengths
3. Check hardware compatibility:
   - Read `registry.json` hardware profile (chip, total_ram_gb)
   - For each model, estimate memory needed: size_gb × 1.2 (overhead factor)
   - Only recommend if: available_ram > estimated_need
4. Score candidates:
   - Strength match: +3 per matching strength
   - Size efficiency: models within 2× needed size get +1
   - Current assignment: already-assigned models get +2
5. Rank by score, return top 3

**Return:**
```javascript
return {
  result: `Recommendations for mode '${params.mode}'`,
  recommendations: [
    {
      rank: 1,
      model_name: 'qwen3:32b-q8_0',
      score: 9,
      reasoning: 'Strong code generation (3), reasoning (+2), current Tier 1 (+2), efficient size (+2)',
      memory_required_gb: 41,
      available_memory_gb: 64
    }
  ]
};
```

#### pull

**Purpose:** Download and register a new model

**Parameters needed:**
- `model_name: string` — exact model identifier (e.g., "mistral:7b-q4_0")

**Behavior:**
1. Verify model_name format (contains ":" separator)
2. Verify not already in registry
3. Call `ollama pull {model_name}` via child_process:
   ```javascript
   const { exec } = require('child_process');
   await exec(`ollama pull ${params.model_name}`);
   ```
4. Wait for completion (can take several minutes)
5. Query Ollama API to get actual size:
   ```
   GET http://localhost:11434/api/tags
   ```
6. Add entry to registry:
   ```json
   {
     "name": "{model_name}",
     "provider": "ollama",
     "parameters": "7B|13B|32B|...",
     "quantization": "q4_0|q8_0|...",
     "size_gb": {actual_from_api},
     "status": "available",
     "assigned_modes": [],
     "strengths": [],
     "weaknesses": [],
     "benchmarks": {},
     "correction_rate": {},
     "last_evaluated": null
   }
   ```
7. Git commit registry update

**Return:**
```javascript
return {
  result: `Model '${params.model_name}' pulled successfully`,
  size_gb: 34,
  status: 'available',
  next_step: `Assign to a mode with /manage-models --action recommend --mode {mode_name}`
};
```

**Errors:**
- `Model name invalid: must include ':' separator`
- `Model already in registry`
- `Ollama API unreachable — is Ollama running?`
- `Pull failed: {stderr from ollama}`

#### evaluate

**Purpose:** Test a candidate model against known correction scenarios

**Parameters needed:**
- `model_name: string` — model to evaluate

**Behavior:**
1. Verify model is in registry
2. Verify model is pulled (can run via Ollama)
3. Read session logs from `.opencode/logs/` and extract correction entries:
   ```json
   {
     "type": "reflection",
     "mode": "{mode}",
     "wrong_approach": "...",
     "correct_approach": "..."
   }
   ```
4. Collect 10-20 recent corrections from the active mode
5. For each correction:
   - Construct test prompt: "What's the best way to {wrong_approach}?"
   - Run prompt through candidate model via Ollama API
   - Compare output to known correct_approach (simple substring matching for v1)
   - Score: 1 if correct, 0 if wrong
6. Calculate:
   - Correction_rate = (corrected / total) × 100
   - Compare to baseline (current mode's model)

**Return:**
```javascript
return {
  result: `Evaluated ${params.model_name}`,
  evaluation: {
    total_test_cases: 15,
    corrections: 13,
    correction_rate: 86.7,
    baseline_rate: 78.2,
    improvement: '+8.5%',
    mode: 'build-ex'
  },
  recommendation: 'This model shows 8.5% improvement — consider assigning to build-ex'
};
```

#### status

**Purpose:** Current state of all models and assignments

**Behavior:**
1. Read registry
2. Check Ollama API for loaded models: `GET http://localhost:11434/api/tags`
3. For each mode, find assigned model from agent config
4. Report:
   - Which models are currently loaded in Ollama (memory usage if available)
   - Which mode is using which model
   - Any unassigned available models

**Return:**
```javascript
return {
  result: 'Model status',
  assignments: {
    'build-py': 'qwen3:32b-q8_0 (34 GB, loaded)',
    'build-ex': 'qwen3:32b-q8_0 (34 GB, loaded)',
    'debug': 'claude-opus-4 (remote, API)'
  },
  loaded_models: [
    {
      name: 'qwen3:32b-q8_0',
      size_gb: 34,
      memory_usage_mb: 27000,
      assigned_modes: 2
    }
  ],
  available_modes_unassigned: 0
};
```

### Registry Schema Reference

Location: `~/.config/opencode/models/registry.json`

```json
{
  "schema_version": 1,
  "hardware": {
    "chip": "M1 Max",
    "total_ram_gb": 64,
    "last_updated": "2026-03-01T10:00:00Z"
  },
  "models": [
    {
      "name": "qwen3:32b-q8_0",
      "provider": "ollama",
      "parameters": "32B",
      "quantization": "Q8_0",
      "size_gb": 34,
      "status": "assigned",
      "assigned_modes": ["build-py", "build-ex", "debug"],
      "strengths": ["code_generation", "reasoning", "tool_use", "bash_scripting"],
      "weaknesses": ["legal_reasoning", "creative_writing"],
      "benchmarks": {
        "pass_@_1": 0.78,
        "code_quality": 8.2,
        "reasoning_depth": 7.9
      },
      "correction_rate": {
        "build-py": 78.2,
        "build-ex": 82.1,
        "debug": 75.3
      },
      "last_evaluated": "2026-02-28T14:22:00Z"
    },
    {
      "name": "claude-opus-4",
      "provider": "anthropic",
      "parameters": "unknown",
      "quantization": null,
      "size_gb": null,
      "status": "assigned",
      "assigned_modes": ["analyst"],
      "api_key_required": true,
      "pricing_per_1m_tokens": {
        "input": 15,
        "output": 75
      },
      "strengths": ["legal_reasoning", "complex_analysis", "creative_writing", "nuanced_judgment"],
      "weaknesses": ["bash_scripting"],
      "benchmarks": {},
      "correction_rate": {
        "analyst": 94.2
      },
      "last_evaluated": "2026-02-25T09:15:00Z"
    },
    {
      "name": "mistral:7b-q4_0",
      "provider": "ollama",
      "parameters": "7B",
      "quantization": "Q4_0",
      "size_gb": 5,
      "status": "available",
      "assigned_modes": [],
      "strengths": ["speed", "lightweight", "instructions"],
      "weaknesses": ["reasoning", "code_quality", "complex_analysis"],
      "benchmarks": {},
      "correction_rate": {},
      "last_evaluated": null
    }
  ]
}
```

---

## Session JSONL Logging Format

All tools should log important operations to `.opencode/logs/{session_id}.jsonl`. Each line is a separate JSON object. Required fields for all entries:

```typescript
{
  timestamp: string       // ISO8601 format
  type: string           // Tool-specific type identifier
  [tool_specific]: any   // Additional fields per tool
}
```

### Log Entry Examples

```json
{"timestamp":"2026-03-05T14:23:45Z","type":"script_execution","script_path":"deploy.sh","risk_level":"high","gates_passed":[1,2,3,4,5],"exit_code":0,"output_lines":42}
{"timestamp":"2026-03-05T14:24:12Z","type":"script_promotion","from_path":".opencode/scripts/session/test.sh","to_path":".opencode/scripts/lib/test.sh","status":"success"}
{"timestamp":"2026-03-05T14:25:03Z","type":"knowledge_lookup","query":"error handling","mode":"build-ex","matches_found":3,"scopes_checked":["project","user"]}
{"timestamp":"2026-03-05T14:26:18Z","type":"handoff_prepared","from_mode":"build-py","to_mode":"analyst","context_bytes":1250}
```

---

## Error Handling Strategy

All tools should:
1. Return structured error responses with `result` field explaining the issue
2. Log errors to session JSONL with `type: "tool_error"`
3. Provide specific, actionable error messages (not generic "failed")
4. Never throw uncaught exceptions — catch and return as error result

Example error return:

```javascript
return {
  result: 'Script validation failed',
  error: 'Risk classification mismatch: script marked "low" but contains rm operation',
  error_code: 'RISK_BEHAVIOR_MISMATCH',
  suggestion: 'Reclassify script as "medium" and add DRY_RUN support'
};
```

---

## Performance Considerations

- **Gate 2 (8B audit):** May take 5-30 seconds. Use 30-second timeout.
- **Gate 3 (32B audit):** Should be faster than Gate 2, but still subject to model load.
- **lookup_knowledge:** Should complete in <1 second for typical projects.
- **manage_models pull:** Model downloads can take minutes. Provide progress indication or spawn async job.
- **list_scripts:** Should scan <100 files, complete in <500ms.

All tools should avoid blocking operations that could exceed 30 seconds without user feedback.

