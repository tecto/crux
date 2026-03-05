import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';

async function findKnowledgeFiles(dirs) {
  const files = [];
  for (const dir of dirs) {
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isFile() && entry.name.endsWith('.md')) {
          files.push(fullPath);
        } else if (entry.isDirectory()) {
          const subEntries = await fs.readdir(fullPath);
          for (const sub of subEntries) {
            if (sub.endsWith('.md')) {
              files.push(path.join(fullPath, sub));
            }
          }
        }
      }
    } catch {
      // Directory may not exist
    }
  }
  return files;
}

function scoreRelevance(content, filename, query) {
  const terms = query.toLowerCase().split(/\s+/);
  const lowerContent = content.toLowerCase();
  const lowerName = filename.toLowerCase();
  let score = 0;

  for (const term of terms) {
    if (lowerName.includes(term)) score += 3;
    const matches = lowerContent.split(term).length - 1;
    score += Math.min(matches, 5);
  }

  return score;
}

export default tool({
  description: 'Search mode-scoped knowledge base across project, user, and shared levels',
  args: {
    query: tool.schema.string().describe('Search query'),
    mode: tool.schema.string().optional().describe('Restrict to specific mode'),
  },
  async execute(args) {
    const { query, mode } = args;
    const projectBase = path.join(process.cwd(), '.crux', 'knowledge');
    const userBase = path.join(process.env.HOME, '.crux', 'knowledge');

    const searchDirs = [];

    if (mode) {
      searchDirs.push(path.join(projectBase, mode));
      searchDirs.push(path.join(userBase, mode));
    }
    searchDirs.push(projectBase);
    searchDirs.push(userBase);
    searchDirs.push(path.join(userBase, 'shared'));

    const files = await findKnowledgeFiles(searchDirs);
    const unique = [...new Set(files)];

    const results = [];
    for (const filePath of unique) {
      try {
        const content = await fs.readFile(filePath, 'utf8');
        const score = scoreRelevance(content, path.basename(filePath), query);
        if (score > 0) {
          results.push({
            path: filePath,
            name: path.basename(filePath, '.md'),
            score,
            excerpt: content.substring(0, 300),
            source: filePath.startsWith(projectBase) ? 'project' : 'user',
          });
        }
      } catch {
        // File read error, skip
      }
    }

    results.sort((a, b) => b.score - a.score);

    return {
      query,
      mode: mode || 'all',
      results: results.slice(0, 10),
      totalFound: results.length,
    };
  },
});
