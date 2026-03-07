import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TOOLS_DIR = path.join(__dirname, '..', 'tools');

const TOOL_FILES = [
  'promote_script.js',
  'list_scripts.js',
  'run_script.js',
  'project_context.js',
  'lookup_knowledge.js',
  'suggest_handoff.js',
  'manage_models.js',
];

// =========================================================================
// Common structure tests for all tools
// =========================================================================

describe('Tool files: common structure', () => {
  for (const file of TOOL_FILES) {
    describe(file, () => {
      let source;

      it('file exists and is readable', () => {
        source = readFileSync(path.join(TOOLS_DIR, file), 'utf8');
        assert.ok(source.length > 0);
      });

      it('imports plugin-shim tool helper', () => {
        source = source || readFileSync(path.join(TOOLS_DIR, file), 'utf8');
        assert.ok(source.includes("from '../lib/plugin-shim.js'"));
      });

      it('uses default export', () => {
        source = source || readFileSync(path.join(TOOLS_DIR, file), 'utf8');
        assert.ok(source.includes('export default'));
      });

      it('has a description', () => {
        source = source || readFileSync(path.join(TOOLS_DIR, file), 'utf8');
        assert.ok(source.includes("description:"));
      });

      it('has args definition', () => {
        source = source || readFileSync(path.join(TOOLS_DIR, file), 'utf8');
        assert.ok(source.includes("args:") || source.includes("args,"));
      });

      it('has an execute method', () => {
        source = source || readFileSync(path.join(TOOLS_DIR, file), 'utf8');
        assert.ok(source.includes("execute(") || source.includes("async execute("));
      });
    });
  }
});

// =========================================================================
// Tool-specific schema validation (import and test)
// =========================================================================

describe('promote_script.js schema and execute', async () => {
  it('can be imported', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'promote_script.js'));
    assert.ok(mod.default);
  });

  it('has correct description', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'promote_script.js'));
    assert.ok(mod.default.description.includes('Promote'));
  });

  it('schema validates correct input', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'promote_script.js'));
    const result = mod.default.schema.safeParse({ scriptPath: 'test.sh' });
    assert.ok(result.success);
  });

  it('schema rejects missing scriptPath', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'promote_script.js'));
    const result = mod.default.schema.safeParse({});
    assert.ok(!result.success);
  });

  it('execute returns error for nonexistent script', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'promote_script.js'));
    const result = await mod.default.execute({ scriptPath: 'nonexistent.sh' });
    assert.ok(result.error);
  });
});

describe('list_scripts.js schema and execute', () => {
  it('schema accepts string filter', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'list_scripts.js'));
    const result = mod.default.schema.safeParse({ filter: 'backup' });
    assert.ok(result.success);
  });

  it('schema accepts empty object', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'list_scripts.js'));
    const result = mod.default.schema.safeParse({});
    assert.ok(result.success);
  });
});

describe('run_script.js schema and execute', () => {
  it('schema requires scriptPath', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'run_script.js'));
    const result = mod.default.schema.safeParse({});
    assert.ok(!result.success);
  });

  it('schema validates full input', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'run_script.js'));
    const result = mod.default.schema.safeParse({
      scriptPath: '/path/to/script.sh',
      args: ['--dry-run'],
      dryRun: true,
      approvalRequired: false,
    });
    assert.ok(result.success);
  });

  it('exposes preflight check for testing', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'run_script.js'));
    assert.ok(typeof mod.default._preflightCheck === 'function');
    assert.ok(typeof mod.default._parseRiskLevel === 'function');
  });
});

describe('project_context.js schema and execute', () => {
  it('schema accepts include array', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'project_context.js'));
    const result = mod.default.schema.safeParse({ include: ['overview', 'stack'] });
    assert.ok(result.success);
  });

  it('schema accepts empty object', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'project_context.js'));
    const result = mod.default.schema.safeParse({});
    assert.ok(result.success);
  });
});

describe('lookup_knowledge.js schema and execute', () => {
  it('schema requires query', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'lookup_knowledge.js'));
    const result = mod.default.schema.safeParse({});
    assert.ok(!result.success);
  });

  it('schema validates query with mode', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'lookup_knowledge.js'));
    const result = mod.default.schema.safeParse({ query: 'auth', mode: 'build-py' });
    assert.ok(result.success);
  });
});

describe('suggest_handoff.js schema and execute', () => {
  it('schema requires both fromMode and taskDescription', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'suggest_handoff.js'));
    assert.ok(!mod.default.schema.safeParse({}).success);
    assert.ok(!mod.default.schema.safeParse({ fromMode: 'plan' }).success);
    assert.ok(!mod.default.schema.safeParse({ taskDescription: 'test' }).success);
  });

  it('schema validates complete input', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'suggest_handoff.js'));
    const result = mod.default.schema.safeParse({
      fromMode: 'plan',
      taskDescription: 'implement auth',
    });
    assert.ok(result.success);
  });
});

describe('manage_models.js schema and execute', () => {
  it('schema requires action', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'manage_models.js'));
    const result = mod.default.schema.safeParse({});
    assert.ok(!result.success);
  });

  it('schema accepts all valid actions', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'manage_models.js'));
    for (const action of ['list', 'pull', 'configure', 'switch']) {
      const result = mod.default.schema.safeParse({ action });
      assert.ok(result.success, `Should accept action: ${action}`);
    }
  });

  it('schema rejects invalid action', async () => {
    const mod = await import(path.join(TOOLS_DIR, 'manage_models.js'));
    const result = mod.default.schema.safeParse({ action: 'delete' });
    assert.ok(!result.success);
  });
});

// =========================================================================
// Plugin shim tests
// =========================================================================

describe('plugin-shim.js', () => {
  it('tool() creates a tool with schema and execute', async () => {
    const { tool } = await import(path.join(__dirname, '..', 'lib', 'plugin-shim.js'));
    const myTool = tool({
      description: 'Test tool',
      args: {
        name: tool.schema.string(),
        count: tool.schema.number().optional(),
      },
      async execute(args) {
        return `Hello ${args.name}`;
      },
    });

    assert.equal(myTool.description, 'Test tool');
    assert.ok(myTool.schema);
    assert.ok(myTool.schema.safeParse({ name: 'world' }).success);
    assert.ok(!myTool.schema.safeParse({}).success);

    const result = await myTool.execute({ name: 'world' });
    assert.equal(result, 'Hello world');
  });

  it('tool.schema exposes zod types', async () => {
    const { tool } = await import(path.join(__dirname, '..', 'lib', 'plugin-shim.js'));
    assert.ok(tool.schema.string);
    assert.ok(tool.schema.number);
    assert.ok(tool.schema.boolean);
    assert.ok(tool.schema.array);
    assert.ok(tool.schema.enum);
    assert.ok(tool.schema.object);
  });
});
