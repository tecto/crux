# Crux Continuous Learning Infrastructure

## Comprehensive Implementation Specification

**Version**: 1.0
**Date**: 2026-03-05
**Status**: Implementation Guide
**Audience**: Engineering team implementing the continuous learning system

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Level 1: Interaction-Level Learning (Real-Time)](#level-1-interaction-level-learning-real-time)
3. [Level 2: Continuous Processing (Threshold-Triggered)](#level-2-continuous-processing-threshold-triggered)
4. [Level 3: Cross-Session Pattern Detection](#level-3-cross-session-pattern-detection)
5. [Level 4: Cross-Project Learning](#level-4-cross-project-learning)
6. [Level 5: Ecosystem Learning](#level-5-ecosystem-learning)
7. [Data Structures and Schemas](#data-structures-and-schemas)
8. [Research Foundation](#research-foundation)
9. [Implementation Guidelines](#implementation-guidelines)
10. [Error Handling and Resilience](#error-handling-and-resilience)

---

## Architecture Overview

### System Constraints and Design Philosophy

The Crux continuous learning infrastructure was designed around three core user requirements:

1. **No manual maintenance** - All learning processes must be fully automatic and organic
2. **No session boundaries** - The system treats Bryan's work as continuous; sleep doesn't create boundaries
3. **No cron jobs** - Processing must be event-driven and threshold-based, not time-based
4. **Daily digest cadence** - Aggregated insights delivered daily given volume of active projects
5. **Escalation behavior** - Unaddressed recommendations escalate daily until acknowledged

### The Five-Level Learning Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  Level 5: Ecosystem Learning                                    │
│  (Community ↔ Public Repository)                                │
└─────────────────────────────────────────────────────────────────┘
                            ↑ ↓
┌─────────────────────────────────────────────────────────────────┐
│  Level 4: Cross-Project Learning                                │
│  (Project → User Library → Public Promotion)                    │
└─────────────────────────────────────────────────────────────────┘
                            ↑ ↓
┌─────────────────────────────────────────────────────────────────┐
│  Level 3: Cross-Session Pattern Detection                       │
│  (Mode Drift, Systemic Gaps, New Mode Proposals)               │
└─────────────────────────────────────────────────────────────────┘
                            ↑ ↓
┌─────────────────────────────────────────────────────────────────┐
│  Level 2: Continuous Processing (Threshold-Triggered)           │
│  (Clustering, Knowledge Generation, Tool Analysis, Scoring)     │
└─────────────────────────────────────────────────────────────────┘
                            ↑ ↓
┌─────────────────────────────────────────────────────────────────┐
│  Level 1: Interaction-Level Learning (Real-Time)                │
│  (Correction Detection, Reflection Entries)                      │
└─────────────────────────────────────────────────────────────────┘
```

Each level feeds into the next with increasing abstraction:
- **Level 1** produces raw correction data (interaction-scoped)
- **Level 2** synthesizes patterns within a session (session-scoped)
- **Level 3** detects systemic issues across sessions (user-scoped)
- **Level 4** promotes proven knowledge to shared libraries (cross-project scope)
- **Level 5** shares validated patterns with the community (ecosystem scope)

---

## Level 1: Interaction-Level Learning (Real-Time)

### Purpose

Capture learning signals at the moment of correction. This is immediate, synchronous processing that stays in active context for the rest of the session, enabling the model to learn and adjust within the same conversation.

### Trigger Mechanism

Automatically fires on every user message and model response pair. Zero latency required - this is inline with message processing.

### The Correction-Detector Plugin

The correction-detector plugin identifies four correction patterns:

#### Pattern 1: User Correction Language

When the user explicitly signals a correction:

```
User: "No, that's not right. You should use Ash resources, not raw Ecto."
```

**Detection logic**: Keywords indicating correction (no, that's wrong, actually, I mean, what I meant, let me clarify, you misunderstood, that's not what I asked)

#### Pattern 2: Model Self-Correction

When the model catches itself making an error:

```
Assistant: "Wait, I should clarify. That approach would cause N+1 queries.
Instead, we should preload the associations..."
```

**Detection logic**: Phrases like "actually," "wait," "let me reconsider," "I made an error," "that won't work because"

#### Pattern 3: Tool Retry

When a tool fails and the model retries with a different approach:

```
Tool execution failed: "Invalid Ash action name"
Model response: "I see the issue. Let me use the correct action definition..."
```

**Detection logic**: Tool failures followed by retry attempts with modified parameters

#### Pattern 4: Script Audit Failure

When a generated script fails validation:

```
Script audit result: FAILED - "Missing error handling in transaction"
Model response: "You're right, let me add transaction wrapping..."
```

**Detection logic**: Audit failures followed by script regeneration

### Reflection Entry Structure

Each detected correction creates a structured reflection entry:

```json
{
  "id": "refl_20260305_143_001",
  "type": "reflection",
  "session_id": "sess_20260305_morning_001",
  "trigger": "user_correction",
  "trigger_pattern": "explicit_language",
  "mode": "build-ex",
  "interaction_number": 14,
  "timestamp": "2026-03-05T14:28:45.000Z",
  "context": {
    "user_message": "No, that's not right. You should use Ash resources, not raw Ecto.",
    "model_message_before": "Let's define this as a raw Ecto schema...",
    "model_correction": "You're right. Let me use an Ash resource with actions instead.",
    "project_id": "ex-auth-system"
  },
  "learning_content": {
    "wrong_approach": "Raw Ecto schema for feature logic",
    "correct_approach": "Ash resource with built-in actions",
    "reasoning": "Ash resources provide automatic authorization, action validation, and error handling",
    "applicable_domains": ["ash", "authorization", "action-design"]
  },
  "metadata": {
    "correction_confidence": 0.95,
    "pattern_similarity": ["ash-pattern-001", "ash-pattern-003"],
    "is_first_correction_in_session": false
  }
}
```

### Code Implementation: Level 1 Detection

```typescript
interface CorrectionPattern {
  type: 'user_correction' | 'model_self_correction' | 'tool_retry' | 'script_audit';
  confidence: number;
  keywords: string[];
}

interface ReflectionEntry {
  id: string;
  type: 'reflection';
  session_id: string;
  trigger: string;
  mode: string;
  interaction_number: number;
  timestamp: string;
  context: {
    user_message: string;
    model_message_before: string;
    model_correction: string;
    project_id: string;
  };
  learning_content: {
    wrong_approach: string;
    correct_approach: string;
    reasoning: string;
    applicable_domains: string[];
  };
  metadata: {
    correction_confidence: number;
    pattern_similarity: string[];
    is_first_correction_in_session: boolean;
  };
}

interface CorrectionDetectorState {
  current_message_index: number;
  session_reflections: ReflectionEntry[];
  unprocessed_queue: ReflectionEntry[];
  last_model_message: string;
  pending_tool_calls: Map<string, ToolCall>;
}

class CorrectionDetector {
  private state: CorrectionDetectorState;
  private reflection_id_counter: number = 0;

  constructor(session_id: string) {
    this.state = {
      current_message_index: 0,
      session_reflections: [],
      unprocessed_queue: [],
      last_model_message: '',
      pending_tool_calls: new Map(),
    };
  }

  /**
   * Check for user correction language patterns
   * Uses keyword matching with context sensitivity
   */
  private detectUserCorrection(
    user_message: string,
    model_previous: string
  ): CorrectionPattern | null {
    const correction_keywords = [
      'no', 'that\'s not right', 'actually', 'I mean',
      'what I meant', 'let me clarify', 'you misunderstood',
      'that\'s not what I asked', 'wrong', 'incorrect',
      'not quite', 'not exactly', 'I was wrong',
      'let me rephrase', 'I misspoke'
    ];

    const has_correction_keyword = correction_keywords.some(
      keyword => user_message.toLowerCase().includes(keyword)
    );

    if (!has_correction_keyword) return null;

    // Require follow-up context (user is explaining the correction)
    const has_follow_up = user_message.length > model_previous.length * 0.1;

    if (!has_follow_up) return null;

    return {
      type: 'user_correction',
      confidence: 0.85 + (has_follow_up ? 0.1 : 0),
      keywords: correction_keywords.filter(k =>
        user_message.toLowerCase().includes(k)
      ),
    };
  }

  /**
   * Check for model self-correction patterns
   * The model catches itself making an error
   */
  private detectModelSelfCorrection(model_message: string): CorrectionPattern | null {
    const self_correction_phrases = [
      'actually', 'wait', 'let me reconsider', 'I made an error',
      'that won\'t work because', 'I apologize', 'I should clarify',
      'let me revise', 'on second thought', 'actually, I realize',
      'I was mistaken', 'I should correct that'
    ];

    // Look for self-correction marker followed by substantive correction
    const has_marker = self_correction_phrases.some(phrase =>
      model_message.toLowerCase().includes(phrase)
    );

    if (!has_marker) return null;

    // Split on markers and ensure there's a substantial difference
    const parts = model_message.split(/(actually|wait|let me reconsider)/i);
    if (parts.length < 3) return null;

    const before_part = parts[0].trim();
    const after_part = parts.slice(2).join(' ').trim();

    // Verify this is a real correction, not just elaboration
    const is_real_correction =
      before_part.length > 50 &&
      after_part.length > 50 &&
      this.calculateSimilarity(before_part, after_part) < 0.7;

    if (!is_real_correction) return null;

    return {
      type: 'model_self_correction',
      confidence: 0.80,
      keywords: self_correction_phrases.filter(p =>
        model_message.toLowerCase().includes(p)
      ),
    };
  }

  /**
   * Check for tool retry pattern
   * A tool failed, and the model is now retrying with different parameters
   */
  private detectToolRetry(
    current_model_message: string,
    previous_tool_failure: ToolFailure | null
  ): CorrectionPattern | null {
    if (!previous_tool_failure) return null;

    // Check for acknowledgment of the error
    const error_keywords = ['I see', 'the issue', 'let me', 'try again', 'different'];
    const acknowledges_error = error_keywords.some(kw =>
      current_model_message.toLowerCase().includes(kw)
    );

    if (!acknowledges_error) return null;

    // The model should be proposing the same tool with different parameters
    // or a different approach entirely
    return {
      type: 'tool_retry',
      confidence: 0.75,
      keywords: error_keywords.filter(kw =>
        current_model_message.toLowerCase().includes(kw)
      ),
    };
  }

  /**
   * Check for script audit failure correction
   * A generated script failed validation and is being regenerated
   */
  private detectScriptAuditFailure(
    audit_result: ScriptAuditResult | null,
    model_response: string
  ): CorrectionPattern | null {
    if (!audit_result || audit_result.status === 'PASSED') return null;

    // Model should acknowledge the failure and explain the fix
    const acknowledges_failure =
      model_response.toLowerCase().includes('you\'re right') ||
      model_response.toLowerCase().includes('I see') ||
      model_response.toLowerCase().includes('let me fix');

    if (!acknowledges_failure) return null;

    return {
      type: 'script_audit',
      confidence: 0.90,
      keywords: ['audit failure', 'let me fix', 'missing'],
    };
  }

  /**
   * Main detection pipeline - called after each model response
   */
  async detectAndRecordCorrection(
    user_message: string,
    model_message: string,
    interaction_number: number,
    context: {
      session_id: string;
      mode: string;
      project_id: string;
      tool_failure?: ToolFailure;
      script_audit?: ScriptAuditResult;
    }
  ): Promise<ReflectionEntry | null> {
    // Try all detection patterns
    let pattern = this.detectUserCorrection(user_message, this.state.last_model_message);
    if (!pattern) {
      pattern = this.detectModelSelfCorrection(model_message);
    }
    if (!pattern) {
      pattern = this.detectToolRetry(model_message, context.tool_failure || null);
    }
    if (!pattern) {
      pattern = this.detectScriptAuditFailure(context.script_audit || null, model_message);
    }

    if (!pattern) {
      this.state.last_model_message = model_message;
      return null;
    }

    // Extract learning content
    const learning_content = this.extractLearningContent(
      user_message,
      model_message,
      pattern
    );

    // Create reflection entry
    const reflection: ReflectionEntry = {
      id: this.generateReflectionId(context.session_id),
      type: 'reflection',
      session_id: context.session_id,
      trigger: pattern.type,
      mode: context.mode,
      interaction_number,
      timestamp: new Date().toISOString(),
      context: {
        user_message,
        model_message_before: this.state.last_model_message,
        model_correction: model_message,
        project_id: context.project_id,
      },
      learning_content,
      metadata: {
        correction_confidence: pattern.confidence,
        pattern_similarity: await this.findSimilarPatterns(learning_content),
        is_first_correction_in_session: this.state.session_reflections.length === 0,
      },
    };

    // Add to both active session reflections and unprocessed queue
    this.state.session_reflections.push(reflection);
    this.state.unprocessed_queue.push(reflection);

    // Update state for next iteration
    this.state.last_model_message = model_message;
    this.state.current_message_index = interaction_number;

    return reflection;
  }

  /**
   * Extract structured learning content from user and model messages
   */
  private extractLearningContent(
    user_message: string,
    model_message: string,
    pattern: CorrectionPattern
  ): ReflectionEntry['learning_content'] {
    // This is a simplified extraction; in production, use the 8B model
    // to extract and structure the learning content more intelligently

    const extraction_prompt = `
Given a correction made by the user or model, extract:
1. wrong_approach: What was done incorrectly
2. correct_approach: What should be done instead
3. reasoning: Why the correct approach is better
4. applicable_domains: Tags for which domains this applies to

User message: "${user_message}"
Model message: "${model_message}"
Pattern type: ${pattern.type}

Output as JSON with keys: wrong_approach, correct_approach, reasoning, applicable_domains (array)
`;

    // In production, call qwen3:8b with this prompt
    // For now, return a placeholder structure
    return {
      wrong_approach: 'Previous approach before correction',
      correct_approach: 'Corrected approach',
      reasoning: 'Why the correction is better',
      applicable_domains: [],
    };
  }

  /**
   * Find similar patterns in historical reflections
   */
  private async findSimilarPatterns(
    learning_content: ReflectionEntry['learning_content']
  ): Promise<string[]> {
    // Compare against historical reflections using cosine similarity
    // Return IDs of reflections with similarity > 0.6
    return [];
  }

  /**
   * Generate a unique reflection ID
   */
  private generateReflectionId(session_id: string): string {
    const timestamp = Date.now().toString(36);
    const counter = (++this.reflection_id_counter).toString(36);
    return `refl_${session_id}_${timestamp}_${counter}`;
  }

  /**
   * Calculate text similarity using simple keyword overlap
   */
  private calculateSimilarity(text1: string, text2: string): number {
    const words1 = new Set(text1.toLowerCase().split(/\s+/));
    const words2 = new Set(text2.toLowerCase().split(/\s+/));

    const intersection = [...words1].filter(w => words2.has(w)).length;
    const union = words1.size + words2.size - intersection;

    return union === 0 ? 1.0 : intersection / union;
  }

  /**
   * Get reflections from active session for in-session learning context
   */
  getSessionReflections(): ReflectionEntry[] {
    return this.state.session_reflections;
  }

  /**
   * Get unprocessed reflections for Level 2 processing
   */
  getUnprocessedReflections(): ReflectionEntry[] {
    return this.state.unprocessed_queue;
  }

  /**
   * Mark reflections as processed
   */
  markAsProcessed(reflection_ids: string[]): void {
    this.state.unprocessed_queue = this.state.unprocessed_queue.filter(
      r => !reflection_ids.includes(r.id)
    );
  }
}
```

### Session Integration

The correction detector must be instantiated per session and persist reflections to a JSONL file:

```typescript
// In session initialization
const detector = new CorrectionDetector(session_id);

// After each model response
const reflection = await detector.detectAndRecordCorrection(
  user_message,
  model_response,
  interaction_number,
  {
    session_id,
    mode,
    project_id,
    tool_failure: last_tool_failure,
    script_audit: last_audit_result,
  }
);

if (reflection) {
  // Append to session JSONL file
  await appendReflectionToFile(
    `~/.crux/sessions/${session_id}/reflections.jsonl`,
    reflection
  );

  // Add to context for next model call so it can learn immediately
  context.session_reflections = detector.getSessionReflections();
}
```

### Key Design Decisions for Level 1

1. **Real-time, in-session availability**: Reflections are immediately available in the context for the next model call, enabling learning within the same conversation. This is critical for preventing repeated mistakes in a single session.

2. **Multiple detection patterns**: By checking four different patterns, we capture corrections expressed in different ways without over-generating false positives.

3. **Confidence scoring**: Each detected correction is scored for confidence (0.75-0.95). This helps Level 2 prioritize high-confidence corrections.

4. **Structured extraction**: Reflections are structured with clear fields (wrong_approach, correct_approach, reasoning) to enable downstream processing.

5. **No blocking**: Detection is fast and synchronous, adding <50ms to response latency.

---

## Level 2: Continuous Processing (Threshold-Triggered)

### Purpose

Synthesize Level 1 reflections into actionable insights while Bryan continues working. This is the continuous learning engine that operates asynchronously in the background.

### Critical Design: NOT Session-Based, NOT Cron-Based

**Bryan's requirement**: "There is no end to a session" and "why can't it just be continuous?"

This means:
- Processing MUST be threshold-based, not event-based at session end
- Processing MUST not wait for predetermined times (cron)
- Processing MUST be continuous in the background
- Processing MUST NOT block the user's primary session

### Threshold Triggers

Level 2 processing spawns when ANY of these conditions are met:

```typescript
interface ProcessingThresholds {
  unprocessed_reflections_count: number;
  interactions_since_last_processing: number;
  tokens_since_last_processing: number;
}

const THRESHOLDS = {
  unprocessed_reflections_count: 10,     // Queue has 10+ unreprocessed reflections
  interactions_since_last_processing: 50, // 50 interactions since last processing
  tokens_since_last_processing: 5000,     // 5000 tokens generated since last
};

// Check thresholds continuously
async function checkAndTriggerLevel2Processing(
  current_state: SystemState
): Promise<void> {
  const unprocessed_count = current_state.unprocessed_reflections.length;
  const interactions_delta =
    current_state.current_interaction -
    current_state.last_level2_processing_interaction;
  const tokens_delta =
    current_state.total_tokens_generated -
    current_state.last_level2_processing_tokens;

  const should_process =
    unprocessed_count >= THRESHOLDS.unprocessed_reflections_count ||
    interactions_delta >= THRESHOLDS.interactions_since_last_processing ||
    tokens_delta >= THRESHOLDS.tokens_since_last_processing;

  if (should_process && !current_state.level2_processing_active) {
    spawnBackgroundProcessing(current_state);
  }
}
```

### Background Processing Implementation

Level 2 runs in a background task that does NOT block the main session:

```typescript
interface BackgroundProcessingState {
  is_active: boolean;
  start_time: number;
  processing_id: string;
  cancelled: boolean;
}

async function spawnBackgroundProcessing(state: SystemState): Promise<void> {
  // Mark as active to prevent concurrent runs
  state.level2_processing_active = true;
  const processing_id = generateProcessingId();

  const timeout_handle = setTimeout(() => {
    // Safety: Never let processing run more than 15 minutes
    cancelProcessing(processing_id);
  }, 15 * 60 * 1000);

  try {
    // Spawn as background task; don't wait for it to complete
    // Use lower-priority background queue
    queueBackgroundTask({
      id: processing_id,
      type: 'level2_processing',
      state_snapshot: captureStateSnapshot(state),
      priority: 'low',
      callback: (result) => {
        state.last_level2_processing_result = result;
        state.last_level2_processing_time = Date.now();
        state.last_level2_processing_interaction = state.current_interaction;
        state.last_level2_processing_tokens = state.total_tokens_generated;
        state.level2_processing_active = false;
      },
    });
  } finally {
    clearTimeout(timeout_handle);
  }
}
```

### Step 1: Reflection Clustering

The first step in Level 2 is to cluster similar corrections by topic. Corrections about the same topic should be grouped together.

**Clustering Algorithm**: Shared keywords with frequency analysis

```typescript
interface ClusterConfig {
  min_cluster_size: number;
  similarity_threshold: number;
}

interface ReflectionCluster {
  id: string;
  topic: string;
  reflections: ReflectionEntry[];
  keywords: string[];
  confidence: number;
  created_at: string;
}

class ReflectionClusterer {
  private config: ClusterConfig = {
    min_cluster_size: 3,
    similarity_threshold: 0.5,
  };

  /**
   * Cluster reflections by topic using keyword matching
   */
  clusterReflections(reflections: ReflectionEntry[]): ReflectionCluster[] {
    if (reflections.length < this.config.min_cluster_size) {
      return [];
    }

    // Extract keywords from each reflection
    const reflection_keywords = reflections.map(r => ({
      reflection_id: r.id,
      keywords: this.extractKeywords(r),
      vector: this.keywordsToVector(this.extractKeywords(r)),
    }));

    // Build similarity matrix
    const similarity_matrix = this.buildSimilarityMatrix(reflection_keywords);

    // Greedy clustering: start with highest-similarity pairs
    const clusters: ReflectionCluster[] = [];
    const assigned = new Set<string>();

    for (let i = 0; i < reflections.length; i++) {
      if (assigned.has(reflections[i].id)) continue;

      // Start a new cluster
      const cluster_members = [reflections[i]];
      assigned.add(reflections[i].id);

      // Find similar reflections
      for (let j = i + 1; j < reflections.length; j++) {
        if (assigned.has(reflections[j].id)) continue;

        const similarity = similarity_matrix[i][j];
        if (similarity >= this.config.similarity_threshold) {
          cluster_members.push(reflections[j]);
          assigned.add(reflections[j].id);
        }
      }

      // Only keep clusters with minimum size
      if (cluster_members.length >= this.config.min_cluster_size) {
        const cluster = this.createCluster(cluster_members);
        clusters.push(cluster);
      }
    }

    return clusters;
  }

  /**
   * Extract important keywords from a reflection
   */
  private extractKeywords(reflection: ReflectionEntry): string[] {
    const text = [
      reflection.learning_content.wrong_approach,
      reflection.learning_content.correct_approach,
      reflection.learning_content.reasoning,
      reflection.context.user_message,
    ].join(' ');

    // Remove common words, tokenize, keep important terms
    const common_words = new Set([
      'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
      'of', 'with', 'is', 'are', 'was', 'were', 'be', 'have', 'has', 'do',
    ]);

    const words = text
      .toLowerCase()
      .match(/\b\w+\b/g) || [];

    return words
      .filter(w => !common_words.has(w) && w.length > 3)
      .slice(0, 20); // Limit to 20 keywords
  }

  /**
   * Convert keywords to a simple vector representation
   */
  private keywordsToVector(keywords: string[]): Map<string, number> {
    const vector = new Map<string, number>();
    keywords.forEach(kw => {
      vector.set(kw, (vector.get(kw) || 0) + 1);
    });
    return vector;
  }

  /**
   * Build pairwise similarity matrix using Jaccard similarity
   */
  private buildSimilarityMatrix(
    reflection_keywords: Array<{
      reflection_id: string;
      keywords: string[];
      vector: Map<string, number>;
    }>
  ): number[][] {
    const n = reflection_keywords.length;
    const matrix: number[][] = Array(n).fill(0).map(() => Array(n).fill(0));

    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const sim = this.jaccardSimilarity(
          reflection_keywords[i].keywords,
          reflection_keywords[j].keywords
        );
        matrix[i][j] = sim;
        matrix[j][i] = sim;
      }
    }

    return matrix;
  }

  /**
   * Calculate Jaccard similarity between two sets of keywords
   */
  private jaccardSimilarity(keywords1: string[], keywords2: string[]): number {
    const set1 = new Set(keywords1);
    const set2 = new Set(keywords2);

    const intersection = [...set1].filter(k => set2.has(k)).length;
    const union = set1.size + set2.size - intersection;

    return union === 0 ? 1.0 : intersection / union;
  }

  /**
   * Create a cluster from grouped reflections
   */
  private createCluster(reflections: ReflectionEntry[]): ReflectionCluster {
    // Infer topic from most common keywords
    const all_keywords = reflections
      .flatMap(r => this.extractKeywords(r));

    const keyword_frequency = new Map<string, number>();
    all_keywords.forEach(kw => {
      keyword_frequency.set(kw, (keyword_frequency.get(kw) || 0) + 1);
    });

    // Top 3-5 keywords become the topic
    const top_keywords = [...keyword_frequency.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([kw]) => kw);

    const topic = top_keywords.join(' + ');

    // Calculate average confidence
    const avg_confidence = reflections.reduce(
      (sum, r) => sum + r.metadata.correction_confidence,
      0
    ) / reflections.length;

    return {
      id: generateClusterId(),
      topic,
      reflections,
      keywords: top_keywords,
      confidence: avg_confidence,
      created_at: new Date().toISOString(),
    };
  }
}
```

### Step 2: Knowledge Entry Draft Generation

For each cluster of 3+ similar corrections, generate a knowledge entry that captures the pattern.

```typescript
interface KnowledgeEntry {
  id: string;
  type: 'technique' | 'pattern' | 'gotcha' | 'best-practice';
  title: string;
  summary: string;
  problem_statement: string;
  solution: string;
  code_example?: string;
  reasoning: string;
  applicable_to: string[];
  source_clusters: string[];
  confidence: number;
  created_at: string;
  metadata: {
    original_reflection_count: number;
    average_correction_confidence: number;
    domains: string[];
  };
}

class KnowledgeEntryGenerator {
  private synthesis_model = 'qwen3:8b'; // 8B model for synthesis

  /**
   * Generate knowledge entry from a reflection cluster
   * Uses the 8B model to synthesize and structure the learning
   */
  async generateFromCluster(
    cluster: ReflectionCluster
  ): Promise<KnowledgeEntry> {
    // Build synthesis prompt
    const synthesis_prompt = this.buildSynthesisPrompt(cluster);

    // Call 8B model for synthesis (not the main 32B model)
    const synthesis_response = await this.callSynthesisModel(synthesis_prompt);

    // Parse response into structured knowledge entry
    const extracted = this.parseModelResponse(synthesis_response);

    return {
      id: generateKnowledgeEntryId(),
      type: this.inferType(cluster),
      title: extracted.title,
      summary: extracted.summary,
      problem_statement: extracted.problem,
      solution: extracted.solution,
      code_example: extracted.code_example,
      reasoning: extracted.reasoning,
      applicable_to: extracted.applicable_to || cluster.keywords,
      source_clusters: [cluster.id],
      confidence: cluster.confidence,
      created_at: new Date().toISOString(),
      metadata: {
        original_reflection_count: cluster.reflections.length,
        average_correction_confidence: cluster.confidence,
        domains: cluster.keywords,
      },
    };
  }

  /**
   * Build the synthesis prompt for the 8B model
   */
  private buildSynthesisPrompt(cluster: ReflectionCluster): string {
    const reflections_summary = cluster.reflections
      .map((r, idx) => {
        return `
Correction ${idx + 1}:
- Wrong: ${r.learning_content.wrong_approach}
- Right: ${r.learning_content.correct_approach}
- Why: ${r.learning_content.reasoning}
`;
      })
      .join('\n');

    return `
You are synthesizing corrections that users made across multiple interactions into a reusable knowledge entry.

CLUSTER TOPIC: ${cluster.topic}
NUMBER OF CORRECTIONS: ${cluster.reflections.length}

INDIVIDUAL CORRECTIONS:
${reflections_summary}

Your task: Extract the underlying pattern and generate a knowledge entry that could prevent this correction from being needed in the future.

Generate a JSON response with:
{
  "title": "Short, memorable title for this pattern",
  "summary": "1-2 sentence summary",
  "problem": "What problem does this address?",
  "solution": "How to solve it",
  "code_example": "If applicable, a brief code example",
  "reasoning": "Why is the solution better?",
  "applicable_to": ["domain", "tags"]
}

Focus on the PATTERN, not specific project details. This should apply broadly.
Use positive framing ("do X" not "don't Y").
`;
  }

  /**
   * Call the 8B synthesis model
   * CRITICAL: Use 8B model, not 32B, to avoid blocking the main model
   */
  private async callSynthesisModel(prompt: string): Promise<string> {
    // Use a separate model inference endpoint for the 8B model
    // This must NOT block the main LLM processing
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'qwen3:8b',
        prompt,
        stream: false,
        temperature: 0.3, // Lower temperature for more consistent synthesis
      }),
    });

    const data = await response.json();
    return data.response;
  }

  /**
   * Parse the 8B model's response into structured fields
   */
  private parseModelResponse(response: string): any {
    // The model should return JSON-structured output
    // If it doesn't, attempt extraction
    try {
      // Find JSON in response
      const json_match = response.match(/\{[\s\S]*\}/);
      if (json_match) {
        return JSON.parse(json_match[0]);
      }
    } catch (e) {
      // Fall back to heuristic extraction
    }

    return {
      title: 'Pattern Detected',
      summary: response.substring(0, 150),
      problem: 'Problem identified',
      solution: 'Solution recommended',
      code_example: null,
      reasoning: response.substring(0, 200),
      applicable_to: [],
    };
  }

  /**
   * Infer the type of knowledge entry from cluster characteristics
   */
  private inferType(
    cluster: ReflectionCluster
  ): KnowledgeEntry['type'] {
    const keywords_str = cluster.keywords.join(' ').toLowerCase();

    if (keywords_str.includes('gotcha') || keywords_str.includes('trap')) {
      return 'gotcha';
    }
    if (keywords_str.includes('best') || keywords_str.includes('practice')) {
      return 'best-practice';
    }
    if (keywords_str.includes('pattern') || keywords_str.includes('architecture')) {
      return 'pattern';
    }

    return 'technique';
  }
}
```

### Step 3: Tool Usage Pattern Analysis

Analyze which tools are being used, which are effective, and which could be promoted to automatable status.

```typescript
interface ToolUsageMetrics {
  tool_name: string;
  call_count: number;
  success_count: number;
  average_latency_ms: number;
  times_retried: number;
  success_rate: number;
  contexts_used_in: string[];
}

interface ToolPromotionCandidate {
  tool_name: string;
  current_status: 'manual' | 'semi-automatic' | 'automatic';
  promotion_target: 'semi-automatic' | 'automatic';
  evidence: string;
  confidence: number;
}

class ToolAnalyzer {
  /**
   * Analyze tool usage patterns
   */
  analyzeToolUsage(
    reflections: ReflectionEntry[]
  ): ToolUsageMetrics[] {
    const metrics_map = new Map<string, ToolUsageMetrics>();

    reflections.forEach(reflection => {
      // Extract tool mentions from learning_content
      const tools_mentioned = this.extractToolMentions(
        reflection.learning_content
      );

      tools_mentioned.forEach(tool => {
        if (!metrics_map.has(tool)) {
          metrics_map.set(tool, {
            tool_name: tool,
            call_count: 0,
            success_count: 0,
            average_latency_ms: 0,
            times_retried: 0,
            success_rate: 0,
            contexts_used_in: [],
          });
        }

        const metrics = metrics_map.get(tool)!;
        metrics.call_count++;

        if (reflection.trigger === 'tool_retry') {
          metrics.times_retried++;
        } else {
          metrics.success_count++;
        }

        if (!metrics.contexts_used_in.includes(reflection.mode)) {
          metrics.contexts_used_in.push(reflection.mode);
        }
      });
    });

    // Calculate aggregate metrics
    return [...metrics_map.values()].map(m => ({
      ...m,
      success_rate: m.success_count / m.call_count,
    }));
  }

  /**
   * Identify tools that should be promoted to higher automation levels
   */
  identifyPromotionCandidates(
    metrics: ToolUsageMetrics[]
  ): ToolPromotionCandidate[] {
    const candidates: ToolPromotionCandidate[] = [];

    metrics.forEach(metric => {
      // Tool used in 3+ contexts consistently = candidate for automation
      if (metric.contexts_used_in.length >= 3 && metric.success_rate > 0.85) {
        candidates.push({
          tool_name: metric.tool_name,
          current_status: 'manual',
          promotion_target: 'semi-automatic',
          evidence: `Used successfully in ${metric.contexts_used_in.length} different modes with ${(metric.success_rate * 100).toFixed(1)}% success rate`,
          confidence: Math.min(metric.success_rate, 0.95),
        });
      }
    });

    return candidates;
  }

  /**
   * Extract tool mentions from learning content
   */
  private extractToolMentions(
    learning_content: ReflectionEntry['learning_content']
  ): string[] {
    // Simple keyword-based extraction; in production could be more sophisticated
    const text = [
      learning_content.wrong_approach,
      learning_content.correct_approach,
      learning_content.reasoning,
    ].join(' ').toLowerCase();

    const known_tools = [
      'shell', 'sql', 'api_call', 'file_write', 'search', 'browser',
      'git', 'docker', 'database', 'transform',
    ];

    return known_tools.filter(tool => text.includes(tool));
  }
}
```

### Step 4: Mode Effectiveness Scoring

Score how well each mode is performing based on correction frequency, success rate, and user satisfaction.

```typescript
interface ModeScores {
  mode_name: string;
  session_count: number;
  correction_frequency: number; // corrections per session
  self_correction_rate: number; // % of corrections that were self-corrections
  user_satisfaction_trend: number; // -1 to +1, based on tone analysis
  effectiveness_score: number; // 0 to 1, composite
  trending: 'improving' | 'stable' | 'degrading';
}

class ModeScorer {
  /**
   * Calculate effectiveness scores for all modes
   */
  scoreAllModes(
    reflections: ReflectionEntry[]
  ): Map<string, ModeScores> {
    const mode_data = new Map<string, ReflectionEntry[]>();

    // Group reflections by mode
    reflections.forEach(r => {
      if (!mode_data.has(r.mode)) {
        mode_data.set(r.mode, []);
      }
      mode_data.get(r.mode)!.push(r);
    });

    // Score each mode
    const scores = new Map<string, ModeScores>();
    mode_data.forEach((reflections, mode) => {
      scores.set(mode, this.scoreMode(mode, reflections));
    });

    return scores;
  }

  /**
   * Score a single mode
   */
  private scoreMode(mode_name: string, reflections: ReflectionEntry[]): ModeScores {
    const self_corrections = reflections.filter(
      r => r.trigger === 'model_self_correction'
    ).length;

    const user_corrections = reflections.filter(
      r => r.trigger === 'user_correction'
    ).length;

    const correction_frequency = reflections.length;
    const self_correction_rate = self_corrections / (reflections.length || 1);

    // Composite score: lower correction frequency is better, self-correction is better
    const base_score =
      (1 / (1 + correction_frequency * 0.1)) * 0.5 +
      self_correction_rate * 0.5;

    return {
      mode_name,
      session_count: 1, // Would aggregate across sessions in real system
      correction_frequency,
      self_correction_rate,
      user_satisfaction_trend: 0, // Would analyze user message tone
      effectiveness_score: Math.max(0, Math.min(1, base_score)),
      trending: 'stable', // Would trend over time
    };
  }
}
```

### Step 5: Project Context Update

Update project-level context files to reflect what's been learned.

```typescript
interface ProjectContext {
  project_id: string;
  last_updated: string;
  active_modes: string[];
  recent_corrections: string[];
  known_patterns: string[];
  tool_preferences: ToolUsageMetrics[];
  mode_scores: ModeScores[];
  knowledge_entries: string[];
}

class ProjectContextUpdater {
  /**
   * Update project context based on processing results
   */
  async updateProjectContext(
    project_id: string,
    results: Level2ProcessingResults
  ): Promise<void> {
    const context_path = `.opencode/context/${project_id}/learning.json`;

    let context: ProjectContext;
    try {
      context = JSON.parse(await readFile(context_path, 'utf-8'));
    } catch {
      context = {
        project_id,
        last_updated: '',
        active_modes: [],
        recent_corrections: [],
        known_patterns: [],
        tool_preferences: [],
        mode_scores: [],
        knowledge_entries: [],
      };
    }

    // Update with new results
    context.last_updated = new Date().toISOString();
    context.active_modes = results.mode_scores.map(m => m.mode_name);
    context.recent_corrections = results.reflections
      .slice(-10)
      .map(r => r.id);
    context.known_patterns = results.clusters.map(c => c.topic);
    context.tool_preferences = results.tool_metrics;
    context.mode_scores = results.mode_scores;
    context.knowledge_entries = results.knowledge_entries.map(ke => ke.id);

    // Write updated context
    await writeFile(
      context_path,
      JSON.stringify(context, null, 2),
      'utf-8'
    );
  }
}
```

### Level 2 Orchestration

```typescript
interface Level2ProcessingResults {
  reflections: ReflectionEntry[];
  clusters: ReflectionCluster[];
  knowledge_entries: KnowledgeEntry[];
  tool_metrics: ToolUsageMetrics[];
  mode_scores: ModeScores[];
  processing_duration_ms: number;
}

async function runLevel2Processing(
  state_snapshot: SystemState
): Promise<Level2ProcessingResults> {
  const start_time = Date.now();

  // Get unprocessed reflections
  const reflections = state_snapshot.unprocessed_reflections;

  if (reflections.length === 0) {
    return {
      reflections: [],
      clusters: [],
      knowledge_entries: [],
      tool_metrics: [],
      mode_scores: [],
      processing_duration_ms: 0,
    };
  }

  // Step 1: Cluster reflections
  const clusterer = new ReflectionClusterer();
  const clusters = clusterer.clusterReflections(reflections);

  // Step 2: Generate knowledge entries from clusters
  const knowledge_generator = new KnowledgeEntryGenerator();
  const knowledge_entries: KnowledgeEntry[] = [];
  for (const cluster of clusters) {
    const entry = await knowledge_generator.generateFromCluster(cluster);
    knowledge_entries.push(entry);

    // Immediately save to knowledge base
    await saveKnowledgeEntry(entry);
  }

  // Step 3: Analyze tool usage
  const tool_analyzer = new ToolAnalyzer();
  const tool_metrics = tool_analyzer.analyzeToolUsage(reflections);

  // Step 4: Score modes
  const mode_scorer = new ModeScorer();
  const mode_scores = Array.from(
    mode_scorer.scoreAllModes(reflections).values()
  );

  // Step 5: Update project context
  const context_updater = new ProjectContextUpdater();
  for (const project_id of state_snapshot.active_projects) {
    await context_updater.updateProjectContext(project_id, {
      reflections,
      clusters,
      knowledge_entries,
      tool_metrics,
      mode_scores,
      processing_duration_ms: Date.now() - start_time,
    });
  }

  return {
    reflections,
    clusters,
    knowledge_entries,
    tool_metrics,
    mode_scores,
    processing_duration_ms: Date.now() - start_time,
  };
}
```

---

## Level 3: Cross-Session Pattern Detection

### Purpose

Identify systemic issues and workflows that repeat across multiple sessions. This level detects:

1. **Recurring correction topics** - When the same correction pattern appears in multiple sessions
2. **Workflow fingerprints** - Multi-step sequences that happen repeatedly
3. **Mode drift** - Using a mode for work outside its intended scope
4. **New mode proposals** - When drift reveals an unserved need

### Trigger

Runs as part of Level 2 processing when sufficient historical data accumulates (typically once daily given daily digest requirement).

### Systemic vs. One-Off Corrections

The key insight: A single correction in a session is fine. Three corrections about the same topic across multiple sessions is a systemic gap.

```typescript
interface SystemicPattern {
  id: string;
  type: 'systemic_gap' | 'workflow' | 'mode_drift';
  topic: string;
  correction_count: number;
  session_count: number;
  affected_projects: string[];
  severity: 'low' | 'medium' | 'high';
  first_seen: string;
  last_seen: string;
  evidence: {
    knowledge_entry_ids: string[];
    cluster_ids: string[];
  };
}

class SystemicPatternDetector {
  /**
   * Detect systemic patterns from Level 2 results over time
   */
  async detectSystemicPatterns(
    historical_results: Level2ProcessingResults[],
    time_window_days: number = 7
  ): Promise<SystemicPattern[]> {
    // Aggregate knowledge entries across time window
    const knowledge_entries_by_topic = new Map<string, {
      entries: KnowledgeEntry[];
      sessions: Set<string>;
    }>();

    historical_results.forEach(result => {
      result.knowledge_entries.forEach(entry => {
        const topic = entry.title;
        if (!knowledge_entries_by_topic.has(topic)) {
          knowledge_entries_by_topic.set(topic, {
            entries: [],
            sessions: new Set(),
          });
        }

        const data = knowledge_entries_by_topic.get(topic)!;
        data.entries.push(entry);
        // Would need to track session ID in results
      });
    });

    // Find topics that appear in 3+ entries = systemic
    const systemic_patterns: SystemicPattern[] = [];

    knowledge_entries_by_topic.forEach((data, topic) => {
      if (data.entries.length >= 3) {
        const pattern: SystemicPattern = {
          id: generatePatternId(),
          type: 'systemic_gap',
          topic,
          correction_count: data.entries.length,
          session_count: data.sessions.size,
          affected_projects: [], // Would extract from entries
          severity: this.calculateSeverity(data.entries.length, data.sessions.size),
          first_seen: data.entries[0].created_at,
          last_seen: data.entries[data.entries.length - 1].created_at,
          evidence: {
            knowledge_entry_ids: data.entries.map(e => e.id),
            cluster_ids: data.entries.flatMap(e => e.source_clusters),
          },
        };
        systemic_patterns.push(pattern);
      }
    });

    return systemic_patterns;
  }

  private calculateSeverity(
    correction_count: number,
    session_count: number
  ): 'low' | 'medium' | 'high' {
    const frequency = correction_count / Math.max(session_count, 1);
    if (frequency >= 2.0) return 'high';
    if (frequency >= 1.0) return 'medium';
    return 'low';
  }
}
```

### Workflow Fingerprint Detection

Detect repeated multi-step sequences that could be automated as transaction scripts.

```typescript
interface WorkflowFingerprint {
  id: string;
  name: string;
  steps: string[];
  first_occurrence: string;
  occurrence_count: number;
  sessions: string[];
  is_automation_candidate: boolean;
  suggested_tool_name: string;
}

class WorkflowFingerprintDetector {
  /**
   * Detect recurring multi-step workflows from interaction sequences
   */
  async detectWorkflows(
    interaction_sequences: InteractionSequence[]
  ): Promise<WorkflowFingerprint[]> {
    // Build n-gram patterns from interaction sequences
    const workflow_patterns = new Map<string, {
      occurrences: number;
      sessions: Set<string>;
      first_seen: string;
    }>();

    interaction_sequences.forEach(seq => {
      // Extract 3-5 step patterns
      for (let window = 3; window <= 5; window++) {
        for (let i = 0; i <= seq.steps.length - window; i++) {
          const pattern = seq.steps
            .slice(i, i + window)
            .map(s => s.type)
            .join(' -> ');

          if (!workflow_patterns.has(pattern)) {
            workflow_patterns.set(pattern, {
              occurrences: 0,
              sessions: new Set(),
              first_seen: seq.timestamp,
            });
          }

          const data = workflow_patterns.get(pattern)!;
          data.occurrences++;
          data.sessions.add(seq.session_id);
        }
      }
    });

    // Filter for patterns that occur 3+ times in different sessions
    const fingerprints: WorkflowFingerprint[] = [];

    workflow_patterns.forEach((data, pattern) => {
      if (data.sessions.size >= 3) {
        const steps = pattern.split(' -> ');
        fingerprints.push({
          id: generateFingerprintId(),
          name: this.generateWorkflowName(steps),
          steps,
          first_occurrence: data.first_seen,
          occurrence_count: data.occurrences,
          sessions: Array.from(data.sessions),
          is_automation_candidate: steps.length >= 3 && data.occurrences >= 5,
          suggested_tool_name: this.suggestToolName(steps),
        });
      }
    });

    return fingerprints;
  }

  private generateWorkflowName(steps: string[]): string {
    return steps.slice(0, 3).join(' + ');
  }

  private suggestToolName(steps: string[]): string {
    return 'workflow_' + steps.join('_').toLowerCase().substring(0, 20);
  }
}
```

### Mode Drift Detection

Detect when a mode is being used for work outside its intended scope.

```typescript
interface ModeDriftEvent {
  id: string;
  mode_name: string;
  detected_use_case: string;
  intended_use_case: string;
  drift_score: number;
  sessions_with_drift: number;
  example_corrections: ReflectionEntry[];
  is_new_mode_candidate: boolean;
}

class ModeDriftDetector {
  /**
   * Detect mode drift by analyzing what work is being done in each mode
   */
  async detectDrift(
    reflections_by_mode: Map<string, ReflectionEntry[]>,
    mode_definitions: Map<string, ModeDefinition>
  ): Promise<ModeDriftEvent[]> {
    const drift_events: ModeDriftEvent[] = [];

    reflections_by_mode.forEach((reflections, mode_name) => {
      const mode_def = mode_definitions.get(mode_name);
      if (!mode_def) return;

      // Extract topics of corrections in this mode
      const correction_topics = reflections.map(r =>
        this.extractMainTopic(r.learning_content)
      );

      // Check if topics align with mode's intended scope
      const drift_score = this.calculateDriftScore(
        correction_topics,
        mode_def.intended_scope
      );

      if (drift_score > 0.3) {
        const detected_use_case = this.inferUseCase(correction_topics);

        drift_events.push({
          id: generateDriftId(),
          mode_name,
          detected_use_case,
          intended_use_case: mode_def.intended_scope,
          drift_score,
          sessions_with_drift: new Set(reflections.map(r => r.session_id)).size,
          example_corrections: reflections.slice(0, 3),
          is_new_mode_candidate: drift_score > 0.6,
        });
      }
    });

    return drift_events;
  }

  private calculateDriftScore(
    topics: string[],
    intended_scope: string
  ): number {
    // Simple similarity-based drift score
    const scope_words = intended_scope.toLowerCase().split(/\s+/);
    const matching_topics = topics.filter(topic =>
      scope_words.some(word => topic.toLowerCase().includes(word))
    ).length;

    return 1 - (matching_topics / Math.max(topics.length, 1));
  }

  private extractMainTopic(learning_content: ReflectionEntry['learning_content']): string {
    const text = [
      learning_content.wrong_approach,
      learning_content.correct_approach,
    ].join(' ');

    const words = text.toLowerCase().split(/\s+/);
    return words.find(w => w.length > 4) || 'general';
  }

  private inferUseCase(topics: string[]): string {
    return topics.slice(0, 3).join(', ');
  }
}
```

### Mode Creation Pipeline

When drift is detected, the system proposes a new mode. This is a three-step process:

**Step 1: Auto-Generate Mode Proposal**

```typescript
interface ModeProposal {
  id: string;
  name: string;
  persona: string;
  tool_constraints: {
    allowed: string[];
    forbidden: string[];
  };
  sample_prompt: string;
  derived_from_drift: ModeDriftEvent;
  created_at: string;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected';
}

class ModeProposalGenerator {
  /**
   * Generate a new mode proposal from detected drift
   */
  async generateProposal(
    drift_event: ModeDriftEvent
  ): Promise<ModeProposal> {
    // Use 8B model to draft mode definition
    const draft_prompt = `
Based on this detected gap in mode coverage:
- Detected use case: ${drift_event.detected_use_case}
- Current mode being misused: ${drift_event.mode_name}
- Example corrections from this gap:
${drift_event.example_corrections
  .map(r => `  - ${r.learning_content.wrong_approach}`)
  .join('\n')}

Generate a new mode that would serve this use case well. Return JSON with:
{
  "name": "descriptive-name-kebab-case",
  "persona": "Brief persona for this mode (20-30 words)",
  "tool_constraints": {
    "allowed": ["tool1", "tool2"],
    "forbidden": ["tool3", "tool4"]
  },
  "description": "What this mode is for"
}
`;

    const response = await this.callSynthesisModel(draft_prompt);
    const parsed = JSON.parse(response);

    // Generate sample prompt for the new mode
    const sample_prompt = await this.generateSamplePrompt(
      parsed.name,
      parsed.persona,
      drift_event.detected_use_case
    );

    return {
      id: generateProposalId(),
      name: parsed.name,
      persona: parsed.persona,
      tool_constraints: parsed.tool_constraints,
      sample_prompt,
      derived_from_drift: drift_event,
      created_at: new Date().toISOString(),
      status: 'draft',
    };
  }

  private async generateSamplePrompt(
    name: string,
    persona: string,
    use_case: string
  ): Promise<string> {
    // Generate a sample system prompt for this mode
    const prompt_gen_prompt = `
Create a system prompt for a new mode called "${name}".
Persona: ${persona}
Use case: ${use_case}

The prompt should be 150-200 words, use positive framing ("do X" not "don't Y"),
put critical rules at the beginning and end, and be task-specific.

Return only the system prompt text, no JSON.
`;

    return await this.callSynthesisModel(prompt_gen_prompt);
  }

  private async callSynthesisModel(prompt: string): Promise<string> {
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'qwen3:8b',
        prompt,
        stream: false,
        temperature: 0.4,
      }),
    });

    const data = await response.json();
    return data.response;
  }
}
```

**Step 2: Present Conversationally to Bryan**

```typescript
interface ModeReviewRequest {
  proposal: ModeProposal;
  drift_evidence: ModeDriftEvent;
  confidence: number;
  deadline: string;
}

