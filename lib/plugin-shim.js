// Lightweight shim for @opencode-ai/plugin
// Provides the tool() helper and tool.schema (which wraps Zod).
// In production OpenCode provides this; in tests we use this shim.
//
// NOTE: Full OpenCode integration verification is deferred to Phase 1 of
// CRUX_ECOSYSTEM_PLAN (CruxCLI hard fork). This shim will be replaced by
// the CruxCLI plugin loader once the hard fork establishes the canonical
// tool registration API.
import { z } from 'zod';

export function tool(definition) {
  // Convert args spec to a Zod schema for validation
  const argEntries = Object.entries(definition.args || {});
  const zodShape = {};
  for (const [key, zodType] of argEntries) {
    zodShape[key] = zodType;
  }
  const schema = z.object(zodShape);

  return {
    description: definition.description,
    args: definition.args,
    schema, // Zod schema for validation (used by tests)
    async execute(rawArgs, context) {
      const parsed = schema.parse(rawArgs);
      return definition.execute(parsed, context || {});
    },
  };
}

// Expose Zod types as tool.schema for the tool() API
tool.schema = z;
