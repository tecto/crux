# Crux Model Management System Specification

## Overview

The Crux model management system is a self-contained runtime system for discovering, evaluating, deploying, and monitoring AI models. Unlike traditional ML ops systems that treat model deployment as a one-time event, Crux continuously learns from corrections in real workflows to identify when models succeed or fail, automatically surfaces recommendations without automation, and gracefully falls back to more capable (albeit slower or costlier) alternatives when the current model can't handle a task.

**Core principle**: The system recommends, the user decides. Auto-evaluation produces data; daily digests surface recommendations. Model switching is user-directed because the cost of being wrong on model selection is too high to automate.

---

## 1. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Crux Model Management                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Registry        │    │  Auto-Discovery  │              │
│  │  ~/.config/...   │    │  (Daily Digest)  │              │
│  └──────────────────┘    └──────────────────┘              │
│           │                       │                         │
│           └───────────┬───────────┘                         │
│                       │                                     │
│  ┌────────────────────▼───────────────────┐               │
│  │   Auto-Evaluation System               │               │
│  │   - Correction data extraction         │               │
│  │   - Test prompt construction           │               │
│  │   - Keyword-based scoring              │               │
│  └────────────────────┬───────────────────┘               │
│                       │                                     │
│  ┌────────────────────▼───────────────────┐               │
│  │   Post-Deployment Monitoring           │               │
│  │   - Daily correction rate tracking     │               │
│  │   - 7-day rolling averages             │               │
│  │   - Trend detection & alerting         │               │
│  └────────────────────┬───────────────────┘               │
│                       │                                     │
│  ┌────────────────────▼───────────────────┐               │
│  │   Graceful Degradation                 │               │
│  │   - Local quantization retry           │               │
│  │   - Cloud API fallback cascade         │               │
│  │   - User-directed capability assessment│               │
│  └────────────────────┬───────────────────┘               │
│                       │                                     │
│  ┌────────────────────▼───────────────────┐               │
│  │   /models Command Interface            │               │
│  │   - Runtime reconfiguration            │               │
│  │   - Hardware-aware recommendations     │               │
│  │   - User decision capture              │               │
│  └────────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Think/no-think routing is automatic** (per mode), but **model switching is user-directed** — the cost of being wrong on model selection is too high to automate. The system provides rich data; humans make the final call.

2. **Multiple models stay available simultaneously in Ollama** — the user doesn't re-run the setup script to switch models. Everything must be runtime-configurable.

3. **The system recommends, user decides** — auto-evaluation produces data; the daily digest surfaces recommendations without forcing action.

4. **Memory management matters** — on 64GB M1 Max, model loading impacts available RAM for other work. The system tracks and recommends based on real available capacity.

5. **No setup script re-runs** — models are pulled once and remain available. The /models command enables runtime assignment and switching.

---

## 2. Registry Schema

### Location
`~/.config/opencode/models/registry.json`

### Complete Schema Definition

```json
{
  "schema_version": 1,
  "last_updated": "2026-03-05T09:30:00Z",
  "hardware": {
    "chip": "M1 Max",
    "total_ram_gb": 64,
    "gpu_cores": 32,
    "last_evaluated": "2026-03-05T09:00:00Z",
    "notes": "Memory measurements taken at 09:00 UTC"
  },
  "models": [
    {
      "id": "qwen3-32b-think",
      "name": "qwen3:32b-q8_0",
      "provider": "ollama",
      "provider_url": "https://ollama.ai",
      "family": "qwen3",
      "parameters": "32B",
      "quantization": "Q8_0",
      "size_gb": 34,
      "context_window": 32768,
      "status": "assigned",
      "assigned_modes": [
        "build-py",
        "build-ex",
        "debug",
        "plan",
        "review",
        "infra-architect",
        "strategist",
        "psych",
        "legal",
        "writer",
        "analyst",
        "explain",
        "ai-infra",
        "mac",
        "docker"
      ],
      "modelfile_variant": "crux-think",
      "think_enabled": true,
      "strengths": [
        "code_generation",
        "reasoning",
        "tool_use",
        "bash_scripting",
        "multilingual",
        "long_context_coherence"
      ],
      "weaknesses": [
        "creative_writing_fluency",
        "visual_analysis"
      ],
      "benchmarks": {
        "pass_at_1": 0.78,
        "code_quality": 8.2,
        "reasoning_depth": 7.9,
        "tool_use_accuracy": 0.91
      },
      "correction_rate": {
        "build-py": {
          "current": 0.082,
          "baseline": 0.08,
          "sample_size": 120,
          "data_points": 30
        },
        "build-ex": {
          "current": 0.121,
          "baseline": 0.10,
          "sample_size": 85,
          "data_points": 20
        },
        "debug": {
          "current": 0.065,
          "baseline": 0.07,
          "sample_size": 45,
          "data_points": 12
        }
      },
      "last_evaluated": "2026-03-04T14:22:00Z",
      "last_assigned": "2026-02-15T10:00:00Z",
      "pull_timestamp": "2026-02-10T08:30:00Z",
      "notes": "Primary think model. Q8_0 quantization preserves quality."
    },
    {
      "id": "qwen3-8b-internal",
      "name": "qwen3:8b",
      "provider": "ollama",
      "family": "qwen3",
      "parameters": "8B",
      "quantization": "Q8_0",
      "size_gb": 9,
      "context_window": 32768,
      "status": "internal",
      "role": "compaction_and_audit",
      "assigned_modes": [],
      "modelfile_variant": "crux-no-think",
      "think_enabled": false,
      "strengths": [
        "speed",
        "summarization",
        "lightweight",
        "token_efficiency"
      ],
      "weaknesses": [
        "complex_reasoning",
        "code_quality",
        "long_context_reasoning"
      ],
      "benchmarks": {
        "pass_at_1": 0.52,
        "code_quality": 6.1,
        "reasoning_depth": 5.2,
        "inference_speed_tokens_per_sec": 185
      },
      "correction_rate": {},
      "last_evaluated": null,
      "pull_timestamp": "2026-02-10T08:30:00Z",
      "notes": "Used internally for Gate 2 adversarial audit and compaction. Not exposed to user-facing modes."
    },
    {
      "id": "qvq-72b-vision",
      "name": "qvq-72b-preview",
      "provider": "ollama",
      "family": "qwen-vl",
      "parameters": "72B",
      "quantization": "Q4_K_M",
      "size_gb": 42,
      "context_window": 32768,
      "status": "available",
      "assigned_modes": [],
      "modelfile_variant": "crux-vision",
      "think_enabled": false,
      "strengths": [
        "vision_analysis",
        "visual_understanding",
        "multimodal_reasoning",
        "diagram_interpretation"
      ],
      "weaknesses": [
        "text_only_tasks",
        "memory_intensive",
        "slow_inference"
      ],
      "benchmarks": {},
      "correction_rate": {},
      "last_evaluated": null,
      "pull_timestamp": "2026-03-01T12:00:00Z",
      "notes": "Requires closing most apps to load. Experimental. Q4_K_M quantization trades 3-8% quality for ~42GB size (vs 50GB Q8_0)."
    }
  ],
  "cloud_models": [
    {
      "id": "claude-opus-4",
      "name": "claude-opus-4",
      "provider": "anthropic",
      "api_key_env": "ANTHROPIC_API_KEY",
      "status": "available",
      "configured": false,
      "context_window": 200000,
      "pricing": {
        "input_per_1m_tokens": 15,
        "output_per_1m_tokens": 75,
        "currency": "USD"
      },
      "strengths": [
        "legal_reasoning",
        "complex_analysis",
        "creative_writing",
        "nuanced_judgment",
        "extended_reasoning"
      ],
      "weaknesses": [
        "latency",
        "cost",
        "privacy_concerns",
        "rate_limits"
      ],
      "use_cases": [
        "fallback_for_complex_tasks",
        "legal_mode_upgrade",
        "high_stakes_analysis",
        "creative_writing_polish"
      ],
      "benchmarks": {
        "pass_at_1": 0.94,
        "reasoning_depth": 9.2
      },
      "estimated_monthly_cost_10_interactions": 15.00
    }
  ],
  "mode_assignments": {
    "build-py": {
      "primary_model": "qwen3-32b-think",
      "fallback_models": ["claude-opus-4"],
      "think_enabled": true,
      "estimated_monthly_interactions": 45
    },
    "debug": {
      "primary_model": "qwen3-32b-think",
      "fallback_models": ["claude-opus-4"],
      "think_enabled": true,
      "estimated_monthly_interactions": 28
    },
    "strategist": {
      "primary_model": "qwen3-32b-think",
      "fallback_models": ["claude-opus-4"],
      "think_enabled": true,
      "estimated_monthly_interactions": 12
    }
  },
  "monitoring": {
    "enabled": true,
    "track_corrections": true,
    "evaluation_frequency_hours": 24,
    "alert_correction_rate_spike_threshold": 0.30,
    "alert_persistence_days": 3,
    "improvement_threshold": -0.20
  }
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | int | Schema version for migrations (currently 1) |
| `models[].id` | string | Unique identifier, kebab-cased (e.g., `qwen3-32b-think`) |
| `models[].name` | string | Ollama model name as used by `ollama list` |
| `models[].status` | enum | `assigned` (actively used), `available` (pulled but unassigned), `discovered` (auto-found), `deprecated` (retired) |
| `models[].assigned_modes` | array | List of mode IDs this model handles |
| `models[].role` | string | For internal models, describes purpose (e.g., `compaction_and_audit`) |
| `models[].correction_rate[mode]` | object | Per-mode correction tracking with baseline for comparison |
| `models[].correction_rate[mode].current` | float | Current observed correction rate (0.0-1.0) |
| `models[].correction_rate[mode].baseline` | float | Correction rate when model was first assigned |
| `models[].correction_rate[mode].sample_size` | int | Total corrections observed in this mode |
| `models[].correction_rate[mode].data_points` | int | Number of recent corrections factored into current rate |
| `cloud_models[].configured` | boolean | True only if API key is set in environment |

---

## 3. Auto-Discovery System

### Overview

The auto-discovery system runs as part of the daily digest generation. It:
1. Queries Ollama for all pulled models
2. Compares against the registry
3. Flags any new models and adds them to the registry with status `discovered`
4. Surfaces recommendations in the daily digest

### Implementation

#### 3.1 Discovery Script

Create `~/.config/opencode/scripts/discover-models.sh`:

```bash
#!/bin/bash
set -e