class ConversationalModeReview {
  /**
   * Present mode proposal to user for feedback
   * This is a conversational interaction, not automatic
   */
  async presentProposalForReview(
    proposal: ModeProposal,
    drift_event: ModeDriftEvent
  ): Promise<void> {
    // Enqueue a conversational message to the user
    await queueConversationalMessage({
      type: 'mode_proposal',
      subject: `New mode proposal: ${proposal.name}`,
      body: `
I've detected that you're using the "${drift_event.mode_name}" mode for work that falls outside its intended scope.

You've made ${drift_event.sessions_with_drift} corrections about this over multiple sessions.

I'm proposing a new mode: **${proposal.name}**

**Persona**: ${proposal.persona}

**Sample prompt**:
${proposal.sample_prompt}

**Tools this mode can use**: ${proposal.tool_constraints.allowed.join(', ')}

You can:
1. Approve this mode as-is
2. Suggest adjustments to the name or persona
3. Modify the tool constraints
4. Reject and continue using "${drift_event.mode_name}"

What would you prefer?
      `,
      proposal_id: proposal.id,
      requires_response: true,
    });
  }
}
```

**Step 3: Finalize Mode File**

```typescript
interface ModeDefinition {
  id: string;
  name: string;
  created_at: string;
  source: 'user_created' | 'ai_proposed' | 'community';
  proposal_id?: string; // Links back to proposal if AI-generated
  system_prompt: string;
  persona: string;
  intended_scope: string;
  tool_constraints: {
    allowed: string[];
    forbidden: string[];
  };
  metadata: {
    effectiveness_score?: number;
    usage_count?: number;
  };
}

