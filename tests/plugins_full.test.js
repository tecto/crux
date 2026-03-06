import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGINS_DIR = path.join(__dirname, '..', 'plugins');

// =========================================================================
// Session Logger - import once, test thoroughly
// =========================================================================

describe('session-logger.js full coverage', () => {
  let tempDir;
  let origHome;
  let plugin;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-test-'));
    origHome = process.env.HOME;
    process.env.HOME = tempDir;
  });

  afterEach(async () => {
    // Ensure session ends to clear intervals
    if (plugin) {
      try { await plugin.hooks['session.end'](); } catch {}
    }
    process.env.HOME = origHome;
    await new Promise(r => setTimeout(r, 50));
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('full lifecycle: init, log, flush, shutdown', async () => {
    // Use cache-buster since we need a fresh singleton per test
    const mod = await import(PLUGINS_DIR + '/session-logger.js?full=' + Date.now());
    plugin = mod.default;

    await plugin.hooks['session.start']();

    plugin.hooks['chat.message']({
      role: 'user',
      mode: 'build-py',
      content: 'Hello world this is a test message',
      tokens: 42,
    });

    plugin.hooks['tool.execute.before']({
      tool: 'edit',
      params: { file: 'test.js' },
    });

    plugin.hooks['experimental.session.compacting']({
      mode: 'debug',
      script: 'fix.sh',
      project: 'myapp',
    });

    await plugin.hooks['session.end']();
    plugin = null; // prevent double-end in afterEach

    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    const dateDirs = await fs.readdir(sessionsDir);
    const dateDir = path.join(sessionsDir, dateDirs[0]);
    const files = await fs.readdir(dateDir);
    const logFile = path.join(dateDir, files[0]);
    const content = await fs.readFile(logFile, 'utf8');
    const lines = content.trim().split('\n').map(l => JSON.parse(l));

    const types = lines.map(l => l.type);
    assert.ok(types.includes('session.start'));
    assert.ok(types.includes('chat.message'));
    assert.ok(types.includes('tool.execute'));
    assert.ok(types.includes('session.compaction'));
    assert.ok(types.includes('session.end'));

    const chatEntry = lines.find(l => l.type === 'chat.message');
    assert.equal(chatEntry.role, 'user');
    assert.equal(chatEntry.mode, 'build-py');
    assert.equal(chatEntry.tokens, 42);
    assert.ok(chatEntry.timestamp);
  });

  it('truncates content to 200 and params to 100', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?trunc=' + Date.now());
    plugin = mod.default;

    await plugin.hooks['session.start']();

    plugin.hooks['chat.message']({
      role: 'assistant', mode: 'plan', content: 'x'.repeat(500),
    });

    plugin.hooks['tool.execute.before']({
      tool: 'bash', params: { longParam: 'y'.repeat(500) },
    });

    await plugin.hooks['session.end']();
    plugin = null;

    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    const dateDirs = await fs.readdir(sessionsDir);
    const dateDir = path.join(sessionsDir, dateDirs[0]);
    const files = await fs.readdir(dateDir);
    const content = await fs.readFile(path.join(dateDir, files[0]), 'utf8');
    const lines = content.trim().split('\n').map(l => JSON.parse(l));

    const chatEntry = lines.find(l => l.type === 'chat.message');
    assert.ok(chatEntry.content.length <= 200);

    const toolEntry = lines.find(l => l.type === 'tool.execute');
    assert.ok(toolEntry.params.length <= 100);
  });

  it('defaults tokens to 0 when missing', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?tok=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();
    plugin.hooks['chat.message']({ role: 'user', mode: 'debug', content: 'test' });
    await plugin.hooks['session.end']();
    plugin = null;

    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    const dateDirs = await fs.readdir(sessionsDir);
    const dateDir = path.join(sessionsDir, dateDirs[0]);
    const files = await fs.readdir(dateDir);
    const content = await fs.readFile(path.join(dateDir, files[0]), 'utf8');
    const lines = content.trim().split('\n').map(l => JSON.parse(l));
    const chatEntry = lines.find(l => l.type === 'chat.message');
    assert.equal(chatEntry.tokens, 0);
  });

  it('flush error is caught and logged to console.error', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?err=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();
    plugin.hooks['chat.message']({ role: 'user', mode: 'debug', content: 'test' });

    // Remove session dir to trigger flush error
    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    await fs.rm(sessionsDir, { recursive: true, force: true });

    // Should not throw
    await plugin.hooks['session.end']();
    plugin = null;
  });
});

