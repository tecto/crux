import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';

const MODE_KEYWORDS = {
  debug: ['debug', 'error', 'bug', 'fix', 'crash', 'timeout', 'exception', 'traceback', 'stack trace'],
  plan: ['plan', 'architect', 'design', 'structure', 'organize', 'architecture'],
  review: ['review', 'check', 'audit', 'inspect', 'examine', 'quality'],
  explain: ['explain', 'teach', 'how does', 'what is', 'why does', 'understand'],
  writer: ['write', 'document', 'draft', 'compose', 'blog', 'article'],
  analyst: ['analyze', 'data', 'metrics', 'statistics', 'report', 'chart'],
  'build-py': ['python', 'pip', 'pytest', 'django', 'fastapi', 'flask'],
  'build-ex': ['elixir', 'phoenix', 'ash', 'ecto', 'mix', 'otp'],
  'infra-architect': ['deploy', 'infrastructure', 'ci', 'cd', 'pipeline', 'kubernetes', 'docker'],
  strategist: ['strategy', 'business', 'market', 'competitive', 'growth'],
  mac: ['macos', 'homebrew', 'defaults', 'launchd'],
  docker: ['container', 'dockerfile', 'compose', 'image'],
};

function suggestMode(taskDescription, fromMode) {
  const lower = taskDescription.toLowerCase();
  let bestMode = null;
  let bestScore = 0;

  for (const [mode, keywords] of Object.entries(MODE_KEYWORDS)) {
    if (mode === fromMode) continue;
    let score = 0;
    for (const kw of keywords) {
      if (lower.includes(kw)) score++;
    }
    if (score > bestScore) {
      bestScore = score;
      bestMode = mode;
    }
  }

  return bestMode || 'plan';
}

export default tool({
  description: 'Suggest mode handoff with context packaging',
  args: {
    fromMode: tool.schema.string().describe('Current mode'),
    taskDescription: tool.schema.string().describe('Task context'),
  },
  async execute(args) {
    const { fromMode, taskDescription } = args;
    const suggestedMode = suggestMode(taskDescription, fromMode);

    const handoffContent = [
      `# Handoff Context`,
      ``,
      `## From: ${fromMode}`,
      `## To: ${suggestedMode}`,
      `## Task: ${taskDescription}`,
      ``,
      `## Return To: ${fromMode}`,
      ``,
      `Generated: ${new Date().toISOString()}`,
    ].join('\n');

    const handoffFile = path.join(process.cwd(), '.crux', 'sessions', 'handoff.md');
    await fs.mkdir(path.dirname(handoffFile), { recursive: true });
    await fs.writeFile(handoffFile, handoffContent, 'utf8');

    return {
      suggestedMode,
      returnTo: fromMode,
      taskDescription,
      handoffFile,
    };
  },
});