class ModeFinalizer {
  /**
   * Create the mode file after user approval
   */
  async finalizeMode(
    proposal: ModeProposal,
    user_adjustments?: {
      name?: string;
      persona?: string;
      tool_constraints?: {
        allowed: string[];
        forbidden: string[];
      };
    }
  ): Promise<ModeDefinition> {
    // Apply user adjustments if provided
    const final_name = user_adjustments?.name || proposal.name;
    const final_persona = user_adjustments?.persona || proposal.persona;
    const final_constraints = user_adjustments?.tool_constraints ||
                              proposal.tool_constraints;

    // Generate the mode file content
    const mode_def: ModeDefinition = {
      id: generateModeId(),
      name: final_name,
      created_at: new Date().toISOString(),
      source: 'ai_proposed',
      proposal_id: proposal.id,
      system_prompt: proposal.sample_prompt,
      persona: final_persona,
      intended_scope: proposal.derived_from_drift.detected_use_case,
      tool_constraints: final_constraints,
      metadata: {
        effectiveness_score: 0.5,
        usage_count: 0,
      },
    };

    // Write to mode file
    const mode_file_path = `~/.config/opencode/modes/${final_name}.yaml`;
    await writeFile(
      mode_file_path,
      this.convertToYaml(mode_def),
      'utf-8'
    );

    return mode_def;
  }

