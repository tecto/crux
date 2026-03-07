import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';

const CRUX_DIR = path.join(process.cwd(), '.crux');
const MARKETING_DIR = path.join(CRUX_DIR, 'marketing');

async function readJson(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return JSON.parse(content);
  } catch {
    return null;
  }
}

async function writeJson(filePath, data) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, JSON.stringify(data, null, 2));
}

export default tool({
  description: 'Update marketing state counters. call after commits, tool uses, or token usage',
  args: {
    commits: tool.schema.number().optional().describe('Number of new commits'),
    tokens: tool.schema.number().optional().describe('Number of tokens used'),
    interactions: tool.schema.number().optional().describe('Number'),
    event: tool.schema.string().optional().describe('High-signal event: test_green, new_mcp_tool, git_tag, pr_merge, crux_switch, crux_adopt, knowledge_promoted, correction_detected'),
  },
  async execute(args) {
    const statePath = path.join(MARKETING_DIR, 'state.json');
    let state = await readJson(statePath) || {
      commits_since_last_post: 0,
      tokens_since_last_post: 0,
      interactions_since_last_post: 0,
      posts_today: 0,
    };

    if (args.commits) state.commits_since_last_post += args.commits;
    if (args.tokens) state.tokens_since_last_post += args.tokens;
    if (args.interactions) state.interactions_since_last_post += args.interactions;

    const today = new Date().toISOString().split('T')[0];
    if (state.last_date !== today) {
      state.posts_today = 0;
      state.last_date = today;
    }

    await writeJson(statePath, state);

    return {
      status: 'updated',
      commits_since_last_post: state.commits_since_last_post,
      tokens_since_last_post: state.tokens_since_last_post,
      interactions_since_last_post: state.interactions_since_last_post,
      posts_today: state.posts_today,
      event: args.event,
    };
  },
});