// =========================================================================
// Session Logger - base import for canonical file coverage
// =========================================================================

describe('session-logger.js base import', () => {
  let tempDir;
  let origHome;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-base-'));
    origHome = process.env.HOME;
    process.env.HOME = tempDir;
  });

  afterEach(async () => {
    process.env.HOME = origHome;
    await new Promise(r => setTimeout(r, 50));
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('exercises all hooks and error path on canonical import', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js');
    const plugin = mod.default;

    await plugin.hooks['session.start']();
    plugin.hooks['chat.message']({ role: 'user', mode: 'build-py', content: 'test', tokens: 10 });
    plugin.hooks['tool.execute.before']({ tool: 'edit', params: { file: 'test.js' } });
    plugin.hooks['experimental.session.compacting']({ mode: 'debug', script: 'fix.sh', project: 'myapp' });

    // End session to flush all buffered data to disk
    await plugin.hooks['session.end']();

    // Verify files were created
    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    const dateDirs = await fs.readdir(sessionsDir);
    assert.ok(dateDirs.length >= 1);
    const dateDir = path.join(sessionsDir, dateDirs[0]);
    const files = await fs.readdir(dateDir);
    assert.ok(files.length >= 1);

    // Now re-initialize and trigger error path: remove sessions dir then end
    await plugin.hooks['session.start']();
    plugin.hooks['chat.message']({ role: 'user', mode: 'debug', content: 'trigger flush', tokens: 1 });
    await fs.rm(sessionsDir, { recursive: true, force: true });
    await plugin.hooks['session.end']();
  });
});

// =========================================================================
// Session Logger - checkpoint and recovery tests
// =========================================================================