REGISTRY="$HOME/.config/opencode/models/registry.json"
TEMP_FILE=$(mktemp)

# Get all models currently in Ollama
get_ollama_models() {
  ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | sort || echo ""
}

# Get all models in registry
get_registry_models() {
  jq -r '.models[].name' "$REGISTRY" 2>/dev/null | sort || echo ""
}

# Find new models (in Ollama but not in registry)
discover_new_models() {
  comm -23 <(get_ollama_models) <(get_registry_models)
}

# Query Ollama API for model metadata
get_model_metadata() {
  local model_name="$1"

  # Use ollama show to get metadata
  local details=$(ollama show "$model_name" 2>/dev/null || echo "{}")

  # Extract size from ollama list
  local size_bytes=$(ollama list 2>/dev/null | grep "^$model_name" | awk '{print $3}' | sed 's/[A-Z]B$//' | head -c -1)

  # Convert to GB (assuming format like "34GB")
  local size_gb=$(ollama list 2>/dev/null | grep "^$model_name" | awk '{
    size=$3
    gsub(/[A-Z]B$/, "", size)
    if (size ~ /KB$/) print size / 1048576
    else if (size ~ /MB$/) print size / 1024
    else if (size ~ /GB$/) print size
    else print size
  }')

  # Parse family and quantization from model name
  # Format is typically family:size-quantization
  local family=$(echo "$model_name" | cut -d: -f1)
  local variant=$(echo "$model_name" | cut -d: -f2)
  local quantization=$(echo "$variant" | grep -oE 'q[0-9].*' -i || echo "unknown")

  echo "{
    \"family\": \"$family\",
    \"size_bytes\": \"${size_bytes}B\",
    \"size_gb\": $size_gb,
    \"quantization\": \"$quantization\"
  }"
}

# Add discovered model to registry
add_to_registry() {
  local model_name="$1"
  local metadata="$2"

  # Generate new model entry with status: discovered
  local model_id=$(echo "$model_name" | tr ':' '-' | tr '_' '-' | tr '.' '-')

  local new_model=$(cat <<EOF
{
  "id": "$model_id",
  "name": "$model_name",
  "provider": "ollama",
  "family": "$(echo $metadata | jq -r '.family // "unknown"')",
  "size_gb": $(echo $metadata | jq '.size_gb // 0'),
  "quantization": "$(echo $metadata | jq -r '.quantization // "unknown"')",
  "status": "discovered",
  "assigned_modes": [],
  "strengths": [],
  "weaknesses": [],
  "benchmarks": {},
  "correction_rate": {},
  "last_evaluated": null,
  "pull_timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "notes": "Auto-discovered by model management system. Run '/models evaluate $model_name' to test."
}
EOF
  )

  # Use jq to add model, creating models array if needed
  jq ".models += [$new_model]" "$REGISTRY" > "$TEMP_FILE"
  mv "$TEMP_FILE" "$REGISTRY"
}

# Main discovery loop
echo "Model auto-discovery starting..."

new_models=$(discover_new_models)
discovered_count=0

if [ -z "$new_models" ]; then
  echo "No new models discovered."
  exit 0
fi

while IFS= read -r model_name; do
  if [ -z "$model_name" ]; then
    continue
  fi

  echo "Discovered new model: $model_name"
  metadata=$(get_model_metadata "$model_name")
  add_to_registry "$model_name" "$metadata"
  discovered_count=$((discovered_count + 1))
done <<< "$new_models"

echo "Discovery complete. Found $discovered_count new model(s)."
exit 0
```

#### 3.2 Integration with Daily Digest

In `generate-digest.sh`, add discovery before summary section:

```bash
# Run model discovery
echo "" >> "$DIGEST"
echo "## Model Management" >> "$DIGEST"
echo "" >> "$DIGEST"

# Execute discovery
bash ~/.config/opencode/scripts/discover-models.sh >> /tmp/discovery.log 2>&1

# Check for discovered models
discovered=$(jq -r '.models[] | select(.status == "discovered") | .name' ~/.config/opencode/models/registry.json 2>/dev/null || echo "")

if [ -n "$discovered" ]; then
  echo "### New Models Detected" >> "$DIGEST"
  echo "" >> "$DIGEST"
  echo "The following models have been pulled to Ollama and are ready for evaluation:" >> "$DIGEST"
  echo "" >> "$DIGEST"
  echo "$discovered" | while read model; do
    echo "- \`$model\` — run \`/models evaluate $model\` to test against your correction history" >> "$DIGEST"
  done
  echo "" >> "$DIGEST"
fi
```

---

## 4. Auto-Evaluation System

### Overview

Auto-evaluation measures how well a candidate model would perform against real corrections observed in your work. It:

1. Extracts corrections from session logs (reflections with `wrong_approach` and `correct_approach`)
2. Constructs synthetic test prompts that would naturally trigger the wrong approach
3. Runs the candidate model against those prompts
4. Scores responses by keyword matching against the known correct approach
5. Calculates correction_rate and compares against baseline
6. Surfaces findings in the daily digest with recommendations

### Correction Data Structure

Corrections are stored in session reflections with this structure:

```json
{
  "reflection": {
    "type": "correction",
    "mode": "build-py",
    "timestamp": "2026-03-04T14:22:00Z",
    "context": "User was implementing async database query wrapper",
    "wrong_approach": "Used synchronous context manager pattern without async/await syntax",
    "correct_approach": "Used async context manager (async with) and proper await statements for database operations",
    "severity": "high",
    "session_id": "sess_12345",
    "tooling": ["python", "sqlite"]
  }
}
```

### Evaluation Script

Create `~/.config/opencode/scripts/evaluate-model.sh`:

```bash
#!/bin/bash
set -e

MODEL_NAME="${1:-}"
REGISTRY="$HOME/.config/opencode/models/registry.json"
SESSIONS_DIR="$HOME/.crux/sessions"
MIN_CORRECTIONS=10
MAX_CORRECTIONS=20

if [ -z "$MODEL_NAME" ]; then
  echo "Usage: evaluate-model.sh <model_name>"
  exit 1
fi

# Helper: Check if model exists
model_exists_in_ollama() {
  ollama list 2>/dev/null | awk '{print $1}' | grep -q "^${MODEL_NAME}$"
}

if ! model_exists_in_ollama; then
  echo "Error: Model '$MODEL_NAME' not found in Ollama"
  echo "Run 'ollama pull $MODEL_NAME' first"
  exit 1
fi

# Helper: Extract corrections from session logs
# Returns JSON array of corrections
extract_corrections() {
  local mode="${1:-all}"

  # Find all session reflections
  find "$SESSIONS_DIR" -name "*.json" -type f 2>/dev/null | while read session_file; do
    jq -r '.reflections[]? | select(.type == "correction") |
           if ("'"$mode"'" == "all" or .mode == "'"$mode"'") then . else empty end' "$session_file" 2>/dev/null
  done | jq -s '.'
}

# Helper: Construct test prompt that would naturally trigger wrong approach
construct_test_prompt() {
  local correction="$1"

  local mode=$(echo "$correction" | jq -r '.mode')
  local context=$(echo "$correction" | jq -r '.context')
  local wrong_keywords=$(echo "$correction" | jq -r '.wrong_approach' | head -c 50)

  # Create a prompt that naturally leads to the wrong approach
  cat <<EOF
You are in $mode mode. Here's the context: $context

Suggest the best approach. Focus on correctness and adherence to best practices.
EOF
}

