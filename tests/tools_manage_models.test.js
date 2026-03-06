import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'path';

const TOOLS_DIR = path.join(import.meta.dirname, '..', 'tools');

describe('manage_models.js implementation', () => {
  let tempDir, origCwd, origHome;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-models-'));
    origCwd = process.cwd();
    origHome = process.env.HOME;
    process.chdir(tempDir);
    process.env.HOME = tempDir;
  });

  afterEach(async () => {
    process.chdir(origCwd);
    process.env.HOME = origHome;
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('lists empty registry', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?list=' + Date.now());
    const result = await mod.default.execute({ action: 'list' });
    assert.equal(result.total, 0);
    assert.deepEqual(result.models, []);
    assert.equal(result.active, null);
  });

  it('configures a new model', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?config=' + Date.now());
    const result = await mod.default.execute({ action: 'configure', model: 'qwen3:32b' });
    assert.equal(result.configured, 'qwen3:32b');
    assert.equal(result.quantization, 'Q4_K_M');

    // Verify persisted
    const listResult = await mod.default.execute({ action: 'list' });
    assert.equal(listResult.total, 1);
    assert.equal(listResult.models[0].name, 'qwen3:32b');
  });

  it('configures with quantization', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?quant=' + Date.now());
    const result = await mod.default.execute({ action: 'configure', model: 'qwen3:32b', quantization: 'Q8_0' });
    assert.equal(result.quantization, 'Q8_0');
  });

  it('updates existing model config', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?update=' + Date.now());
    await mod.default.execute({ action: 'configure', model: 'qwen3:32b' });
    const result = await mod.default.execute({ action: 'configure', model: 'qwen3:32b', quantization: 'Q5_K_M' });
    assert.equal(result.quantization, 'Q5_K_M');

    const list = await mod.default.execute({ action: 'list' });
    assert.equal(list.total, 1); // Not duplicated
  });

  it('switches to configured model', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?switch=' + Date.now());
    await mod.default.execute({ action: 'configure', model: 'qwen3:32b' });
    const result = await mod.default.execute({ action: 'switch', model: 'qwen3:32b' });
    assert.equal(result.active, 'qwen3:32b');

    const list = await mod.default.execute({ action: 'list' });
    assert.equal(list.active, 'qwen3:32b');
  });

  it('rejects switch to unknown model', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?unkn=' + Date.now());
    const result = await mod.default.execute({ action: 'switch', model: 'nonexistent' });
    assert.ok(result.error);
    assert.ok(result.error.includes('not in registry'));
  });

  it('pull attempts Ollama pull and handles unavailability', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?pull=' + Date.now());
    const result = await mod.default.execute({ action: 'pull', model: 'llama3:8b' });
    // Either completed (if Ollama running) or failed (if not)
    assert.ok(['completed', 'failed'].includes(result.status));
    assert.equal(result.action, 'pull');
    assert.equal(result.model, 'llama3:8b');
  });

  it('requires model for pull/configure/switch', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?req=' + Date.now());
    for (const action of ['pull', 'configure', 'switch']) {
      const result = await mod.default.execute({ action });
      assert.ok(result.error);
      assert.ok(result.error.includes('required'));
    }
  });

  it('validates with zod schema', async () => {
    const mod = await import(TOOLS_DIR + '/manage_models.js?zod=' + Date.now());
    await assert.rejects(
      () => mod.default.execute({}),
      (err) => err.name === 'ZodError'
    );
  });
});
