import fs from 'fs/promises';
import path from 'path';

class SessionLogger {
  constructor() {
    this.sessionId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this.sessionDir = null;
    this.logFile = null;
    this.checkpointFile = null;
    this.buffer = [];
    this.flushInterval = null;
    this.interactionCount = 0;
    this.checkpointInterval = 5;
    this.currentMode = null;
    this.recentKnowledgeLookups = [];
    this.activeScripts = [];
    this.recovered = null;
  }

  async initialize() {
    const sessionsBase = path.join(process.env.HOME, '.crux/analytics/sessions');
    const today = new Date().toISOString().split('T')[0];
    this.sessionDir = path.join(sessionsBase, today);
    this.checkpointFile = path.join(sessionsBase, 'checkpoint.json');

    await fs.mkdir(this.sessionDir, { recursive: true });
    this.logFile = path.join(this.sessionDir, `${this.sessionId}.jsonl`);

    await this._tryRecover();

    this.flushInterval = setInterval(() => this.flush(), 5000);
    if (this.flushInterval.unref) this.flushInterval.unref();

    this.log({
      type: 'session.start',
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      recovered: this.recovered,
    });
  }

  async _tryRecover() {
    try {
      const data = await fs.readFile(this.checkpointFile, 'utf8');
      const checkpoint = JSON.parse(data);
      this.recovered = {
        previousSessionId: checkpoint.sessionId,
        timestamp: checkpoint.timestamp,
        mode: checkpoint.mode,
        interactionCount: checkpoint.interactionCount,
      };
      this.currentMode = checkpoint.mode;
      this.recentKnowledgeLookups = checkpoint.recentKnowledgeLookups || [];
      this.activeScripts = checkpoint.activeScripts || [];
    } catch {
      this.recovered = null;
    }
  }

  async _saveCheckpoint() {
    const checkpoint = {
      sessionId: this.sessionId,
      timestamp: new Date().toISOString(),
      mode: this.currentMode,
      interactionCount: this.interactionCount,
      recentKnowledgeLookups: this.recentKnowledgeLookups.slice(-5),
      activeScripts: this.activeScripts.slice(-10),
    };
    try {
      await fs.writeFile(this.checkpointFile, JSON.stringify(checkpoint, null, 2), 'utf8');
    } catch (err) {
      console.error('Checkpoint save error:', err);
    }
  }

  log(entry) {
    this.buffer.push({
      ...entry,
      timestamp: entry.timestamp || new Date().toISOString(),
    });
  }

  trackInteraction(mode) {
    this.interactionCount++;
    if (mode) this.currentMode = mode;
    if (this.interactionCount % this.checkpointInterval === 0) {
      this._saveCheckpoint();
      this.log({
        type: 'session.checkpoint',
        interactionCount: this.interactionCount,
        mode: this.currentMode,
      });
    }
  }

  trackKnowledgeLookup(query, mode) {
    this.recentKnowledgeLookups.push({ query, mode, timestamp: new Date().toISOString() });
    if (this.recentKnowledgeLookups.length > 10) {
      this.recentKnowledgeLookups = this.recentKnowledgeLookups.slice(-10);
    }
  }

  trackScript(scriptName) {
    if (!this.activeScripts.includes(scriptName)) {
      this.activeScripts.push(scriptName);
    }
  }

  getRecoveryInfo() {
    return this.recovered;
  }

  async flush() {
    if (this.buffer.length === 0) return;

    try {
      const lines = this.buffer
        .map(entry => JSON.stringify(entry))
        .join('\n') + '\n';

      await fs.appendFile(this.logFile, lines, 'utf8');
      this.buffer = [];
    } catch (err) {
      console.error('Session logger flush error:', err);
    }
  }

  async shutdown() {
    if (this.flushInterval) clearInterval(this.flushInterval);
    await this.flush();

    this.log({
      type: 'session.end',
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      interactionCount: this.interactionCount,
    });

    await this.flush();

    try {
      await fs.unlink(this.checkpointFile);
    } catch {
      // Checkpoint may not exist
    }
  }
}

// Factory function creates a fresh logger per plugin load
function createPlugin() {
  const logger = new SessionLogger();

  const plugin = async (ctx) => {
    return {
      event: async ({ event }) => {
        if (event.type === 'session.created') {
          await logger.initialize();
        } else if (event.type === 'session.deleted') {
          await logger.shutdown();
        }
      },

      'tool.execute.before': async (input, output) => {
        logger.log({
          type: 'tool.execute',
          tool: input.tool,
          params: JSON.stringify(output.args || {}).substring(0, 100),
        });
        if (input.tool === 'lookup_knowledge') {
          logger.trackKnowledgeLookup(
            output.args?.query || '',
            output.args?.mode || ''
          );
        }
        if (input.tool === 'run_script') {
          logger.trackScript(output.args?.scriptPath || 'unknown');
        }
      },

      'chat.message': async ({}, { message }) => {
        logger.log({
          type: 'chat.message',
          role: message.role,
          mode: message.mode,
          content: (message.content || '').substring(0, 200),
          tokens: message.tokens || 0,
        });
        logger.trackInteraction(message.mode);
      },

      'experimental.session.compacting': async (input, output) => {
        logger.log({
          type: 'session.context',
          mode: input.mode,
          scriptName: input.script,
          projectName: input.project,
          timestamp: new Date().toISOString(),
        });
      },
    };
  };

  // Expose logger for testing
  plugin._logger = logger;
  return plugin;
}

// Export both the factory (for OpenCode) and a hooks-based shim (for tests)
const pluginFactory = createPlugin();

// Backward-compatible hooks interface for tests
const hooks = {
  'session.start': async () => {
    await pluginFactory._logger.initialize();
  },
  'chat.message': (message) => {
    pluginFactory._logger.log({
      type: 'chat.message',
      role: message.role,
      mode: message.mode,
      content: (message.content || '').substring(0, 200),
      tokens: message.tokens || 0,
    });
    pluginFactory._logger.trackInteraction(message.mode);
  },
  'tool.execute.before': (execution) => {
    pluginFactory._logger.log({
      type: 'tool.execute',
      tool: execution.tool,
      params: JSON.stringify(execution.params || {}).substring(0, 100),
    });
    if (execution.tool === 'lookup_knowledge') {
      pluginFactory._logger.trackKnowledgeLookup(
        execution.params?.query || '',
        execution.params?.mode || ''
      );
    }
    if (execution.tool === 'run_script') {
      pluginFactory._logger.trackScript(execution.params?.scriptPath || 'unknown');
    }
  },
  'experimental.session.compacting': (context) => {
    pluginFactory._logger.log({
      type: 'session.context',
      mode: context.mode,
      scriptName: context.script,
      projectName: context.project,
      timestamp: new Date().toISOString(),
    });
  },
  'session.end': async () => {
    await pluginFactory._logger.shutdown();
  },
};

export const SessionLoggerPlugin = pluginFactory;
export default { hooks, _logger: pluginFactory._logger };