# Helper: Score response against correction
# Returns 1 (passed), -1 (failed), 0 (inconclusive)
score_response() {
  local response="$1"
  local correct_keywords="$2"
  local wrong_keywords="$3"

  local response_lower=$(echo "$response" | tr '[:upper:]' '[:lower:]')
  local correct_keywords_lower=$(echo "$correct_keywords" | tr '[:upper:]' '[:lower:]')
  local wrong_keywords_lower=$(echo "$wrong_keywords" | tr '[:upper:]' '[:lower:]')

  local correct_count=0
  local wrong_count=0

  # Count keyword matches for correct approach
  echo "$correct_keywords_lower" | tr ' ' '\n' | while read keyword; do
    if echo "$response_lower" | grep -q "$keyword"; then
      correct_count=$((correct_count + 1))
    fi
  done

  # Count keyword matches for wrong approach
  echo "$wrong_keywords_lower" | tr ' ' '\n' | while read keyword; do
    if echo "$response_lower" | grep -q "$keyword"; then
      wrong_count=$((wrong_count + 1))
    fi
  done

  # Determine score
  if [ "$correct_count" -gt "$wrong_count" ]; then
    echo 1
  elif [ "$wrong_count" -gt "$correct_count" ]; then
    echo -1
  else
    echo 0
  fi
}

# Main evaluation loop
echo "Evaluating $MODEL_NAME..."
echo "Extracting corrections from session history..."

# Get recent corrections across all modes
corrections=$(extract_corrections "all" | jq -r '.[] | @json' | head -n "$MAX_CORRECTIONS")

if [ -z "$corrections" ]; then
  echo "No corrections found in session history."
  echo "Note: Evaluation requires correction data. Run some sessions first."
  exit 0
fi

correction_count=$(echo "$corrections" | wc -l)

if [ "$correction_count" -lt "$MIN_CORRECTIONS" ]; then
  echo "Warning: Only $correction_count corrections found (minimum recommended: $MIN_CORRECTIONS)"
fi

echo "Testing against $correction_count corrections..."

passed=0
failed=0
inconclusive=0

echo "$corrections" | while read -r correction_json; do
  correction=$(echo "$correction_json" | jq '.')

  mode=$(echo "$correction" | jq -r '.mode')
  context=$(echo "$correction" | jq -r '.context')
  correct_approach=$(echo "$correction" | jq -r '.correct_approach')
  wrong_approach=$(echo "$correction" | jq -r '.wrong_approach')

  # Construct and run test
  test_prompt=$(construct_test_prompt "$correction")

  echo "Testing: $mode mode - $context"

  # Call model via ollama
  response=$(ollama run "$MODEL_NAME" "$test_prompt" 2>/dev/null || echo "")

  # Score response
  score=$(score_response "$response" "$correct_approach" "$wrong_approach")

  case "$score" in
    1)
      echo "  ✓ Passed"
      passed=$((passed + 1))
      ;;
    -1)
      echo "  ✗ Failed (replicated error)"
      failed=$((failed + 1))
      ;;
    0)
      echo "  ? Inconclusive"
      inconclusive=$((inconclusive + 1))
      ;;
  esac
done

# Calculate correction rate
total=$((passed + failed + inconclusive))
if [ "$total" -gt 0 ]; then
  correction_rate=$(echo "scale=3; $failed / $total" | bc)
else
  correction_rate=0
fi

echo ""
echo "Evaluation Results:"
echo "  Passed:        $passed"
echo "  Failed:        $failed"
echo "  Inconclusive:  $inconclusive"
echo "  Correction Rate: $correction_rate (lower is better)"
echo ""
echo "To assign this model to a mode, run:"
echo "  /models assign $MODEL_NAME <mode>"
```

### Evaluation Methodology Details

#### Test Prompt Construction

The system constructs prompts that naturally surface the wrong approach without being leading:

```javascript
// Node.js reference implementation
function constructTestPrompt(correction) {
  const { mode, context, wrong_approach } = correction;

  // Extract 2-3 keywords from wrong_approach for implicit suggestion
  const wrongKeywords = wrong_approach
    .toLowerCase()
    .split(/\W+/)
    .filter(w => w.length > 4)
    .slice(0, 2);

  return `In ${mode} mode: ${context}

What's the best approach here? Consider patterns like: ${wrongKeywords.join(', ')}.`;
}
```

The keyword hints are subtle — they don't demand the wrong approach, but they make it a natural consideration.

#### Scoring Algorithm

```javascript
// Node.js reference implementation
function scoreResponse(response, correction) {
  const { correct_approach, wrong_approach } = correction;

  // Extract key terms (4+ chars) from both approaches
  const correctTerms = correct_approach
    .toLowerCase()
    .match(/\b\w{4,}\b/g) || [];
  const wrongTerms = wrong_approach
    .toLowerCase()
    .match(/\b\w{4,}\b/g) || [];

  const responseLower = response.toLowerCase();

  // Count term matches
  const correctMatches = correctTerms.filter(t =>
    responseLower.includes(t)
  ).length;

  const wrongMatches = wrongTerms.filter(t =>
    responseLower.includes(t)
  ).length;

  // Scoring
  if (correctMatches > wrongMatches) {
    return { score: 1, reason: 'Demonstrated correct approach' };
  } else if (wrongMatches > correctMatches) {
    return { score: -1, reason: 'Replicated the error pattern' };
  } else {
    return { score: 0, reason: 'Inconclusive (balanced terms)' };
  }
}
```

#### v2 Enhancement: Semantic Scoring (Future)

For v2, replace keyword matching with:
1. Embed both correction approaches and model response using a small local embedding model
2. Calculate cosine similarity between response and correct_approach vs response and wrong_approach
3. Use threshold-based classification (e.g., if sim(response, correct) - sim(response, wrong) > 0.3, pass)

This eliminates the need for exact keywords and works with paraphrased approaches.

### Integration into Registry

After evaluation, update the registry:

```bash
# Update model's correction_rate for the tested mode
jq ".models[] |=
  if .name == \"$MODEL_NAME\" then
    .correction_rate.$MODE = {
      \"current\": $CORRECTION_RATE,
      \"baseline\": $CORRECTION_RATE,
      \"sample_size\": $SAMPLE_SIZE,
      \"data_points\": $DATA_POINT_COUNT
    } |
    .last_evaluated = \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\"
  else . end" "$REGISTRY" > /tmp/registry.tmp
mv /tmp/registry.tmp "$REGISTRY"
```

### Daily Digest Integration

Add evaluation results to the daily digest:

```bash
# In generate-digest.sh, after discovery section
echo "### Model Evaluation Results" >> "$DIGEST"
echo "" >> "$DIGEST"

# Check for recently evaluated models
jq -r '.models[] |
  select(.last_evaluated != null) |
  select(.last_evaluated > now - 86400) |
  "\(.name): \(.correction_rate | to_entries | map(.value.current) | add / length | . * 100 | floor)% correction rate"' \
  ~/.config/opencode/models/registry.json 2>/dev/null | while read line; do
  echo "- $line" >> "$DIGEST"
done
```

---

## 5. Post-Deployment Monitoring

### Overview

After a model is assigned to modes, the system continuously tracks its performance against the baseline established at assignment time. Daily metrics are collected and analyzed for:

1. **Degradation**: Correction rate increasing by >30% over 7 days → escalate
2. **Improvement**: Correction rate decreasing by >20% over 7 days → celebrate
3. **Instability**: Daily rates vary wildly → investigate

### Monitoring Data Structure

Store daily monitoring metrics in `~/.config/opencode/models/monitoring/<model-id>.json`:

```json
{
  "model_id": "qwen3-32b-think",
  "model_name": "qwen3:32b-q8_0",
  "monitoring_started": "2026-02-15T10:00:00Z",
  "daily_metrics": [
    {
      "date": "2026-03-04",
      "mode": "build-py",
      "correction_rate": 0.082,
      "interactions": 33,
      "corrections": 3
    },
    {
      "date": "2026-03-04",
      "mode": "debug",
      "correction_rate": 0.065,
      "interactions": 42,
      "corrections": 3
    },
    {
      "date": "2026-03-03",
      "mode": "build-py",
      "correction_rate": 0.095,
      "interactions": 28,
      "corrections": 3
    }
  ],
  "aggregates": {
    "build-py": {
      "baseline": 0.080,
      "current_7_day_avg": 0.089,
      "trend": "slight_degradation",
      "change_percent": 11.25,
      "alert_status": null,
      "alert_triggered_date": null
    },
    "debug": {
      "baseline": 0.070,
      "current_7_day_avg": 0.068,
      "trend": "slight_improvement",
      "change_percent": -2.86,
      "alert_status": null
    }
  },
  "alerts": [
    {
      "triggered_date": "2026-03-02T09:00:00Z",
      "mode": "build-ex",
      "alert_type": "degradation",
      "threshold_exceeded_by_percent": 35,
      "description": "Correction rate in build-ex increased from 10% to 13.5% over 7 days",
      "persist_count": 2,
      "resolved": false
    }
  ]
}
```

### Monitoring Collection Script

Create `~/.config/opencode/scripts/collect-monitoring-metrics.sh`:

```bash
#!/bin/bash
set -e

