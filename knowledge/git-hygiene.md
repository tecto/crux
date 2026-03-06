# Git Workspace Hygiene

Rules for working in git repositories, especially dirty worktrees.

## Commit Discipline
- Commit only when the user explicitly asks
- Amend commits only when explicitly requested
- Avoid destructive commands (`git reset --hard`, `git checkout --`) unless the user approves

## Dirty Worktree Handling
- Preserve existing uncommitted changes made by the user
- When editing files with unrelated uncommitted changes, work around them rather than reverting
- When committing, stage only your own changes — leave unrelated modifications unstaged

## Secrets
- Check for `.env`, credentials, and keys before staging
- Exclude sensitive files from commits

Tags: git, safety, conventions
