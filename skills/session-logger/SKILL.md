# Skill: Session Logger

## Purpose
Automatically logs all sessions with full context for recovery and analysis.

## Capabilities
- JSONL session logging with structured data
- Crash recovery context preservation
- Session resumption with full state restoration
- Analytics data collection
- Integration with digest and stats commands

## Implementation
Implemented as a plugin that hooks into session lifecycle events:
- `session.start`: Begin session logging
- `chat.message`: Log each interaction
- `experimental.session.compacting`: Preserve critical context
- `session.end`: Finalize session record

## Log Format
Each line is a JSON object containing:
```json
{
  "timestamp": "2026-03-05T14:30:45Z",
  "type": "message|command|error",
  "mode": "build-py",
  "content": "message content",
  "duration": 125,
  "tokens": 1500,
  "result": "success|error"
}
```

## Retention
- Active sessions: Live in `.opencode/sessions/YYYY-MM-DD/`
- Archived sessions: Moved to archive after 90 days
- Log deletion: Never automatic, requires explicit command

## Data Privacy
- Logs contain potentially sensitive information
- Store in user-only readable directory: `.config/opencode/`
- Never upload without explicit consent
- Local-only by default
