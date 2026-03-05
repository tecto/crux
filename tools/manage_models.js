import { tool } from '../lib/plugin-shim.js';
import fs from 'fs/promises';
import path from 'path';

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
        return {
          action: 'pull',
          model,
          status: 'pending',
          message: 'Ollama API integration pending. Add model to registry with configure action.',
        };

      case 'configure':
        if (!model) return { error: 'Model name required for configure action' };
        return configureModel(registry, registryPath, model, quantization);

      case 'switch':
        if (!model) return { error: 'Model name required for switch action' };
        return switchModel(registry, registryPath, model);
    }
  },
});
