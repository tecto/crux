const THINK_MODES = ['debug', 'plan', 'infra-architect', 'review', 'legal', 'strategist', 'psych', 'security', 'design-review', 'design-accessibility'];
const NO_THINK_MODES = ['build-py', 'build-ex', 'writer', 'analyst', 'mac', 'docker', 'explain', 'test', 'design-ui', 'design-system', 'design-responsive'];
const NEUTRAL_MODES = ['ai-infra'];

function routeThinkDirective(content, mode) {
  if (content.startsWith('/think') || content.startsWith('/no_think')) {
    return content;
  }

  let directive = '';
  if (THINK_MODES.includes(mode)) {
    directive = '/think ';
  } else if (NO_THINK_MODES.includes(mode)) {
    directive = '/no_think ';
  }

  return directive ? directive + content : content;
}

// OpenCode plugin factory
export const ThinkRouterPlugin = async (ctx) => {
  return {
    'chat.message': async ({}, { message }) => {
      const currentMode = message.mode || 'default';
      message.content = routeThinkDirective(message.content || '', currentMode);
    },
  };
};

// Backward-compatible hooks interface for tests
export default {
  hooks: {
    'chat.message': (message) => {
      const currentMode = message.mode || 'default';

      if (message.content.startsWith('/think') || message.content.startsWith('/no_think')) {
        return;
      }

      let directive = '';

      if (THINK_MODES.includes(currentMode)) {
        directive = '/think ';
      } else if (NO_THINK_MODES.includes(currentMode)) {
        directive = '/no_think ';
      }

      if (directive) {
        message.content = directive + message.content;
      }

      return message;
    },
  },
};
