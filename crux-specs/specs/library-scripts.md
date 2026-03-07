# OpenCode Library Scripts Specification

## Overview

Library scripts are reusable bash scripts stored in `.opencode/scripts/lib/` (project) or `~/.config/opencode/scripts/lib/` (user/global). They are long-lived, stable, and invoked by custom tools or other scripts.

All library scripts follow the standard template and must support the five-gate safety pipeline (preflight validation, auditing, dry-run).

## Standard Script Template

All library scripts must follow this structure:

```bash
#!/usr/bin/env bash
# ────────────────────────────────
# Name:        script-name
# Risk:        low | medium | high
# Created:     YYYY-MM-DD
# Status:      promoted | archived | deprecated
# Description: What this script does in one sentence
# ────────────────────────────────
set -euo pipefail
DRY_RUN="${DRY_RUN:-false}"

# Main script body here
```

Key requirements:
- First line: `#!/usr/bin/env bash`
- Header block with required fields (verified by Gate 1 preflight)
- `set -euo pipefail` for safety
- `DRY_RUN` environment variable support for medium/high risk scripts
- Clear comments explaining logic
- No external dependencies beyond standard Unix tools (or document them)

---

## Script 1: preflight-validator.sh

### Purpose

Deterministic pre-flight validation for scripts before execution. Implements Gate 1 of the five-gate pipeline. Invoked by `run_script.js` tool.

### Usage

```bash
./preflight-validator.sh /path/to/script.sh
```

### Exit Codes

- `0` — Script passes all checks, output "PASS"
- `1` — Script fails a check, output error message with specific reason

### Validation Checks (in order, exit on first failure)

#### Check 1: Header Compliance

**What to verify:**
- Line 1 is `#!/usr/bin/env bash`
- Header block (lines 2-8, starting with `#`) contains:
  - `# Name: {name}`
  - `# Risk: {low|medium|high}`
  - `# Created: {YYYY-MM-DD}` (date format)
  - `# Status: {promoted|archived|deprecated}`
  - `# Description: {description}` (non-empty)

**Exit on failure:**
```
Error: Missing required header field: Description
```

**Logic:**
```bash
# Extract header lines
header=$(sed -n '2,10p' "$script_path" | grep '^#')

# Check for each required field
for field in "Name" "Risk" "Created" "Status" "Description"; do
  if ! echo "$header" | grep -q "# $field:"; then
    echo "Error: Missing required header field: $field"
    exit 1
  fi
done
```

#### Check 2: Safety Pragma

**What to verify:**
- Script contains `set -euo pipefail` or at minimum `set -e`

**Exit on failure:**
```
Error: Missing safety pragma: set -euo pipefail
```

**Logic:**
```bash
if ! grep -q "set -euo pipefail" "$script_path"; then
  if ! grep -q "^set -e" "$script_path"; then
    echo "Error: Missing safety pragma: set -euo pipefail"
    exit 1
  fi
fi
```

#### Check 3: Risk-Behavior Consistency

**What to verify:**

If script header declares Risk as "low":
- Script must NOT contain destructive patterns:
  - `rm ` (unless followed by `-i`, e.g., `rm -i`)
  - `rmdir`
  - `unlink`
  - `DROP ` (SQL)
  - `DELETE FROM` (SQL)
  - `TRUNCATE` (SQL)
  - `docker down` or `docker rm` or `docker rmi` or `docker system prune`
  - `git push --force` or `git reset --hard`
  - Write redirects (`> /path`) to paths outside project (but allow `> ./` and `> $PROJECT_DIR/`)
  - `chmod`, `chown` on other users' files

If script declares Risk as "medium" or "high":
- Script body must reference `DRY_RUN` variable at least once
- This ensures the script supports dry-run validation

**Exit on failure:**

For "low" risk with destructive ops:
```
Error: Risk classification mismatch: script marked 'low' but contains destructive operations. Reclassify as medium or high.
```

For "medium"/"high" without DRY_RUN:
```
Error: Medium/high risk scripts must support DRY_RUN mode.
```

**Logic:**

