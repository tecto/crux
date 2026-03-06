import fs from 'fs/promises';
import path from 'path';

const PRESERVE_FIELDS = ['mode', 'script', 'project', 'branch'];

async function logCompactionEvent(context, instructions, scripts, knowledge) {
  try {
    const today = new Date().toISOString().split('T')[0];
    const logDir = path.join(process.env.HOME, '.crux/analytics/compactions');
    await fs.mkdir(logDir, { recursive: true });

    const entry = {
      type: 'compaction',
      timestamp: new Date().toISOString(),
      mode: context.mode || null,
      project: context.project || null,
      branch: context.branch || null,
      instructions,
    };

    if (scripts.length > 0) {
      entry.activeScripts = scripts;
    }
    if (knowledge.length > 0) {
      entry.knowledgeQueries = knowledge.map(k => k.query);
    }

    await fs.appendFile(
      path.join(logDir, `${today}.jsonl`),
      JSON.stringify(entry) + '\n',
      'utf8'
    );
  } catch {
    // Don't let logging failures break compaction
  }
}

async function loadActiveScripts() {
  try {
    const sessionsDir = path.join(process.env.HOME, '.crux/analytics/sessions');
    const checkpointFile = path.join(sessionsDir, 'checkpoint.json');
    const data = JSON.parse(await fs.readFile(checkpointFile, 'utf8'));
    return data.activeScripts || [];
  } catch {
    return [];
  }
}

async function loadRecentKnowledge() {
  try {
    const sessionsDir = path.join(process.env.HOME, '.crux/analytics/sessions');
    const checkpointFile = path.join(sessionsDir, 'checkpoint.json');
    const data = JSON.parse(await fs.readFile(checkpointFile, 'utf8'));
    return data.recentKnowledgeLookups || [];
  } catch {
    return [];
  }
}

function buildCompactionInstructions(context, scripts, knowledge) {
  const instructions = [];

  if (context.mode) {
    instructions.push(`Active mode: ${context.mode}. Preserve mode-specific context.`);
  }

  if (scripts.length > 0) {
    instructions.push(`Active scripts: ${scripts.join(', ')}. Keep script names and paths.`);
  }

  if (knowledge.length > 0) {
    const queries = knowledge.map(k => k.query).join(', ');
    instructions.push(`Recent knowledge lookups: ${queries}. Preserve relevant findings.`);
  }

  if (context.project) {
    instructions.push(`Project: ${context.project}. Maintain project context.`);
  }

  if (context.branch) {
    instructions.push(`Branch: ${context.branch}. Preserve git context.`);
  }

  instructions.push('Preserve error messages and stack traces verbatim.');
  instructions.push('Keep file paths and line numbers exact.');
  instructions.push('Summarize verbose tool outputs but keep key findings.');

  return instructions.join(' ');
}

// OpenCode plugin factory
export const CompactionHookPlugin = async (ctx) => {
  return {
    'experimental.session.compacting': async (input, output) => {
      const scripts = await loadActiveScripts();
      const knowledge = await loadRecentKnowledge();
      const instrText = buildCompactionInstructions(input, scripts, knowledge);

      output.instructions = instrText;

      for (const field of PRESERVE_FIELDS) {
        if (input[field] !== undefined) {
          output[field] = input[field];
        }
      }

      if (scripts.length > 0) {
        output.activeScripts = scripts;
      }
      if (knowledge.length > 0) {
        output.recentKnowledge = knowledge;
      }

      await logCompactionEvent(input, instrText, scripts, knowledge);
    },
  };
};

// Backward-compatible hooks interface for tests
export default {
  hooks: {
    'experimental.session.compacting': async (context) => {
      const scripts = await loadActiveScripts();
      const knowledge = await loadRecentKnowledge();
      const instructions = buildCompactionInstructions(context, scripts, knowledge);

      const compacted = {
        timestamp: new Date().toISOString(),
        instructions,
      };

      for (const field of PRESERVE_FIELDS) {
        if (context[field] !== undefined) {
          compacted[field] = context[field];
        }
      }

      if (scripts.length > 0) {
        compacted.activeScripts = scripts;
      }

      if (knowledge.length > 0) {
        compacted.recentKnowledge = knowledge;
      }

      await logCompactionEvent(context, instructions, scripts, knowledge);

      return compacted;
    },
  },

  // Exposed for testing
  _buildCompactionInstructions: buildCompactionInstructions,
  _loadActiveScripts: loadActiveScripts,
  _loadRecentKnowledge: loadRecentKnowledge,
};
