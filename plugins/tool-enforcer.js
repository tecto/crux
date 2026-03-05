const TOOL_TIERS = {
  // Tier 1: Custom tools
  lookup_knowledge: 1,
  suggest_handoff: 1,
  project_context: 1,
  run_script: 1,
  promote_script: 1,
  list_scripts: 1,
  manage_models: 1,
  // Tier 5: Raw tools
  read: 5,
  glob: 5,
  grep: 5,
  edit: 5,
  write: 5,
  bash: 5,
};

const READ_ONLY_MODES = ['plan', 'review', 'explain'];
const WRITE_TOOLS = ['edit', 'write', 'bash'];

// Modes with restricted tool access
const MODE_RESTRICTIONS = {
  plan: { maxTier: 5, writeAllowed: false },
  review: { maxTier: 5, writeAllowed: false },
  explain: { maxTier: 5, writeAllowed: false },
  writer: { maxTier: 5, writeAllowed: true, blockedTools: ['bash'] },
  legal: { maxTier: 5, writeAllowed: false, allowedWrite: ['write'] },
  strategist: { maxTier: 5, writeAllowed: false },
  mac: { maxTier: 5, writeAllowed: true },
  psych: { maxTier: 5, writeAllowed: false },
};

// Track tier usage for analytics
let tierUsage = {};

function getTier(tool) {
  return TOOL_TIERS[tool] || 5;
}

function checkAccess(tool, mode) {
  const restrictions = MODE_RESTRICTIONS[mode];

  if (!restrictions) {
    return { allowed: true };
  }

  if (!restrictions.writeAllowed && WRITE_TOOLS.includes(tool)) {
    if (restrictions.allowedWrite && restrictions.allowedWrite.includes(tool)) {
      return { allowed: true };
    }
    return { allowed: false, reason: `${tool} not allowed in ${mode} mode (read-only)` };
  }

  if (restrictions.blockedTools && restrictions.blockedTools.includes(tool)) {
    return { allowed: false, reason: `${tool} is blocked in ${mode} mode` };
  }

  return { allowed: true };
}

function trackUsage(tool, mode) {
  const tier = getTier(tool);
  const key = `${mode || 'default'}:tier${tier}`;
  tierUsage[key] = (tierUsage[key] || 0) + 1;
}

// OpenCode plugin factory
export const ToolEnforcerPlugin = async (ctx) => {
  return {
    'tool.execute.before': async (input, output) => {
      const mode = input.mode || 'default';
      const toolName = input.tool;

      const access = checkAccess(toolName, mode);
      if (!access.allowed) {
        throw new Error(access.reason);
      }

      trackUsage(toolName, mode);
    },
  };
};

// Backward-compatible hooks interface for tests
export default {
  hooks: {
    'tool.execute.before': async (execution, context) => {
      const mode = (context && context.mode) || 'default';
      const tool = execution.tool;

      const access = checkAccess(tool, mode);
      if (!access.allowed) {
        throw new Error(access.reason);
      }

      trackUsage(tool, mode);

      return true;
    },
  },

  // Exposed for testing
  _checkAccess: checkAccess,
  _getTier: getTier,
  _getUsageStats: () => ({ ...tierUsage }),
  _resetUsage: () => { tierUsage = {}; },
};
