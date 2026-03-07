import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const TOOLS_DIR = path.join(import.meta.dirname, '..', 'tools');

// =========================================================================
// lookup_knowledge.js
// =========================================================================

describe('lookup_knowledge.js implementation', () => {
  let tempDir, origHome, origCwd;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-know-'));
    origHome = process.env.HOME;
    origCwd = process.cwd();
    process.env.HOME = tempDir;
    process.chdir(tempDir);

    // Create project-level knowledge
    const projectKnow = path.join(tempDir, '.crux', 'knowledge');
    await fs.mkdir(path.join(projectKnow, 'build-py'), { recursive: true });
    await fs.writeFile(path.join(projectKnow, 'redis-setup.md'),
      '# Redis Setup\n\nAlways install redis-py. Check connection params.\nTags: redis, python');
    await fs.writeFile(path.join(projectKnow, 'build-py', 'pytest-fixtures.md'),
      '# Pytest Fixtures\n\nUse conftest.py for shared fixtures.\nTags: pytest, python');

    // Create user-level knowledge
    const userKnow = path.join(tempDir, '.crux', 'knowledge');
    await fs.mkdir(path.join(userKnow, 'shared'), { recursive: true });
    await fs.mkdir(path.join(userKnow, 'build-py'), { recursive: true });
    await fs.writeFile(path.join(userKnow, 'shared', 'docker-basics.md'),
      '# Docker Basics\n\nAlways use multi-stage builds.\nTags: docker');
    await fs.writeFile(path.join(userKnow, 'build-py', 'venv-setup.md'),
      '# Virtual Environment\n\nAlways use venv for Python projects.\nTags: python, venv');
  });

  afterEach(async () => {
    process.env.HOME = origHome;
    process.chdir(origCwd);
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('finds knowledge matching query', async () => {
    const mod = await import(TOOLS_DIR + '/lookup_knowledge.js?q=' + Date.now());
    const result = await mod.default.execute({ query: 'redis' });
    assert.ok(result.totalFound >= 1);
    assert.ok(result.results[0].name.includes('redis'));
    assert.equal(result.mode, 'all');
  });

  it('filters by mode', async () => {
    const mod = await import(TOOLS_DIR + '/lookup_knowledge.js?mode=' + Date.now());
    const result = await mod.default.execute({ query: 'python', mode: 'build-py' });
    assert.ok(result.totalFound >= 1);
    assert.equal(result.mode, 'build-py');
    // Should include both project and user level build-py entries
    const names = result.results.map(r => r.name);
    assert.ok(names.some(n => n.includes('pytest') || n.includes('venv')));
  });

  it('returns empty results for no match', async () => {
    const mod = await import(TOOLS_DIR + '/lookup_knowledge.js?empty=' + Date.now());
    const result = await mod.default.execute({ query: 'nonexistent-topic-xyz' });
    assert.equal(result.totalFound, 0);
    assert.deepEqual(result.results, []);
  });

  it('includes source field (project vs user)', async () => {
    const mod = await import(TOOLS_DIR + '/lookup_knowledge.js?src=' + Date.now());
    const result = await mod.default.execute({ query: 'redis python docker' });
    const sources = result.results.map(r => r.source);
    assert.ok(sources.includes('project') || sources.includes('user'));
  });

  it('truncates excerpt to 300 chars', async () => {
    // Create a long knowledge file
    const projectKnow = path.join(tempDir, '.crux', 'knowledge');
    await fs.writeFile(path.join(projectKnow, 'long-entry.md'),
      '# Long Entry\n\n' + 'searchterm '.repeat(200));

    const mod = await import(TOOLS_DIR + '/lookup_knowledge.js?long=' + Date.now());
    const result = await mod.default.execute({ query: 'searchterm' });
    const entry = result.results.find(r => r.name === 'long-entry');
    assert.ok(entry);
    assert.ok(entry.excerpt.length <= 300);
  });

  it('handles missing directories gracefully', async () => {
    // Remove all knowledge dirs
    await fs.rm(path.join(tempDir, '.crux'), { recursive: true, force: true });
    await fs.rm(path.join(tempDir, '.config'), { recursive: true, force: true });

    const mod = await import(TOOLS_DIR + '/lookup_knowledge.js?miss=' + Date.now());
    const result = await mod.default.execute({ query: 'anything' });
    assert.equal(result.totalFound, 0);
  });

  it('validates input with zod schema', async () => {
    const mod = await import(TOOLS_DIR + '/lookup_knowledge.js?zod=' + Date.now());
    await assert.rejects(
      () => mod.default.execute({}),
      (err) => err.name === 'ZodError'
    );
  });

  it('limits results to 10', async () => {
    const projectKnow = path.join(tempDir, '.crux', 'knowledge');
    for (let i = 0; i < 15; i++) {
      await fs.writeFile(path.join(projectKnow, `entry-${i}.md`),
        `# Entry ${i}\n\nKeyword match content here`);
    }

    const mod = await import(TOOLS_DIR + '/lookup_knowledge.js?limit=' + Date.now());
    const result = await mod.default.execute({ query: 'keyword' });
    assert.ok(result.results.length <= 10);
    assert.ok(result.totalFound >= 10);
  });
});