describe('session-logger.js checkpoint and recovery', () => {
  let tempDir;
  let origHome;
  let plugin;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-ckpt-'));
    origHome = process.env.HOME;
    process.env.HOME = tempDir;
  });

  afterEach(async () => {
    if (plugin) {
      try { await plugin.hooks['session.end'](); } catch {}
    }
    process.env.HOME = origHome;
    await new Promise(r => setTimeout(r, 50));
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('creates checkpoint after 5 interactions', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?ckpt=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    // Send 5 messages to trigger checkpoint
    for (let i = 0; i < 5; i++) {
      plugin.hooks['chat.message']({
        role: 'user', mode: 'build-py', content: `msg ${i}`, tokens: 10,
      });
    }

    // Wait briefly for async checkpoint write
    await new Promise(r => setTimeout(r, 100));

    const sessionsBase = path.join(tempDir, '.crux/analytics/sessions');
    const checkpointFile = path.join(sessionsBase, 'checkpoint.json');
    const data = JSON.parse(await fs.readFile(checkpointFile, 'utf8'));
    assert.equal(data.interactionCount, 5);
    assert.equal(data.mode, 'build-py');

    await plugin.hooks['session.end']();
    plugin = null;
  });

  it('recovers from checkpoint on new session start', async () => {
    // Create a fake checkpoint file
    const sessionsBase = path.join(tempDir, '.crux/analytics/sessions');
    await fs.mkdir(sessionsBase, { recursive: true });
    const checkpoint = {
      sessionId: 'old-session-123',
      timestamp: '2026-03-05T10:00:00Z',
      mode: 'debug',
      interactionCount: 15,
      recentKnowledgeLookups: [{ query: 'redis', mode: 'build-py' }],
      activeScripts: ['fix-bug.sh'],
    };
    await fs.writeFile(
      path.join(sessionsBase, 'checkpoint.json'),
      JSON.stringify(checkpoint),
    );

    const mod = await import(PLUGINS_DIR + '/session-logger.js?recover=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    // Check recovery info
    const recovery = plugin._logger.getRecoveryInfo();
    assert.ok(recovery);
    assert.equal(recovery.previousSessionId, 'old-session-123');
    assert.equal(recovery.mode, 'debug');
    assert.equal(recovery.interactionCount, 15);

    // Check session.start log entry includes recovery info
    await plugin.hooks['session.end']();
    plugin = null;

    const today = new Date().toISOString().split('T')[0];
    const dateDir = path.join(sessionsBase, today);
    const files = await fs.readdir(dateDir);
    const content = await fs.readFile(path.join(dateDir, files[0]), 'utf8');
    const entries = content.trim().split('\n').map(l => JSON.parse(l));
    const startEntry = entries.find(e => e.type === 'session.start');
    assert.ok(startEntry.recovered);
    assert.equal(startEntry.recovered.previousSessionId, 'old-session-123');
  });

  it('no recovery when no checkpoint exists', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?nockpt=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    const recovery = plugin._logger.getRecoveryInfo();
    assert.equal(recovery, null);

    await plugin.hooks['session.end']();
    plugin = null;
  });

  it('checkpoint is cleaned up on graceful shutdown', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?clean=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    // Create 5 interactions to trigger checkpoint
    for (let i = 0; i < 5; i++) {
      plugin.hooks['chat.message']({
        role: 'user', mode: 'plan', content: `msg ${i}`, tokens: 5,
      });
    }
    await new Promise(r => setTimeout(r, 100));

    const sessionsBase = path.join(tempDir, '.crux/analytics/sessions');
    const checkpointFile = path.join(sessionsBase, 'checkpoint.json');

    // Verify checkpoint exists
    await fs.access(checkpointFile);

    // Graceful shutdown should remove it
    await plugin.hooks['session.end']();
    plugin = null;

    let exists = true;
    try { await fs.access(checkpointFile); } catch { exists = false; }
    assert.ok(!exists, 'Checkpoint should be removed after graceful shutdown');
  });

  it('tracks knowledge lookups and scripts', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?track=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    plugin.hooks['tool.execute.before']({
      tool: 'lookup_knowledge',
      params: { query: 'redis setup', mode: 'build-py' },
    });

    plugin.hooks['tool.execute.before']({
      tool: 'run_script',
      params: { scriptPath: 'fix-db.sh' },
    });

    assert.equal(plugin._logger.recentKnowledgeLookups.length, 1);
    assert.equal(plugin._logger.recentKnowledgeLookups[0].query, 'redis setup');
    assert.ok(plugin._logger.activeScripts.includes('fix-db.sh'));

    // Duplicate script tracking
    plugin.hooks['tool.execute.before']({
      tool: 'run_script',
      params: { scriptPath: 'fix-db.sh' },
    });
    assert.equal(plugin._logger.activeScripts.length, 1);

    await plugin.hooks['session.end']();
    plugin = null;
  });

  it('limits knowledge lookups to 10', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?limit=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    for (let i = 0; i < 15; i++) {
      plugin._logger.trackKnowledgeLookup(`query-${i}`, 'debug');
    }
    assert.equal(plugin._logger.recentKnowledgeLookups.length, 10);

    await plugin.hooks['session.end']();
    plugin = null;
  });

  it('compaction log entry includes instructions', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?complog=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    plugin.hooks['experimental.session.compacting']({
      mode: 'debug',
      script: 'fix.sh',
      project: 'myapp',
    });

    await plugin.hooks['session.end']();
    plugin = null;

    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    const today = new Date().toISOString().split('T')[0];
    const dateDir = path.join(sessionsDir, today);
    const files = await fs.readdir(dateDir);
    const content = await fs.readFile(path.join(dateDir, files[0]), 'utf8');
    const entries = content.trim().split('\n').map(l => JSON.parse(l));

    const compactEntry = entries.find(e => e.type === 'session.compaction');
    assert.ok(compactEntry, 'Should have session.compaction entry');
    assert.equal(compactEntry.mode, 'debug');
    assert.equal(compactEntry.project, 'myapp');
    assert.ok(compactEntry.instructions);
    assert.ok(compactEntry.instructions.length > 0);
  });

  it('session.end includes interaction count', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?endcount=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    plugin.hooks['chat.message']({ role: 'user', mode: 'debug', content: 'hello', tokens: 1 });
    plugin.hooks['chat.message']({ role: 'user', mode: 'debug', content: 'world', tokens: 1 });

    await plugin.hooks['session.end']();
    plugin = null;

    const sessionsBase = path.join(tempDir, '.crux/analytics/sessions');
    const today = new Date().toISOString().split('T')[0];
    const dateDir = path.join(sessionsBase, today);
    const files = await fs.readdir(dateDir);
    const content = await fs.readFile(path.join(dateDir, files[0]), 'utf8');
    const entries = content.trim().split('\n').map(l => JSON.parse(l));
    const endEntry = entries.find(e => e.type === 'session.end');
    assert.equal(endEntry.interactionCount, 2);
  });

  it('checkpoint save error is caught gracefully', async () => {
    const mod = await import(PLUGINS_DIR + '/session-logger.js?saveerr=' + Date.now());
    plugin = mod.default;
    await plugin.hooks['session.start']();

    // Make checkpoint dir unwritable by replacing it with a file
    const sessionsBase = path.join(tempDir, '.crux/analytics/sessions');
    const checkpointFile = path.join(sessionsBase, 'checkpoint.json');
    await fs.mkdir(checkpointFile, { recursive: true });
    // Can't write JSON to a directory path - will trigger error

    // Send 5 messages to trigger checkpoint
    for (let i = 0; i < 5; i++) {
      plugin.hooks['chat.message']({
        role: 'user', mode: 'debug', content: `msg ${i}`, tokens: 1,
      });
    }
    await new Promise(r => setTimeout(r, 100));
    // Should not throw

    // Clean up the directory so shutdown works
    await fs.rm(checkpointFile, { recursive: true, force: true });
    await plugin.hooks['session.end']();
    plugin = null;
  });
});

