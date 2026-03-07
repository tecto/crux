import { describe, it, beforeEach, mock } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGINS_DIR = path.join(__dirname, '..', 'plugins');

// =========================================================================
// Think Router Plugin
// =========================================================================

describe('think-router.js', () => {
  let plugin;

  beforeEach(async () => {
    plugin = (await import(path.join(PLUGINS_DIR, 'think-router.js'))).default;
  });

  it('exports a hooks object', () => {
    assert.ok(plugin.hooks);
    assert.ok(typeof plugin.hooks === 'object');
  });

  it('has a chat.message hook', () => {
    assert.ok(typeof plugin.hooks['chat.message'] === 'function');
  });

  it('prepends /think for debug mode', () => {
    const msg = { mode: 'debug', content: 'find the bug' };
    const result = plugin.hooks['chat.message'](msg);
    assert.ok(result.content.startsWith('/think '));
  });

  it('prepends /think for plan mode', () => {
    const msg = { mode: 'plan', content: 'design the system' };
    const result = plugin.hooks['chat.message'](msg);
    assert.ok(result.content.startsWith('/think '));
  });

  it('prepends /think for all think modes', () => {
    const thinkModes = ['debug', 'plan', 'infra-architect', 'review', 'legal', 'strategist', 'psych'];
    for (const mode of thinkModes) {
      const msg = { mode, content: 'test' };
      const result = plugin.hooks['chat.message'](msg);
      assert.ok(result.content.startsWith('/think '), `Expected /think for mode: ${mode}`);
    }
  });

  it('prepends /no_think for all no_think modes', () => {
    const noThinkModes = ['build-py', 'build-ex', 'writer', 'analyst', 'mac', 'docker', 'explain'];
    for (const mode of noThinkModes) {
      const msg = { mode, content: 'test' };
      const result = plugin.hooks['chat.message'](msg);
      assert.ok(result.content.startsWith('/no_think '), `Expected /no_think for mode: ${mode}`);
    }
  });

  it('does not prepend directive for neutral modes', () => {
    const msg = { mode: 'ai-infra', content: 'configure model' };
    const result = plugin.hooks['chat.message'](msg);
    assert.equal(result.content, 'configure model');
  });

  it('does not prepend directive for unknown modes', () => {
    const msg = { mode: 'unknown-mode', content: 'hello' };
    const result = plugin.hooks['chat.message'](msg);
    assert.equal(result.content, 'hello');
  });

  it('does not prepend if content already starts with /think', () => {
    const msg = { mode: 'debug', content: '/think already thinking' };
    plugin.hooks['chat.message'](msg);
    // Should return undefined (no modification) since the content already has /think
    assert.ok(!msg.content.startsWith('/think /think'));
  });

  it('does not prepend if content already starts with /no_think', () => {
    const msg = { mode: 'build-py', content: '/no_think already set' };
    plugin.hooks['chat.message'](msg);
    assert.ok(!msg.content.startsWith('/no_think /no_think'));
  });

  it('handles missing mode gracefully', () => {
    const msg = { content: 'test' };
    const result = plugin.hooks['chat.message'](msg);
    // Default mode should not add directive
    assert.equal(result.content, 'test');
  });
});

// =========================================================================
// Token Budget Plugin
// =========================================================================

describe('token-budget.js', () => {
  let plugin;

  beforeEach(async () => {
    plugin = (await import(path.join(PLUGINS_DIR, 'token-budget.js') + `?t=${Date.now()}`)).default;
  });

  it('exports a hooks object', () => {
    assert.ok(plugin.hooks);
  });

  it('has a tool.execute.before hook', () => {
    assert.ok(typeof plugin.hooks['tool.execute.before'] === 'function');
  });

  it('blocks write tools in read-only modes', async () => {
    for (const mode of ['plan', 'review', 'explain']) {
      for (const tool of ['edit', 'write', 'bash']) {
        await assert.rejects(
          () => plugin.hooks['tool.execute.before']({ tool }, { mode }),
          { message: new RegExp(`${tool} not allowed in ${mode} mode`) },
          `Expected ${tool} to be blocked in ${mode} mode`
        );
      }
    }
  });

  it('allows read tools in read-only modes', async () => {
    const result = await plugin.hooks['tool.execute.before'](
      { tool: 'read' },
      { mode: 'plan' }
    );
    assert.equal(result, true);
  });

  it('allows write tools in non-read-only modes', async () => {
    const result = await plugin.hooks['tool.execute.before'](
      { tool: 'edit' },
      { mode: 'build-py' }
    );
    assert.equal(result, true);
  });

  it('allows any tool with default mode', async () => {
    const result = await plugin.hooks['tool.execute.before'](
      { tool: 'bash' },
      { mode: 'default' }
    );
    assert.equal(result, true);
  });
});

