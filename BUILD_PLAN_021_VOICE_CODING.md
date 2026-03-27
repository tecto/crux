# BUILD_PLAN_021: Voice Coding — Speech-to-Code

**Created:** 2026-03-27
**Status:** NOT STARTED
**Priority:** SHOULD-CLOSE
**Competitive Gap:** Aider has voice coding (dictate code changes). No other tool in our category has it.
**Goal:** `crux voice` starts a voice input session — speech-to-text via local Whisper model, then processes as a normal prompt.

**Covers:** voice coding

## Architecture

```
$ crux voice
Listening... (press Enter to stop)
[User speaks: "add a function called validate_email that checks for @ symbol"]

Transcribed: "add a function called validate_email that checks for @ symbol"
Processing as prompt...
```

## Phase 1: Local Speech-to-Text

- [ ] 1.1 Integrate whisper.cpp or whisper-rs for local transcription
- [ ] 1.2 `crux voice` CLI — record audio, transcribe, process as command
- [ ] 1.3 Push-to-talk mode (hold key to record)
- [ ] 1.4 Tests

## Phase 2: Integration with Agent

- [ ] 2.1 Voice input feeds into `crux agent` REPL
- [ ] 2.2 Continuous listening mode with silence detection
- [ ] 2.3 Tests

## Convergence Criteria
- Local speech-to-text (no cloud API required)
- Voice input processed as agent commands
- Two consecutive clean audit passes