```bash
# Extract risk level from header
risk=$(grep '^# Risk:' "$script_path" | sed 's/.*Risk: //')

if [ "$risk" = "low" ]; then
  # Check for destructive patterns
  destructive_patterns=(
    "rm [^-]"  # rm without -i flag
    "rmdir"
    "unlink"
    "DROP "
    "DELETE FROM"
    "TRUNCATE"
    "docker down"
    "docker rm"
    "git push"
    "git reset --hard"
    "chmod"
    "chown"
  )

  for pattern in "${destructive_patterns[@]}"; do
    if grep -E "$pattern" "$script_path" > /dev/null 2>&1; then
      echo "Error: Risk classification mismatch: script marked 'low' but contains destructive operations. Reclassify as medium or high."
      exit 1
    fi
  done
elif [ "$risk" = "medium" ] || [ "$risk" = "high" ]; then
  if ! grep -q "DRY_RUN" "$script_path"; then
    echo "Error: Medium/high risk scripts must support DRY_RUN mode."
    exit 1
  fi
fi
```

#### Check 4: Path Containment

**What to verify:**
- All write operations stay within project directory or `.opencode/scripts/`
- No writes escape to system directories or user home (except `.opencode/` and `.config/opencode/`)

**Pattern detection:**
- `> path` — output redirection
- `>> path` — append redirection
- `tee path` — write via tee
- `mv src dest` — move
- `cp src dest` — copy (dest is target)
- `mkdir path` — create directory
- `rm path` — remove (path is target)

**Exit on failure:**
```
Error: Path containment violation: script writes to /etc/app.conf which is outside project scope.
```

**Logic:**

```bash
# Find all write targets
write_patterns=(
  '\s>\s+\([^>]\)'     # > redirection
  '\s>>\s+\([^>]\)'    # >> redirection
  'tee\s+\S+'          # tee command
  'cp\s+\S+\s+\S+\s*$' # cp destination
  'mv\s+\S+\s+\S+\s*$' # mv destination
)

# Extract paths from write operations
paths=$(grep -oE '(>|>>|tee|cp|mv|mkdir|rm)\s+[^$\s]+' "$script_path" | awk '{print $NF}')

for path in $paths; do
  # Remove trailing symbols
  path="${path%[;&|]}"

  # Skip variables
  [[ "$path" == \$* ]] && continue

  # Check if path is absolute and outside project
  if [[ "$path" == /* ]]; then
    if [[ ! "$path" == "$PROJECT_DIR"/* ]] && \
       [[ ! "$path" == "$HOME/.opencode/"* ]] && \
       [[ ! "$path" == "$HOME/.config/opencode/"* ]]; then
      echo "Error: Path containment violation: script writes to $path which is outside project scope."
      exit 1
    fi
  fi
done
```

#### Check 5: Multi-File Write Detection

**What to verify:**
- If script writes to multiple unrelated files, it should be refactored into a transaction script with discrete steps

**Definition:**
- Count unique write target directories
- If 2+ directories are targeted and they don't share a common parent, it's a multi-file change
- Exception: if one file imports/sources the other (script1.sh is sourced by script2.sh), they're related

**Exit on failure:**
```
Error: Multi-file coordinated change detected. Refactor into a transaction script with discrete steps and rollback handlers.
```

**Logic:**

```bash
# Extract all write target directories
write_dirs=$(grep -oE '(>|>>|tee|cp|mv|mkdir)\s+[^$\s]+' "$script_path" \
  | awk '{print $NF}' \
  | sed 's|/[^/]*$||' \
  | sort -u)

# Count unique directories
dir_count=$(echo "$write_dirs" | wc -l)

if [ "$dir_count" -gt 2 ]; then
  # Check if any files reference each other
  files=$(grep -oE '(>|>>|tee|cp|mv|mkdir)\s+[^$\s]+' "$script_path" \
    | awk '{print $NF}')

  any_sourced=false
  for file in $files; do
    if grep -q "$(basename "$file")" "$script_path"; then
      any_sourced=true
    fi
  done

  if [ "$any_sourced" = false ]; then
    echo "Error: Multi-file coordinated change detected. Refactor into a transaction script with discrete steps and rollback handlers."
    exit 1
  fi
fi
```

#### Check 6: Transaction Script Template Compliance

**What to verify:**
- If script calls/sources other scripts (contains `bash ` or `source ` followed by a script path), verify it has rollback logic

**Exit on failure:**
```
Error: Transaction script missing rollback handlers.
```

**Logic:**

