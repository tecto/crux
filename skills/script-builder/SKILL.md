# Skill: Script Builder

## Purpose
Streamlines creation of new scripts following project standards.

## Capabilities
- Script template generation with proper headers
- Validation of script structure
- DRY_RUN support injection
- Error handling framework
- Git integration for commits
- Script registration in system

## Workflow
1. User requests script for specific task
2. Skill generates template with appropriate header
3. User provides implementation
4. Skill validates against requirements
5. Skill registers script and creates git commit
6. Script available for execution via `run_script` tool

## Template Injection
Automatically creates script with:
- Proper shebang and error handling
- DRY_RUN environment variable support
- Logging functions
- Error message templates
- Git-ready structure

## Validation Checks
- Header format verification
- Risk level appropriateness
- Idempotency testing
- No shell injection vulnerabilities
- Proper quoting and escaping

## Integration
Works with:
- `run_script` tool for execution
- `promote_script` tool for library promotion
- Session logger for tracking
- Knowledge base for documentation