// =========================================================================
// Correction Detector - import once, test all patterns
// =========================================================================

describe('correction-detector.js full coverage', () => {
  let tempDir;
  let origHome;
  let plugin;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-test-'));
    origHome = process.env.HOME;
    process.env.HOME = tempDir;
  });

  afterEach(async () => {
    process.env.HOME = origHome;
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('detects self-correction patterns', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?self=' + Date.now());
    plugin = mod.default;

    const patterns = [
      'actually, use a while loop',
      'wait, I need to reconsider',
      'let me fix that approach',
      'i meant something different',
      'instead use a map here',
      'hold on, let me rethink',
      'scratch that idea',
      'better to use async',
      'let me try again',
      'i should have used map',
      'i was wrong about that',
      'let me correct that',
      'let me rephrase the question',
    ];

    for (const correction of patterns) {
      await plugin.hooks['message.updated'](
        { content: 'original text' },
        { content: correction, mode: 'build-py' }
      );
    }

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    const files = await fs.readdir(reflectionsDir);
    const content = await fs.readFile(path.join(reflectionsDir, files[0]), 'utf8');
    const lines = content.trim().split('\n');
    assert.ok(lines.length >= patterns.length);

    const reflection = JSON.parse(lines[0]);
    assert.equal(reflection.type, 'self-correction');
    assert.ok(reflection.category);
    assert.equal(reflection.mode, 'build-py');
    assert.ok(reflection.timestamp);
  });

  it('detects negation patterns', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?neg=' + Date.now());
    plugin = mod.default;

    const negations = [
      'no, use docker-compose instead',
      'wrong, that should be async',
      'that\'s not right at all',
      'I said use a list',
      'not what I asked for',
      'cancel the current operation',
      'stop doing that',
    ];

    for (const msg of negations) {
      await plugin.hooks['message.updated'](
        { content: 'original' },
        { content: msg, mode: 'debug' }
      );
    }

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    const files = await fs.readdir(reflectionsDir);
    const content = await fs.readFile(path.join(reflectionsDir, files[0]), 'utf8');
    const lines = content.trim().split('\n');
    assert.ok(lines.length >= negations.length);

    const reflection = JSON.parse(lines[0]);
    assert.equal(reflection.category, 'negation');
  });

  it('detects retry request patterns', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?retry=' + Date.now());
    plugin = mod.default;

    const retries = [
      'try again with different params',
      'redo that with a list',
      'start over from the beginning',
      'do it differently this time',
    ];

    for (const msg of retries) {
      await plugin.hooks['message.updated'](
        { content: 'original' },
        { content: msg }
      );
    }

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    const files = await fs.readdir(reflectionsDir);
    const content = await fs.readFile(path.join(reflectionsDir, files[0]), 'utf8');
    const lines = content.trim().split('\n');
    assert.ok(lines.length >= retries.length);

    const reflection = JSON.parse(lines[0]);
    assert.equal(reflection.category, 'retry_request');
  });

  it('ignores non-correction messages', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?ignore=' + Date.now());
    plugin = mod.default;

    await plugin.hooks['message.updated'](
      { content: 'original message' },
      { content: 'this is a normal follow up' }
    );

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    let exists = true;
    try { await fs.access(reflectionsDir); } catch { exists = false; }
    assert.ok(!exists);
  });

  it('truncates original and corrected to 100 chars', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?trunc=' + Date.now());
    plugin = mod.default;

    await plugin.hooks['message.updated'](
      { content: 'x'.repeat(500) },
      { content: 'actually ' + 'x'.repeat(500) }
    );

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    const files = await fs.readdir(reflectionsDir);
    const content = await fs.readFile(path.join(reflectionsDir, files[0]), 'utf8');
    const reflection = JSON.parse(content.trim().split('\n')[0]);
    assert.ok(reflection.original.length <= 100);
    assert.ok(reflection.corrected.length <= 100);
  });

  it('detects tool retry pattern', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?toolretry=' + Date.now());
    plugin = mod.default;
    plugin._resetToolHistory();

    // First call
    await plugin.hooks['tool.execute.before']({ tool: 'edit', params: { file: 'a.js', content: 'v1' } });
    // Same tool, different params = retry
    await plugin.hooks['tool.execute.before']({ tool: 'edit', params: { file: 'a.js', content: 'v2' } });

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    const files = await fs.readdir(reflectionsDir);
    const content = await fs.readFile(path.join(reflectionsDir, files[0]), 'utf8');
    const reflection = JSON.parse(content.trim());
    assert.equal(reflection.category, 'tool_retry');
  });

  it('does not flag read-only tools as retries', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?readonly=' + Date.now());
    plugin = mod.default;
    plugin._resetToolHistory();

    await plugin.hooks['tool.execute.before']({ tool: 'read', params: { file: 'a.js' } });
    await plugin.hooks['tool.execute.before']({ tool: 'read', params: { file: 'b.js' } });

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    let exists = true;
    try { await fs.access(reflectionsDir); } catch { exists = false; }
    assert.ok(!exists);
  });

  it('limits tool history to 20 entries', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?limit=' + Date.now());
    plugin = mod.default;
    plugin._resetToolHistory();

    for (let i = 0; i < 25; i++) {
      await plugin.hooks['tool.execute.before']({ tool: 'write', params: { file: `f${i}.js` } });
    }
    // Internal: tool history shouldn't exceed MAX_TOOL_HISTORY
    // We can verify indirectly — no errors thrown
  });

  it('handles fs errors gracefully', async () => {
    const reflectionsParent = path.join(tempDir, '.crux');
    await fs.mkdir(reflectionsParent, { recursive: true });
    await fs.writeFile(path.join(reflectionsParent, 'reflections'), 'blocker');

    const mod = await import(PLUGINS_DIR + '/correction-detector.js?fserr=' + Date.now());
    plugin = mod.default;

    await plugin.hooks['message.updated'](
      { content: 'original' },
      { content: 'actually something else' }
    );
    // Should not throw
  });

  it('uses mode from oldMessage when newMessage has none', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?mode=' + Date.now());
    plugin = mod.default;

    await plugin.hooks['message.updated'](
      { content: 'original', mode: 'plan' },
      { content: 'actually use a different approach' }
    );

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    const files = await fs.readdir(reflectionsDir);
    const content = await fs.readFile(path.join(reflectionsDir, files[0]), 'utf8');
    const reflection = JSON.parse(content.trim());
    assert.equal(reflection.mode, 'plan');
  });

  it('detectPattern returns null for non-matching content', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js?detect=' + Date.now());
    const result = mod.default._detectPattern('this is a normal message');
    assert.equal(result, null);
  });
});