  private convertToYaml(mode_def: ModeDefinition): string {
    // Convert mode definition to YAML format
    // This would use a YAML serializer in production
    return `
id: ${mode_def.id}
name: ${mode_def.name}
created_at: ${mode_def.created_at}
source: ${mode_def.source}
persona: |
  ${mode_def.persona}
intended_scope: ${mode_def.intended_scope}
system_prompt: |
  ${mode_def.system_prompt.split('\n').join('\n  ')}
tool_constraints:
  allowed:
${mode_def.tool_constraints.allowed.map(t => `    - ${t}`).join('\n')}
  forbidden:
${mode_def.tool_constraints.forbidden.map(t => `    - ${t}`).join('\n')}
metadata:
  effectiveness_score: ${mode_def.metadata.effectiveness_score}
  usage_count: ${mode_def.metadata.usage_count}
    `.trim();
  }
}
```

---

## Level 4: Cross-Project Learning

### Purpose

Promote proven patterns from single projects to the shared user library, and identify improvements that benefit all projects.

### Three-Tier Scope Architecture

```
Project Level:     .opencode/knowledge/{mode}/
                   Project-specific, not shared
                   ↓
User Level:        ~/.config/opencode/knowledge/{mode}/
                   Shared across all your projects
                   ↓
Public Level:      ~/.config/opencode/community/outbound/
                   Staged for community sharing
