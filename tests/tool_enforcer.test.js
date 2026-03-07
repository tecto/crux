import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';

const PLUGINS_DIR = path.join(import.meta.dirname, '..', 'plugins');

describe('tool-enforcer.js plugin', () => {
  let plugin;

  beforeEach(async () => {
    const mod = await import(PLUGINS_DIR + '/tool-enforcer.js?t=' + Date.now());
    plugin = mod.default;
    plugin._resetUsage();
  });

  it('allows all tools in unrestricted modes', async () => {
    for (const tool of ['read', 'edit', 'write', 'bash', 'lookup_knowledge']) {
      const result = await plugin.hooks['tool.execute.before']({ tool }, { mode: 'build-py' });
      assert.equal(result, true);
    }
  });

  it('blocks write tools in read-only modes', async () => {
    for (const mode of ['plan', 'review', 'explain']) {
      for (const tool of ['edit', 'write', 'bash']) {
        await assert.rejects(
          () => plugin.hooks['tool.execute.before']({ tool }, { mode }),
          { message: new RegExp(`${tool} not allowed in ${mode} mode`) }
        );
      }
    }
  });

  it('allows read tools in read-only modes', async () => {
    for (const tool of ['read', 'glob', 'grep', 'lookup_knowledge']) {
      const result = await plugin.hooks['tool.execute.before']({ tool }, { mode: 'plan' });
      assert.equal(result, true);
    }
  });

  it('blocks bash in writer mode', async () => {
    await assert.rejects(
      () => plugin.hooks['tool.execute.before']({ tool: 'bash' }, { mode: 'writer' }),
      { message: /bash is blocked in writer mode/ }
    );
  });

  it('allows edit in writer mode', async () => {
    const result = await plugin.hooks['tool.execute.before']({ tool: 'edit' }, { mode: 'writer' });
    assert.equal(result, true);
  });

  it('blocks write in strategist mode', async () => {
    await assert.rejects(
      () => plugin.hooks['tool.execute.before']({ tool: 'edit' }, { mode: 'strategist' }),
    );
  });

  it('blocks write in psych mode', async () => {
    await assert.rejects(
      () => plugin.hooks['tool.execute.before']({ tool: 'write' }, { mode: 'psych' }),
    );
  });

  it('allows write tool in legal mode if in allowedWrite', async () => {
    const result = await plugin.hooks['tool.execute.before']({ tool: 'write' }, { mode: 'legal' });
    assert.equal(result, true);
  });

  it('blocks edit in legal mode', async () => {
    await assert.rejects(
      () => plugin.hooks['tool.execute.before']({ tool: 'edit' }, { mode: 'legal' }),
    );
  });

  it('allows all tools with default/unknown mode', async () => {
    const result = await plugin.hooks['tool.execute.before']({ tool: 'bash' }, {});
    assert.equal(result, true);
  });

  it('tracks tier usage', async () => {
    await plugin.hooks['tool.execute.before']({ tool: 'read' }, { mode: 'build-py' });
    await plugin.hooks['tool.execute.before']({ tool: 'lookup_knowledge' }, { mode: 'build-py' });

    const stats = plugin._getUsageStats();
    assert.equal(stats['build-py:tier5'], 1);
    assert.equal(stats['build-py:tier1'], 1);
  });

  it('returns correct tier for tools', () => {
    assert.equal(plugin._getTier('lookup_knowledge'), 1);
    assert.equal(plugin._getTier('run_script'), 1);
    assert.equal(plugin._getTier('read'), 5);
    assert.equal(plugin._getTier('bash'), 5);
    assert.equal(plugin._getTier('unknown_tool'), 5);
  });

  it('checkAccess returns allowed for unrestricted modes', () => {
    const result = plugin._checkAccess('bash', 'build-py');
    assert.ok(result.allowed);
  });

  it('checkAccess returns not allowed with reason', () => {
    const result = plugin._checkAccess('edit', 'plan');
    assert.ok(!result.allowed);
    assert.ok(result.reason.includes('not allowed'));
  });
});