```bash
# Check if script sources or calls other scripts
if grep -qE '(bash|source)\s+' "$script_path"; then
  # Verify rollback logic exists
  if ! grep -qE '(rollback|trap)' "$script_path"; then
    echo "Error: Transaction script missing rollback handlers."
    exit 1
  fi
fi
```

### Output

On success:
```
PASS
```

On failure:
```
Error: {specific reason}
```

The custom tool `run_script.js` parses this output. Exit code is the ultimate signal.

---

## Script 2: extract-corrections.sh

### Purpose

Scan session JSONL logs for correction patterns, cluster them by topic, generate knowledge entry drafts, and identify promotion candidates for the daily digest.

### Usage

```bash
./extract-corrections.sh /path/to/project
```

### Input

Reads all JSONL files from `.opencode/logs/`:
- Filters for entries with `type: "reflection"`
- Each reflection has: `mode`, `wrong_approach`, `correct_approach`, `timestamp`
- Compares against `.opencode/knowledge/_processed_reflections.json` to avoid reprocessing

### Step 1: Find Unprocessed Reflections

```bash
# Read all JSONL files
for log_file in "$PROJECT/.opencode/logs"/*.jsonl; do
  jq -r 'select(.type == "reflection") | @json' "$log_file"
done > /tmp/reflections.jsonl

# Read processed IDs
processed=$(jq -r '.processed_ids[]' "$PROJECT/.opencode/knowledge/_processed_reflections.json" 2>/dev/null || echo "")

# Filter unprocessed
jq --arg processed "$processed" \
  'select(.id | IN($processed) | not)' /tmp/reflections.jsonl > /tmp/unprocessed.jsonl
```

Count: `wc -l /tmp/unprocessed.jsonl`

### Step 2: Cluster by Topic

**Algorithm:**

1. Group reflections by mode
2. For each mode, group by similarity:
   - Extract key words from `wrong_approach` and `correct_approach` fields
   - Remove stop words (the, a, is, to, etc.)
   - If two reflections share 3+ key words, they belong in the same cluster
3. Identify clusters with 3+ reflections (promotion candidates)

**Implementation:**

```bash
# Simple similarity: count common words
cluster_id=0
declare -A clusters

while IFS= read -r reflection; do
  mode=$(echo "$reflection" | jq -r '.mode')
  wrong=$(echo "$reflection" | jq -r '.wrong_approach' | tr ' ' '\n' | grep -v -E '^(the|a|is|to|in|it|for|and|or)$')
  correct=$(echo "$reflection" | jq -r '.correct_approach' | tr ' ' '\n' | grep -v -E '^(the|a|is|to|in|it|for|and|or)$')

  # For simplicity: hash the first 3 words as cluster key
  cluster_key="$mode:$(echo "$wrong" | head -3 | tr '\n' '-')"

  if [ -z "${clusters[$cluster_key]}" ]; then
    clusters[$cluster_key]=1
  else
    clusters[$cluster_key]=$((${clusters[$cluster_key]} + 1))
  fi
done < /tmp/unprocessed.jsonl

# Filter clusters with 3+ reflections
for cluster_key in "${!clusters[@]}"; do
  if [ "${clusters[$cluster_key]}" -ge 3 ]; then
    echo "$cluster_key"
  fi
done
```

### Step 3: Generate Knowledge Entry Drafts

For each cluster with 3+ reflections:

1. Extract mode and topic
2. Create file: `.opencode/knowledge/{mode}/draft-{topic}.md`
3. Fill with template:

```markdown
---
provenance: auto-generated from corrections
source_sessions: [{session1}, {session2}, ...]
correction_count: {N}
confidence: {high|medium}
status: draft
---

# {Topic}

## Pattern

{Synthesized rule}

## Evidence

- Correction 1: {wrong} → {correct}
- Correction 2: {wrong} → {correct}
- ...
```

**Synthesized rule generation:**

- If Ollama is running, send all raw corrections to qwen3:8b with prompt:
  ```
  You are a knowledge engineer. Given these correction patterns, synthesize one clear rule or principle that explains all of them. Be concise (1-2 sentences).

  Patterns:
  {list of wrong → correct pairs}
  ```
- If Ollama is unavailable, write raw corrections without synthesis and flag for later processing

**Confidence level:**
- `high` if 5+ reflections in cluster
- `medium` if 3-4 reflections

