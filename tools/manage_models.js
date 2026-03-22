import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';
import { execFile } from 'child_process';

const REGISTRY_PATH_PROJECT = '.crux/models/registry.json';
const REGISTRY_PATH_USER = '.crux/models/registry.json';

async function loadRegistry() {
  const projectPath = path.join(process.cwd(), REGISTRY_PATH_PROJECT);
  const userPath = path.join(process.env.HOME, REGISTRY_PATH_USER);

  for (const regPath of [projectPath, userPath]) {
    try {
      const data = await fs.readFile(regPath, 'utf8');
      return { registry: JSON.parse(data), path: regPath };
    } catch {
      continue;
    }
  }

  return {
    registry: { models: [], active: null, lastUpdated: null },
    path: projectPath,
  };
}

async function saveRegistry(registry, registryPath) {
  registry.lastUpdated = new Date().toISOString();
  await fs.mkdir(path.dirname(registryPath), { recursive: true });
  await fs.writeFile(registryPath, JSON.stringify(registry, null, 2), 'utf8');
}

async function listModels(registry) {
  return {
    models: registry.models,
    active: registry.active,
    total: registry.models.length,
  };
}

async function configureModel(registry, registryPath, model, quantization) {
  const existing = registry.models.find(m => m.name === model);
  if (existing) {
    if (quantization) existing.quantization = quantization;
    existing.updatedAt = new Date().toISOString();
  } else {
    registry.models.push({
      name: model,
      quantization: quantization || 'Q4_K_M',
      addedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
  }
  await saveRegistry(registry, registryPath);
  return { configured: model, quantization: quantization || 'Q4_K_M' };
}

async function switchModel(registry, registryPath, model) {
  const exists = registry.models.some(m => m.name === model);
  if (!exists) {
    return { error: `Model '${model}' not in registry. Add it with action: 'configure' first.` };
  }
  registry.active = model;
  await saveRegistry(registry, registryPath);
  return { switched: model, active: model };
}

// Model pulling is handled by the MCP server via crux_ollama.py, which
// provides the full pull_model implementation using Ollama's REST API.
// This JS bridge is retained for non-MCP environments where tools are
// loaded directly by OpenCode's plugin system.
function pullModelViaOllama(modelName) {
  return new Promise((resolve) => {
    const code = `
import json
from scripts.lib.crux_ollama import pull_model
result = pull_model(${JSON.stringify(modelName)})
print(json.dumps(result))
`;
    execFile('python3', ['-c', code], {
      timeout: 300000,  // 5 min for large model pulls
      maxBuffer: 1024 * 1024,
      cwd: process.env.CRUX_DIR || process.cwd(),
    }, (error, stdout, stderr) => {
      if (error) {
        resolve({
          success: false,
          error: `Ollama pull failed: ${error.message}`,
          model: modelName,
        });
        return;
      }
      try {
        resolve(JSON.parse(stdout.trim()));
      } catch {
        resolve({ success: false, error: 'Failed to parse Ollama response', model: modelName });
      }
    });
  });
}

async function pullModel(registry, registryPath, model, quantization) {
  // Pull from Ollama
  const pullResult = await pullModelViaOllama(model);

  if (pullResult.success) {
    // Auto-configure in registry after successful pull
    await configureModel(registry, registryPath, model, quantization);
    return {
      action: 'pull',
      model,
      status: 'completed',
      pull_result: pullResult,
      registered: true,
    };
  }

  return {
    action: 'pull',
    model,
    status: 'failed',
    error: pullResult.error || 'Pull failed',
    message: 'Ollama may not be running. Start it with: ollama serve',
  };
}

export default tool({
  description: 'Manage model registry and configuration',
  args: {
    action: tool.schema.enum(['list', 'pull', 'configure', 'switch']).describe('Action to perform'),
    model: tool.schema.string().optional().describe('Model name'),
    quantization: tool.schema.string().optional().describe('Quantization level'),
  },
  async execute(params) {
    const { action, model, quantization } = params;
    const { registry, path: registryPath } = await loadRegistry();

    switch (action) {
      case 'list':
        return listModels(registry);

      case 'pull':
        if (!model) return { error: 'Model name required for pull action' };
        return pullModel(registry, registryPath, model, quantization);

      case 'configure':
        if (!model) return { error: 'Model name required for configure action' };
        return configureModel(registry, registryPath, model, quantization);

      case 'switch':
        if (!model) return { error: 'Model name required for switch action' };
        return switchModel(registry, registryPath, model);
    }
  },
});