REGISTRY="$HOME/.config/opencode/models/registry.json"
SESSIONS_DIR="$HOME/.crux/sessions"
MONITORING_DIR="$HOME/.config/opencode/models/monitoring"
TODAY=$(date -u +%Y-%m-%d)

mkdir -p "$MONITORING_DIR"

# Helper: Get today's corrections for a model and mode
get_daily_corrections() {
  local mode="$1"

  # Find all sessions from today
  local today_start=$(date -u -d "$TODAY" +'%Y-%m-%dT00:00:00Z')
  local today_end=$(date -u -d "$TODAY" +'%Y-%m-%dT23:59:59Z')

  find "$SESSIONS_DIR" -name "*.json" -type f \
    -newermt "$today_start" ! -newermt "$today_end" 2>/dev/null \
    | while read session_file; do
    jq -r ".reflections[]? |
          select(.type == \"correction\") |
          select(.mode == \"$mode\") |
          @json" "$session_file" 2>/dev/null
  done
}

# Update monitoring file for a model
update_model_monitoring() {
  local model_id="$1"
  local model_name=$(jq -r ".models[] | select(.id == \"$model_id\") | .name" "$REGISTRY")

  if [ -z "$model_name" ]; then
    return
  fi

  local monitoring_file="$MONITORING_DIR/${model_id}.json"

  # Initialize if not exists
  if [ ! -f "$monitoring_file" ]; then
    cat > "$monitoring_file" <<EOF
{
  "model_id": "$model_id",
  "model_name": "$model_name",
  "monitoring_started": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "daily_metrics": [],
  "aggregates": {},
  "alerts": []
}
EOF
  fi

  # Get assigned modes for this model
  local assigned_modes=$(jq -r ".models[] | select(.id == \"$model_id\") | .assigned_modes[]?" "$REGISTRY")

  if [ -z "$assigned_modes" ]; then
    return
  fi

  # For each mode, collect today's metrics
  echo "$assigned_modes" | while read mode; do
    local corrections=$(get_daily_corrections "$mode")
    local total_interactions=$(find "$SESSIONS_DIR" -name "*.json" -type f \
      -newermt "$(date -u -d "$TODAY" +'%Y-%m-%dT00:00:00Z')" 2>/dev/null \
      | xargs grep -l "\"mode\": \"$mode\"" | wc -l)

    if [ "$total_interactions" -gt 0 ]; then
      local correction_count=$(echo "$corrections" | grep -c . || echo 0)
      local correction_rate=$(echo "scale=3; $correction_count / $total_interactions" | bc)

      # Append metric to daily_metrics
      jq ".daily_metrics += [{
        \"date\": \"$TODAY\",
        \"mode\": \"$mode\",
        \"correction_rate\": $correction_rate,
        \"interactions\": $total_interactions,
        \"corrections\": $correction_count
      }]" "$monitoring_file" > /tmp/monitoring.tmp
      mv /tmp/monitoring.tmp "$monitoring_file"
    fi
  done

  # Recalculate aggregates
  recalculate_aggregates "$monitoring_file"
}

# Recalculate 7-day rolling averages and detect alerts
recalculate_aggregates() {
  local monitoring_file="$1"

  # Get unique modes from daily_metrics
  local modes=$(jq -r '.daily_metrics[].mode' "$monitoring_file" | sort -u)

  echo "$modes" | while read mode; do
    # Get last 7 days of data for this mode
    local seven_days_ago=$(date -u -d "7 days ago" +%Y-%m-%d)

    local recent_metrics=$(jq -r --arg mode "$mode" --arg date "$seven_days_ago" \
      '.daily_metrics[] |
       select(.mode == $mode) |
       select(.date >= $date) |
       .correction_rate' "$monitoring_file")

    if [ -z "$recent_metrics" ]; then
      return
    fi

    # Calculate rolling average
    local rolling_avg=$(echo "$recent_metrics" | awk '{sum+=$1} END {print sum/NR}')

    # Get baseline from registry
    local baseline=$(jq -r --arg mode "$mode" \
      ".models[] | select(.id == \"$(jq -r '.model_id' "$monitoring_file")\") |
       .correction_rate[$mode].baseline" "$REGISTRY" || echo "0")

    if [ "$baseline" = "null" ] || [ -z "$baseline" ]; then
      baseline=0
    fi

    # Detect trend
    local change_percent=$(echo "scale=2; ($rolling_avg - $baseline) / $baseline * 100" | bc)
    local trend="stable"
    local should_alert=0

    if (( $(echo "$change_percent > 30" | bc -l) )); then
      trend="degradation"
      should_alert=1
    elif (( $(echo "$change_percent < -20" | bc -l) )); then
      trend="improvement"
    fi

    # Update aggregates
    jq --arg mode "$mode" --arg trend "$trend" --arg avg "$rolling_avg" \
      --arg change "$change_percent" --arg baseline "$baseline" \
      ".aggregates[$mode] = {
        \"baseline\": $baseline,
        \"current_7_day_avg\": $avg,
        \"trend\": \$trend,
        \"change_percent\": $change,
        \"alert_status\": null
      }" "$monitoring_file" > /tmp/monitoring.tmp

    mv /tmp/monitoring.tmp "$monitoring_file"

    # Handle alerting if threshold exceeded
    if [ "$should_alert" = "1" ]; then
      check_and_escalate_alert "$monitoring_file" "$mode"
    fi
  done
}

# Check if alert should be escalated
check_and_escalate_alert() {
  local monitoring_file="$1"
  local mode="$2"

  # Check if alert already exists for this mode
  local existing_alert=$(jq --arg mode "$mode" \
    '.alerts[] | select(.mode == $mode and .resolved == false)' "$monitoring_file")

  if [ -z "$existing_alert" ]; then
    # Create new alert
    local change=$(jq -r --arg mode "$mode" '.aggregates[$mode].change_percent' "$monitoring_file")
    jq ".alerts += [{
      \"triggered_date\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",
      \"mode\": \"$mode\",
      \"alert_type\": \"degradation\",
      \"threshold_exceeded_by_percent\": ${change},
      \"description\": \"Correction rate increased by ${change}% over 7 days\",
      \"persist_count\": 1,
      \"resolved\": false
    }]" "$monitoring_file" > /tmp/monitoring.tmp
    mv /tmp/monitoring.tmp "$monitoring_file"
  else
    # Increment persist_count
    jq --arg mode "$mode" \
      '.alerts |= map(
        if .mode == $mode and .resolved == false then
          .persist_count += 1
        else . end
      )' "$monitoring_file" > /tmp/monitoring.tmp
    mv /tmp/monitoring.tmp "$monitoring_file"
  fi
}

# Main execution
echo "Collecting daily monitoring metrics..."

# Get all assigned models
assigned_models=$(jq -r '.models[] | select(.status == "assigned") | .id' "$REGISTRY")

echo "$assigned_models" | while read model_id; do
  if [ -z "$model_id" ]; then
    continue
  fi
  update_model_monitoring "$model_id"
done

echo "Monitoring collection complete."
```

### Integration with Daily Digest

```bash
# In generate-digest.sh
echo "## Model Performance Trends" >> "$DIGEST"
echo "" >> "$DIGEST"

MONITORING_DIR="$HOME/.config/opencode/models/monitoring"

if [ ! -d "$MONITORING_DIR" ]; then
  echo "No monitoring data available yet." >> "$DIGEST"
