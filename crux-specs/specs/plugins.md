# Crux Plugins Implementation Specification

**Last Updated:** 2026-03-05
**Purpose:** Complete implementation guide for all 5 Crux OpenCode plugins

This document contains everything a developer needs to implement each plugin correctly, including exact hook names, data structures, behavior specifications, and design reasoning.

---

## Table of Contents
1. [Plugin Architecture Overview](#plugin-architecture-overview)
2. [Plugin 1: session-logger.js](#plugin-1-session-loggerjs)
3. [Plugin 2: think-router.js](#plugin-2-think-routerjs)
4. [Plugin 3: correction-detector.js](#plugin-3-correction-detectorjs)
5. [Plugin 4: compaction-hook.js](#plugin-4-compaction-hookjs)
6. [Plugin 5: token-budget.js](#plugin-5-token-budgetjs)
7. [Shared State & Coordination](#shared-state--coordination)
8. [Testing & Validation](#testing--validation)

---

## Plugin Architecture Overview

### General Plugin Structure

All Crux plugins follow the OpenCode plugin API. The standard export format is:

```javascript
export const PluginNamePlugin = async ({ project, client, $, directory }) => {
  // Initialize plugin state
  // Set up any file system resources

  return {
    event: async ({ event, output, message, tool }) => {
      // Handle hook events
      if (event.type === 'hook.name') {
        // Implement behavior
      }
    }
  };
};
```

**Parameters passed to plugin:**
- `project`: Project metadata (name, path, etc.)
- `client`: Qwen client instance for executing code
- `$`: Shell execution utility
- `directory`: Current working directory

**Hook Event Handler Signature:**
The `event` handler receives an object with:
- `event`: The hook event (has `type` field and event-specific data)
- `output`: Object to mutate with results (structure depends on hook)
- `message`: Current message context (when relevant)
- `tool`: Current tool context (when relevant)

### Hook Events Available

| Hook | Fired When | Mutability | Use Case |
|------|-----------|-----------|----------|
| `session.created` | Session starts | Read-only | Initialize per-session state |
| `message.updated` | User or assistant sends message | Mutate message | Transform message content |
| `chat.message` | User submits message | Mutate message | Pre-processing before agent |
| `tool.execute.before` | Before tool invocation | Block/allow tool | Enforce constraints |
| `tool.execute.after` | After tool completes | Read tool output | Audit and track |
| `session.idle` | Session enters idle state | Read-only | Finalize and checkpoint |
| `experimental.session.compacting` | Before context compaction | Inject context | Preserve critical info |

### Design Principles

1. **Silent Failures**: All I/O errors should be caught and logged silently. A plugin crash breaks the user's session.
2. **Minimal Overhead**: Plugins run synchronously in the hot path. Keep event handlers fast.
3. **Stateless by Default**: Plugins should derive state from files or context when possible, not memory.
4. **Composability**: Plugins coordinate via shared checkpoint.json, not direct communication.
5. **Debuggable Logs**: Every significant action should be logged in the session JSONL.

---

## Plugin 1: session-logger.js

### Purpose

Captures every interaction to JSONL for three purposes:
1. **Crash Recovery**: Detect incomplete sessions and allow resumption
2. **Analytics**: Track interaction patterns, tool usage, error rates
3. **Continuous Learning Pipeline**: Train on real-world OpenCode usage patterns

The session logger is the foundation for all other plugins' audit trail.

### Hook Events

#### `session.created`
Fires when a new session is created.

**Behavior:**
1. Generate session ID: `{YYYY-MM-DD}-session-{N}` where N = count of existing .jsonl files for today + 1
   - Example: `2026-03-05-session-1`, `2026-03-05-session-2`, etc.
2. Determine log directory: `{project_directory}/.opencode/logs/`
3. Create directory if needed
4. Write session_start entry to `{log_directory}/{session_id}.jsonl`
5. **Crash Recovery**: Scan logs directory for previous incomplete sessions
   - Sort JSONL files by date descending
   - For each file, read the last line
   - If last line is NOT `{"type": "session_end", ...}`, mark as incomplete
   - Log a `crash_recovery` entry with incomplete session ID and last 20 entries from that file
6. **Resume Context**: Check for `{project_directory}/.opencode/resume-context.md`
   - If exists, read it and log a `resume_context` entry

**Data:**
```json
{
  "type": "session_start",
  "session": "2026-03-05-session-1",
  "directory": "/absolute/path/to/project",
  "ts": "2026-03-05T14:22:45.123Z"
}
```

#### `message.updated`
Fires whenever a message is added or updated (user message, assistant response, tool output).

**Behavior:**
1. Extract message metadata:
   - `role`: "user" or "assistant"
   - `content`: Full message text (if role="user") or response text (if role="assistant")
   - Truncate content to 2000 characters if longer
   - `interaction`: Current interaction number (count of user+assistant message pairs since session start)
   - `mode`: Current active mode from message context (if available)
2. Write entry to JSONL log file (append with newline)
3. Every 5 interactions, update `checkpoint.json` with latest state

**Data:**
```json
{
  "type": "user",
  "content": "User message truncated to 2000 chars...",
  "interaction": 1,
  "mode": "build-py",
  "ts": "2026-03-05T14:23:01.456Z"
}
```

```json
{
  "type": "assistant",
  "content": "Assistant response truncated to 2000 chars...",
  "interaction": 2,
  "mode": "build-py",
  "ts": "2026-03-05T14:23:05.789Z"
}
```

#### `tool.execute.after`
Fires after a tool completes execution (successful or with error).

**Behavior:**
1. Extract tool metadata:
   - `name`: Tool name (e.g., "write", "bash", "read", "edit")
   - `interaction`: Current interaction number
2. **Special tracking for script creation**: If tool is "write" or "edit" and path contains `/scripts/` patterns:
   - Extract script path
   - Add to scripts_created list in checkpoint.json
3. Write entry to JSONL log

**Data:**
```json
{
  "type": "tool",
  "name": "bash",
  "interaction": 3,
  "ts": "2026-03-05T14:23:08.234Z"
}
```

```json
{
  "type": "script_created",
  "path": ".opencode/scripts/session/fix-auth.sh",
  "interaction": 3,
  "ts": "2026-03-05T14:23:08.234Z"
}
```

#### `session.idle`
Fires when session enters idle state (user stops interacting for a period or explicitly ends).

**Behavior:**
1. Write session_end entry with metadata:
   - Total interactions count
   - All scripts created (from checkpoint.json)
   - Final mode
2. Update checkpoint.json with session end timestamp
3. Write `resume-context.md` for potential resumption:
   - Include last interaction number
   - Include mode
   - List all scripts created with brief descriptions (if available)
   - Timestamp for reference

**Data:**
```json
{
  "type": "session_end",
  "session": "2026-03-05-session-1",
  "interactions": 47,
  "scripts": [
    ".opencode/scripts/session/fix-auth.sh",
    ".opencode/scripts/session/update-config.sh"
  ],
  "ts": "2026-03-05T14:35:22.567Z"
}
```

### Data Structures

#### JSONL Log Format

The session log is a JSON Lines file (newline-delimited JSON) stored at:
```
{project}/.opencode/logs/{session-id}.jsonl
```

**Entry Types:**

```json
{"type": "session_start", "session": "2026-03-05-session-1", "directory": "/path/to/project", "ts": "2026-03-05T14:22:45.123Z"}

{"type": "user", "content": "message text truncated to 2000 chars", "interaction": 1, "mode": "build-py", "ts": "2026-03-05T14:23:01.456Z"}

{"type": "assistant", "content": "response text truncated to 2000 chars", "interaction": 2, "mode": "build-py", "ts": "2026-03-05T14:23:05.789Z"}

{"type": "tool", "name": "bash", "interaction": 3, "ts": "2026-03-05T14:23:08.234Z"}

{"type": "script_created", "path": ".opencode/scripts/session/fix-auth.sh", "interaction": 3, "ts": "2026-03-05T14:23:08.234Z"}

{"type": "crash_recovery", "incomplete_session": "2026-03-04-session-3", "last_entries": [...last 20 lines...], "ts": "2026-03-05T14:22:46.000Z"}

{"type": "resume_context", "content": "...content of resume-context.md...", "ts": "2026-03-05T14:22:46.100Z"}

{"type": "reflection", "trigger": "user_correction", "mode": "build-ex", "interaction": 14, "context": "User corrected Ash resource naming", "wrong_approach": "Raw Ecto schema", "correct_approach": "Ash resource with actions", "ts": "2026-03-05T14:28:45.000Z"}

{"type": "session_end", "session": "2026-03-05-session-1", "interactions": 47, "scripts": ["path1", "path2"], "ts": "2026-03-05T14:35:22.567Z"}
```

#### checkpoint.json

File: `{project}/.opencode/checkpoint.json`

Maintained by session-logger, read by other plugins.

```json
{
  "session": "2026-03-05-session-1",
  "last_interaction": 45,
  "scripts_created": [
    ".opencode/scripts/session/fix-auth.sh",
    ".opencode/scripts/session/update-config.sh"
  ],
  "mode": "build-py",
  "updated": "2026-03-05T14:33:22.500Z"
}
```

**Fields:**
- `session`: Current session ID
- `last_interaction`: Most recent interaction number
- `scripts_created`: Array of script paths created this session
- `mode`: Current active mode (must be kept in sync with actual mode)
- `updated`: ISO timestamp of last checkpoint write

#### resume-context.md

File: `{project}/.opencode/resume-context.md`

Written at session end, read by session-logger on next session.created to offer resumption.

```markdown
# Resume Context

Last updated: 2026-03-05T14:35:22.567Z
Session: 2026-03-05-session-1

## State

- Mode: build-py
- Interactions: 47
- Last interaction timestamp: 2026-03-05T14:35:00.000Z

## Scripts Created This Session

- `.opencode/scripts/session/fix-auth.sh` - Fix authentication middleware
- `.opencode/scripts/session/update-config.sh` - Update configuration values
- `.opencode/scripts/session/validate-schema.sh` - Validate database schema

## Recent Work Summary

- Fixed authentication middleware in user service
- Updated configuration for new database schema
- Validated schema changes against production compatibility

## Recommended Next Steps

- Deploy fixes to staging environment
- Run integration tests
- Monitor error logs for related issues
```

### Crash Recovery Logic

**Initialization (on session.created):**

```
1. List all .jsonl files in {project}/.opencode/logs/
2. Sort files by modification date descending (newest first, excluding current session)
3. For each file in list:
   a. Open file in read mode
   b. Read last non-empty line
   c. Parse as JSON
   d. If parsed JSON has type != "session_end":
      - Mark this session as INCOMPLETE
      - Extract session ID from filename
      - Read last 20 lines from file (or all if fewer than 20)
      - Log crash_recovery entry with incomplete session ID and last lines
      - Mark recovery as "available" (user can be offered resumption)
   e. If file is malformed (can't parse), skip with silent failure

4. Check for resume-context.md existence
   a. If exists, read entire content
   b. Log resume_context entry with content
   c. Optionally offer to user (implementation detail)

5. Write session_start entry to current session log
```

**Why this matters:**
- If OpenCode crashes mid-session, the incomplete .jsonl file has no session_end marker
- Detecting this allows the system to:
  - Warn the user about the crash
  - Offer to resume from a checkpoint
  - Analyze what caused the crash (via last_entries)
- Synchronous writes to JSONL (using appendFileSync) ensure data survives process crashes

### Critical Implementation Details

#### Synchronous JSONL Writes

**IMPORTANT**: All writes to the .jsonl log must use `appendFileSync()`, not `writeFileSync()` or async methods.

```javascript
const fs = require('fs');
const entry = { type: 'user', content: '...', interaction: 1, ts: new Date().toISOString() };
fs.appendFileSync(logFilePath, JSON.stringify(entry) + '\n', 'utf8');
```

**Rationale:**
- Async writes (`fs.writeFile()`) buffer data in memory
- If the process crashes, buffered writes are lost
- The entire point of the session logger is crash recovery
- Synchronous writes guarantee data hits disk before the next operation
- OpenCode sessions are I/O-bound (waiting for user/tool execution), so sync I/O overhead is negligible

#### Checkpoint Update Frequency

Update checkpoint.json every 5 interactions, not every message.

```javascript
if (currentInteraction % 5 === 0) {
  updateCheckpointFile();
}
```

**Rationale:**
- `checkpoint.json` is for resumption and other plugins' state lookup
- Updating every interaction (every message) causes excessive I/O
- Updating every 5 interactions is a reasonable balance:
  - 5 interactions = ~2-3 minutes of real-world usage
  - If crash occurs, at most 4 interactions of work is lost
  - Plugins can still read the last valid checkpoint

#### Session ID Generation

```javascript
function generateSessionId(logDirectory) {
  // Format: YYYY-MM-DD-session-N
  const today = new Date().toISOString().split('T')[0]; // '2026-03-05'

  // List all files in log directory
  const files = fs.readdirSync(logDirectory).filter(f => f.endsWith('.jsonl'));

  // Count files starting with today's date
  const todayFiles = files.filter(f => f.startsWith(today));
  const nextN = todayFiles.length + 1;

  return `${today}-session-${nextN}`;
}
```

#### Content Truncation

When logging user or assistant messages, truncate to 2000 characters:

```javascript
function truncateContent(content, maxLength = 2000) {
  if (content.length <= maxLength) return content;
  return content.substring(0, maxLength - 3) + '...';
}
```

**Rationale:**
- Full responses can be 10,000+ characters
- Logging full content would make logs enormous and slow to parse
- 2000 chars captures enough context for recovery and analysis
- The ellipsis (`...`) signals truncation

#### Silent Failure Pattern

Every I/O operation must be wrapped in try-catch:

```javascript
try {
  // I/O operation
} catch (error) {
  // Silent failure - do not throw
  // Optionally log to console in debug mode
  if (process.env.OPENCODE_DEBUG) {
    console.error(`[session-logger] I/O error:`, error);
  }
}
```

**Rationale:**
- A plugin crash breaks the user's session
- Logging is nice-to-have, not essential
- Network issues, permission errors, full disk shouldn't stop the session
- Users can retrieve logs after the session if needed

#### Log Directory Structure

Create and maintain:
```
{project}/.opencode/
├── logs/
│   ├── 2026-03-04-session-1.jsonl
│   ├── 2026-03-04-session-2.jsonl
│   ├── 2026-03-05-session-1.jsonl
│   └── ...
├── checkpoint.json
└── resume-context.md
```

The `.opencode/` directory may already exist (used by other OpenCode components). Verify it exists or create it:

```javascript
const opencodePath = path.join(directory, '.opencode');
const logsPath = path.join(opencodePath, 'logs');

if (!fs.existsSync(opencodePath)) fs.mkdirSync(opencodePath, { recursive: true });
if (!fs.existsSync(logsPath)) fs.mkdirSync(logsPath, { recursive: true });
```

### OpenCode Plugin Export Format

**CRITICAL VERIFICATION NEEDED**: The plugin export pattern may vary. Check the OpenCode documentation for the correct format.

**Pattern 1 (Assumed Correct):**
```javascript
export const SessionLoggerPlugin = async ({ project, client, $, directory }) => {
  // Setup code
  return {
    event: async ({ event, output, message, tool }) => {
      if (event.type === 'session.created') { /* ... */ }
      if (event.type === 'message.updated') { /* ... */ }
      // ... other hooks
    }
  };
};
```

**Pattern 2 (Alternative - Check OpenCode Docs):**
```javascript
export default {
  hooks: {
    'session.created': async ({ event, output }) => { /* ... */ },
    'message.updated': async ({ event, output, message }) => { /* ... */ },
    // ... etc
  }
};
```

**MUST VERIFY**: Look at OpenCode source or existing plugins to determine which pattern is correct. This document assumes Pattern 1 based on the original setup.sh, but this must be verified against current OpenCode plugin API.

### Implementation Checklist

- [ ] Create `.opencode/logs/` directory on session.created
- [ ] Implement session ID generation with date + counter
- [ ] Write session_start entry on session.created
- [ ] Implement crash recovery scanning on session.created
- [ ] Implement message logging for user and assistant messages
- [ ] Truncate messages to 2000 characters
- [ ] Track interaction count across messages
- [ ] Update checkpoint.json every 5 interactions
- [ ] Detect script creation via tool.execute.after
- [ ] Add script paths to scripts_created array
- [ ] Write session_end entry on session.idle
- [ ] Generate resume-context.md on session.idle
- [ ] Implement silent failure for all I/O errors
- [ ] Use appendFileSync for JSONL writes (never async)
- [ ] Test crash recovery by manually breaking a session

---

## Plugin 2: think-router.js

### Purpose

Automatically prepends `/think` or `/no_think` directives to user messages based on the active mode. This optimizes token usage for Qwen models where extended chain-of-thought reasoning is beneficial for some tasks but wasteful for others.

The router intercepts messages before the agent processes them, so the prepended directive is invisible to the user but shapes the model's reasoning depth.

### Hook Event

**`chat.message`**

Fires when a user submits a message, after the message is added to the chat history but before the agent processes it.

**Behavior:**
1. Check if message content already starts with `/think` or `/no_think`
   - If yes, skip (user override)
2. Get current mode from context
   - Modes are set by the user via `/mode {mode}` command or persist from previous interactions
3. Classify mode:
   - If in THINK_MODES: prepend `/think ` to message.content
   - If in NO_THINK_MODES: prepend `/no_think ` to message.content
   - If in NEUTRAL_MODES or unknown mode: do nothing
4. Update message.content with prepended directive
5. Return (no explicit return needed, mutation is in-place)

### Mode Classification

```javascript
const THINK_MODES = [
  'debug',            // Debugging requires deep analysis of code flow
  'plan',             // Planning needs thorough reasoning about tradeoffs
  'infra-architect',  // Architecture requires examining multiple approaches
  'review',           // Code review needs careful reasoning about quality
  'legal',            // Legal analysis must be thorough and justified
  'strategist',       // Strategic decisions need extensive reasoning
  'psych'             // Psychological analysis needs deep contextual reasoning
];

const NO_THINK_MODES = [
  'build-py',         // Python building is execution-focused; model knows patterns
  'build-ex',         // Elixir building is execution-focused; model knows patterns
  'writer',           // Writing is creative/fluent; extended thinking hurts readability
  'analyst',          // Analytical tasks are straightforward data extraction
  'mac',              // Mac dev is direct execution; thinking adds no value
  'docker',           // Docker config is formulaic; thinking is wasteful
  'explain'           // Explanation should be clear and concise, not verbose
];

const NEUTRAL_MODES = [
  'ai-infra'          // AI infrastructure sometimes needs reasoning, sometimes doesn't
];
```

### Design Reasoning

#### THINK_MODES
These tasks benefit measurably from extended chain-of-thought reasoning:

- **debug**: The model must trace execution flow, consider multiple failure paths, and reason about state changes. Shallow thinking misses subtle bugs.
- **plan**: Planning involves comparing multiple approaches, considering tradeoffs, and justifying decisions. Extended reasoning is essential.
- **infra-architect**: Architecture decisions have long-term consequences. The model should explore options deeply.
- **review**: Code review requires checking correctness, style, security, and maintainability. These need careful reasoning.
- **legal**: Legal analysis must be justified and thorough. The cost of shallow legal reasoning is catastrophic.
- **strategist**: Strategic decisions require considering context, competitors, risks, and opportunities. Extended reasoning is necessary.
- **psych**: Psychological analysis of user behavior, team dynamics, etc., requires deep contextual understanding.

#### NO_THINK_MODES
These tasks execute better with shallow, fast processing:

- **build-py**, **build-ex**: The model has strong pattern knowledge for these languages. It knows how to structure code, which libraries to use, etc. Extended thinking generates verbose explanations instead of clean code.
- **writer**: Writing benefits from fluency and directness. Extended thinking makes prose verbose and overthought.
- **analyst**: Extracting data and summarizing patterns is straightforward. The model doesn't need to reason deeply.
- **mac**, **docker**: Configuration is formulaic. The model has strong pattern knowledge. Thinking just wastes tokens.
- **explain**: Explanations should be clear and concise. Extended thinking generates verbose, meandering explanations.

#### NEUTRAL_MODES
- **ai-infra**: Sometimes needs deep thinking (architecture decisions), sometimes needs fast execution (config snippets). User control is appropriate.

### Hook Implementation

```javascript
export const ThinkRouterPlugin = async ({ project, client, $, directory }) => {
  const THINK_MODES = ['debug', 'plan', 'infra-architect', 'review', 'legal', 'strategist', 'psych'];
  const NO_THINK_MODES = ['build-py', 'build-ex', 'writer', 'analyst', 'mac', 'docker', 'explain'];
  const NEUTRAL_MODES = ['ai-infra'];

  return {
    event: async ({ event, output, message }) => {
      if (event.type !== 'chat.message') return;

      // Skip if user already specified directive
      if (message.content.startsWith('/think') || message.content.startsWith('/no_think')) {
        return;
      }

      // Get current mode from context
      const currentMode = getCurrentMode(); // Implementation: derive from context/state

      // Prepend directive based on mode
      let directive = null;
      if (THINK_MODES.includes(currentMode)) {
        directive = '/think ';
      } else if (NO_THINK_MODES.includes(currentMode)) {
        directive = '/no_think ';
      }

      if (directive && isQwenModel()) { // Only for Qwen models
        message.content = directive + message.content;
      }
    }
  };
};
```

### Critical Detail: Model-Specific Directives

**IMPORTANT**: The `/think` and `/no_think` directives are Qwen3-specific. They are not understood by other models.

**Implementation:**

1. Check the active model name before prepending:

```javascript
function isQwenModel() {
  const modelName = (client?.modelName || '').toLowerCase();
  return modelName.includes('qwen') ||
         modelName.includes('crux-think') ||
         modelName.includes('crux-chat');
}
```

2. If the user switches to a non-Qwen model (e.g., Claude API):
   - Do NOT prepend `/think` or `/no_think`
   - Treat the message normally
   - These directives would appear as literal text in the prompt to Claude, which is incorrect

3. Consider logging mode-switch events to checkpoint.json for debugging:

```json
{
  "type": "mode_switch",
  "from": "build-py",
  "to": "plan",
  "model": "qwen3-large",
  "ts": "2026-03-05T14:25:00.000Z"
}
```

### Implementation Checklist

- [ ] Implement THINK_MODES, NO_THINK_MODES, NEUTRAL_MODES constants
- [ ] Hook into chat.message event
- [ ] Skip if message already has `/think` or `/no_think` prefix
- [ ] Get current mode from context/state
- [ ] Check if model is Qwen-based before prepending
- [ ] Prepend directive to message.content
- [ ] Log mode classification for debugging
- [ ] Test with different modes and verify directives are prepended
- [ ] Test that user-specified directives are not overridden

---

## Plugin 3: correction-detector.js

### Purpose

Detects when the user corrects the AI's behavior or approach and writes structured reflection entries to the session log. These reflections capture what was wrong, what was correct, and the rule that was violated or learned. This data feeds the continuous learning pipeline.

### Hook Event

**`message.updated`**

Fires on every message update (user message, assistant response, tool output). The plugin analyzes the conversation context to detect corrections.

### Detection Patterns

The plugin must detect ALL of the following correction signals:

#### Pattern 1: User Correction Language

Check the most recent user message for negation/redirection/correction language:

```javascript
const CORRECTION_STARTERS = [
  /^no,?\s/i,
  /^no\s+(?:that|this)/i,
  /^wrong/i,
  /^that's\s+not\s/i,
  /^I\s+(?:said|meant|want)/i,
  /^don't\s/i,
  /^don't\s+(?:do|use|create)/i,
  /^stop\s+/i,
  /^actually,?\s/i,
  /^wait,?\s/i
];

const CORRECTION_PHRASES = [
  /instead,?\s/i,
  /I\s+meant\s+/i,
  /what\s+I\s+(?:want|meant|asked)\s+/i,
  /not\s+what\s+I\s+asked/i,
  /the\s+correct\s+(?:way|approach)/i,
  /(?:it\s+)?should\s+(?:be|have)/i,
  /you\s+should\s+have\s+/i
];
```

**Implementation:**
```javascript
function isUserCorrection(userMessage) {
  const text = userMessage.toLowerCase();
  const startsWithNegation = CORRECTION_STARTERS.some(pattern => pattern.test(text));
  const containsRedirection = CORRECTION_PHRASES.some(pattern => pattern.test(text));
  return startsWithNegation || containsRedirection;
}
```

#### Pattern 2: Model Self-Correction

Check the most recent assistant message for self-correction language:

```javascript
const SELF_CORRECTION_PHRASES = [
  /\bsorry,/i,
  /my\s+mistake/i,
  /let\s+me\s+fix/i,
  /you're\s+right/i,
  /I\s+apologize/i,
  /correction:/i,
  /I\s+was\s+wrong/i,
  /let\s+me\s+correct/i
];
```

**Implementation:**
```javascript
function isModelSelfCorrection(assistantMessage) {
  return SELF_CORRECTION_PHRASES.some(pattern => pattern.test(assistantMessage));
}
```

#### Pattern 3: Tool Retry Pattern

Detect when the same tool is called twice in succession with different parameters:

```javascript
function isToolRetry(recentTools) {
  // recentTools: array of last N tool calls, each with { name, params }
  if (recentTools.length < 2) return false;

  const lastTool = recentTools[recentTools.length - 1];
  const secondLastTool = recentTools[recentTools.length - 2];

  return lastTool.name === secondLastTool.name &&
         JSON.stringify(lastTool.params) !== JSON.stringify(secondLastTool.params);
}
```

**Rationale**: When the model calls the same tool twice with different parameters, it's typically:
1. Trying something
2. Seeing it fail
3. Trying a different approach

This is a correction signal.

#### Pattern 4: Script Audit Failure

Detect when a script fails pre-flight validation and is rewritten:

```javascript
function isScriptAuditFailure(recentScriptWrites) {
  // recentScriptWrites: array of { path, timestamp, validationResult, rewritten }
  const recent = recentScriptWrites.slice(-2); // Last two writes to same script

  if (recent.length < 2) return false;

  const [first, second] = recent;
  return first.path === second.path &&
         first.validationResult !== 'pass' &&
         second.timestamp > first.timestamp;
}
```

**Rationale**: If a script is written, fails validation, then rewritten, the second write is a correction of the first.

### Reflection Entry Format

Reflections are written to the SAME JSONL log as regular session entries (they are interspersed).

```json
{
  "type": "reflection",
  "trigger": "user_correction",
  "mode": "build-ex",
  "interaction": 14,
  "context": "User corrected Ash resource naming convention",
  "wrong_approach": "Used raw Ecto schema instead of Ash resource",
  "correct_approach": "Use Ash resource with proper actions",
  "rule": "Always use domain layer abstractions in Elixir",
  "ts": "2026-03-05T14:28:45.000Z"
}
```

```json
{
  "type": "reflection",
  "trigger": "tool_retry",
  "mode": "debug",
  "interaction": 23,
  "context": "Model retried bash command after first attempt failed",
  "wrong_approach": "grep pattern didn't match file structure",
  "correct_approach": "Used more flexible regex pattern",
  "rule": "Test assumptions about file structure before running commands",
  "ts": "2026-03-05T14:35:12.000Z"
}
```

```json
{
  "type": "reflection",
  "trigger": "audit_failure",
  "mode": "build-py",
  "interaction": 8,
  "context": "Script failed security audit on first attempt",
  "wrong_approach": "Hard-coded database credentials in script",
  "correct_approach": "Read credentials from environment variables",
  "rule": "Never hard-code secrets in scripts",
  "ts": "2026-03-05T14:20:33.000Z"
}
```

### Field Specifications

- **type**: Always `"reflection"`
- **trigger**: One of: `"user_correction"`, `"self_correction"`, `"tool_retry"`, `"audit_failure"`
- **mode**: Current active mode when correction was detected
- **interaction**: Interaction number when correction occurred
- **context**: Short (50-100 chars) human-readable description of the correction. Extract from the conversation.
  - Example: "User corrected Ash resource naming convention"
  - Example: "Script failed security audit"
- **wrong_approach**: What was incorrect (max 200 chars). Extract from the message before the correction.
  - Truncate if necessary with ellipsis
  - Example: "Used raw Ecto schema instead of Ash resource"
- **correct_approach**: What the correct approach is (max 200 chars). Extract from the correction message.
  - Example: "Use Ash resource with proper actions"
- **rule**: (Optional but recommended) The underlying rule or pattern that was violated/learned.
  - Example: "Always use domain layer abstractions in Elixir"
  - Can be omitted if not clear from context
- **ts**: ISO 8601 timestamp

### Implementation Strategy

The correction-detector needs access to conversation history. Implement it as a sliding window analysis:

```javascript
export const CorrectionDetectorPlugin = async ({ project, client, $, directory }) => {
  let recentMessages = []; // Keep last N messages
  let recentTools = [];    // Keep last N tool calls

  return {
    event: async ({ event, output, message, tool }) => {
      if (event.type !== 'message.updated') return;

      // Update sliding windows
      if (message) {
        recentMessages.push({
          role: message.role,
          content: message.content,
          timestamp: Date.now()
        });
        if (recentMessages.length > 10) recentMessages.shift();
      }

      if (tool) {
        recentTools.push({
          name: tool.name,
          params: tool.params,
          timestamp: Date.now()
        });
        if (recentTools.length > 5) recentTools.shift();
      }

      // Run detection patterns
      const detectedCorrection = detectCorrection(recentMessages, recentTools);

      if (detectedCorrection) {
        const reflectionEntry = formatReflection(detectedCorrection);
        writeToLog(reflectionEntry);
      }
    }
  };

  function detectCorrection(messages, tools) {
    if (messages.length < 2) return null;

    // Pattern 1: User correction
    const lastUserMsg = messages.filter(m => m.role === 'user').slice(-1)[0];
    const lastAssistantMsg = messages.filter(m => m.role === 'assistant').slice(-1)[0];

    if (lastUserMsg && lastAssistantMsg &&
        isUserCorrection(lastUserMsg.content) &&
        lastUserMsg.timestamp > lastAssistantMsg.timestamp) {
      return {
        trigger: 'user_correction',
        wrongMsg: lastAssistantMsg,
        correctMsg: lastUserMsg
      };
    }

    // Pattern 2: Model self-correction
    if (lastAssistantMsg && isModelSelfCorrection(lastAssistantMsg.content)) {
      return {
        trigger: 'self_correction',
        selfCorrectionMsg: lastAssistantMsg
      };
    }

    // Pattern 3: Tool retry
    if (isToolRetry(tools)) {
      return {
        trigger: 'tool_retry',
        tools: tools.slice(-2)
      };
    }

    return null;
  }

  function formatReflection(correction) {
    const context = extractContext(correction);
    const wrongApproach = extractWrongApproach(correction);
    const correctApproach = extractCorrectApproach(correction);
    const rule = inferRule(correction);

    return {
      type: 'reflection',
      trigger: correction.trigger,
      mode: getCurrentMode(),
      interaction: getCurrentInteraction(),
      context: context,
      wrong_approach: wrongApproach,
      correct_approach: correctApproach,
      rule: rule,
      ts: new Date().toISOString()
    };
  }
};
```

### Coordination with session-logger

**Two options:**

**Option A: Same JSONL File (Recommended)**
- Correction-detector writes reflection entries directly to the session JSONL
- Both plugins use the same log file path
- Reflections are interspersed with regular log entries

**Option B: Separate Reflections File**
- Correction-detector writes to `.opencode/logs/{session-id}.reflections.jsonl`
- A separate extract-corrections script reads both files
- More modular but requires coordination

**Recommendation**: Use Option A (same JSONL file). Simpler, and reflections are part of the session record.

**Implementation**: Both plugins can independently write to the same JSONL file. Append-write is atomic at the filesystem level.

```javascript
// In correction-detector
function writeReflection(reflectionEntry) {
  const logPath = path.join(directory, '.opencode', 'logs', `${getCurrentSessionId()}.jsonl`);
  try {
    fs.appendFileSync(logPath, JSON.stringify(reflectionEntry) + '\n', 'utf8');
  } catch (error) {
    // Silent failure
  }
}
```

### False Positive Management

To reduce false positives:

1. **Require confirmation**
   - User saying "No" in response to a yes/no question is NOT a correction
   - Only flag as correction if:
     - Negation/redirection + assistant message contains acknowledgment language ("I understand", "let me fix", "you're right")
     - Or explicit correction phrases ("instead", "what I meant")

2. **Context window**
   - Only consider corrections in the last 2 assistant messages
   - Ignore corrections to very old messages

3. **Manual review**
   - Write all detected reflections but mark uncertain ones with `confidence: "low"`
   - Data pipeline can filter low-confidence entries

### Implementation Checklist

- [ ] Hook into message.updated event
- [ ] Maintain sliding window of recent messages (last 10)
- [ ] Maintain sliding window of recent tool calls (last 5)
- [ ] Implement user correction language detection
- [ ] Implement model self-correction detection
- [ ] Implement tool retry pattern detection
- [ ] Implement script audit failure detection
- [ ] Format reflection entries with all required fields
- [ ] Write reflections to session JSONL (not separate file)
- [ ] Implement context extraction from messages
- [ ] Implement rule inference (optional but recommended)
- [ ] Test with manual corrections in build mode
- [ ] Verify low false-positive rate
- [ ] Test coordination with session-logger (both writing to same file)

---

## Plugin 4: compaction-hook.js

### Purpose

Injects domain-specific, Crux-aware instructions into the context compaction process. When OpenCode summarizes the conversation to free context space, this plugin ensures that critical task-specific information survives compaction so work can continue seamlessly.

### Hook Event

**`experimental.session.compacting`**

Fires right before the LLM generates a continuation summary to compress old context.

**Event Data:**
```javascript
{
  type: 'experimental.session.compacting',
  tokens: {
    current: 45000,      // Current token count
    threshold: 50000,    // Limit before compaction
    budget: 8000         // Available tokens for compaction summary
  },
  output: {
    context: [],         // Array of context entries to include
    prompt: null         // Default compaction prompt (can be replaced)
  }
}
```

### What Must Survive Compaction

1. **Active script names and paths**
   - If working on `.opencode/scripts/session/fix-auth.sh`, the compacted context must remember this
   - Include full path and purpose

2. **Current mode and task context**
   - Not just "mode: debug" but "debugging auth failure in user service"
   - Include what problem is being solved

3. **Project state snapshots**
   - Current git branch
   - Recently modified files
   - Pending operations (mid-refactor, etc.)

4. **Active handoff context**
   - If switched from `build-py` to `debug`, the reason must survive
   - "Switched to debug because user reported auth failures"

5. **Key decisions made this session**
   - Architectural choices ("Using Ecto instead of Ash for this service")
   - Rejected approaches ("Tried middleware-based auth, didn't work for this use case")
   - Why decisions were made

6. **Scripts created this session**
   - Names, paths, purposes
   - Enables referring to scripts post-compaction

### Implementation Approach

The hook receives the compaction context and can:

**Option 1: Push Additional Context Entries** (Recommended)
```javascript
output.context.push({
  role: 'system',
  content: `CRITICAL CONTEXT TO PRESERVE:
[structured critical info]`
});
```

**Option 2: Replace the Compaction Prompt**
```javascript
output.prompt = `You are compacting a session about [task].
CRITICAL: Preserve [specific requirements]
[custom summarization instructions]`;
```

**Recommendation**: Use Option 1 (push additional entries). Reasons:
- Doesn't replace the entire compaction logic
- Lets OpenCode's default compaction run
- Less fragile
- Easier to maintain

### Implementation

```javascript
export const CompactionHookPlugin = async ({ project, client, $, directory }) => {
  return {
    event: async ({ event, output }) => {
      if (event.type !== 'experimental.session.compacting') return;

      // Read checkpoint.json to get session state
      const checkpoint = readCheckpoint(directory);
      if (!checkpoint) return; // Silent failure

      // Inject critical context entries
      const criticalContext = generateCriticalContext(checkpoint, directory);
      output.context.push(criticalContext);
    }
  };

  function generateCriticalContext(checkpoint, directory) {
    const scriptsInfo = formatScriptsInfo(checkpoint.scripts_created);
    const mode = checkpoint.mode;
    const gitBranch = getGitBranch(directory);
    const recentFiles = getRecentlyModifiedFiles(directory);
    const keyDecisions = extractKeyDecisions(directory);
    const handoffContext = readHandoffContext(directory);

    return {
      role: 'system',
      content: `# CRITICAL CONTEXT TO PRESERVE THROUGH COMPACTION

## Active Task
- Mode: ${mode}
- Task: [Extract from conversation history or checkpoint]

## Scripts Created This Session
${scriptsInfo}

## Git State
- Branch: ${gitBranch}
- Recently modified:
  ${recentFiles.join('\n  ')}

## Key Decisions Made This Session
${keyDecisions.map(d => `- ${d}`).join('\n')}

## Handoff Context
${handoffContext || 'None'}

## PRESERVATION REQUIREMENT
This information is critical for continuing work after context compaction.
Do NOT summarize away: script paths, mode justification, decision rationale, or handoff reasons.
Preserve specific file paths and mode/task relationships.`
    };
  }

  function formatScriptsInfo(scripts) {
    if (!scripts || scripts.length === 0) return 'None';
    return scripts.map(script => {
      const purpose = extractScriptPurpose(script);
      return `- ${script}: ${purpose}`;
    }).join('\n');
  }

  function getGitBranch(directory) {
    try {
      const result = require('child_process').execSync('git rev-parse --abbrev-ref HEAD', {
        cwd: directory,
        encoding: 'utf8'
      });
      return result.trim();
    } catch {
      return 'unknown';
    }
  }

  function getRecentlyModifiedFiles(directory) {
    try {
      const result = require('child_process').execSync('git log --oneline -5 --name-only', {
        cwd: directory,
        encoding: 'utf8'
      });
      const files = result.split('\n').filter(f => f && !f.includes(' '));
      return [...new Set(files)].slice(0, 10); // Unique, max 10
    } catch {
      return [];
    }
  }

  function extractKeyDecisions(directory) {
    // Extract from session log via grep for "decision", "chose", "architect", etc.
    // For now, return placeholder
    return ['Placeholder: extract from session log'];
  }

  function readHandoffContext(directory) {
    // Check if a handoff-context.md file exists
    const handoffPath = path.join(directory, '.opencode', 'handoff-context.md');
    try {
      return fs.readFileSync(handoffPath, 'utf8').slice(0, 500); // First 500 chars
    } catch {
      return null;
    }
  }

  function readCheckpoint(directory) {
    const checkpointPath = path.join(directory, '.opencode', 'checkpoint.json');
    try {
      return JSON.parse(fs.readFileSync(checkpointPath, 'utf8'));
    } catch {
      return null;
    }
  }
};
```

### Shared State Mechanism

**Problem**: The compaction-hook needs data from other plugins (scripts from session-logger, mode from think-router, decisions from correction-detector).

**Solution: File-Based State via checkpoint.json**

All plugins read/write to the same `checkpoint.json` file:

```json
{
  "session": "2026-03-05-session-1",
  "last_interaction": 45,
  "scripts_created": [
    ".opencode/scripts/session/fix-auth.sh",
    ".opencode/scripts/session/update-config.sh"
  ],
  "mode": "build-py",
  "updated": "2026-03-05T14:33:22.500Z",
  "key_decisions": [
    "Using Ecto instead of Ash for user service",
    "Middleware-based auth rejected due to scope issues",
    "Decided to refactor auth service before adding features"
  ],
  "handoff_context": "Switched from build-py to debug due to user reports of auth failures",
  "git_branch": "feature/auth-refactor",
  "task_description": "Refactor authentication service to fix scope issues"
}
```

**Adding to checkpoint.json:**
- When a key decision is made (by user or inferred), add to `key_decisions` array
- When switching modes, set `handoff_context` with reason
- All plugins share this file as the source of truth

**Coordination Pattern:**
```javascript
function updateCheckpoint(directory, updates) {
  const checkpointPath = path.join(directory, '.opencode', 'checkpoint.json');
  try {
    let checkpoint = {};
    if (fs.existsSync(checkpointPath)) {
      checkpoint = JSON.parse(fs.readFileSync(checkpointPath, 'utf8'));
    }
    Object.assign(checkpoint, updates);
    checkpoint.updated = new Date().toISOString();
    fs.writeFileSync(checkpointPath, JSON.stringify(checkpoint, null, 2), 'utf8');
  } catch (error) {
    // Silent failure
  }
}
```

### Implementation Checklist

- [ ] Hook into experimental.session.compacting event
- [ ] Read checkpoint.json for session state
- [ ] Format scripts_created with purposes
- [ ] Extract git branch and recent files
- [ ] Extract key decisions from checkpoint
- [ ] Read handoff context if available
- [ ] Inject critical context entries into output.context
- [ ] Ensure context is human-readable and compaction-friendly
- [ ] Do NOT replace the entire compaction prompt (use Option 1)
- [ ] Test compaction with verbose output to verify preservation
- [ ] Verify that script paths survive compaction
- [ ] Verify that mode/task relationship is preserved
- [ ] Add logging for debugging compaction issues

---

## Plugin 5: token-budget.js

### Purpose

Enforces per-mode token discipline by:
1. Tracking tool output volume for each interaction sequence
2. Issuing warnings when approaching budgets
3. Hard-blocking write operations in read-only modes

This plugin prevents token waste in fast modes and prevents accidental writes in read-only modes.

### Hook Events

**`tool.execute.before`** (for read-only enforcement and pre-checks)
**`tool.execute.after`** (for token tracking)

### Mode Budget Classification

```javascript
const TIGHT_BUDGET = {
  modes: ['plan', 'review', 'strategist', 'legal', 'psych'],
  threshold: 2000,
  warningMessage: "⚠ Token budget approaching (2000 char threshold). Summarize findings before continuing exploration."
};

const STANDARD_BUDGET = {
  modes: ['ai-infra', 'writer', 'analyst', 'explain'],
  threshold: 4000,
  warningMessage: "⚠ Tool output accumulating. Consider summarizing before requesting more."
};

const GENEROUS_BUDGET = {
  modes: ['build-py', 'build-ex', 'debug', 'docker', 'mac'],
  threshold: 8000,
  warningMessage: "ℹ High tool output volume. Verify all retrieved content is necessary."
};
```

**Rationale:**
- **Tight (2000)**: Planning and review focus on quality over quantity. Extended exploration wastes tokens.
- **Standard (4000)**: Analytical and explanation modes need moderate tool output but shouldn't go overboard.
- **Generous (8000)**: Build and debug modes often need to explore multiple files/approaches. Higher tolerance.

### Read-Only Mode Enforcement

```javascript
const READ_ONLY_MODES = ['plan', 'review', 'explain'];
const WRITE_TOOLS = ['write', 'edit', 'bash'];  // bash can write (needs inspection)
```

#### Behavior for Read-Only Modes

**If mode in READ_ONLY_MODES and tool in WRITE_TOOLS:**

**For 'bash' tool:**
- Inspect the command
- Allow if command is read-only:
  - Starts with: `ls`, `cat`, `grep`, `find`, `git log`, `git status`, `git diff`, `head`, `tail`, `wc`, `stat`
  - Pattern: `^(ls|cat|grep|find|git\s+(?:log|status|diff)|head|tail|wc|stat)\b`
- Block if command contains write indicators:
  - Contains: `>`, `>>`, `rm`, `mv`, `cp`, `mkdir`, `chmod`, `sed -i`, `git commit`, `git push`, `git merge`, `git rebase`, `git reset`, `git clean`
  - Pattern: `(>|>>|rm\s|mv\s|cp\s|mkdir|chmod|git\s+(?:commit|push|merge|rebase|reset|clean)|sed\s+-i)`

**For 'write' and 'edit' tools:**
- Always block unconditionally

#### Error Response

```javascript
{
  error: true,
  message: `Tool '${toolName}' is not available in '${mode}' mode. Write operations are disabled in read-only modes. Switch to a build mode (build-py, build-ex, debug, docker, mac) to make file changes.`
}
```

### Token Tracking

**Tracking Mechanism:**

1. Maintain a running count of tool output characters for the current interaction sequence
2. On `tool.execute.after`, estimate output tokens:
   ```javascript
   const estimatedTokens = Math.ceil(toolOutput.length / 4); // Rough estimate: 4 chars per token
   ```
3. Add to running total
4. When total reaches 80% of threshold, inject warning into next tool result
5. When total exceeds 100% of threshold, inject stronger warning (but don't block)
6. Reset count when user sends new message (new interaction sequence starts)

**Implementation:**

```javascript
export const TokenBudgetPlugin = async ({ project, client, $, directory }) => {
  let tokenUsageThisInteraction = 0;
  let lastInteractionNumber = 0;

  const budgetMap = {
    'plan': TIGHT_BUDGET,
    'review': TIGHT_BUDGET,
    'strategist': TIGHT_BUDGET,
    'legal': TIGHT_BUDGET,
    'psych': TIGHT_BUDGET,
    'ai-infra': STANDARD_BUDGET,
    'writer': STANDARD_BUDGET,
    'analyst': STANDARD_BUDGET,
    'explain': STANDARD_BUDGET,
    'build-py': GENEROUS_BUDGET,
    'build-ex': GENEROUS_BUDGET,
    'debug': GENEROUS_BUDGET,
    'docker': GENEROUS_BUDGET,
    'mac': GENEROUS_BUDGET
  };

  return {
    event: async ({ event, output, tool }) => {
      const currentMode = getCurrentMode();
      const currentInteraction = getCurrentInteraction();

      // Reset counter on new interaction
      if (currentInteraction !== lastInteractionNumber) {
        tokenUsageThisInteraction = 0;
        lastInteractionNumber = currentInteraction;
      }

      // tool.execute.before: Enforce read-only constraints
      if (event.type === 'tool.execute.before') {
        if (READ_ONLY_MODES.includes(currentMode) && WRITE_TOOLS.includes(tool.name)) {
          // Check if bash command is actually read-only
          if (tool.name === 'bash') {
            if (isWriteCommand(tool.command)) {
              output.error = true;
              output.message = generateReadOnlyError(tool.name, currentMode);
              return;
            }
            // else: allow read-only bash command
          } else {
            // write or edit tool: always block
            output.error = true;
            output.message = generateReadOnlyError(tool.name, currentMode);
            return;
          }
        }
      }

      // tool.execute.after: Track token usage
      if (event.type === 'tool.execute.after') {
        const outputLength = (tool.output || '').length;
        const estimatedTokens = Math.ceil(outputLength / 4);
        tokenUsageThisInteraction += estimatedTokens;

        const budget = budgetMap[currentMode] || STANDARD_BUDGET;

        if (tokenUsageThisInteraction >= budget.threshold * 0.8) {
          // Inject warning into tool output
          if (!tool.output.includes('⚠')) { // Don't double-warn
            tool.output = budget.warningMessage + '\n\n' + (tool.output || '');
          }
        }

        if (tokenUsageThisInteraction >= budget.threshold * 1.2) {
          // Strong warning
          if (!tool.output.includes('STRONG WARNING')) {
            tool.output = '🛑 STRONG WARNING: Token budget significantly exceeded. Stop requesting tool output and summarize findings.\n\n' + tool.output;
          }
        }
      }
    }
  };

  function isWriteCommand(command) {
    const writeIndicators = /([>]{1,2}|\\brm\\s|\\bmv\\s|\\bcp\\s|\\bmkdir|chmod|git\\s+(?:commit|push|merge|rebase|reset|clean)|sed\\s+-i)/;
    return writeIndicators.test(command);
  }

  function generateReadOnlyError(toolName, mode) {
    return `Tool '${toolName}' is not available in '${mode}' mode. Write operations are disabled in read-only modes. Switch to a build mode (build-py, build-ex, debug, docker, mac) to make file changes.`;
  }
};
```

### Important Design Notes

#### Don't Block Based on Token Budget
Token budgets are **soft limits** — they warn and nag but **never block** tool execution.

**Reasoning:**
- A tool call may be in the middle of a multi-step operation
- Blocking could break the operation and force restart
- The model reads warnings and typically adjusts naturally
- If the model doesn't adjust, a hard block would just frustrate
- Warnings are sufficient incentive to limit token waste

#### Read-Only Enforcement is Hard
Read-only mode enforcement is a **hard block** because:
- Write operations in planning/review modes indicate a misunderstanding
- The user probably accidentally didn't switch modes
- Blocking prevents data corruption from accidental writes
- The error message guides the user to fix the mode

#### Token Estimation
The `outputLength / 4` estimate is rough but reasonable:
- Qwen tokenizer: ~1 token per 4 characters on average
- Some variability based on language/content
- For warnings, precision doesn't matter — rough estimate is fine

### Implementation Checklist

- [ ] Implement TIGHT_BUDGET, STANDARD_BUDGET, GENEROUS_BUDGET constants
- [ ] Create budgetMap for mode → budget mapping
- [ ] Hook into tool.execute.before for read-only enforcement
- [ ] Implement isWriteCommand() to detect write-intent bash commands
- [ ] Allow read-only bash in read-only modes
- [ ] Block write/edit tools in read-only modes
- [ ] Hook into tool.execute.after for token tracking
- [ ] Maintain tokenUsageThisInteraction counter
- [ ] Reset counter on new interaction (compare interaction numbers)
- [ ] Estimate output tokens (outputLength / 4)
- [ ] Inject warning at 80% threshold
- [ ] Inject strong warning at 120% threshold
- [ ] Test read-only enforcement with read commands (should pass)
- [ ] Test read-only enforcement with write commands (should block)
- [ ] Test token budget warnings in different modes
- [ ] Verify that warnings are non-blocking (tools execute but show message)

---

## Shared State & Coordination

### Checkpoint.json as Shared Source of Truth

All plugins use `{project}/.opencode/checkpoint.json` as the central coordination point:

```json
{
  "session": "2026-03-05-session-1",
  "last_interaction": 45,
  "scripts_created": [
    ".opencode/scripts/session/fix-auth.sh",
    ".opencode/scripts/session/update-config.sh"
  ],
  "mode": "build-py",
  "updated": "2026-03-05T14:33:22.500Z",
  "key_decisions": [
    "Use Ecto instead of Ash for user service",
    "Rejected middleware auth due to scope issues"
  ],
  "handoff_context": "Switched to debug due to user auth failure report",
  "git_branch": "feature/auth-refactor",
  "task_description": "Refactor authentication service"
}
```

### Plugin Responsibilities

| Plugin | Reads From Checkpoint | Writes To Checkpoint |
|--------|----------------------|----------------------|
| session-logger | scripts_created, mode | All fields (every 5 interactions) |
| think-router | mode | - (read-only) |
| correction-detector | - (reads from logs) | key_decisions (optional) |
| compaction-hook | scripts_created, mode, key_decisions, handoff_context, task_description | - (read-only) |
| token-budget | mode | - (read-only) |

### Safe Concurrent Write Pattern

Multiple plugins may write to checkpoint.json simultaneously. Use atomic writes:

```javascript
function safeUpdateCheckpoint(directory, updates) {
  const checkpointPath = path.join(directory, '.opencode', 'checkpoint.json');
  try {
    let checkpoint = {};
    if (fs.existsSync(checkpointPath)) {
      checkpoint = JSON.parse(fs.readFileSync(checkpointPath, 'utf8'));
    }

    // Merge updates
    Object.assign(checkpoint, updates);
    checkpoint.updated = new Date().toISOString();

    // Write atomically (single write operation)
    fs.writeFileSync(checkpointPath, JSON.stringify(checkpoint, null, 2), 'utf8');
  } catch (error) {
    // Silent failure
  }
}
```

**Why this works:**
- Single `writeFileSync()` call is atomic at the OS level
- Even if two plugins call this simultaneously, one blocks, then the other reads the updated file
- No corruption due to interleaving

---

## Testing & Validation

### Unit Test Framework

For each plugin, write tests that verify:

1. **Hook firing**: Verify hook is called with correct parameters
2. **Data format**: Verify output matches specified structures
3. **Edge cases**: Empty input, malformed data, missing fields
4. **Error handling**: Silent failures, no crashes

### Integration Tests

1. **Multi-plugin coordination**
   - Start session, create scripts (session-logger)
   - Verify checkpoint.json is updated (session-logger)
   - Verify compaction-hook can read checkpoint.json (compaction-hook)

2. **Crash recovery**
   - Create session, log some interactions
   - Terminate process (kill -9)
   - Start new session, verify crash recovery detected
   - Verify resume-context.md was created

3. **Token budget enforcement**
   - Set mode to 'review' (read-only)
   - Attempt write tool → should block
   - Switch to 'build-py' → write tool should pass

4. **Correction detection**
   - Generate conversation with user correction
   - Verify reflection entry is written to JSONL
   - Verify fields are populated correctly

### Manual Testing Checklist

- [ ] Create a session, log multiple interactions, verify JSONL format is valid
- [ ] Manually kill the process mid-session, restart, verify crash recovery
- [ ] Test mode switching and verify think-router prepends correct directive
- [ ] Manually make a correction ("actually, let me try...") and verify reflection entry
- [ ] Monitor token usage in a build mode, verify warnings appear
- [ ] Switch to review mode, attempt to write a file, verify blocked
- [ ] Read git log in review mode, verify allowed
- [ ] Trigger context compaction (if possible), verify critical info is preserved
- [ ] Inspect checkpoint.json, verify all fields are populated
- [ ] Verify no plugin crashes break the session

### Debugging Helpers

Add debug logging (optional, disabled by default):

```javascript
function log(message) {
  if (process.env.OPENCODE_DEBUG) {
    console.error(`[plugin-name] ${message}`);
  }
}
```

Enable with: `export OPENCODE_DEBUG=1`

---

## Summary

This document specifies all 5 Crux plugins with:
- Complete hook event specifications
- Exact data structure formats
- Detailed algorithm descriptions
- Design reasoning for every choice
- Implementation patterns and best practices
- Coordination mechanisms between plugins
- Testing and validation strategies

A developer with no prior context can implement each plugin by following these specs. The plugins work together via shared checkpoint.json to provide crash recovery, continuous learning, token discipline, and intelligent context preservation.

---

**Document Version:** 1.0
**Last Updated:** 2026-03-05
**Status:** Ready for Implementation