// =========================================================================
// list_scripts.js
// =========================================================================

describe('list_scripts.js implementation', () => {
  let tempDir, origCwd;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-list-'));
    origCwd = process.cwd();
    process.chdir(tempDir);

    const sessionDir = path.join(tempDir, '.crux', 'scripts', 'session');
    const libDir = path.join(tempDir, '.crux', 'scripts', 'lib');
    await fs.mkdir(sessionDir, { recursive: true });
    await fs.mkdir(libDir, { recursive: true });

    await fs.writeFile(path.join(libDir, 'backup-db.sh'), [
      '#!/bin/bash',
      '################################################################################',
      '# Name: backup-db',
      '# Risk: high',
      '# Created: 2026-03-01',
      '# Status: library',
      '# Description: Backs up the database',
      '################################################################################',
      'set -euo pipefail',
    ].join('\n'));

    await fs.writeFile(path.join(sessionDir, 'fix-bug.sh'), [
      '#!/bin/bash',
      '################################################################################',
      '# Name: fix-bug',
      '# Risk: low',
      '# Created: 2026-03-05',
      '# Status: session',
      '# Description: Fixes a bug',
      '################################################################################',
      'set -euo pipefail',
    ].join('\n'));

    await fs.writeFile(path.join(libDir, 'not-a-script.txt'), 'ignore me');
  });

  afterEach(async () => {
    process.chdir(origCwd);
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('lists all scripts from lib and session', async () => {
    const mod = await import(TOOLS_DIR + '/list_scripts.js?all=' + Date.now());
    const result = await mod.default.execute({});
    assert.ok(result.scripts.length >= 2);
    const names = result.scripts.map(s => s.name);
    assert.ok(names.includes('backup-db'));
    assert.ok(names.includes('fix-bug'));
  });

  it('parses script headers correctly', async () => {
    const mod = await import(TOOLS_DIR + '/list_scripts.js?hdr=' + Date.now());
    const result = await mod.default.execute({});
    const backup = result.scripts.find(s => s.name === 'backup-db');
    assert.ok(backup);
    assert.equal(backup.risk, 'high');
    assert.equal(backup.status, 'library');
    assert.equal(backup.description, 'Backs up the database');
  });

  it('filters by keyword', async () => {
    const mod = await import(TOOLS_DIR + '/list_scripts.js?filter=' + Date.now());
    const result = await mod.default.execute({ filter: 'backup' });
    assert.equal(result.scripts.length, 1);
    assert.equal(result.scripts[0].name, 'backup-db');
  });

  it('handles missing directories', async () => {
    await fs.rm(path.join(tempDir, '.crux'), { recursive: true });

    const mod = await import(TOOLS_DIR + '/list_scripts.js?miss=' + Date.now());
    const result = await mod.default.execute({});
    assert.deepEqual(result.scripts, []);
  });

  it('ignores non-.sh files', async () => {
    const mod = await import(TOOLS_DIR + '/list_scripts.js?ignore=' + Date.now());
    const result = await mod.default.execute({});
    const names = result.scripts.map(s => s.name);
    assert.ok(!names.includes('not-a-script'));
  });
});

// =========================================================================
// suggest_handoff.js
// =========================================================================

describe('suggest_handoff.js implementation', () => {
  let tempDir, origCwd;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-handoff-'));
    origCwd = process.cwd();
    process.chdir(tempDir);
    await fs.mkdir(path.join(tempDir, '.crux'), { recursive: true });
  });

  afterEach(async () => {
    process.chdir(origCwd);
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('writes handoff context file', async () => {
    const mod = await import(TOOLS_DIR + '/suggest_handoff.js?write=' + Date.now());
    const result = await mod.default.execute({
      fromMode: 'build-py',
      taskDescription: 'Debug timeout error in database connection',
    });
    assert.ok(result.handoffFile);
    assert.equal(result.suggestedMode, 'debug');

    const content = await fs.readFile(path.join(tempDir, '.crux', 'sessions', 'handoff.md'), 'utf8');
    assert.ok(content.includes('build-py'));
    assert.ok(content.includes('timeout'));
  });

  it('suggests appropriate target modes', async () => {
    const mod = await import(TOOLS_DIR + '/suggest_handoff.js?suggest=' + Date.now());

    const debugResult = await mod.default.execute({
      fromMode: 'build-py',
      taskDescription: 'debug this error',
    });
    assert.equal(debugResult.suggestedMode, 'debug');

    const planResult = await mod.default.execute({
      fromMode: 'build-ex',
      taskDescription: 'need to plan the architecture',
    });
    assert.equal(planResult.suggestedMode, 'plan');

    const reviewResult = await mod.default.execute({
      fromMode: 'build-py',
      taskDescription: 'review the code',
    });
    assert.equal(reviewResult.suggestedMode, 'review');
  });

  it('validates required parameters', async () => {
    const mod = await import(TOOLS_DIR + '/suggest_handoff.js?validate=' + Date.now());
    await assert.rejects(
      () => mod.default.execute({ fromMode: 'build-py' }),
      (err) => err.name === 'ZodError'
    );
  });

  it('includes return-to mode in handoff', async () => {
    const mod = await import(TOOLS_DIR + '/suggest_handoff.js?return=' + Date.now());
    const result = await mod.default.execute({
      fromMode: 'build-py',
      taskDescription: 'debug issue',
    });
    assert.equal(result.returnTo, 'build-py');
  });
});