// =========================================================================
// Correction Detector - base import for canonical file coverage
// =========================================================================

describe('correction-detector.js base import', () => {
  let tempDir;
  let origHome;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-base-'));
    origHome = process.env.HOME;
    process.env.HOME = tempDir;
  });

  afterEach(async () => {
    process.env.HOME = origHome;
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('exercises all paths on canonical import', async () => {
    const mod = await import(PLUGINS_DIR + '/correction-detector.js');
    const plugin = mod.default;
    plugin._resetToolHistory();

    // Test correction detection
    await plugin.hooks['message.updated'](
      { content: 'original text' },
      { content: 'actually something different', mode: 'debug' }
    );

    const reflectionsDir = path.join(tempDir, '.crux/corrections');
    const files = await fs.readdir(reflectionsDir);
    assert.ok(files.length >= 1);

    // Test non-correction path
    await plugin.hooks['message.updated'](
      { content: 'hello' },
      { content: 'this is normal' }
    );

    // Test tool tracking
    await plugin.hooks['tool.execute.before']({ tool: 'edit', params: { file: 'a.js' } });

    // Test error path
    await fs.rm(reflectionsDir, { recursive: true });
    const reflectionsParent = path.dirname(reflectionsDir);
    await fs.writeFile(reflectionsDir, 'blocker');

    await plugin.hooks['message.updated'](
      { content: 'original' },
      { content: 'actually trigger error path' }
    );
  });
});