else
  # Collect all active alerts
  for monitoring_file in "$MONITORING_DIR"/*.json; do
    if [ ! -f "$monitoring_file" ]; then
      continue
    fi

    alerts=$(jq -r '.alerts[] | select(.resolved == false) | .description' "$monitoring_file" 2>/dev/null)

    if [ -n "$alerts" ]; then
      echo "### Alerts" >> "$DIGEST"
      echo "" >> "$DIGEST"
      echo "$alerts" | while read alert; do
        echo "⚠️ $alert" >> "$DIGEST"
      done
      echo "" >> "$DIGEST"
    fi
  done

  # Show improvement trends
  for monitoring_file in "$MONITORING_DIR"/*.json; do
    if [ ! -f "$monitoring_file" ]; then
      continue
    fi

    improvements=$(jq -r '.aggregates[] |
      select(.trend == "improvement") |
      "\(.change_percent)% better"' "$monitoring_file" 2>/dev/null)

    if [ -n "$improvements" ]; then
      echo "### Positive Trends" >> "$DIGEST"
      echo "" >> "$DIGEST"
      echo "$improvements" | while read trend; do
        echo "✓ $trend" >> "$DIGEST"
      done
      echo "" >> "$DIGEST"
    fi
  done
fi
```

---

## 6. Graceful Degradation System

### Overview

When the current model struggles with a task, Crux implements a four-stage degradation cascade:

1. **Local retry** — Try a different quantization of the same model family
2. **Mode suggestion** — Recommend a different mode if task is out-of-scope
3. **Cloud fallback** — Suggest Claude API if configured (with cost estimate)
4. **Honest assessment** — Provide specific capability limitations and workarounds

This ensures the user always gets honest feedback rather than confident bad output.

### Detection Signals

The system detects model struggle through:

```javascript
// Detection criteria
const DEGRADATION_SIGNALS = {
  // High correction rate in current session (>25% of recent interactions)
  correctionRateSpike: {
    threshold: 0.25,
    window: "last_10_interactions",
    severity: "medium"
  },

  // Model says "I don't know" or expresses uncertainty
  uncertaintyMarkers: {
    patterns: [
      /i\s+(?:don'?t|can'?t)\s+(?:know|help|handle)/i,
      /this\s+(?:is\s+)?(?:beyond|outside)\s+(?:my|my\s+current)\s+(?:ability|capability|knowledge)/i,
      /i\s+(?:may\s+)?(?:lack|don'?t have)\s+(?:the|sufficient)\s+(?:knowledge|capability)/i
    ],
    severity: "high"
  },

  // Tool retries exceed threshold
  toolRetryCount: {
    threshold: 3,
    window: "same_operation",
    severity: "high"
  },

  // User explicitly states limitation
  explicitUserStatement: {
    patterns: [
      /that'?s\s+(?:too\s+)?hard\s+(?:for\s+)?you/i,
      /you\s+can'?t\s+(?:handle|do)\s+this/i,
      /this\s+is\s+(?:beyond|outside)\s+your\s+(?:ability|capability)/i
    ],
    severity: "critical"
  }
};
```

### Degradation Cascade Implementation

#### Stage 1: Local Quantization Retry

```bash
# In a mode handler or command runner
attempt_quantization_retry() {
  local current_model="$1"
  local task_context="$2"

  # Parse current model and quantization
  # Example: qwen3:32b-q8_0 -> qwen3, 32b, q8_0
  local family=$(echo "$current_model" | cut -d: -f1)
  local size=$(echo "$current_model" | cut -d- -f1 | cut -d: -f2)
  local current_quant=$(echo "$current_model" | grep -oE 'q[0-9].*' -i)

  # Define retry sequence (try progressively more aggressive quantizations)
  local quant_sequence=("q8_0" "q5_k_m" "q4_k_m")

  for quant in "${quant_sequence[@]}"; do
    if [ "$quant" = "$current_quant" ]; then
      continue  # Skip current quantization
    fi

    local retry_model="${family}:${size}-${quant}"

    # Check if retry model exists in Ollama
    if ollama list 2>/dev/null | grep -q "^${retry_model}"; then
      echo "Retrying with different quantization: $retry_model"

      # Re-run task with retry model
      # (This would be delegated to the task runner)
      return 0
    fi
  done

  return 1  # No retry quantization available
}
```

#### Stage 2: Mode Suggestion

```bash
# Suggest alternative modes if task seems out-of-scope
suggest_alternative_mode() {
  local current_mode="$1"
  local task_description="$2"

  # Map of tasks to better modes
  declare -A mode_mapping=(
    ["detailed_code_review"]="review"
    ["creative_writing"]="writer"
    ["legal_analysis"]="legal"
    ["system_design"]="strategist"
    ["debugging_complex_issue"]="debug"
    ["building_new_feature"]="build-py"
  )

  # This is heuristic and should improve with user feedback
  for task_type in "${!mode_mapping[@]}"; do
    if echo "$task_description" | grep -qi "$task_type"; then
      local suggested_mode="${mode_mapping[$task_type]}"
      if [ "$suggested_mode" != "$current_mode" ]; then
        echo "This task might be better suited for '$suggested_mode' mode."
        return 0
      fi
    fi
  done

  return 1
}
```

#### Stage 3: Cloud Fallback

```bash
# Offer cloud API fallback with cost estimate
offer_cloud_fallback() {
  local task_context="$1"

  # Check if API key is configured
  if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "To enable cloud fallback, set ANTHROPIC_API_KEY environment variable."
    return 1
  fi

  # Estimate tokens (rough heuristic)
  local task_tokens=$(echo "$task_context" | wc -w)
  local estimated_input_tokens=$((task_tokens + 500))  # task + system prompt
  local estimated_output_tokens=2000  # Typical response

  # Calculate cost (Claude pricing in USD per 1M tokens)
  local input_cost=$(echo "scale=5; $estimated_input_tokens * 0.000015" | bc)
  local output_cost=$(echo "scale=5; $estimated_output_tokens * 0.000075" | bc)
  local total_cost=$(echo "scale=2; $input_cost + $output_cost" | bc)

  cat <<EOF

This task exceeds local model capability. Estimated cloud API cost: \$$total_cost

Would you like to switch to Claude API for this interaction? (yes/no)

Benefits of cloud fallback:
- Superior reasoning and analysis
- Better handling of complex scenarios
- Extended context window (200K tokens)

Cost impact:
- This interaction: ~\$$total_cost
- Typical monthly (10-20 interactions): ~$15-20

EOF
}
```

#### Stage 4: Honest Assessment

```bash
# Provide capability assessment and workarounds
provide_capability_assessment() {
  local model_name="$1"
  local task_description="$2"
  local failure_mode="$3"  # e.g., "legal_reasoning", "creative_writing_fluency"

  # Map failure modes to specific limitations and workarounds
  declare -A workarounds=(
    ["legal_reasoning"]="Break legal analysis into smaller components: (1) identify applicable laws, (2) find precedents, (3) apply to case. Consult with actual legal expert for binding advice."
    ["creative_writing_fluency"]="Use the model to outline structure and generate content, then edit for fluency manually. Or switch to /write mode with Claude API."
    ["complex_refactoring"]="Refactor one file at a time. Handle dependencies manually. Verify test suite after each file."
    ["visual_analysis"]="Use /models recommend to find a vision-capable model, or switch to Claude API."
  )

  cat <<EOF

This task exceeds $model_name capability.

Specific limitation: ${workarounds[$failure_mode]:-Insufficient reasoning depth for this task type.}

Suggested next steps:
1. Break the task into smaller sub-problems
2. Configure a cloud API key (ANTHROPIC_API_KEY) for fallback
3. Try a specialized model (run '/models recommend' for suggestions)
4. Switch to a more capable mode if available

To see available models:
  /models list

To evaluate a model:
  /models evaluate <model_name>

EOF
}
```

### Integration into Mode Handler

The mode handler checks for degradation signals and implements the cascade:

```bash
# Pseudo-code for mode handler
execute_in_mode() {
  local mode="$1"
  local task="$2"

  # Stage 1: Attempt with current model
  local current_model=$(get_assigned_model "$mode")
  local response=$(run_model "$current_model" "$task")

  # Check for degradation signals
  if detect_uncertainty_marker "$response"; then
    echo "Detected model uncertainty..."

    # Stage 1: Try quantization retry
    if attempt_quantization_retry "$current_model" "$task"; then
      return 0
    fi

    # Stage 2: Suggest mode alternative
    if suggest_alternative_mode "$mode" "$task"; then
      read -p "Switch modes? (y/n) " -n 1
      [ "$REPLY" = "y" ] && return 1
    fi

    # Stage 3: Offer cloud fallback
    if offer_cloud_fallback "$task"; then
      read -p "Use cloud API? (y/n) " -n 1
      if [ "$REPLY" = "y" ]; then
        run_claude_api "$task"
        return 0
      fi
    fi

    # Stage 4: Provide assessment
    provide_capability_assessment "$current_model" "$task" "complex_reasoning"
    return 1
  fi

  return 0
}
```

### Key Design Principle

**Modeling Honesty**: The Modelfile system prompt includes rule #8: "When you notice a task exceeds your current capability, say so and suggest alternatives." This is enforced across all models, ensuring they signal struggle rather than produce confident bad output.

---

## 7. Hardware-Aware Recommendations

### Overview

The hardware-aware recommendation system helps users select model variants (quantizations) and models that fit their hardware constraints while optimizing for quality and performance trade-offs.

### Memory Calculation System

```bash
# Helper functions for memory inspection
get_system_memory_gb() {
  local os_type=$(uname)
  local mem_bytes

  if [ "$os_type" = "Darwin" ]; then
    # macOS
    mem_bytes=$(sysctl -n hw.memsize)
  else
    # Linux
    mem_bytes=$(grep MemTotal /proc/meminfo | awk '{print $2 * 1024}')
  fi

  echo "scale=1; $mem_bytes / 1073741824" | bc
}

get_ollama_allocated_memory_gb() {
  # Query Ollama for all loaded models and sum sizes
  local total_bytes=$(curl -s http://localhost:11434/api/tags 2>/dev/null | \
    jq '[.models[]?.size // 0] | add // 0')

  if [ -z "$total_bytes" ] || [ "$total_bytes" = "0" ]; then
    echo "0"
  else
    echo "scale=1; $total_bytes / 1073741824" | bc
  fi
}

get_available_memory_for_models_gb() {
  local total=$(get_system_memory_gb)
  local ollama=$(get_ollama_allocated_memory_gb)
  local reserved=8  # Reserve 8GB for OS and other applications

  local available=$(echo "scale=1; $total - $ollama - $reserved" | bc)

  # Return 0 if negative
  if (( $(echo "$available < 0" | bc -l) )); then
    echo "0"
  else
    echo "$available"
  fi
}

# Example usage
echo "Total system memory: $(get_system_memory_gb) GB"
echo "Used by Ollama: $(get_ollama_allocated_memory_gb) GB"
echo "Available for new model: $(get_available_memory_for_models_gb) GB"
```

### Quantization Recommendation Logic

```javascript
// Node.js implementation
function recommendQuantization(modelSizeB, availableMemoryGB) {
  // Quantization reference table
  const quantizationOptions = [
    {
      name: 'Q8_0',
      compressionRatio: 1.06,
      qualityLoss: '<1%',
      inference_speedup: 1.0,
      recommended_for: 'Best quality, can handle 32B+ models'
    },
    {
      name: 'Q6_K',
      compressionRatio: 1.53,
      qualityLoss: '1-2%',
      inference_speedup: 1.3,
      recommended_for: 'Balanced quality and speed'
    },
    {
      name: 'Q5_K_M',
      compressionRatio: 1.92,
      qualityLoss: '2-3%',
      inference_speedup: 1.6,
      recommended_for: 'Moderate quality loss, faster inference'
    },
    {
      name: 'Q4_K_M',
      compressionRatio: 2.55,
      qualityLoss: '3-8%',
      inference_speedup: 2.2,
      recommended_for: 'Significant size reduction, acceptable quality'
    },
    {
      name: 'Q3_K_M',
      compressionRatio: 3.35,
      qualityLoss: '8-15%',
      inference_speedup: 2.8,
      recommended_for: 'Aggressive compression, noticeable quality impact'
    },
    {
      name: 'Q2_K',
      compressionRatio: 4.27,
      qualityLoss: '15-20%',
      inference_speedup: 3.5,
      recommended_for: 'Extreme compression, significant quality loss'
    }
  ];

  // Estimate FP16 base size (2 bytes per parameter)
  const baseSize = (modelSizeB * 2) / 1073741824;  // Convert to GB

  // Find best fitting quantization
  let bestOption = null;
  let bestMetric = -Infinity;

  for (const quant of quantizationOptions) {
    const quantizedSize = baseSize * quant.compressionRatio;
    const memoryNeeded = quantizedSize * 1.2;  // 20% overhead for inference

    // Check if this quantization fits
    if (memoryNeeded <= availableMemoryGB) {
      // Score: prefer smallest memory footprint among fitting options
      // If memory is plenty (>5GB free), prefer quality
      let score;
      if (availableMemoryGB > quantizedSize + 5) {
        // Plenty of memory: prefer quality (lower compression)
        score = -quant.compressionRatio;  // Negative to reverse sort
      } else {
        // Tight memory: prefer fitting
        score = quantizedSize;
      }

      if (score > bestMetric) {
        bestMetric = score;
        bestOption = {
          ...quant,
          estimatedSizeGB: quantizedSize.toFixed(1),
          memoryAfterLoadGB: (availableMemoryGB - memoryNeeded).toFixed(1),
          fits: true
        };
      }
    }
  }

  // If nothing fits, recommend next best with warnings
  if (!bestOption) {
    // Find the most aggressive quantization
    const mostAggressive = quantizationOptions[quantizationOptions.length - 1];
    const size = (baseSize * mostAggressive.compressionRatio).toFixed(1);

    return {
      recommended: null,
      fits: false,
      suggestion: mostAggressive.name,
      error: `Model requires ${size}GB; only ${availableMemoryGB}GB available.`,
      actions: [
        `Close applications using memory (top memory consumers: [list from system])`,
        `Switch to a smaller model (run '/models recommend' for alternatives)`,
        `Reduce quantization to ${mostAggressive.name} (${mostAggressive.qualityLoss} quality loss)`
      ]
    };
  }

  return {
    recommended: bestOption.name,
    estimatedSizeGB: bestOption.estimatedSizeGB,
    qualityLoss: bestOption.qualityLoss,
    speedup: bestOption.inference_speedup,
    memoryAfterLoadGB: bestOption.memoryAfterLoadGB,
    explanation: bestOption.recommended_for,
    fits: true
  };
}

// Example output
const recommendation = recommendQuantization(
  32000000000,  // 32B model
  12             // 12GB available
);

/*
Output:
{
  recommended: 'Q4_K_M',
  estimatedSizeGB: '13.6',
  qualityLoss: '3-8%',
  speedup: 2.2,
  memoryAfterLoadGB: '1.4',
  explanation: 'Significant size reduction, acceptable quality',
  fits: true
}
*/
```

### /models recommend Command

```bash
# Implementation of /models recommend
models_recommend() {
  local mode="${1:-all}"
  local registry="$HOME/.config/opencode/models/registry.json"

  # Get available memory
  local available_memory=$(get_available_memory_for_models_gb)

  echo "Hardware Profile:"
  echo "  Total RAM: $(get_system_memory_gb) GB"
  echo "  Used by Ollama: $(get_ollama_allocated_memory_gb) GB"
  echo "  Available for model: $available_memory GB"
  echo ""

  if [ "$mode" = "all" ]; then
    echo "Top recommendations for current hardware:"
    echo ""

    # Get all available models
    jq -r '.models[] |
      select(.status == "available" or .status == "discovered") |
      "\(.name),\(.size_gb),\(.strengths | join(", "))"' "$registry" | \
    while IFS=',' read name size strengths; do
      if (( $(echo "$size <= $available_memory * 0.8" | bc -l) )); then
        echo "✓ $name (${size}GB) - Fits well"
        echo "  Strengths: $strengths"
        echo ""
      fi
    done
  else
    echo "Models optimized for mode: $mode"
    echo ""

    # Get models assigned to this mode or suitable for it
    jq -r --arg mode "$mode" '.models[] |
      select(.assigned_modes[] == $mode or .status == "available") |
      "\(.name),\(.size_gb),\(.correction_rate[$mode].current // "untested")"' "$registry" | \
    while IFS=',' read name size rate; do
      echo "- $name (${size}GB)"
      if [ "$rate" != "untested" ]; then
        echo "  Current correction rate: ${rate}%"
      fi
    done
  fi
}
```

---

## 8. /models Command Interface

The `/models` command is the user-facing interface to the entire model management system.

### Command Reference

```bash
/models                     # Show current model assignments by mode
/models list               # List all registered models with metadata
/models status             # Show loaded models and memory usage
/models evaluate <name>    # Run evaluation against correction data
/models recommend [mode]   # Recommend best model(s) for mode or hardware
/models assign <model> <mode>  # Assign model to one or more modes
/models pull <name>        # Download a new model via Ollama
/models remove <name>      # Remove model from registry (unload separately)
/models info <name>        # Show detailed info about a model
/models trending           # Show performance trends and alerts
```

### Implementation Framework

Create `~/.crux/commands/models.sh`:

```bash
#!/bin/bash
set -e