### Step 4: Update Processed Tracker

Append processed reflection IDs to `.opencode/knowledge/_processed_reflections.json`:

```json
{
  "last_updated": "2026-03-05T14:23:45Z",
  "processed_ids": ["id1", "id2", "id3"]
}
```

### Step 5: Flag Promotion Candidates

Append to `~/.config/opencode/knowledge/_candidates.md`:

```markdown
- [build-ex] Error Handling Pattern — 5 corrections, confidence: high — review with /review-knowledge
- [build-py] Type Annotations — 3 corrections, confidence: medium — review with /review-knowledge
```

### Output

The script logs its work:
```
Processed 12 unprocessed reflections
Found 3 clusters with 3+ corrections
Generated drafts:
  - build-ex/draft-error-handling.md
  - build-py/draft-type-annotations.md
Updated _processed_reflections.json with 12 IDs
Appended 2 candidates to _candidates.md
```

---

## Script 3: update-project-context.sh

### Purpose

Regenerate PROJECT.md from current directory state and recent session activity. Pure scripted logic — no LLM inference.

### Usage

```bash
./update-project-context.sh /path/to/project
```

### Output File

Writes to `.opencode/PROJECT.md`

### Generated Content

#### Section: Header

```markdown
# Project Context
Generated: {YYYY-MM-DD HH:MM}
Last session: {session-id}
```

#### Section: Tech Stack

**Auto-detection logic:**

```bash
# Check for language/framework indicators
tech=()

[ -f "mix.exs" ] && tech+=("Elixir")
[ -f "pyproject.toml" ] && tech+=("Python")
[ -f "package.json" ] && tech+=("Node.js")
[ -f "Cargo.toml" ] && tech+=("Rust")
[ -f "pom.xml" ] && tech+=("Java")

[ -f "Dockerfile" ] && tech+=("Docker")
[ -f "docker-compose.yml" ] && tech+=("Docker Compose")
[ -d ".github/workflows/" ] && tech+=("GitHub Actions")

# Framework detection
[ -f "mix.exs" ] && grep -q "{:phoenix" "mix.exs" && tech+=("Phoenix")
[ -f "mix.exs" ] && grep -q "{:ash" "mix.exs" && tech+=("Ash Framework")

[ -f "package.json" ] && grep -q '"react"' "package.json" && tech+=("React")
[ -f "package.json" ] && grep -q '"next"' "package.json" && tech+=("Next.js")

echo "## Tech Stack"
echo "$(IFS=, ; echo "${tech[*]}")"
```

Extract version info from config files:
- From `mix.exs`: Elixir version comment
- From `pyproject.toml`: `python = "^X.Y"`
- From `package.json`: `node`: version constraint

#### Section: Directory Structure

```bash
echo "## Directory Structure"
tree -L 3 -I 'node_modules|_build|dist|.git|__pycache__|.next' "$PROJECT" | head -50
echo "[... tree truncated to 50 lines]"
```

#### Section: Key Files

**Hot files detection:**

```bash
# Read recent session logs
for log_file in "$PROJECT/.opencode/logs"/*.jsonl; do
  # Extract file paths from tool calls
  jq -r '.file_path // .script_path // empty' "$log_file"
done | sort | uniq -c | sort -rn | head -10 > /tmp/hot_files.txt
```

Format:
```markdown
## Key Files

Files modified most frequently in recent sessions:

- lib/app_web/router.ex — 12 modifications
- lib/app.ex — 8 modifications
- config/config.exs — 6 modifications
- lib/app_web/components/layout.ex — 5 modifications
```

#### Section: Active Context

```bash
echo "## Active Context"
echo ""
echo "Current branch: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo ""
echo "Recent commits:"
git log --oneline -3 2>/dev/null | sed 's/^/  /'
echo ""
echo "Hot files (last 3 sessions):"
tail -3 /tmp/hot_files.txt | sed 's/^/  /'
```

#### Section: Conventions

Extract from existing config files:

