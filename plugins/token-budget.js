const READ_ONLY_MODES = ['plan', 'review', 'explain'];
const WRITE_TOOLS = ['edit', 'write', 'bash'];

const BUDGET_TIERS = {
  tight: { budget: 4000, warnAt: 0.70, ceilAt: 0.90 },
  generous: { budget: 8000, warnAt: 0.80, ceilAt: 0.95 },
  standard: { budget: 6000, warnAt: 0.75, ceilAt: 0.90 },
};

const MODE_TIERS = {
  plan: 'tight',
  review: 'tight',
  strategist: 'tight',
  legal: 'tight',
  psych: 'tight',
  'build-py': 'generous',
  'build-ex': 'generous',
  debug: 'generous',
  docker: 'generous',
  writer: 'standard',
  analyst: 'standard',
  explain: 'standard',
  mac: 'standard',
  'ai-infra': 'standard',
  'infra-architect': 'tight',
};

let sessionTokens = 0;
let toolCallCount = 0;

function getTierForMode(mode) {
  return BUDGET_TIERS[MODE_TIERS[mode] || 'standard'];
}

function getTokenStatus(mode) {
  const tier = getTierForMode(mode);
  const used = sessionTokens;
  const remaining = Math.max(0, tier.budget - used);
  const ratio = used / tier.budget;

  let status = 'ok';
  if (ratio >= tier.ceilAt) {
    status = 'exceeded';
  } else if (ratio >= tier.warnAt) {
    status = 'warning';
  }

  return { used, remaining, budget: tier.budget, status, ratio };
}

function estimateToolTokens(tool) {
  const estimates = {
    read: 500,
    glob: 100,
    grep: 200,
    edit: 300,
    write: 400,
    bash: 600,
    lookup_knowledge: 200,
    run_script: 500,
  };
  return estimates[tool] || 200;
}

// OpenCode plugin factory
export const TokenBudgetPlugin = async (ctx) => {
  return {
    event: async ({ event }) => {
      if (event.type === 'session.created') {
        sessionTokens = 0;
        toolCallCount = 0;
      }
    },

    'tool.execute.before': async (input, output) => {
      const mode = input.mode || 'default';
      const isReadOnly = READ_ONLY_MODES.includes(mode);

      if (isReadOnly && WRITE_TOOLS.includes(input.tool)) {
        throw new Error(`${input.tool} not allowed in ${mode} mode`);
      }

      toolCallCount++;
      const estimatedTokens = estimateToolTokens(input.tool);
      sessionTokens += estimatedTokens;

      const tokenStatus = getTokenStatus(mode);
      if (tokenStatus.status === 'exceeded') {
        output.metadata = output.metadata || {};
        output.metadata.warning = `Token budget exceeded for ${mode} mode. ${tokenStatus.remaining}/${tokenStatus.budget} remaining.`;
      }
    },
  };
};

// Backward-compatible hooks interface for tests
export default {
  hooks: {
    'tool.execute.before': async (execution, context) => {
      const mode = (context && context.mode) || 'default';
      const isReadOnly = READ_ONLY_MODES.includes(mode);

      if (isReadOnly && WRITE_TOOLS.includes(execution.tool)) {
        throw new Error(`${execution.tool} not allowed in ${mode} mode`);
      }

      toolCallCount++;
      const estimatedTokens = estimateToolTokens(execution.tool);
      sessionTokens += estimatedTokens;

      const tokenStatus = getTokenStatus(mode);
      if (tokenStatus.status === 'exceeded') {
        return {
          allowed: true,
          warning: `Token budget exceeded for ${mode} mode. ${tokenStatus.remaining}/${tokenStatus.budget} remaining. Consider switching modes or starting a new session.`,
          tokenStatus,
        };
      }

      if (tokenStatus.status === 'warning') {
        return {
          allowed: true,
          warning: `Approaching token budget for ${mode} mode. ${tokenStatus.remaining}/${tokenStatus.budget} remaining.`,
          tokenStatus,
        };
      }

      return true;
    },

    'session.start': () => {
      sessionTokens = 0;
      toolCallCount = 0;
    },
  },

  // Exposed for testing
  _getTokenStatus: getTokenStatus,
  _getTierForMode: getTierForMode,
  _resetSession: () => { sessionTokens = 0; toolCallCount = 0; },
  _getSessionTokens: () => sessionTokens,
  _getToolCallCount: () => toolCallCount,
};