```

### Cross-Project Aggregation

```typescript
interface CrossProjectMetrics {
  correction_topic: string;
  project_count: number;
  affected_projects: string[];
  total_occurrences: number;
  is_systemic_across_projects: boolean;
  recommendation: 'promote_to_user_lib' | 'promote_to_public' | 'watch';
}

class CrossProjectAggregator {
  /**
   * Aggregate knowledge entries from multiple projects
   * Identify patterns that appear in 2+ projects
   */
  async aggregateCrossProject(
    project_ids: string[]
  ): Promise<CrossProjectMetrics[]> {
    const knowledge_by_topic = new Map<string, {
      projects: Set<string>;
      entry_ids: string[];
      total_count: number;
    }>();

    // Scan knowledge base in each project
    for (const project_id of project_ids) {
      const knowledge_path = `.opencode/knowledge/`;
      const entries = await this.loadProjectKnowledge(project_id, knowledge_path);

      entries.forEach(entry => {
        const topic = entry.title;
        if (!knowledge_by_topic.has(topic)) {
          knowledge_by_topic.set(topic, {
            projects: new Set(),
            entry_ids: [],
            total_count: 0,
          });
        }

        const data = knowledge_by_topic.get(topic)!;
        data.projects.add(project_id);
        data.entry_ids.push(entry.id);
        data.total_count += entry.metadata.original_reflection_count;
      });
    }

    // Filter for cross-project patterns (2+ projects)
    const metrics: CrossProjectMetrics[] = [];
    knowledge_by_topic.forEach((data, topic) => {
      if (data.projects.size >= 2) {
        metrics.push({
          correction_topic: topic,
          project_count: data.projects.size,
          affected_projects: Array.from(data.projects),
          total_occurrences: data.total_count,
          is_systemic_across_projects: true,
          recommendation: data.projects.size >= 3 ? 'promote_to_public' : 'promote_to_user_lib',
        });
      }
    });

    return metrics;
  }