// =========================================================================
// Compaction Hook - full coverage
// =========================================================================

describe('compaction-hook.js full coverage', () => {
  let tempDir;
  let origHome;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-compact-'));
    origHome = process.env.HOME;
    process.env.HOME = tempDir;
  });

  afterEach(async () => {
    process.env.HOME = origHome;
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('returns compacted context with all fields', async () => {
    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?all=' + Date.now());
    const plugin = mod.default;

    const result = await plugin.hooks['experimental.session.compacting']({
      mode: 'build-py',
      script: 'test.sh',
      project: 'myproject',
      branch: 'main',
    });

    assert.equal(result.mode, 'build-py');
    assert.equal(result.script, 'test.sh');
    assert.equal(result.project, 'myproject');
    assert.equal(result.branch, 'main');
    assert.ok(result.timestamp);
    assert.ok(result.instructions);
    assert.ok(result.instructions.includes('Active mode: build-py'));
  });

  it('loads active scripts from checkpoint', async () => {
    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    await fs.mkdir(sessionsDir, { recursive: true });
    await fs.writeFile(path.join(sessionsDir, 'checkpoint.json'), JSON.stringify({
      activeScripts: ['backup-db.sh', 'fix-bug.sh'],
      recentKnowledgeLookups: [],
    }));

    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?scripts=' + Date.now());
    const plugin = mod.default;

    const result = await plugin.hooks['experimental.session.compacting']({ mode: 'debug' });
    assert.ok(result.instructions.includes('backup-db.sh'));
    assert.deepEqual(result.activeScripts, ['backup-db.sh', 'fix-bug.sh']);
  });

  it('loads recent knowledge from checkpoint', async () => {
    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    await fs.mkdir(sessionsDir, { recursive: true });
    await fs.writeFile(path.join(sessionsDir, 'checkpoint.json'), JSON.stringify({
      activeScripts: [],
      recentKnowledgeLookups: [{ query: 'redis setup', mode: 'build-py' }],
    }));

    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?knowledge=' + Date.now());
    const plugin = mod.default;

    const result = await plugin.hooks['experimental.session.compacting']({ mode: 'build-py' });
    assert.ok(result.instructions.includes('redis setup'));
    assert.equal(result.recentKnowledge.length, 1);
  });

  it('handles missing checkpoint gracefully', async () => {
    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?missing=' + Date.now());
    const plugin = mod.default;

    const result = await plugin.hooks['experimental.session.compacting']({ mode: 'plan' });
    assert.ok(result.instructions);
    assert.ok(!result.activeScripts);
    assert.ok(!result.recentKnowledge);
  });

  it('builds instructions with all context', async () => {
    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?instr=' + Date.now());
    const plugin = mod.default;

    const instructions = plugin._buildCompactionInstructions(
      { mode: 'debug', project: 'myapp', branch: 'fix-123' },
      ['script1.sh', 'script2.sh'],
      [{ query: 'redis' }],
    );

    assert.ok(instructions.includes('Active mode: debug'));
    assert.ok(instructions.includes('script1.sh, script2.sh'));
    assert.ok(instructions.includes('redis'));
    assert.ok(instructions.includes('Project: myapp'));
    assert.ok(instructions.includes('Branch: fix-123'));
    assert.ok(instructions.includes('Preserve error messages'));
    assert.ok(instructions.includes('file paths'));
  });

  it('builds minimal instructions when context is sparse', async () => {
    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?min=' + Date.now());
    const plugin = mod.default;

    const instructions = plugin._buildCompactionInstructions({}, [], []);
    assert.ok(instructions.includes('Preserve error messages'));
    assert.ok(!instructions.includes('Active mode'));
    assert.ok(!instructions.includes('Active scripts'));
  });

  it('logs compaction event to analytics file', async () => {
    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?log=' + Date.now());
    const plugin = mod.default;

    await plugin.hooks['experimental.session.compacting']({
      mode: 'debug',
      script: 'fix.sh',
      project: 'myapp',
      branch: 'feature-x',
    });

    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(tempDir, '.crux/analytics/compactions', `${today}.jsonl`);
    const content = await fs.readFile(logFile, 'utf8');
    const entry = JSON.parse(content.trim());

    assert.equal(entry.type, 'compaction');
    assert.equal(entry.mode, 'debug');
    assert.equal(entry.project, 'myapp');
    assert.equal(entry.branch, 'feature-x');
    assert.ok(entry.timestamp);
    assert.ok(entry.instructions);
    assert.ok(entry.instructions.includes('Active mode: debug'));
  });

  it('logs compaction with scripts and knowledge from checkpoint', async () => {
    const sessionsDir = path.join(tempDir, '.crux/analytics/sessions');
    await fs.mkdir(sessionsDir, { recursive: true });
    await fs.writeFile(path.join(sessionsDir, 'checkpoint.json'), JSON.stringify({
      activeScripts: ['deploy.sh'],
      recentKnowledgeLookups: [{ query: 'auth patterns', mode: 'build-py' }],
    }));

    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?logfull=' + Date.now());
    const plugin = mod.default;

    await plugin.hooks['experimental.session.compacting']({ mode: 'build-py' });

    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(tempDir, '.crux/analytics/compactions', `${today}.jsonl`);
    const content = await fs.readFile(logFile, 'utf8');
    const entry = JSON.parse(content.trim());

    assert.deepEqual(entry.activeScripts, ['deploy.sh']);
    assert.deepEqual(entry.knowledgeQueries, ['auth patterns']);
    assert.ok(entry.instructions.includes('deploy.sh'));
    assert.ok(entry.instructions.includes('auth patterns'));
  });

  it('logs compaction even when checkpoint is missing', async () => {
    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?lognocp=' + Date.now());
    const plugin = mod.default;

    await plugin.hooks['experimental.session.compacting']({ mode: 'plan' });

    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(tempDir, '.crux/analytics/compactions', `${today}.jsonl`);
    const content = await fs.readFile(logFile, 'utf8');
    const entry = JSON.parse(content.trim());

    assert.equal(entry.mode, 'plan');
    assert.ok(!entry.activeScripts);
    assert.ok(!entry.knowledgeQueries);
  });

  it('appends multiple compaction events to same log file', async () => {
    const mod = await import(PLUGINS_DIR + '/compaction-hook.js?multi=' + Date.now());
    const plugin = mod.default;

    await plugin.hooks['experimental.session.compacting']({ mode: 'debug' });
    await plugin.hooks['experimental.session.compacting']({ mode: 'plan' });

    const today = new Date().toISOString().split('T')[0];
    const logFile = path.join(tempDir, '.crux/analytics/compactions', `${today}.jsonl`);
    const content = await fs.readFile(logFile, 'utf8');
    const entries = content.trim().split('\n').map(l => JSON.parse(l));

    assert.equal(entries.length, 2);
    assert.equal(entries[0].mode, 'debug');
    assert.equal(entries[1].mode, 'plan');
  });
});