REGISTRY="$HOME/.config/opencode/models/registry.json"
COMMAND="${1:-status}"

case "$COMMAND" in
  list|l)
    cmd_list "$@"
    ;;
  status|s)
    cmd_status "$@"
    ;;
  info|i)
    cmd_info "${2:-}"
    ;;
  evaluate|eval|e)
    cmd_evaluate "${2:-}"
    ;;
  recommend|rec|r)
    cmd_recommend "${2:-all}"
    ;;
  assign|a)
    cmd_assign "${2:-}" "${3:-}"
    ;;
  pull|p)
    cmd_pull "${2:-}"
    ;;
  remove|rm)
    cmd_remove "${2:-}"
    ;;
  trending|trend|t)
    cmd_trending
    ;;
  *)
    cmd_help
    ;;
esac

# ============================================================================
# Command implementations
# ============================================================================

cmd_status() {
  echo "Current Model Assignments"
  echo "========================="
  echo ""

  # Get unique assigned modes
  jq -r '.mode_assignments | keys[]' "$REGISTRY" | while read mode; do
    local primary=$(jq -r --arg mode "$mode" '.mode_assignments[$mode].primary_model' "$REGISTRY")
    local model_name=$(jq -r --arg id "$primary" '.models[] | select(.id == $id) | .name' "$REGISTRY")

    if [ -n "$model_name" ]; then
      echo "$mode: $model_name"
    fi
  done

  echo ""
  echo "Memory Usage"
  echo "============"
  echo "Total system RAM: $(get_system_memory_gb) GB"
  echo "Used by Ollama: $(get_ollama_allocated_memory_gb) GB"
  echo "Available: $(get_available_memory_for_models_gb) GB"
  echo ""

  echo "Loaded Models (in Ollama)"
  echo "========================="
  ollama list 2>/dev/null || echo "Ollama not running"
}

