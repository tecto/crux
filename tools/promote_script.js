import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';

export default tool({
  description: 'Promote a script from session to library',
  args: {
    scriptPath: tool.schema.string().describe('Relative path to script'),
    category: tool.schema.string().optional().describe('Library category'),
  },
  async execute(args) {
    const fullPath = path.resolve(process.cwd(), args.scriptPath);

    let content;
    try {
      content = await fs.readFile(fullPath, 'utf8');
    } catch {
      return { error: `Script not found: ${args.scriptPath}` };
    }

    // Update status header
    content = content.replace(/^(#\s*Status:\s*).*$/m, '$1library');

    // Determine destination
    const libDir = path.join(process.cwd(), '.crux', 'scripts', 'lib');
    await fs.mkdir(libDir, { recursive: true });
    const destPath = path.join(libDir, path.basename(fullPath));

    await fs.writeFile(destPath, content, 'utf8');

    // Remove original if it's in session dir
    if (fullPath.includes(path.join('scripts', 'session'))) {
      await fs.unlink(fullPath);
    }

    return {
      promoted: true,
      from: args.scriptPath,
      to: path.relative(process.cwd(), destPath),
    };
  },
});