  private async loadProjectKnowledge(
    project_id: string,
    knowledge_path: string
  ): Promise<KnowledgeEntry[]> {
    // Load all knowledge entries from a project's knowledge base
    try {
      const files = await listFiles(`${project_id}/${knowledge_path}`);
      const entries: KnowledgeEntry[] = [];

      for (const file of files) {
        if (file.endsWith('.json')) {
          const content = await readFile(
            `${project_id}/${knowledge_path}/${file}`,
            'utf-8'
          );
          entries.push(JSON.parse(content));
        }
      }

      return entries;
    } catch {
      return [];
    }
  }
}
```

### Promotion Pipeline

```typescript
interface PromotionEvent {
  id: string;
  source_level: 'project' | 'user';
  target_level: 'user' | 'public';
  knowledge_entry_id: string;
  source_projects: string[];
  validation_status: 'pending' | 'validated' | 'rejected';
  privacy_check: boolean;
  promoted_at?: string;
}

class PromotionPipeline {
  /**
   * Promote a knowledge entry from project to user library
   */
  async promoteToUserLibrary(
    knowledge_entry: KnowledgeEntry,
    source_projects: string[]
  ): Promise<PromotionEvent> {
    // Step 1: Privacy check
    const has_sensitive_data = this.checkForSensitiveData(knowledge_entry);
    if (has_sensitive_data) {
      return {
        id: generatePromotionId(),
        source_level: 'project',
        target_level: 'user',
        knowledge_entry_id: knowledge_entry.id,
        source_projects,
        validation_status: 'rejected',
        privacy_check: false,
      };
    }

    // Step 2: Validate applicability
    const is_broadly_applicable = this.validateApplicability(knowledge_entry);
    if (!is_broadly_applicable) {
      return {
        id: generatePromotionId(),
        source_level: 'project',
        target_level: 'user',
        knowledge_entry_id: knowledge_entry.id,
        source_projects,
        validation_status: 'pending', // Manual review needed
        privacy_check: true,
      };
    }

    // Step 3: Copy to user library
    const user_lib_path = `~/.config/opencode/knowledge/${knowledge_entry.type}/${knowledge_entry.id}.json`;
    await this.ensureDirectory(user_lib_path);
    await writeFile(user_lib_path, JSON.stringify(knowledge_entry, null, 2));

    return {
      id: generatePromotionId(),
      source_level: 'project',
      target_level: 'user',
      knowledge_entry_id: knowledge_entry.id,
      source_projects,
      validation_status: 'validated',
      privacy_check: true,
      promoted_at: new Date().toISOString(),
    };
  }

  /**
   * Promote from user library to public repository
   */
  async promoteToPublic(
    knowledge_entry: KnowledgeEntry,
    affected_projects: string[]
  ): Promise<PromotionEvent> {
    // Step 1: Privacy check (stricter for public)
    const has_sensitive_data = this.checkForSensitiveDataStrict(knowledge_entry);
    if (has_sensitive_data) {
      return {
        id: generatePromotionId(),
        source_level: 'user',
        target_level: 'public',
        knowledge_entry_id: knowledge_entry.id,
        source_projects: affected_projects,
        validation_status: 'rejected',
        privacy_check: false,
      };
    }

    // Step 2: Add provenance metadata
    const public_entry = this.addProvenanceMetadata(
      knowledge_entry,
      affected_projects
    );

    // Step 3: Stage in outbound folder
    const outbound_path = `~/.config/opencode/community/outbound/${knowledge_entry.id}.json`;
    await writeFile(outbound_path, JSON.stringify(public_entry, null, 2));

    return {
      id: generatePromotionId(),
      source_level: 'user',
      target_level: 'public',
      knowledge_entry_id: knowledge_entry.id,
      source_projects: affected_projects,
      validation_status: 'pending', // Requires user approval before public push
      privacy_check: true,
      promoted_at: new Date().toISOString(),
    };
  }

  private checkForSensitiveData(entry: KnowledgeEntry): boolean {
    const text = JSON.stringify(entry).toLowerCase();
    const sensitive_patterns = [
      'password', 'key', 'token', 'secret', 'credential',
      'api_key', 'database_url', 'email@', 'phone:',
    ];

    return sensitive_patterns.some(pattern => text.includes(pattern));
  }

  private checkForSensitiveDataStrict(entry: KnowledgeEntry): boolean {
    // Stricter check for public promotion
    return this.checkForSensitiveData(entry) ||
           entry.metadata.original_reflection_count < 5; // Too few occurrences
  }

  private validateApplicability(entry: KnowledgeEntry): boolean {
    // Check if the entry is broadly applicable
    // (not domain-specific or project-specific)
    const text = JSON.stringify(entry).toLowerCase();

    // If it mentions specific project names or company names, it's not broadly applicable
    const specific_keywords = ['mycompany', 'internal', 'proprietary'];
    const is_specific = specific_keywords.some(kw => text.includes(kw));

    return !is_specific;
  }