```bash
echo "## Conventions"

# From .formatter.exs (Elixir)
if [ -f ".formatter.exs" ]; then
  echo "### Code Formatting"
  echo "- Line length: $(grep -oP 'line_length: \K\d+' .formatter.exs || echo 'default')"
fi

# From .credo.exs (Elixir)
if [ -f ".credo.exs" ]; then
  echo "### Linting Rules"
  grep -oP 'disabled.*?\K[\[\{].*[\]\}]' .credo.exs | head -5
fi

# From .eslintrc.json or .eslintrc.js
if [ -f ".eslintrc.json" ] || [ -f ".eslintrc.js" ]; then
  echo "### JavaScript Linting"
  echo "- Config present"
fi

# From pyproject.toml (Python)
if [ -f "pyproject.toml" ]; then
  if grep -q "\[tool.black\]" pyproject.toml; then
    echo "### Python Formatting"
    echo "- Black formatter configured"
  fi
fi
```

### Final Structure

```markdown
# Project Context
Generated: 2026-03-05 14:25
Last session: abc123def456

## Tech Stack
Elixir 1.14, Phoenix 1.7, Ash Framework 2.x
Database: PostgreSQL 15

## Directory Structure
project/
├── config/
│   ├── config.exs
│   ├── dev.exs
│   └── test.exs
├── lib/
│   ├── app.ex
│   ├── app_web/
│   │   ├── components/
│   │   ├── controllers/
│   │   └── router.ex
├── priv/
├── test/
└── mix.exs

## Key Files
- lib/app_web/router.ex — 12 modifications
- lib/app.ex — 8 modifications
- config/config.exs — 6 modifications

## Active Context
Current branch: main
Recent commits:
  abc1234 Add user authentication
  def5678 Fix login flow bug
  ghi9012 Refactor components

## Conventions
- Line length: 120
- Code formatter: Black (Python)
- Linting: Credo with custom disabled rules
```

### Size Constraint

- Target: 200-400 tokens
- If exceeding 500 tokens, truncate directory tree and reduce recent commits to 2
- Log warning if content is truncated

### Session Logging

```json
{
  "type": "project_context_update",
  "content_tokens": 280,
  "sections_updated": ["tech_stack", "directory", "key_files", "active_context", "conventions"],
  "timestamp": "ISO8601"
}
```

---

## Script 4: promote-knowledge.sh

### Purpose

Promote knowledge entries across scope levels: project → user → public staging. Includes privacy checking and evidence merging.

### Usage

```bash
./promote-knowledge.sh --from project --to user --entry path/to/entry.md
./promote-knowledge.sh --from user --to public --entry path/to/entry.md
```

### Parameters

- `--from` — source scope: project, user
- `--to` — destination scope: user, public
- `--entry` — relative path to entry file (e.g., `build-ex/error-handling.md`)

### Step 1: Validate Parameters

```bash
# Check required flags
[ -z "$FROM" ] || [ -z "$TO" ] || [ -z "$ENTRY" ] && {
  echo "Usage: promote-knowledge.sh --from {project|user} --to {user|public} --entry path/to/entry.md"
  exit 1
}

# Check entry exists in source
source_dir=$([ "$FROM" = "project" ] && echo "$PROJECT/.opencode/knowledge" || echo "$HOME/.config/opencode/knowledge")
[ ! -f "$source_dir/$ENTRY" ] && {
  echo "Error: Entry not found at $source_dir/$ENTRY"
  exit 1
}
```

### Step 2: Project → User Promotion

```bash
# Read source entry
entry_content=$(<"$PROJECT/.opencode/knowledge/$ENTRY")

# Strip project-specific references
# - Replace $PROJECT_DIR with {project_root}
# - Replace absolute paths with relative paths where possible
# - Remove project-specific variable names and local paths
entry_content=$(echo "$entry_content" | sed "s|$PROJECT|\{project_root\}|g")
entry_content=$(echo "$entry_content" | sed "s|$HOME|\{home\}|g")

# Update YAML front matter: add promotion note and date
promoted_entry="---
$(echo "$entry_content" | grep '^provenance:' | sed "s/.*/provenance: promoted from project $(date +%Y-%m-%d)/")"
promoted_entry+=$'\n'
promoted_entry+="$(echo "$entry_content" | grep -v '^provenance:' | grep '^---' -A 999)"

# Check if entry already exists at user level
user_dir="$HOME/.config/opencode/knowledge"
if [ -f "$user_dir/$ENTRY" ]; then
  # Merge: append new evidence sections
  existing=$(cat "$user_dir/$ENTRY")

  # Extract evidence sections
  new_evidence=$(echo "$promoted_entry" | sed -n '/^## Evidence/,/^##/p')

  # Append to existing evidence
  merged=$(echo "$existing" | sed -n '/^## Evidence/,$p')

  # Write merged version
  echo "$promoted_entry" > "$user_dir/$ENTRY"
else
  # Copy new entry
  mkdir -p "$(dirname "$user_dir/$ENTRY")"
  echo "$promoted_entry" > "$user_dir/$ENTRY"
fi
```

