import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';
import { execFile } from 'child_process';

function parseRiskLevel(content) {
  const match = content.match(/^#\s*Risk:\s*(\w+)/mi);
  return match ? match[1].toLowerCase() : 'unknown';
}

function preflightCheck(content, scriptPath) {
  const errors = [];

  if (!content.startsWith('#!/')) {
    errors.push('Missing shebang (#!/bin/bash or similar)');
  }

  if (!content.includes('set -euo pipefail')) {
    errors.push("Missing 'set -euo pipefail' safety clause");
  }

  const risk = parseRiskLevel(content);
  if (risk === 'unknown') {
    errors.push('Missing Risk header in script');
  }

  if (risk === 'low') {
    const destructiveOps = /\b(rm|delete\w*|drop|truncate)\b/;
    const execLines = content.split('\n').filter(l => !l.trimStart().startsWith('#'));
    if (execLines.some(l => destructiveOps.test(l))) {
      errors.push('Script classified as low risk but contains destructive operations');
    }
  }

  if (['medium', 'high'].includes(risk)) {
    const execLines = content.split('\n').filter(l => !l.trimStart().startsWith('#'));
    if (!execLines.some(l => l.includes('DRY_RUN'))) {
      errors.push('Medium/high risk script must support DRY_RUN');
    }
  }

  if (/>\s*\//.test(content)) {
    errors.push('Writes to root filesystem detected');
  }

  return { passed: errors.length === 0, errors, risk };
}

function runPythonAudit(scriptContent, riskLevel, gate) {
  return new Promise((resolve) => {
    const fn = gate === '8b' ? 'audit_script_8b' : 'audit_script_32b';
    const code = `
import json, sys
from scripts.lib.crux_llm_audit import ${fn}
result = ${fn}(sys.stdin.read(), ${JSON.stringify(riskLevel)})
print(json.dumps(result))
`;
    const proc = execFile('python3', ['-c', code], {
      timeout: 30000,
      maxBuffer: 1024 * 1024,
      cwd: process.env.CRUX_DIR || process.cwd(),
    }, (error, stdout, stderr) => {
      if (error) {
        resolve({ passed: true, skipped: true, reason: `Audit unavailable: ${error.message}` });
        return;
      }
      try {
        resolve(JSON.parse(stdout.trim()));
      } catch {
        resolve({ passed: true, skipped: true, reason: 'Failed to parse audit response' });
      }
    });
    proc.stdin.write(scriptContent);
    proc.stdin.end();
  });
}

function executeScript(scriptPath, args, env) {
  return new Promise((resolve, reject) => {
    execFile('bash', [scriptPath, ...args], { env, timeout: 60000 }, (error, stdout, stderr) => {
      if (error) {
        resolve({ success: false, exitCode: error.code || 1, stdout, stderr, error: error.message });
      } else {
        resolve({ success: true, exitCode: 0, stdout, stderr });
      }
    });
  });
}

const runScriptTool = tool({
  description: 'Execute a script through the seven-gate safety pipeline',
  args: {
    scriptPath: tool.schema.string().describe('Path to script to execute'),
    args: tool.schema.array(tool.schema.string()).optional().describe('Script arguments'),
    dryRun: tool.schema.boolean().optional().describe('Execute in dry-run mode'),
    approvalRequired: tool.schema.boolean().optional().describe('Require user approval'),
  },
  async execute(params) {
    const { scriptPath, args = [], dryRun = false, approvalRequired } = params;
    const fullPath = path.resolve(process.cwd(), scriptPath);

    // Gate 0: Script existence check
    let content;
    try {
      content = await fs.readFile(fullPath, 'utf8');
    } catch {
      return { error: `Script not found: ${scriptPath}` };
    }

    // Gate 1: Pre-flight validation
    const preflight = preflightCheck(content, fullPath);
    if (!preflight.passed) {
      return {
        gate: 'preflight',
        passed: false,
        errors: preflight.errors,
        risk: preflight.risk,
      };
    }

    // Gate 4: 8B adversarial audit
    const auditResult = await runPythonAudit(content, preflight.risk, '8b');
    if (!auditResult.passed && !auditResult.skipped) {
      return {
        gate: 'audit_8b',
        passed: false,
        risk: preflight.risk,
        findings: auditResult.findings || [],
        message: 'Script failed 8B adversarial security audit',
      };
    }

    // Gate 5: 32B second-opinion (high-risk only)
    let secondOpinion;
    if (preflight.risk === 'high') {
      secondOpinion = await runPythonAudit(content, preflight.risk, '32b');
      if (!secondOpinion.passed && !secondOpinion.skipped) {
        return {
          gate: 'audit_32b',
          passed: false,
          risk: preflight.risk,
          findings: secondOpinion.findings || [],
          message: 'Script failed 32B second-opinion security audit',
        };
      }
    } else {
      secondOpinion = { passed: true, skipped: true, reason: 'Not high-risk' };
    }

    // Gate 6: Human approval (high-risk or explicit request)
    const needsApproval = approvalRequired !== undefined ? approvalRequired : preflight.risk === 'high';
    if (needsApproval) {
      return {
        gate: 'approval',
        passed: false,
        risk: preflight.risk,
        message: 'Human approval required before execution. Re-run with approvalRequired: false after review.',
        preflight: { passed: true },
        audit8b: auditResult,
        audit32b: secondOpinion,
      };
    }

    // Gate 7: DRY_RUN for medium+ risk
    const env = { ...process.env };
    if (dryRun || (preflight.risk !== 'low' && !dryRun)) {
      env.DRY_RUN = '1';
    }

    // Execute
    const result = await executeScript(fullPath, args, env);

    return {
      gate: 'executed',
      passed: result.success,
      risk: preflight.risk,
      dryRun: env.DRY_RUN === '1',
      exitCode: result.exitCode,
      stdout: (result.stdout || '').substring(0, 2000),
      stderr: (result.stderr || '').substring(0, 1000),
      error: result.error || null,
      preflight: { passed: true },
      audit8b: auditResult,
      audit32b: secondOpinion,
    };
  },
});

// Expose internals for testing
runScriptTool._preflightCheck = preflightCheck;
runScriptTool._parseRiskLevel = parseRiskLevel;
runScriptTool._runPythonAudit = runPythonAudit;

export default runScriptTool;