  private addProvenanceMetadata(
    entry: KnowledgeEntry,
    affected_projects: string[]
  ): any {
    return {
      ...entry,
      provenance: {
        original_id: entry.id,
        sourced_from_projects: affected_projects,
        validation_count: affected_projects.length,
        measured_improvement: 'placeholder', // Would calculate actual improvement
        promoted_at: new Date().toISOString(),
      },
    };
  }

  private async ensureDirectory(file_path: string): Promise<void> {
    const dir = file_path.substring(0, file_path.lastIndexOf('/'));
    try {
      await stat(dir);
    } catch {
      await mkdir(dir, { recursive: true });
    }
  }
}
```

---

## Level 5: Ecosystem Learning

### Purpose

Bidirectional knowledge exchange with the community. Outbound: proven artifacts are shared with proper provenance. Inbound: community contributions are validated before integration.

### Outbound Learning

Promoted artifacts move from user library to public repository with provenance tracking.

```typescript
interface ProvenanceMetadata {
  original_author_id: string; // Anonymous user ID
  source_correction_pattern: string;
  validation_count: number; // How many projects validated it
  measurable_improvements: {
    metric: string;
    before: number;
    after: number;
  }[];
  promoted_at: string;
  license: string;
}

class OutboundSharingPipeline {
  /**
   * Publish validated user-library knowledge to community
   */
  async publishToPublicRepository(
    knowledge_entry: KnowledgeEntry,
    provenance: ProvenanceMetadata
  ): Promise<void> {
    // Create public artifact with provenance
    const public_artifact = {
      ...knowledge_entry,
      provenance,
      license: 'CC-BY-4.0', // Creative Commons with attribution
    };

    // Push to community repository
    const repo_path = `https://github.com/crux-community/knowledge-base`;
    await this.pushToCommunityRepo(public_artifact, repo_path);

    // Log for tracking
    await logPublicPromotion({
      entry_id: knowledge_entry.id,
      timestamp: new Date().toISOString(),
      provenance,
    });
  }

  private async pushToCommunityRepo(
    artifact: any,
    repo_path: string
  ): Promise<void> {
    // Implementation: Push to community repo with proper attribution
    // This would use git commands or API calls
  }
}
```

### Inbound Learning

Community contributions enter through a staging layer and must prove value before integration.

```typescript
interface CommunityContribution {
  id: string;
  source_url: string;
  source_user_id: string;
  staged_at: string;
  status: 'staged' | 'testing' | 'integrated' | 'rejected';
  test_sessions: number;
  validation_score: number;
}

class InboundValidationPipeline {
  /**
   * Stage community contributions for testing
   */
  async stageContribution(
    contribution_metadata: {
      url: string;
      user_id: string;
    }
  ): Promise<CommunityContribution> {
    const staged: CommunityContribution = {
      id: generateContributionId(),
      source_url: contribution_metadata.url,
      source_user_id: contribution_metadata.user_id,
      staged_at: new Date().toISOString(),
      status: 'staged',
      test_sessions: 0,
      validation_score: 0,
    };

    // Store in staging directory
    await writeFile(
      `~/.config/opencode/community/staged/${staged.id}.json`,
      JSON.stringify(staged, null, 2)
    );

    return staged;
  }

  /**
   * Validate a contribution by testing it in user's projects
   * This is automatic and happens over multiple sessions
   */
  async validateContribution(
    contribution_id: string,
    project_ids: string[]
  ): Promise<void> {
    const contribution = await this.loadStagedContribution(contribution_id);

    // Fetch the contribution from community source
    const artifact = await fetch(contribution.source_url).then(r => r.json());

    // Copy to each project's testing directory
    for (const project_id of project_ids) {
      const test_path = `${project_id}/.opencode/test-community/${contribution_id}/`;
      await mkdir(test_path, { recursive: true });
      await writeFile(
        `${test_path}/contribution.json`,
        JSON.stringify(artifact, null, 2)
      );
    }

    // Update status
    contribution.status = 'testing';
    contribution.test_sessions = 0;
    await writeFile(
      `~/.config/opencode/community/staged/${contribution_id}.json`,
      JSON.stringify(contribution, null, 2)
    );
  }

  /**
   * Check validation results after contribution has been tested
   */
  async checkValidationResults(
    contribution_id: string
  ): Promise<'integrate' | 'reject' | 'continue_testing'> {
    const contribution = await this.loadStagedContribution(contribution_id);

    // Calculate validation score based on:
    // - Usage frequency in test sessions
    // - Correction reductions in tested areas
    // - User satisfaction signals

    if (contribution.validation_score >= 0.8) {
      return 'integrate';
    } else if (contribution.validation_score >= 0.5) {
      return 'continue_testing';
    } else {
      return 'reject';
    }
  }

  /**
   * Integrate validated community contribution
   */
  async integrateContribution(contribution_id: string): Promise<void> {
    const contribution = await this.loadStagedContribution(contribution_id);
    const artifact = await this.loadArtifact(contribution.source_url);

    // Move from staging to user library
    const user_lib_path = `~/.config/opencode/knowledge/${artifact.type}/${contribution_id}.json`;
    await writeFile(user_lib_path, JSON.stringify(artifact, null, 2));

    // Mark as integrated
    contribution.status = 'integrated';
    await writeFile(
      `~/.config/opencode/community/staged/${contribution_id}.json`,
      JSON.stringify(contribution, null, 2)
    );
  }

  private async loadStagedContribution(
    id: string
  ): Promise<CommunityContribution> {
    const content = await readFile(
      `~/.config/opencode/community/staged/${id}.json`,
      'utf-8'
    );
    return JSON.parse(content);
  }

  private async loadArtifact(url: string): Promise<any> {
    const response = await fetch(url);
    return response.json();
  }
}
```

---

## Data Structures and Schemas

### Complete Type Definitions

```typescript
// Level 1
interface ReflectionEntry {
  id: string;
  type: 'reflection';
  session_id: string;
  trigger: 'user_correction' | 'model_self_correction' | 'tool_retry' | 'script_audit';
  mode: string;
  interaction_number: number;
  timestamp: string;
  context: {
    user_message: string;
    model_message_before: string;
    model_correction: string;
    project_id: string;
  };
  learning_content: {
    wrong_approach: string;
    correct_approach: string;
    reasoning: string;
    applicable_domains: string[];
  };
  metadata: {
    correction_confidence: number;
    pattern_similarity: string[];
    is_first_correction_in_session: boolean;
  };
}

// Level 2
interface ReflectionCluster {
  id: string;
  topic: string;
  reflections: ReflectionEntry[];
  keywords: string[];
  confidence: number;
  created_at: string;
}

interface KnowledgeEntry {
  id: string;
  type: 'technique' | 'pattern' | 'gotcha' | 'best-practice';
  title: string;
  summary: string;
  problem_statement: string;
  solution: string;
  code_example?: string;
  reasoning: string;
  applicable_to: string[];
  source_clusters: string[];
  confidence: number;
  created_at: string;
  metadata: {
    original_reflection_count: number;
    average_correction_confidence: number;
    domains: string[];
  };
}

// Level 3
interface SystemicPattern {
  id: string;
  type: 'systemic_gap' | 'workflow' | 'mode_drift';
  topic: string;
  correction_count: number;
  session_count: number;
  affected_projects: string[];
  severity: 'low' | 'medium' | 'high';
  first_seen: string;
  last_seen: string;
  evidence: {
    knowledge_entry_ids: string[];
    cluster_ids: string[];
  };
}

interface ModeDriftEvent {
  id: string;
  mode_name: string;
  detected_use_case: string;
  intended_use_case: string;
  drift_score: number;
  sessions_with_drift: number;
  example_corrections: ReflectionEntry[];
  is_new_mode_candidate: boolean;
}

interface ModeProposal {
  id: string;
  name: string;
  persona: string;
  tool_constraints: {
    allowed: string[];
    forbidden: string[];
  };
  sample_prompt: string;
  derived_from_drift: ModeDriftEvent;
  created_at: string;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected';
}

interface ModeDefinition {
  id: string;
  name: string;
  created_at: string;
  source: 'user_created' | 'ai_proposed' | 'community';
  proposal_id?: string;
  system_prompt: string;
  persona: string;
  intended_scope: string;
  tool_constraints: {
    allowed: string[];
    forbidden: string[];
  };
  metadata: {
    effectiveness_score?: number;
    usage_count?: number;
  };
}

// Level 4
interface CrossProjectMetrics {
  correction_topic: string;
  project_count: number;
  affected_projects: string[];
  total_occurrences: number;
  is_systemic_across_projects: boolean;
  recommendation: 'promote_to_user_lib' | 'promote_to_public' | 'watch';
}

interface PromotionEvent {
  id: string;
  source_level: 'project' | 'user';
  target_level: 'user' | 'public';
  knowledge_entry_id: string;
  source_projects: string[];
  validation_status: 'pending' | 'validated' | 'rejected';
  privacy_check: boolean;
  promoted_at?: string;
}

// Level 5
interface ProvenanceMetadata {
  original_author_id: string;
  source_correction_pattern: string;
  validation_count: number;
  measurable_improvements: {
    metric: string;
    before: number;
    after: number;
  }[];
  promoted_at: string;
  license: string;
}

interface CommunityContribution {
  id: string;
  source_url: string;
  source_user_id: string;
  staged_at: string;
  status: 'staged' | 'testing' | 'integrated' | 'rejected';
  test_sessions: number;
  validation_score: number;
}
```

### Persistent Storage Layout

```
~/.crux/
├── sessions/
│   └── {session_id}/
│       ├── reflections.jsonl          # Level 1 reflections (append-only)
│       └── context.json                # Session context
│
├── projects/
│   └── {project_id}/
│       ├── .opencode/
│       │   ├── knowledge/              # Level 2 knowledge entries
│       │   │   ├── techniques/
│       │   │   ├── patterns/
│       │   │   └── gotchas/
│       │   ├── context/
│       │   │   └── learning.json       # Level 2 context
│       │   └── test-community/         # Level 5 inbound testing
│       │       └── {contribution_id}/
│       │
│       └── level3-patterns/            # Level 3 systemic patterns
│           ├── mode-drift/
│           └── workflows/
│
~/.config/opencode/
├── knowledge/                          # Level 4 user library
│   ├── techniques/
│   ├── patterns/
│   ├── gotchas/
│   └── best-practices/
│
├── modes/                              # Mode definitions
│   ├── build-ex.yaml
│   ├── debug-py.yaml
│   └── {auto_created_modes}/
│
├── community/
│   ├── outbound/                       # Level 5 ready for publishing
│   │   └── {knowledge_id}.json
│   │
│   └── staged/                         # Level 5 inbound validation
│       └── {contribution_id}.json
│
└── learning-state/
    ├── level2-processing.json          # Last processing timestamp
    └── promotion-history.jsonl         # Level 4/5 audit trail