### Step 3: User → Public Promotion

```bash
# Read source entry
entry_content=$(<"$HOME/.config/opencode/knowledge/$ENTRY")

# Privacy check: scan for sensitive data
sensitive_patterns=(
  "^/Users/"              # Absolute path
  "^/home/"               # Absolute path
  "@[a-z0-9.-]+\.[a-z]+" # Email addresses
  "[a-zA-Z0-9]{40}"       # SHA1 hashes (potential credentials)
  "sk-[a-zA-Z0-9]"        # OpenAI API keys
)

privacy_violations=()
for pattern in "${sensitive_patterns[@]}"; do
  if grep -E "$pattern" "$HOME/.config/opencode/knowledge/$ENTRY" > /dev/null; then
    privacy_violations+=("Pattern '$pattern' found")
  fi
done

if [ ${#privacy_violations[@]} -gt 0 ]; then
  echo "Error: Privacy check failed:"
  printf '%s\n' "${privacy_violations[@]}"
  echo "Remove or redact sensitive data before promoting to public."
  exit 1
fi

# Copy to staging directory
public_dir="$HOME/.config/opencode/community/outbound"
mkdir -p "$(dirname "$public_dir/$ENTRY")"
cp "$HOME/.config/opencode/knowledge/$ENTRY" "$public_dir/$ENTRY"

# Log promotion for later git commit
echo "$ENTRY — promoted to public staging" >> "$HOME/.config/opencode/community/outbound/.promotion_log"
```

### Step 4: Git Commit

```bash
# For user-level promotion (project scope)
cd "$PROJECT"
git add "$PROJECT/.opencode/knowledge/$ENTRY"
git commit -m "Promote knowledge: $ENTRY from project to user scope" 2>/dev/null || true

# For public promotion
git -C "$HOME/.config/opencode" add "community/outbound/$ENTRY" .promotion_log
git -C "$HOME/.config/opencode" commit -m "Stage knowledge for public repo: $ENTRY" 2>/dev/null || true
```

### Output

```
Promoted $ENTRY from project to user scope
New location: ~/.config/opencode/knowledge/$ENTRY
Stripped: 3 project-specific references
Git commit: [hash]
```

Or on merge:
```
Merged $ENTRY with existing user-level entry
Updated evidence: +5 new entries
Merged location: ~/.config/opencode/knowledge/$ENTRY
```

---

## Script 5: generate-digest.sh

### Purpose

Aggregate analytics into a daily digest shown at session startup. Identifies patterns, correction rates, knowledge gaps, and actionable recommendations.

### Usage

```bash
./generate-digest.sh
```

Reads from: `~/.config/opencode/analytics/` and project-level logs

Writes to: `~/.config/opencode/analytics/digest.md`

### Step 1: Mode Usage Distribution

```bash
# Read last 24 hours of logs across all projects
all_logs=$(find ~/.opencode/logs ~/.config/opencode/logs -name "*.jsonl" -mtime -1 2>/dev/null | xargs cat)

# Count interactions per mode
echo "## Mode Usage (Last 24 Hours)" >> "$DIGEST"
echo "" >> "$DIGEST"

echo "$all_logs" | jq -r '.mode // empty' | sort | uniq -c | sort -rn | while read count mode; do
  echo "- $mode: $count interactions" >> "$DIGEST"
done

# Flag idle modes (no usage in 30 days)
echo "" >> "$DIGEST"
echo "⚠️ Idle modes (no activity in 30 days):" >> "$DIGEST"
find ~/.opencode/logs -name "*.jsonl" -mtime +30 | xargs -I {} basename {} | sed 's/-.*//' | sort -u | while read mode; do
  echo "  - $mode" >> "$DIGEST"
done
```

### Step 2: Correction Rates by Mode

