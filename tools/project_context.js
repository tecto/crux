import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';

export default tool({
  description: 'Read and return PROJECT.md context',
  args: {
    include: tool.schema.array(tool.schema.string()).optional().describe('Sections to include'),
  },
  async execute(args) {
    const projectFile = path.join(process.cwd(), '.crux', 'context', 'PROJECT.md');

    let content;
    try {
      content = await fs.readFile(projectFile, 'utf8');
    } catch {
      return {
        instruction: 'PROJECT.md not found. Run update-project-context to generate it.',
      };
    }

    if (args.include && args.include.length > 0) {
      const sections = content.split(/^## /m);
      const filtered = sections.filter((section, i) => {
        if (i === 0) return true;
        const sectionName = section.split('\n')[0].trim();
        return args.include.some(inc => sectionName.includes(inc));
      });
      content = filtered.join('## ');
    }

    return { content };
  },
});