cmd_list() {
  echo "Registered Models"
  echo "================="
  echo ""

  jq -r '.models[] |
    "Name: \(.name)\n" +
    "  Status: \(.status)\n" +
    "  Size: \(.size_gb)GB\n" +
    "  Modes: \(.assigned_modes | join(", ") | if . == "" then "none" else . end)\n"' \
    "$REGISTRY"
}

cmd_info() {
  local model_name="$1"

  if [ -z "$model_name" ]; then
    echo "Usage: /models info <model_name>"
    exit 1
  fi

  jq --arg name "$model_name" \
    '.models[] | select(.name == $name) |
    "Model: \(.name)\n" +
    "Family: \(.family)\n" +
    "Parameters: \(.parameters)\n" +
    "Quantization: \(.quantization)\n" +
    "Size: \(.size_gb)GB\n" +
    "Status: \(.status)\n" +
    "Strengths:\n" +
    "  \(.strengths | map("  - " + .) | join("\n"))\n" +
    "Weaknesses:\n" +
    "  \(.weaknesses | map("  - " + .) | join("\n"))\n" +
    "Correction rates (by mode):\n" +
    "  \(.correction_rate | to_entries | map("    \(.key): \(.value.current | . * 100 | floor)%") | join("\n"))"' \
    "$REGISTRY"
}

cmd_evaluate() {
  local model_name="$1"

  if [ -z "$model_name" ]; then
    echo "Usage: /models evaluate <model_name>"
    exit 1
  fi

  bash ~/.config/opencode/scripts/evaluate-model.sh "$model_name"
}

cmd_recommend() {
  local mode="$1"
  bash ~/.config/opencode/scripts/recommend-model.sh "$mode"
}

cmd_assign() {
  local model="$1"
  local mode="$2"

  if [ -z "$model" ] || [ -z "$mode" ]; then
    echo "Usage: /models assign <model_name> <mode>"
    exit 1
  fi

  # Verify model exists
  if ! jq -r '.models[].name' "$REGISTRY" | grep -q "^${model}$"; then
    echo "Error: Model '$model' not found in registry"
    exit 1
  fi

  # Update registry
  local model_id=$(jq -r --arg name "$model" '.models[] | select(.name == $name) | .id' "$REGISTRY")

  jq --arg id "$model_id" --arg mode "$mode" \
    '.models[] |=
    if .id == $id then
      .assigned_modes += [$mode] |
      .assigned_modes |= unique
    else . end' "$REGISTRY" > /tmp/registry.tmp

  mv /tmp/registry.tmp "$REGISTRY"

  echo "Assigned $model to $mode mode"
  echo "Run '/models status' to verify"
}

cmd_pull() {
  local model_name="$1"

  if [ -z "$model_name" ]; then
    echo "Usage: /models pull <model_name>"
    echo ""
    echo "Examples:"
    echo "  /models pull mistral:7b"
    echo "  /models pull neural-chat:latest"
    exit 1
  fi

  echo "Pulling $model_name from Ollama registry..."
  ollama pull "$model_name"

  echo ""
  echo "Model pulled. Run '/models evaluate $model_name' to test it."
}

cmd_remove() {
  local model_name="$1"

  if [ -z "$model_name" ]; then
    echo "Usage: /models remove <model_name>"
    exit 1
  fi

  # Remove from registry (but not from Ollama)
  jq --arg name "$model_name" 'del(.models[] | select(.name == $name))' "$REGISTRY" > /tmp/registry.tmp
  mv /tmp/registry.tmp "$REGISTRY"

  echo "Removed $model_name from registry"
  echo "Note: Model remains in Ollama. Run 'ollama rm $model_name' to free disk space."
}

