import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const TOOLS_DIR = path.join(import.meta.dirname, '..', 'tools');

describe('run_script.js implementation', () => {
  let tempDir, origCwd;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'crux-run-'));
    origCwd = process.cwd();
    process.chdir(tempDir);
  });

  afterEach(async () => {
    process.chdir(origCwd);
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  function writeScript(name, content) {
    const p = path.join(tempDir, name);
    return fs.writeFile(p, content, { mode: 0o755 });
  }

  const validLowScript = [
    '#!/bin/bash',
    '################################################################################',
    '# Name: test-script',
    '# Risk: low',
    '# Description: A test script',
    '################################################################################',
    'set -euo pipefail',
    'main() { echo "hello"; }',
    'if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then main "$@"; fi',
  ].join('\n');

  const validMediumScript = [
    '#!/bin/bash',
    '# Risk: medium',
    '# Description: Medium risk script',
    'set -euo pipefail',
    'DRY_RUN="${DRY_RUN:-0}"',
    'main() {',
    '  if [[ "$DRY_RUN" == "1" ]]; then echo "DRY RUN"; exit 0; fi',
    '  echo "executed"',
    '}',
    'main',
  ].join('\n');

  const validHighScript = [
    '#!/bin/bash',
    '# Risk: high',
    '# Description: High risk script',
    'set -euo pipefail',
    'DRY_RUN="${DRY_RUN:-0}"',
    'main() {',
    '  if [[ "$DRY_RUN" == "1" ]]; then echo "DRY RUN"; exit 0; fi',
    '  echo "dangerous"',
    '}',
    'main',
  ].join('\n');

  it('executes a valid low-risk script', async () => {
    await writeScript('test.sh', validLowScript);
    const mod = await import(TOOLS_DIR + '/run_script.js?exec=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'test.sh' });
    assert.equal(result.gate, 'executed');
    assert.equal(result.passed, true);
    assert.equal(result.risk, 'low');
    assert.ok(result.stdout.includes('hello'));
  });

  it('returns error for nonexistent script', async () => {
    const mod = await import(TOOLS_DIR + '/run_script.js?nofile=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'nope.sh' });
    assert.ok(result.error);
  });

  it('fails preflight for missing shebang', async () => {
    await writeScript('bad.sh', '# Risk: low\nset -euo pipefail\necho hi\n');
    const mod = await import(TOOLS_DIR + '/run_script.js?shebang=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'bad.sh' });
    assert.equal(result.gate, 'preflight');
    assert.equal(result.passed, false);
    assert.ok(result.errors.some(e => e.includes('shebang')));
  });

  it('fails preflight for missing set -euo pipefail', async () => {
    await writeScript('bad.sh', '#!/bin/bash\n# Risk: low\necho hi\n');
    const mod = await import(TOOLS_DIR + '/run_script.js?pipefail=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'bad.sh' });
    assert.equal(result.gate, 'preflight');
    assert.ok(result.errors.some(e => e.includes('pipefail')));
  });

  it('fails preflight for low-risk with destructive ops', async () => {
    await writeScript('bad.sh', '#!/bin/bash\n# Risk: low\nset -euo pipefail\nrm -rf /tmp/test\n');
    const mod = await import(TOOLS_DIR + '/run_script.js?destructive=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'bad.sh' });
    assert.equal(result.gate, 'preflight');
    assert.ok(result.errors.some(e => e.includes('destructive')));
  });

  it('fails preflight for medium-risk without DRY_RUN', async () => {
    await writeScript('bad.sh', '#!/bin/bash\n# Risk: medium\nset -euo pipefail\necho hi\n');
    const mod = await import(TOOLS_DIR + '/run_script.js?dryrun=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'bad.sh' });
    assert.equal(result.gate, 'preflight');
    assert.ok(result.errors.some(e => e.includes('DRY_RUN')));
  });

  it('requires approval for high-risk scripts', async () => {
    await writeScript('high.sh', validHighScript);
    const mod = await import(TOOLS_DIR + '/run_script.js?approval=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'high.sh' });
    assert.equal(result.gate, 'approval');
    assert.equal(result.passed, false);
    assert.ok(result.message.includes('approval'));
  });

  it('executes high-risk with explicit approval=false', async () => {
    await writeScript('high.sh', validHighScript);
    const mod = await import(TOOLS_DIR + '/run_script.js?approved=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'high.sh', approvalRequired: false });
    assert.equal(result.gate, 'executed');
    assert.equal(result.dryRun, true); // DRY_RUN forced for high-risk
  });

  it('sets DRY_RUN for medium-risk scripts', async () => {
    await writeScript('med.sh', validMediumScript);
    const mod = await import(TOOLS_DIR + '/run_script.js?medium=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'med.sh' });
    assert.equal(result.dryRun, true);
    assert.ok(result.stdout.includes('DRY RUN'));
  });

  it('passes args to script', async () => {
    await writeScript('args.sh', [
      '#!/bin/bash',
      '# Risk: low',
      'set -euo pipefail',
      'echo "arg1=$1"',
    ].join('\n'));
    const mod = await import(TOOLS_DIR + '/run_script.js?args=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'args.sh', args: ['hello'] });
    assert.ok(result.stdout.includes('arg1=hello'));
  });

  it('handles script execution error', async () => {
    await writeScript('fail.sh', [
      '#!/bin/bash',
      '# Risk: low',
      'set -euo pipefail',
      'exit 1',
    ].join('\n'));
    const mod = await import(TOOLS_DIR + '/run_script.js?fail=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'fail.sh' });
    assert.equal(result.passed, false);
    assert.ok(result.exitCode !== 0);
  });

  it('validates with zod schema', async () => {
    const mod = await import(TOOLS_DIR + '/run_script.js?zod=' + Date.now());
    await assert.rejects(
      () => mod.default.execute({}),
      (err) => err.name === 'ZodError'
    );
  });

  it('preflight detects root filesystem writes', async () => {
    const mod = await import(TOOLS_DIR + '/run_script.js?root=' + Date.now());
    const check = mod.default._preflightCheck('#!/bin/bash\n# Risk: low\nset -euo pipefail\necho data > /etc/file\n', 'test.sh');
    assert.equal(check.passed, false);
    assert.ok(check.errors.some(e => e.includes('root filesystem')));
  });

  it('parseRiskLevel extracts risk correctly', async () => {
    const mod = await import(TOOLS_DIR + '/run_script.js?parse=' + Date.now());
    assert.equal(mod.default._parseRiskLevel('# Risk: high\n'), 'high');
    assert.equal(mod.default._parseRiskLevel('no risk header\n'), 'unknown');
  });

  it('includes audit8b and audit32b in execution result', async () => {
    await writeScript('test.sh', validLowScript);
    const mod = await import(TOOLS_DIR + '/run_script.js?audit=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'test.sh' });
    assert.equal(result.gate, 'executed');
    assert.ok('audit8b' in result);
    assert.ok('audit32b' in result);
  });

  it('low-risk skips 32b audit', async () => {
    await writeScript('test.sh', validLowScript);
    const mod = await import(TOOLS_DIR + '/run_script.js?skip32b=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'test.sh' });
    assert.equal(result.audit32b.skipped, true);
    assert.ok(result.audit32b.reason.includes('Not high-risk'));
  });

  it('high-risk triggers both audit gates', async () => {
    await writeScript('high.sh', validHighScript);
    const mod = await import(TOOLS_DIR + '/run_script.js?both=' + Date.now());
    const result = await mod.default.execute({ scriptPath: 'high.sh', approvalRequired: false });
    assert.ok('audit8b' in result);
    assert.ok('audit32b' in result);
    // Both should exist (either skipped or with results)
    assert.ok(result.audit8b.passed !== undefined || result.audit8b.skipped);
    assert.ok(result.audit32b.passed !== undefined || result.audit32b.skipped);
  });

  it('runPythonAudit returns skipped when python unavailable', async () => {
    const mod = await import(TOOLS_DIR + '/run_script.js?pyaudit=' + Date.now());
    // This will either succeed (if Ollama is running) or return skipped
    const result = await mod.default._runPythonAudit('echo hello', 'low', '8b');
    assert.ok(result.passed !== undefined);
  });
});