// =========================================================================
// project_context.js
// =========================================================================

describe('project_context.js implementation', () => {
  let tempDir, origCwd;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-ctx-'));
    origCwd = process.cwd();
    process.chdir(tempDir);
    await fs.mkdir(path.join(tempDir, '.crux', 'context'), { recursive: true });
  });

  afterEach(async () => {
    process.chdir(origCwd);
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('reads PROJECT.md and returns parsed sections', async () => {
    await fs.writeFile(path.join(tempDir, '.crux', 'context', 'PROJECT.md'), [
      '# Project: test-app',
      '',
      '## Tech Stack',
      '- Language: Python',
      '- Framework: FastAPI',
      '',
      '## Directory Structure',
      '```',
      'app/',
      '  main.py',
      '```',
      '',
      '## Key Files',
      '- app/main.py - entry point',
      '',
      '## Recent Changes',
      '- Added user model',
    ].join('\n'));

    const mod = await import(TOOLS_DIR + '/project_context.js?read=' + Date.now());
    const result = await mod.default.execute({});
    assert.ok(result.content);
    assert.ok(result.content.includes('Python'));
  });

  it('returns instruction when PROJECT.md missing', async () => {
    const mod = await import(TOOLS_DIR + '/project_context.js?miss=' + Date.now());
    const result = await mod.default.execute({});
    assert.ok(result.error || result.instruction);
  });

  it('filters by include sections', async () => {
    await fs.writeFile(path.join(tempDir, '.crux', 'context', 'PROJECT.md'), [
      '# Project: test-app',
      '',
      '## Tech Stack',
      '- Language: Python',
      '',
      '## Directory Structure',
      'app/',
      '',
      '## Key Files',
      '- main.py',
    ].join('\n'));

    const mod = await import(TOOLS_DIR + '/project_context.js?include=' + Date.now());
    const result = await mod.default.execute({ include: ['Tech Stack'] });
    assert.ok(result.content.includes('Python'));
  });
});

// =========================================================================
// promote_script.js
// =========================================================================

describe('promote_script.js implementation', () => {
  let tempDir, origCwd;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-promote-'));
    origCwd = process.cwd();
    process.chdir(tempDir);

    const sessionDir = path.join(tempDir, '.crux', 'scripts', 'session');
    const libDir = path.join(tempDir, '.crux', 'scripts', 'lib');
    const archiveDir = path.join(tempDir, '.crux', 'scripts', 'archive');
    await fs.mkdir(sessionDir, { recursive: true });
    await fs.mkdir(libDir, { recursive: true });
    await fs.mkdir(archiveDir, { recursive: true });

    await fs.writeFile(path.join(sessionDir, 'my-script.sh'), [
      '#!/bin/bash',
      '################################################################################',
      '# Name: my-script',
      '# Risk: low',
      '# Created: 2026-03-05',
      '# Status: session',
      '# Description: Test script',
      '################################################################################',
      'set -euo pipefail',
      'main() { echo "hello"; }',
      'if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then main "$@"; fi',
    ].join('\n'));
  });

  afterEach(async () => {
    process.chdir(origCwd);
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  it('promotes script from session to lib', async () => {
    const mod = await import(TOOLS_DIR + '/promote_script.js?promote=' + Date.now());
    const result = await mod.default.execute({ scriptPath: '.crux/scripts/session/my-script.sh' });
    assert.ok(result.promoted);

    // Verify file moved
    const libFile = path.join(tempDir, '.crux', 'scripts', 'lib', 'my-script.sh');
    const content = await fs.readFile(libFile, 'utf8');
    assert.ok(content.includes('# Status: library'));
  });

  it('rejects nonexistent script', async () => {
    const mod = await import(TOOLS_DIR + '/promote_script.js?nofile=' + Date.now());
    const result = await mod.default.execute({ scriptPath: '.crux/scripts/session/nope.sh' });
    assert.ok(result.error);
  });

  it('validates required scriptPath', async () => {
    const mod = await import(TOOLS_DIR + '/promote_script.js?validate=' + Date.now());
    await assert.rejects(
      () => mod.default.execute({}),
      (err) => err.name === 'ZodError'
    );
  });
});