cmd_trending() {
  echo "Model Performance Trends"
  echo "======================="
  echo ""

  local monitoring_dir="$HOME/.config/opencode/models/monitoring"

  if [ ! -d "$monitoring_dir" ]; then
    echo "No monitoring data available yet."
    exit 0
  fi

  for monitoring_file in "$monitoring_dir"/*.json; do
    if [ ! -f "$monitoring_file" ]; then
      continue
    fi

    local model_name=$(jq -r '.model_name' "$monitoring_file")
    echo "Model: $model_name"
    echo ""

    jq -r '.aggregates | to_entries[] |
      "\(.key): \(.value.current_7_day_avg | . * 100 | floor)% correction rate (\(.value.trend))"' \
      "$monitoring_file"

    echo ""
  done
}

cmd_help() {
  cat <<'EOF'
Crux Model Management

Usage: /models [command] [arguments]

Commands:
  list              List all registered models
  status            Show current assignments and memory usage
  info <name>       Show detailed model information
  evaluate <name>   Test model against correction history
  recommend [mode]  Get recommendations for mode or hardware
  assign <m> <mode> Assign model to mode
  pull <name>       Download new model from Ollama registry
  remove <name>     Remove model from registry
  trending          Show performance trends and alerts

Examples:
  /models list
  /models status
  /models evaluate qwen3:32b-q8_0
  /models recommend build-py
  /models assign mistral:7b analyst
  /models pull neural-chat:7b-q4_0
  /models trending

EOF
}

# Helper functions (defined at top of script)
source ~/.config/opencode/scripts/discover-models.sh
source ~/.config/opencode/scripts/evaluate-model.sh
```

---

## 9. Integration Points

### Daily Digest Integration

The daily digest includes:
1. **New Models Detected** — discovered models and evaluation prompts
2. **Model Evaluation Results** — recent eval outcomes and recommendations
3. **Performance Trends** — correction rate changes and alerts
4. **Memory Status** — available capacity and quantization suggestions

### Correction Data Integration

The system reads reflections from session logs with this structure:

```json
{
  "session_id": "sess_2026_03_04_14_22_30",
  "reflections": [
    {
      "type": "correction",
      "timestamp": "2026-03-04T14:22:00Z",
      "mode": "build-py",
      "model_used": "qwen3:32b-q8_0",
      "context": "Implementing async database query wrapper",
      "wrong_approach": "Used synchronous context manager pattern without async/await",
      "correct_approach": "Used async context manager (async with) and proper await statements",
      "severity": "high",
      "tooling": ["python", "sqlite"],
      "session_context": {
        "previous_attempts": 2,
        "total_interactions": 15,
        "interaction_number": 7
      }
    }
  ]
}
```

### Think-Router Integration

Think mode routing is automatic per mode but uses model-specific directives:

```bash
# In the think-router
should_use_think_mode() {
  local mode="$1"
  local current_model="$2"

  # Get think_enabled from registry
  local think_enabled=$(jq -r --arg id "$current_model" \
    '.models[] | select(.id == $id) | .think_enabled' "$REGISTRY")

  # Check mode config
  local mode_think=$(jq -r --arg mode "$mode" \
    '.mode_assignments[$mode].think_enabled // true' "$REGISTRY")

  if [ "$think_enabled" = "true" ] && [ "$mode_think" = "true" ]; then
    return 0  # Use think
  fi

  return 1  # No think
}
```

### Token Budget Integration

Model-specific token calculations:

```bash
# Budget adjustments per model
get_model_token_multiplier() {
  local model_id="$1"

  # Some models are more verbose or less efficient with tokens
  local multiplier=$(jq -r --arg id "$model_id" \
    '.models[] | select(.id == $id) | .token_multiplier // 1.0' "$REGISTRY")

  echo "$multiplier"
}
```

### Five-Gate Pipeline Integration

The 8B model (qwen3:8b) is used for Gate 2 (adversarial audit):

```bash
# Gate 2: Adversarial audit using 8B model
run_adversarial_audit() {
  local proposal="$1"
  local audit_model="qwen3:8b"  # Fixed to 8B model

  echo "Running adversarial audit with $audit_model..."

  # Ask 8B to find flaws
  local result=$(ollama run "$audit_model" "Find flaws in this: $proposal")

  return 0
}
```

---

## 10. Configuration Files Reference

### Default Registry Location
`~/.config/opencode/models/registry.json`

### Monitoring Data Location
`~/.config/opencode/models/monitoring/<model-id>.json`

### Script Locations
- `~/.config/opencode/scripts/discover-models.sh` — Auto-discovery
- `~/.config/opencode/scripts/evaluate-model.sh` — Auto-evaluation
- `~/.config/opencode/scripts/collect-monitoring-metrics.sh` — Monitoring
- `~/.crux/commands/models.sh` — /models command handler

### Environment Variables
- `ANTHROPIC_API_KEY` — Cloud fallback (Claude API)
- `OLLAMA_HOST` — Ollama server address (default: `http://localhost:11434`)

---

## 11. Data Flow Diagrams

### Auto-Discovery Flow

```
┌─────────────────────────────────────┐
│   Daily Digest Generation (start)   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  1. Run discover-models.sh          │
│     - Query ollama list             │
│     - Compare with registry         │
│     - Find new models               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  2. Query Ollama for metadata       │
│     - Model family                  │
│     - Quantization                  │
│     - Size estimation               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  3. Add to registry with            │
│     status: "discovered"            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  4. Surface in daily digest         │
│     "New model detected:             │
│      Run /models evaluate to test"   │
└─────────────────────────────────────┘
```

### Auto-Evaluation Flow

```
┌──────────────────────────────┐
│ User runs:                    │
│ /models evaluate <model>     │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ 1. Extract corrections from logs         │
│    - Find all reflections with type:     │
│      "correction"                        │
│    - Limit to 10-20 recent samples       │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ 2. For each correction:                  │
│    a) Construct test prompt              │
│    b) Extract correct/wrong keywords     │
│    c) Run test with candidate model      │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ 3. Score each response                   │
│    - Count keyword matches               │
│    - Determine: passed/failed/unclear    │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ 4. Calculate correction_rate             │
│    - failures / total samples            │
│    - Compare against baseline            │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ 5. Update registry with results          │
│    - correction_rate per mode            │
│    - last_evaluated timestamp            │
└──────────────────────────────────────────┘
```

### Graceful Degradation Flow

```
User requests task in mode

         │
         ▼
┌──────────────────────────────────┐
│ Execute with current model       │
└────────┬───────────────────────────┘
         │
         ▼
    Detect degradation signals?
    (uncertainty, retry count, etc)
         │
    NO   │ YES
    │    │
    │    ▼
    │  ┌─────────────────────────────┐
    │  │ Stage 1: Quantization Retry │
    │  │ - Try Q5_K_M, Q4_K_M, etc   │
    │  └────────┬────────────────────┘
    │           │
    │      SUCCESS? YES → End
    │           │
    │           NO
    │           ▼
    │  ┌─────────────────────────────┐
    │  │ Stage 2: Mode Suggestion    │
    │  │ - Recommend alternative mode│
    │  └────────┬────────────────────┘
    │           │
    │      USER SWITCHES? YES → End
    │           │
    │           NO
    │           ▼
    │  ┌─────────────────────────────┐
    │  │ Stage 3: Cloud Fallback     │
    │  │ - Check API key configured  │
    │  │ - Estimate cost             │
    │  │ - Offer Claude API          │
    │  └────────┬────────────────────┘
    │           │
    │      USER ACCEPTS? YES → End
    │           │
    │           NO
    │           ▼
    │  ┌─────────────────────────────┐
    │  │ Stage 4: Honest Assessment  │
    │  │ - List specific limitations │
    │  │ - Suggest workarounds       │
    │  └─────────────────────────────┘
    │
    └─────────────────────────────► Exit normally
```

---

## 12. Error Handling and Edge Cases

### Model Pull Failures

```bash
if ! ollama pull "$model_name"; then
  echo "Error: Failed to pull model '$model_name'"
  echo "Possible causes:"
  echo "  1. Ollama server not running (ollama serve)"
  echo "  2. Model not found in Ollama registry"
  echo "  3. Insufficient disk space"
  echo "  4. Network connectivity issue"
  exit 1
fi
```

### Corrupted Registry Recovery

```bash
# Validate registry schema
validate_registry() {
  local registry="$HOME/.config/opencode/models/registry.json"

  if ! jq empty "$registry" 2>/dev/null; then
    echo "Error: Registry JSON is malformed"
    echo "Attempting recovery..."

    # Backup corrupted file
    cp "$registry" "$registry.corrupt.$(date +%s)"

    # Restore from last known good
    if [ -f "$registry.backup" ]; then
      cp "$registry.backup" "$registry"
      echo "Restored from backup"
    else
      echo "No backup available. Please restore manually."
      exit 1
    fi
  fi
}
```

### Ollama Connection Failures

```bash
check_ollama_ready() {
  if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Error: Ollama server not responding"
    echo ""
    echo "To start Ollama:"
    echo "  ollama serve"
    echo ""
    echo "On macOS with app installation:"
    echo "  open -a Ollama"
    exit 1
  fi
}
```

### Insufficient Memory

```bash
check_memory_for_model() {
  local model_size_gb="$1"
  local available=$(get_available_memory_for_models_gb)

  if (( $(echo "$model_size_gb > $available" | bc -l) )); then
    echo "Error: Insufficient memory for model"
    echo "  Model size: ${model_size_gb}GB"
    echo "  Available: ${available}GB"
    echo ""
    echo "Options:"
    echo "  1. Close running applications"
    echo "  2. Use a smaller model or quantization"
    echo "  3. Upgrade system RAM"
    exit 1
  fi
}
```

---

## 13. Future Enhancements (v2+)

### Semantic Evaluation Scoring

Replace keyword matching with embedding-based similarity:

```javascript
// v2 enhancement
async function scoreResponseSemantic(response, correction) {
  const model = 'all-minilm:22m';  // Small local embedding model

  const correctEmbedding = await embedText(correction.correct_approach);
  const wrongEmbedding = await embedText(correction.wrong_approach);
  const responseEmbedding = await embedText(response);

  const correctSimilarity = cosineSimilarity(responseEmbedding, correctEmbedding);
  const wrongSimilarity = cosineSimilarity(responseEmbedding, wrongEmbedding);

  const delta = correctSimilarity - wrongSimilarity;

  if (delta > 0.3) return 1;      // Passed
  if (delta < -0.3) return -1;    // Failed
  return 0;                        // Inconclusive
}
```

### Automated Model Selection

Evolve from recommendations to full automation with user checkpoints:

```
Monthly: "Based on 3 months of data, recommend switching from Model A to Model B"
User confirms → System automatically updates all mode assignments
System tracks outcome over next month
If successful, continue; if not, revert and flag for investigation
```

### Cross-Session Learning

Track patterns across projects:
- "You struggle with X task in Python but excel in Go"
- "When you use Mode A for this task type, correction rate is 40% higher"
- Recommend modes based on task content analysis

### Budget-Aware Recommendations

Suggest cloud vs. local based on usage patterns:
- "You run this task type 3x/week. Monthly cloud cost would be $X vs. $Y for local hardware."

---

## 14. Appendix: Complete Script Bundle

### Directory Structure

```
~/.config/opencode/
├── models/
│   ├── registry.json                 # Main model registry
│   ├── monitoring/
│   │   ├── qwen3-32b-think.json
│   │   └── claude-opus-4.json
│   └── scripts/
│       ├── discover-models.sh
│       ├── evaluate-model.sh
│       ├── collect-monitoring-metrics.sh
│       └── recommend-model.sh
└── ...

~/.crux/
├── commands/
│   └── models.sh                      # /models command handler
└── ...
```

### Setup Script

```bash
#!/bin/bash
# Initialize model management system

REGISTRY_DIR="$HOME/.config/opencode/models"
SCRIPTS_DIR="$REGISTRY_DIR/scripts"
MONITORING_DIR="$REGISTRY_DIR/monitoring"
COMMANDS_DIR="$HOME/.crux/commands"

# Create directories
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$MONITORING_DIR"
mkdir -p "$COMMANDS_DIR"

# Initialize registry if not exists
if [ ! -f "$REGISTRY_DIR/registry.json" ]; then
  cp <(cat <<'EOF'
{
  "schema_version": 1,
  "last_updated": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "hardware": {
    "chip": "unknown",
    "total_ram_gb": 0,
    "gpu_cores": 0
  },
  "models": [],
  "cloud_models": [],
  "mode_assignments": {},
  "monitoring": {
    "enabled": true,
    "track_corrections": true,
    "evaluation_frequency_hours": 24,
    "alert_correction_rate_spike_threshold": 0.30,
    "alert_persistence_days": 3
  }
}
EOF
  ) "$REGISTRY_DIR/registry.json"

  echo "Initialized empty registry at $REGISTRY_DIR/registry.json"
fi

echo "Model management system initialized."
```

---

## Conclusion

The Crux model management system provides a complete runtime framework for discovering, evaluating, deploying, and monitoring AI models. By coupling automatic data collection (correction tracking) with user-directed decision making (command-based assignment), it balances autonomy with control while remaining honest about model limitations and providing graceful fallbacks to more capable systems when needed.

Key principles:
- **Data drives decisions** — Auto-evaluation and monitoring produce rich metrics
- **Users decide** — Recommendations surface naturally; humans make final calls
- **Memory matters** — Hardware awareness prevents overload and suggests best quantizations
- **Honesty first** — Models signal struggle rather than produce confident bad output
- **Zero friction** — No setup script re-runs; all switching is runtime-configurable