```

---

## Research Foundation

### DSPy: Automated Prompt Optimization

The Crux system uses insights from DSPy (Stanford) for prompt engineering:

- **Modular prompt design**: System prompts are composed of discrete, testable components
- **Metric-driven optimization**: Effectiveness measured by correction reduction rate
- **Bootstrapping**: Short, concrete examples (modes) outperform elaborate backstories

**Implication for Crux**: Knowledge entries should be concise, action-oriented, and paired with working examples.

### Reflexion Architecture (Shinn et al.)

The correction detection mechanism is informed by Reflexion's linguistic reinforcement learning pattern:

- **Self-correction signals**: The model learns when to second-guess itself
- **Trajectory analysis**: Looking at the conversation flow (not just final output)
- **Reinforced patterns**: Corrections that the user validates are reinforced in context

**Implication for Crux**: Level 1 detection benefits from multiple signals (user explicit, model implicit, tool failure), mirroring Reflexion's multi-signal approach.

### LLM-as-Judge Biases

Research on LLM evaluation reveals systemic biases that must be mitigated:

- **Self-enhancement bias** (5-7%): Models inflate their own correctness
- **Position bias** (~40%): First and last positions in system prompts receive disproportionate weight
- **Verbosity bias** (~15%): Longer explanations rate higher regardless of correctness

**Mitigations in Crux**:

1. **Five-gate auditing pipeline**: Use a different model family (8B) as "auditor" to catch self-enhancement bias
2. **Prime position placement**: Critical rules at beginning and end of mode prompts
3. **Positive framing**: All knowledge entries and prompts use "do X" not "don't Y" to reduce verbosity inflation

### Prompt Optimization Research

**Optimal prompt length for modes**: 150-200 words
- Shorter: Too vague
- Longer: Triggers verbosity bias, reduces recall of critical rules

**Simple personas outperform elaborate backstories**:
- Good: "You are a backend architect designing scalable systems"
- Bad: "You are a 20-year veteran architect who learned from every major platform disaster"

The elaborate version triggers position bias toward the narrative, distracting from the actual task.

---

## Implementation Guidelines

### Error Handling and Resilience

```typescript
class ProcessingErrorHandler {
  /**
   * Graceful degradation for Level 2 processing failures
   */
  async runWithFallback(
    operation: () => Promise<any>
  ): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      const data = await operation();
      return { success: true, data };
    } catch (error) {
      // Log but don't block
      await logProcessingError({
        error: error.message,
        timestamp: new Date().toISOString(),
        operation: operation.name,
      });

      // Return empty results instead of failing
      return { success: false, error: error.message };
    }
  }

  /**
   * Prevent infinite loops in mode creation
   */
  async withProposalRateLimiting(
    mode_name: string,
    operation: () => Promise<ModeProposal>
  ): Promise<ModeProposal | null> {
    // Check if we've recently proposed a mode for this issue
    const recent_proposals = await this.getRecentProposals(mode_name);

    if (recent_proposals.length >= 3) {
      // Don't spam proposals; wait 7 days
      return null;
    }

    return operation();
  }

  private async getRecentProposals(topic: string): Promise<ModeProposal[]> {
    // Implementation: Query recent proposals
    return [];
  }
}
```

### Configuration and Tuning

```typescript
interface ContinuousLearningConfig {
  // Level 2 thresholds
  unprocessed_reflections_threshold: number;       // Default: 10
  interactions_since_processing_threshold: number; // Default: 50
  tokens_since_processing_threshold: number;       // Default: 5000

  // Level 3 systemic pattern detection
  min_sessions_for_systemic: number;    // Default: 3
  min_reflections_for_systemic: number; // Default: 5

  // Level 4 promotion requirements
  min_validation_projects: number;      // Default: 2 for user lib, 3 for public
  privacy_check_enabled: boolean;       // Default: true

  // Level 5 community features
  allow_outbound_sharing: boolean;      // Default: false
  auto_validate_community: boolean;     // Default: false
  community_test_duration_days: number; // Default: 7

  // Model selection
  synthesis_model: string;              // Default: 'qwen3:8b'
  main_model: string;                   // Default: main LLM (32B+)

  // Mode creation
  conversational_mode_creation: boolean; // Default: true
  mode_proposal_cooldown_days: number;   // Default: 7
}
```

### Integration Hooks

The continuous learning system must integrate with the main Crux system via these hooks:

```typescript
interface ContinuousLearningHooks {
  // Called after each model response
  onInteractionComplete(
    interaction: {
      user_message: string;
      model_response: string;
      tools_used?: string[];
      mode: string;
      session_id: string;
    }
  ): Promise<void>;

  // Called periodically to check processing thresholds
  checkProcessingThresholds(): Promise<void>;

  // Called when mode drift is detected
  onModeDriftDetected(drift: ModeDriftEvent): Promise<void>;

  // Called when promotion is ready
  onPromotionReady(
    entry: KnowledgeEntry,
    target_level: 'user' | 'public'
  ): Promise<void>;

  // Called to present conversational interactions
  queueConversationalMessage(message: ConversationalMessage): Promise<void>;
}
```

---

## Daily Digest System

### Purpose

Summarize daily learning and escalate unaddressed recommendations.

### Daily Digest Structure

```typescript
interface DailyDigest {
  date: string;
  session_count: number;
  total_interactions: number;
  highlights: {
    systemic_gaps: SystemicPattern[];
    mode_drift_events: ModeDriftEvent[];
    new_mode_proposals: ModeProposal[];
    promoted_entries: KnowledgeEntry[];
  };
  escalations: {
    ignored_for_days: number;
    recommendation: string;
    action_required: boolean;
  }[];
  statistics: {
    corrections_detected: number;
    knowledge_entries_generated: number;
    promoted_to_user_library: number;
  };
  generated_at: string;
}

class DailyDigestGenerator {
  /**
   * Generate daily digest of learning activities
   */
  async generateDailyDigest(date: string): Promise<DailyDigest> {
    const start_of_day = new Date(date).getTime();
    const end_of_day = start_of_day + 24 * 60 * 60 * 1000;

    // Gather today's activities
    const reflections = await this.getReflectionsInRange(start_of_day, end_of_day);
    const level2_results = await this.getLevel2ResultsInRange(start_of_day, end_of_day);
    const level3_events = await this.getLevel3EventsInRange(start_of_day, end_of_day);
    const promotions = await this.getPromotionsInRange(start_of_day, end_of_day);

    // Identify escalations (unaddressed items from previous days)
    const escalations = await this.identifyEscalations(date);

    return {
      date,
      session_count: new Set(reflections.map(r => r.session_id)).size,
      total_interactions: reflections.reduce((sum, r) => sum + r.interaction_number, 0),
      highlights: {
        systemic_gaps: level3_events.filter(e => e.type === 'systemic_gap'),
        mode_drift_events: level3_events.filter(e => e.type === 'mode_drift'),
        new_mode_proposals: level3_events.filter(e => e.type === 'mode_proposal'),
        promoted_entries: promotions.map(p => p.entry),
      },
      escalations,
      statistics: {
        corrections_detected: reflections.length,
        knowledge_entries_generated: level2_results.flatMap(r => r.knowledge_entries).length,
        promoted_to_user_library: promotions.filter(p => p.target === 'user').length,
      },
      generated_at: new Date().toISOString(),
    };
  }

  private async identifyEscalations(current_date: string): Promise<any[]> {
    // Check what was recommended yesterday
    const yesterday = new Date(current_date);
    yesterday.setDate(yesterday.getDate() - 1);

    const yesterday_digest = await this.loadDigest(yesterday.toISOString().split('T')[0]);
    if (!yesterday_digest) return [];

    // See which items were ignored
    const ignored_items = yesterday_digest.highlights.new_mode_proposals.filter(
      proposal => !this.wasActionTaken(proposal.id)
    );

    return ignored_items.map(item => ({
      ignored_for_days: 1,
      recommendation: `Mode proposal: ${item.name}`,
      action_required: true,
    }));
  }

  private wasActionTaken(item_id: string): boolean {
    // Check if user has approved/rejected/engaged with item
    return false; // Placeholder
  }

  private async loadDigest(date: string): Promise<DailyDigest | null> {
    try {
      const content = await readFile(
        `~/.crux/digests/${date}.json`,
        'utf-8'
      );
      return JSON.parse(content);
    } catch {
      return null;
    }
  }

  private async getReflectionsInRange(start: number, end: number): Promise<ReflectionEntry[]> {
    return []; // Placeholder
  }

  private async getLevel2ResultsInRange(start: number, end: number): Promise<Level2ProcessingResults[]> {
    return []; // Placeholder
  }

  private async getLevel3EventsInRange(start: number, end: number): Promise<SystemicPattern[]> {
    return []; // Placeholder
  }

  private async getPromotionsInRange(start: number, end: number): Promise<PromotionEvent[]> {
    return []; // Placeholder
  }
}
```

---

## Conclusion

The Crux continuous learning infrastructure is a five-level system designed around the principle of organic, automatic learning with zero manual maintenance. Each level builds on the previous:

1. **Level 1** captures corrections in real-time, staying in context for immediate in-session learning
2. **Level 2** synthesizes patterns asynchronously without blocking the user
3. **Level 3** detects systemic issues and proposes new modes conversationally
4. **Level 4** promotes proven patterns across projects
5. **Level 5** shares validated knowledge with the community

The system respects research findings on LLM optimization, uses tiered model sizes (8B for synthesis to avoid blocking), implements strict privacy controls, and provides daily digests with escalation logic.

All processing is threshold-driven (not time-based), background-executed (not blocking), and conversational where human judgment is needed (mode creation).
