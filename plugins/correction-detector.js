import fs from 'fs/promises';
import path from 'path';

// Pattern categories for structured detection
const PATTERNS = {
  self_correction: [
    /^(?:actually|wait|hold on|never mind|scratch that)/i,
    /^(?:instead|better)\s/i,
    /^let me (?:try|fix|correct|rephrase)/i,
    /^i (?:meant|should have|was wrong)/i,
  ],
  negation: [
    /^no[,.\s]/i,
    /\b(?:wrong|incorrect|that's not right)\b/i,
    /\bi said\b/i,
    /\bnot what i (?:asked|wanted|meant)\b/i,
    /^(?:cancel|disregard|stop)\s/i,
  ],
  retry_request: [
    /\btry again\b/i,
    /\bredo (?:that|this|it)\b/i,
    /\bstart over\b/i,
    /\bdo it (?:differently|another way)\b/i,
  ],
};

// Track recent tool calls for retry detection
let recentToolCalls = [];
const MAX_TOOL_HISTORY = 20;

function detectPattern(content) {
  for (const [category, patterns] of Object.entries(PATTERNS)) {
    for (const pattern of patterns) {
      if (pattern.test(content)) {
        return { category, pattern: pattern.toString() };
      }
    }
  }
  return null;
}

function detectToolRetry(execution) {
  const recent = recentToolCalls.filter(
    tc => tc.tool === execution.tool && tc.tool !== 'read' && tc.tool !== 'glob' && tc.tool !== 'grep'
  );
  if (recent.length === 0) return false;

  const last = recent[recent.length - 1];
  const currentParams = JSON.stringify(execution.params);
  const lastParams = JSON.stringify(last.params);
  return currentParams !== lastParams;
}

async function _writeReflection(reflection) {
  try {
    const reflectionsDir = path.join(process.env.HOME, '.crux/corrections');
    await fs.mkdir(reflectionsDir, { recursive: true });

    const today = new Date().toISOString().split('T')[0];
    const reflectionFile = path.join(reflectionsDir, `${today}.jsonl`);

    await fs.appendFile(
      reflectionFile,
      JSON.stringify(reflection) + '\n',
      'utf8'
    );
  } catch (err) {
    console.error('Correction detector error:', err);
  }
}

// OpenCode plugin factory
export const CorrectionDetectorPlugin = async (ctx) => {
  return {
    event: async ({ event }) => {
      if (event.type === 'message.updated') {
        const oldMessage = event.properties?.old || { content: '' };
        const newMessage = event.properties?.new || { content: '' };
        const detection = detectPattern(newMessage.content);
        if (!detection) return;

        const reflection = {
          timestamp: new Date().toISOString(),
          type: 'self-correction',
          category: detection.category,
          original: oldMessage.content.substring(0, 100),
          corrected: newMessage.content.substring(0, 100),
          pattern: detection.pattern,
          mode: newMessage.mode || oldMessage.mode || 'unknown',
        };

        await _writeReflection(reflection);
      }
    },

    'tool.execute.before': async (input, output) => {
      const tool = input.tool;
      const params = output.args || {};
      const isRetry = detectToolRetry({ tool, params });

      recentToolCalls.push({ tool, params, timestamp: Date.now() });
      if (recentToolCalls.length > MAX_TOOL_HISTORY) {
        recentToolCalls = recentToolCalls.slice(-MAX_TOOL_HISTORY);
      }

      if (isRetry) {
        const reflection = {
          timestamp: new Date().toISOString(),
          type: 'self-correction',
          category: 'tool_retry',
          original: `${tool} called with different params`,
          corrected: JSON.stringify(params).substring(0, 100),
          pattern: 'tool_retry',
          mode: 'unknown',
        };
        await _writeReflection(reflection);
      }
    },
  };
};

// Backward-compatible hooks interface for tests
export default {
  hooks: {
    'message.updated': async (oldMessage, newMessage) => {
      const detection = detectPattern(newMessage.content);
      if (!detection) return;

      const reflection = {
        timestamp: new Date().toISOString(),
        type: 'self-correction',
        category: detection.category,
        original: oldMessage.content.substring(0, 100),
        corrected: newMessage.content.substring(0, 100),
        pattern: detection.pattern,
        mode: newMessage.mode || oldMessage.mode || 'unknown',
      };

      await _writeReflection(reflection);
    },

    'tool.execute.before': async (execution) => {
      const isRetry = detectToolRetry(execution);

      recentToolCalls.push({
        tool: execution.tool,
        params: execution.params,
        timestamp: Date.now(),
      });
      if (recentToolCalls.length > MAX_TOOL_HISTORY) {
        recentToolCalls = recentToolCalls.slice(-MAX_TOOL_HISTORY);
      }

      if (isRetry) {
        const reflection = {
          timestamp: new Date().toISOString(),
          type: 'self-correction',
          category: 'tool_retry',
          original: `${execution.tool} called with different params`,
          corrected: JSON.stringify(execution.params).substring(0, 100),
          pattern: 'tool_retry',
          mode: 'unknown',
        };
        await _writeReflection(reflection);
      }
    },
  },

  // Expose for testing
  _detectPattern: detectPattern,
  _detectToolRetry: detectToolRetry,
  _resetToolHistory: () => { recentToolCalls = []; },
};
