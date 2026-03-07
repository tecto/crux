import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';

function parseHeader(content) {
  const headers = {};
  const lines = content.split('\n');
  for (const line of lines) {
    const match = line.match(/^#\s*(Name|Risk|Created|Status|Description):\s*(.+)/i);
    if (match) {
      headers[match[1].toLowerCase()] = match[2].trim();
    }
  }
  return headers;
}

async function scanDir(dir) {
  const scripts = [];
  try {
    const entries = await fs.readdir(dir);
    for (const entry of entries) {
      if (!entry.endsWith('.sh')) continue;
      const fullPath = path.join(dir, entry);
      const content = await fs.readFile(fullPath, 'utf8');
      const headers = parseHeader(content);
      scripts.push({
        name: headers.name || path.basename(entry, '.sh'),
        risk: headers.risk || 'unknown',
        created: headers.created || null,
        status: headers.status || 'unknown',
        description: headers.description || '',
        path: fullPath,
      });
    }
  } catch {
    // Directory may not exist
  }
  return scripts;
}

export default tool({
  description: 'List all available scripts with metadata',
  args: {
    filter: tool.schema.string().optional().describe('Keyword filter for script names/descriptions'),
  },
  async execute(args) {
    const base = path.join(process.cwd(), '.crux', 'scripts');

    const dirs = ['session', 'lib', 'archive'].map(d => path.join(base, d));
    const allScripts = [];
    for (const dir of dirs) {
      const scripts = await scanDir(dir);
      allScripts.push(...scripts);
    }

    let filtered = allScripts;
    if (args.filter) {
      const kw = args.filter.toLowerCase();
      filtered = allScripts.filter(s =>
        s.name.toLowerCase().includes(kw) ||
        s.description.toLowerCase().includes(kw)
      );
    }

    return { scripts: filtered };
  },
});