```bash
echo "## Correction Rates by Mode" >> "$DIGEST"
echo "" >> "$DIGEST"

# Count reflections in last 24 hours
recent_logs=$(find ~/.opencode/logs ~/.config/opencode/logs -name "*.jsonl" -mtime -1 2>/dev/null | xargs cat)

echo "$recent_logs" | jq -r '.mode // empty' | sort -u | while read mode; do
  total_interactions=$(echo "$recent_logs" | jq "select(.mode == \"$mode\")" | wc -l)
  corrections=$(echo "$recent_logs" | jq "select(.mode == \"$mode\" and .type == \"reflection\")" | wc -l)

  if [ "$total_interactions" -gt 0 ]; then
    rate=$(echo "scale=1; $corrections * 100 / $total_interactions" | bc)
    echo "- $mode: $rate% correction rate ($corrections / $total_interactions)" >> "$DIGEST"
  fi
done
```

Compare to 7-day rolling average:
```bash
# Calculate 7-day average for comparison
seven_day_logs=$(find ~/.opencode/logs ~/.config/opencode/logs -name "*.jsonl" -mtime -7 2>/dev/null | xargs cat)

echo "  (7-day avg: X%, trend: ↑↓→)" >> "$DIGEST"
```

### Step 3: Tool Tier Usage

```bash
echo "## Tool Usage by Tier" >> "$DIGEST"
echo "" >> "$DIGEST"

# Extract tool calls from recent logs
echo "$all_logs" | jq -r '.tool_name // .command // empty' | sort | uniq -c | sort -rn | head -10 | \
  while read count tool; do
    echo "- $tool: $count calls" >> "$DIGEST"
  done

# Flag high Tier 5 usage (bash commands)
tier5_count=$(echo "$all_logs" | jq "select(.tier == 5 or .type == \"bash_execution\")" | wc -l)
if [ "$tier5_count" -gt 20 ]; then
  echo "" >> "$DIGEST"
  echo "⚠️ High Tier 5 usage detected: $tier5_count bash commands" >> "$DIGEST"
  echo "Consider promoting repeated patterns to reusable tools." >> "$DIGEST"

  # Identify bash patterns that repeat 3+ times
  echo "" >> "$DIGEST"
  echo "Bash patterns (3+ occurrences):" >> "$DIGEST"
  echo "$all_logs" | jq -r '.command // empty' | sort | uniq -c | sort -rn | awk '$1 >= 3' | \
    while read count cmd; do
      echo "  - (used $count times) $cmd" >> "$DIGEST"
    done
fi
```

### Step 4: Knowledge Promotion Candidates

```bash
echo "## Knowledge Promotion Candidates" >> "$DIGEST"
echo "" >> "$DIGEST"

if [ -f "$HOME/.config/opencode/knowledge/_candidates.md" ]; then
  candidate_count=$(wc -l < "$HOME/.config/opencode/knowledge/_candidates.md")
  echo "$candidate_count pending candidates ready for review:" >> "$DIGEST"
  echo "" >> "$DIGEST"
  cat "$HOME/.config/opencode/knowledge/_candidates.md" >> "$DIGEST"
else
  echo "No pending candidates" >> "$DIGEST"
fi
```

### Step 5: Escalated Items

```bash
echo "## Escalated Items (3+ consecutive digests)" >> "$DIGEST"
echo "" >> "$DIGEST"

if [ -f "$HOME/.config/opencode/analytics/escalations.json" ]; then
  jq -r '.recurring[]? | "\(.item) — \(.consecutive_days) days, cost: \(.cost_tokens) tokens"' \
    "$HOME/.config/opencode/analytics/escalations.json" >> "$DIGEST"
else
  echo "No escalated items" >> "$DIGEST"
fi
```

### Step 6: Actionable Recommendations

Generate concrete action items based on the above data:

```bash
echo "## Actionable Recommendations" >> "$DIGEST"
echo "" >> "$DIGEST"

# Recommendation 1: bash pattern promotion
echo "🛠️ Tool Promotion Opportunities:" >> "$DIGEST"
bash_patterns=$(echo "$all_logs" | jq -r '.command // empty' | sort | uniq -c | awk '$1 >= 3' | wc -l)
if [ "$bash_patterns" -gt 0 ]; then
  echo "- $bash_patterns bash patterns ready for tool promotion" >> "$DIGEST"
fi

# Recommendation 2: correction rate spike
echo "- Review modes with correction rate increase >30%" >> "$DIGEST"

# Recommendation 3: idle modes
echo "- Consider archiving modes unused for 30+ days" >> "$DIGEST"

# Recommendation 4: knowledge gaps
echo "- 3 high-confidence knowledge entries pending review" >> "$DIGEST"

# Recommendation 5: cross-mode patterns
echo "- Handoff pattern detected: build-py ↔ analyst (11 times)" >> "$DIGEST"
echo "  Consider shared knowledge base entry" >> "$DIGEST"

# Recommendation 6: escalated items
echo "- 2 recurring recommendations without action" >> "$DIGEST"
echo "  These consumed ~2,400 tokens this week" >> "$DIGEST"
```

### Step 7: Escalation Logic

Maintain `escalations.json`:

```json
{
  "recurring": [
    {
      "item": "build-ex correction rate up 40%",
      "consecutive_days": 3,
      "cost_tokens": 1200,
      "status": "RECURRING"
    }
  ]
}
```

Logic:
```bash
# Read escalations
escalations=$(<"$HOME/.config/opencode/analytics/escalations.json")

# For each recommendation in digest, check if it appeared yesterday
if grep -q "build-ex correction rate" "$HOME/.config/opencode/analytics/digest.$(date -d yesterday +%Y-%m-%d).md" 2>/dev/null; then
  # Increment consecutive_days
  jq '.recurring[] |= if .item == "build-ex correction rate up 40%" then .consecutive_days += 1 else . end' \
    -i "$HOME/.config/opencode/analytics/escalations.json"

  # If consecutive_days >= 3, set status to RECURRING
  jq '.recurring[] |= if .consecutive_days >= 3 then .status = "RECURRING" else . end' \
    -i "$HOME/.config/opencode/analytics/escalations.json"
fi
```

### Final Digest Structure

```markdown
# Daily Digest — 2026-03-05

## Mode Usage (Last 24 Hours)
- build-py: 42 interactions
- build-ex: 38 interactions
- debug: 12 interactions

⚠️ Idle modes (no activity in 30 days):
  - analyst

## Correction Rates by Mode
- build-py: 8.5% correction rate (3 / 35)
  (7-day avg: 7.2%, trend: ↑)
- build-ex: 12.1% correction rate (4 / 33)
  (7-day avg: 9.8%, trend: ↑)

## Tool Usage by Tier
- run_script: 18 calls
- lookup_knowledge: 14 calls
- bash (Tier 5): 24 calls

⚠️ High Tier 5 usage detected: 24 bash commands
Bash patterns (3+ occurrences):
  - (used 5 times) grep -r "pattern" lib/

## Knowledge Promotion Candidates
3 pending candidates ready for review:
  - [build-ex] Error Handling Pattern — 5 corrections, confidence: high
  - [build-py] Type Annotations — 3 corrections, confidence: medium

## Escalated Items (3+ consecutive digests)
- build-ex correction rate up 40% — 3 days, cost: 1200 tokens

## Actionable Recommendations
🛠️ Tool Promotion Opportunities:
- 1 bash pattern ready for tool promotion
- Review modes with correction rate increase >30%
- Consider archiving modes unused for 30+ days
- 3 high-confidence knowledge entries pending review
- Handoff pattern detected: build-py ↔ analyst (11 times)
  Consider shared knowledge base entry
- 1 recurring recommendation without action
  This consumed ~600 tokens this week
```

---

## Error Handling

All scripts should:
1. Exit with code 1 on fatal errors
2. Print error message to stderr
3. Log errors to session JSONL if applicable
4. Never silently fail

Example error handling:

```bash
handle_error() {
  local msg="$1"
  echo "Error: $msg" >&2
  exit 1
}

[ -d "$PROJECT" ] || handle_error "Project directory not found: $PROJECT"
```

---

## Performance Targets

- `preflight-validator.sh` — <100ms (deterministic checks only)
- `extract-corrections.sh` — <2 seconds (file scanning, basic clustering)
- `update-project-context.sh` — <1 second (file detection, tree generation)
- `promote-knowledge.sh` — <500ms (file copy, git operations)
- `generate-digest.sh` — <3 seconds (log aggregation, stat calculation)

All scripts should report timing in their session logs.