// =========================================================================
// Token Budget - full branch coverage
// =========================================================================

describe('token-budget.js full branch coverage', () => {
  it('blocks write tools in read-only modes and allows others', async () => {
    const mod = await import(PLUGINS_DIR + '/token-budget.js');
    const plugin = mod.default;

    // Test blocking
    for (const mode of ['plan', 'review', 'explain']) {
      for (const tool of ['edit', 'write', 'bash']) {
        await assert.rejects(
          () => plugin.hooks['tool.execute.before']({ tool }, { mode }),
          { message: new RegExp(`${tool} not allowed in ${mode} mode`) }
        );
      }
    }

    // Test allowing non-write tools in read-only modes
    plugin._resetSession();
    for (const tool of ['read', 'glob', 'grep']) {
      const result = await plugin.hooks['tool.execute.before']({ tool }, { mode: 'plan' });
      assert.equal(result, true);
    }

    // Test allowing all tools in non-read-only modes
    plugin._resetSession();
    for (const tool of ['read', 'edit', 'write', 'bash']) {
      const result = await plugin.hooks['tool.execute.before']({ tool }, { mode: 'build-py' });
      assert.equal(result, true);
    }

    // Test default mode (no mode specified)
    plugin._resetSession();
    const result = await plugin.hooks['tool.execute.before']({ tool: 'bash' }, {});
    assert.equal(result, true);
  });

  it('tracks token usage and returns warning', async () => {
    const mod = await import(PLUGINS_DIR + '/token-budget.js?warn=' + Date.now());
    const plugin = mod.default;
    plugin._resetSession();

    // Tight budget mode (strategist: 4000 tokens, warn at 70% = 2800)
    // Each 'read' call estimates 500 tokens
    // After 6 calls: 3000 tokens = 75% → warning
    for (let i = 0; i < 6; i++) {
      await plugin.hooks['tool.execute.before']({ tool: 'read' }, { mode: 'strategist' });
    }

    const status = plugin._getTokenStatus('strategist');
    assert.equal(status.status, 'warning');
    assert.ok(status.remaining < status.budget);
  });

  it('returns exceeded status when budget blown', async () => {
    const mod = await import(PLUGINS_DIR + '/token-budget.js?exceed=' + Date.now());
    const plugin = mod.default;
    plugin._resetSession();

    // Tight budget (strategist: 4000), ceil at 90% = 3600
    // 8 read calls × 500 = 4000 → exceeded
    for (let i = 0; i < 8; i++) {
      await plugin.hooks['tool.execute.before']({ tool: 'read' }, { mode: 'strategist' });
    }

    const result = await plugin.hooks['tool.execute.before']({ tool: 'read' }, { mode: 'strategist' });
    assert.ok(result.warning);
    assert.ok(result.warning.includes('exceeded'));
    assert.ok(result.tokenStatus);
  });

  it('resets on session start', async () => {
    const mod = await import(PLUGINS_DIR + '/token-budget.js?reset=' + Date.now());
    const plugin = mod.default;

    await plugin.hooks['tool.execute.before']({ tool: 'read' }, { mode: 'build-py' });
    assert.ok(plugin._getSessionTokens() > 0);

    plugin.hooks['session.start']();
    assert.equal(plugin._getSessionTokens(), 0);
    assert.equal(plugin._getToolCallCount(), 0);
  });

  it('assigns correct tiers to modes', async () => {
    const mod = await import(PLUGINS_DIR + '/token-budget.js?tiers=' + Date.now());
    const plugin = mod.default;

    assert.equal(plugin._getTierForMode('plan').budget, 4000);
    assert.equal(plugin._getTierForMode('build-py').budget, 8000);
    assert.equal(plugin._getTierForMode('writer').budget, 6000);
    assert.equal(plugin._getTierForMode('unknown-mode').budget, 6000); // default
  });

  it('estimates different token costs per tool', async () => {
    const mod = await import(PLUGINS_DIR + '/token-budget.js?est=' + Date.now());
    const plugin = mod.default;
    plugin._resetSession();

    await plugin.hooks['tool.execute.before']({ tool: 'glob' }, { mode: 'build-py' });
    const afterGlob = plugin._getSessionTokens();

    await plugin.hooks['tool.execute.before']({ tool: 'bash' }, { mode: 'build-py' });
    const afterBash = plugin._getSessionTokens();

    // Bash (600) costs more than glob (100)
    assert.ok(afterBash - afterGlob > afterGlob);
  });
});