// =========================================================================
// Compaction Hook Plugin
// =========================================================================

describe('compaction-hook.js', () => {
  let plugin;

  beforeEach(async () => {
    plugin = (await import(path.join(PLUGINS_DIR, 'compaction-hook.js') + `?t=${Date.now()}`)).default;
  });

  it('exports a hooks object', () => {
    assert.ok(plugin.hooks);
  });

  it('has experimental.session.compacting hook', () => {
    assert.ok(typeof plugin.hooks['experimental.session.compacting'] === 'function');
  });

  it('returns compacted context with expected fields', async () => {
    const context = {
      mode: 'build-py',
      script: 'test.sh',
      project: 'myproject',
      branch: 'main',
    };
    const result = await plugin.hooks['experimental.session.compacting'](context);

    assert.equal(result.mode, 'build-py');
    assert.equal(result.script, 'test.sh');
    assert.equal(result.project, 'myproject');
    assert.equal(result.branch, 'main');
    assert.ok(result.timestamp);
    assert.ok(result.instructions);
  });
});

// =========================================================================
// Correction Detector Plugin - structure only (no filesystem mocking)
// =========================================================================

describe('correction-detector.js', () => {
  let pluginSource;

  beforeEach(() => {
    pluginSource = readFileSync(path.join(PLUGINS_DIR, 'correction-detector.js'), 'utf8');
  });

  it('file exists and is valid JavaScript module', () => {
    assert.ok(pluginSource.length > 0);
    assert.ok(pluginSource.includes('export default'));
  });

  it('defines PATTERNS object with categories', () => {
    assert.ok(pluginSource.includes('PATTERNS'));
    assert.ok(pluginSource.includes('self_correction'));
    assert.ok(pluginSource.includes('negation'));
    assert.ok(pluginSource.includes('retry_request'));
  });

  it('has message.updated hook', () => {
    assert.ok(pluginSource.includes("'message.updated'"));
  });

  it('uses path.join with process.env.HOME instead of invalid path.expand', () => {
    const hasPathExpand = pluginSource.includes('path.expand');
    assert.ok(!hasPathExpand, 'correction-detector.js should not use path.expand()');
    assert.ok(pluginSource.includes('process.env.HOME'));
  });
});

// =========================================================================
// Session Logger Plugin - structure only (no filesystem mocking)
// =========================================================================

describe('session-logger.js', () => {
  let pluginSource;

  beforeEach(() => {
    pluginSource = readFileSync(path.join(PLUGINS_DIR, 'session-logger.js'), 'utf8');
  });

  it('file exists and is valid JavaScript module', () => {
    assert.ok(pluginSource.length > 0);
    assert.ok(pluginSource.includes('export default'));
  });

  it('defines SessionLogger class', () => {
    assert.ok(pluginSource.includes('class SessionLogger'));
  });

  it('has all expected hooks', () => {
    const expectedHooks = ['session.start', 'chat.message', 'tool.execute.before', 'experimental.session.compacting', 'session.end'];
    for (const hook of expectedHooks) {
      assert.ok(pluginSource.includes(`'${hook}'`), `Missing hook: ${hook}`);
    }
  });

  it('uses path.join with process.env.HOME instead of invalid path.expand', () => {
    const hasPathExpand = pluginSource.includes('path.expand');
    assert.ok(!hasPathExpand, 'session-logger.js should not use path.expand()');
    assert.ok(pluginSource.includes('process.env.HOME'));
  });

  it('truncates message content to 200 chars', () => {
    assert.ok(pluginSource.includes('substring(0, 200)'));
  });

  it('generates unique session IDs', () => {
    assert.ok(pluginSource.includes('Date.now()'));
    assert.ok(pluginSource.includes('Math.random()'));
  });
});
