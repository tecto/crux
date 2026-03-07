import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';
import { execSync } from 'child_process';
import https from 'https';

const CRUX_DIR = path.join(process.cwd(), '.crux');
const MARKETING_DIR = path.join(CRUX_DIR, 'marketing');
const SITE_DIR = path.join(process.cwd(), 'site');

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

async function readFile(filePath) {
  try {
    return await fs.readFile(filePath, 'utf8');
  } catch {
    return '';
  }
}

function execGit(args) {
  try {
    return execSync(args, { encoding: 'utf8', cwd: process.cwd() });
  } catch {
    return '';
  }
}

async function typefullyRequest(method, endpoint, body = null) {
  const config = await readJson(path.join(MARKETING_DIR, 'config.json'));
  const keyPath = path.join(process.cwd(), config.typefully.api_key_path);
  const apiKey = (await readFile(keyPath)).trim();
  const socialSetId = config.typefully.social_set_id;

  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.typefully.com',
      port: 443,
      path: `/v2${endpoint.replace('{id}', socialSetId)}`,
      method,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve(data);
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function checkTriggers(state, config) {
  const triggers = config.triggers;
  const reasons = [];

  if (state.commits_since_last_post >= triggers.commit_threshold) {
    reasons.push(`commits: ${state.commits_since_last_post} >= ${triggers.commit_threshold}`);
  }

  if (state.tokens_since_last_post >= triggers.token_threshold) {
    reasons.push(`tokens: ${state.tokens_since_last_post} >= ${triggers.token_threshold}`);
  }

  if (state.interactions_since_last_post >= triggers.interaction_threshold) {
    reasons.push(`interactions: ${state.interactions_since_last_post} >= ${triggers.interaction_threshold}`);
  }

  if (state.last_queued_at) {
    const lastPost = new Date(state.last_queued_at);
    const now = new Date();
    const minutesSince = (now - lastPost) / (1000 * 60);
    if (minutesSince < triggers.cooldown_minutes) {
      return { triggered: false, reason: `cooldown: ${minutesSince.toFixed(1)}min < ${triggers.cooldown_minutes}min` };
    }
  }

  return { triggered: reasons.length > 0, reason: reasons.join(', ') || 'no trigger' };
}

async function gatherSources() {
  const sources = { commits: [], sessions: [], corrections: [], knowledge: [] };

  const lastPostDate = execGit("git log -1 --format=%ai -- '.crux/marketing/state.json' 2>/dev/null || echo '1970-01-01'").trim() || '1970-01-01';
  
  const logOutput = execGit(`git log --since="${lastPostDate}" --oneline -- '.crux/marketing/state.json' 2>/dev/null | head -20`);
  sources.commits = logOutput.split('\n').filter(Boolean);

  const sessionsDir = path.join(CRUX_DIR, 'sessions');
  try {
    const files = await fs.readdir(sessionsDir);
    for (const file of files.slice(-5)) {
      if (file.endsWith('.json')) {
        const content = await readFile(path.join(sessionsDir, file));
        if (content) sources.sessions.push({ file, content: JSON.parse(content) });
      }
    }
  } catch {}

  const correctionsFile = path.join(CRUX_DIR, 'corrections', 'corrections.jsonl');
  const corrections = await readFile(correctionsFile);
  if (corrections) {
    sources.corrections = corrections.split('\n').filter(Boolean).slice(-10);
  }

  const knowledgeDir = path.join(CRUX_DIR, 'knowledge');
  try {
    const files = await fs.readdir(knowledgeDir, { recursive: true });
    sources.knowledge = files.filter(f => String(f).endsWith('.md')).slice(-5);
  } catch {}

  return sources;
}

function generateDraft(sources, config) {
  const voice = config.voice;
  const commits = sources.commits.filter(c => c && c.trim());
  
  let draft = { type: 'tweet', platform: 'x', text: '', hashtags: ['buildinpublic', 'opensource', 'aitools'] };
  
  if (commits.length >= 3) {
    const lastCommit = commits[0] || '';
    draft.text = `shipping: ${lastCommit}. ${commits.length} commits since last update. building in public.`;
  } else if (sources.corrections.length > 0) {
    draft.text = `the AI learned something new today. corrections compound. that's the whole point.`;
  } else if (sources.knowledge.length > 0) {
    draft.text = `new knowledge entry promoted. the system gets smarter every time you use it.`;
  } else {
    draft.text = `still building. still shipping. crux day 1.`;
  }

  if (draft.text.length > 280) {
    draft.text = draft.text.substring(0, 277) + '...';
  }

  return draft;
}

async function queueToTypefully(draft, config) {
  const publishAt = new Date(Date.now() + 5 * 60 * 1000).toISOString();
  
  const payload = {
    platforms: { x: { enabled: true, posts: [{ text: draft.text }] } },
    publish_at: publishAt,
  };

  const result = await typefullyRequest('POST', '/social-sets/{id}/drafts', payload);
  return result;
}

export default tool({
  description: 'Generate and queue marketing content. checks triggers, gathers sources, generates draft, queues to Typefully',
  args: {
    force: tool.schema.boolean().optional().describe('Bypass cooldown gate'),
    platform: tool.schema.string().optional().describe('Platform: x, reddit, blog, all'),
    generate_blog: tool.schema.boolean().optional().describe('Also generate blog post'),
  },
  async execute(args) {
    const config = await readJson(path.join(MARKETING_DIR, 'config.json'));
    const statePath = path.join(MARKETING_DIR, 'state.json');
    let state = await readJson(statePath) || {
      commits_since_last_post: 0,
      tokens_since_last_post: 0,
      interactions_since_last_post: 0,
      posts_today: 0,
      last_queued_at: null,
    };

    if (!args.force) {
      const triggerCheck = await checkTriggers(state, config);
      if (!triggerCheck.triggered) {
        return { status: 'skipped', reason: triggerCheck.reason };
      }
    }

    const sources = await gatherSources();
    const draft = generateDraft(sources, config);

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const draftPath = path.join(MARKETING_DIR, 'drafts', `${timestamp}.md`);
    await fs.writeFile(draftPath, `---\ntype: ${draft.type}\nplatform: ${draft.platform}\n---\n\n${draft.text}\n`);

    try {
      const result = await queueToTypefully(draft, config);
      
      state.commits_since_last_post = 0;
      state.tokens_since_last_post = 0;
      state.interactions_since_last_post = 0;
      state.posts_today = (state.posts_today || 0) + 1;
      state.last_queued_at = new Date().toISOString();
      state.last_queued_id = result?.draft?.id || null;
      await writeJson(statePath, state);

      return {
        status: 'queued',
        draft_path: draftPath,
        preview: draft.text.substring(0, 100),
        char_count: draft.text.length,
        scheduled: result?.draft?.publish_at || 'now',
      };
    } catch (err) {
      return { status: 'error', reason: err.message, draft_path: draftPath };
    }
  },
});
