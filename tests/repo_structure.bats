#!/usr/bin/env bats
# Tests for overall repository structure and cross-file consistency.

REPO="/Users/user/personal/crux"

# =========================================================================
# Directory structure
# =========================================================================

@test "all expected top-level directories exist" {
    for dir in modes plugins tools commands scripts templates knowledge docs bin skills; do
        if [ ! -d "$REPO/$dir" ]; then
            echo "Missing directory: $dir"
            return 1
        fi
    done
}

@test "scripts/templates directory exists" {
    [ -d "$REPO/scripts/templates" ]
}

@test "knowledge has per-mode subdirectories" {
    for dir in build-py build-ex shared; do
        if [ ! -d "$REPO/knowledge/$dir" ]; then
            echo "Missing knowledge subdirectory: $dir"
            return 1
        fi
    done
}

# =========================================================================
# Key files exist
# =========================================================================

@test "README.md exists and is non-trivial" {
    [ -f "$REPO/README.md" ]
    size=$(wc -c < "$REPO/README.md" | tr -d ' ')
    [ "$size" -gt 1000 ]
}

@test "CONTRIBUTING.md exists" {
    [ -f "$REPO/CONTRIBUTING.md" ]
}

@test "LICENSE exists and is MIT" {
    [ -f "$REPO/LICENSE" ]
    grep -q 'MIT' "$REPO/LICENSE"
}

@test "setup.sh is executable" {
    [ -x "$REPO/setup.sh" ]
}

@test "CLAUDE.md exists" {
    [ -f "$REPO/CLAUDE.md" ]
}

# =========================================================================
# File counts match CLAUDE.md claims
# =========================================================================

@test "15 mode files exist (excluding template)" {
    count=$(ls -1 "$REPO/modes"/*.md 2>/dev/null | grep -v '_template' | wc -l | tr -d ' ')
    [ "$count" -eq 15 ]
}

@test "6 plugin files exist" {
    count=$(ls -1 "$REPO/plugins"/*.js 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 6 ]
}

@test "7 tool files exist" {
    count=$(ls -1 "$REPO/tools"/*.js 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 7 ]
}

@test "11 command files exist" {
    count=$(ls -1 "$REPO/commands"/*.md 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 11 ]
}

@test "2 script templates exist" {
    count=$(ls -1 "$REPO/scripts/templates"/*.sh 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 2 ]
}

# =========================================================================
# Template files
# =========================================================================

@test "AGENTS.md template exists" {
    [ -f "$REPO/templates/AGENTS.md" ]
}

@test "PROJECT.md template exists" {
    [ -f "$REPO/templates/PROJECT.md" ]
}

@test "knowledge template exists" {
    [ -f "$REPO/knowledge/_template.md" ]
}

# =========================================================================
# Cross-file consistency: modes in think-router match mode files
# =========================================================================

@test "think-router THINK_MODES all have corresponding mode files" {
    # Extract THINK_MODES from think-router.js
    modes=$(grep 'THINK_MODES' "$REPO/plugins/think-router.js" | head -1 | grep -oE "'[a-z-]+'" | tr -d "'")
    for mode in $modes; do
        if [ ! -f "$REPO/modes/${mode}.md" ]; then
            echo "think-router references mode '$mode' but no mode file exists"
            return 1
        fi
    done
}

@test "think-router NO_THINK_MODES all have corresponding mode files" {
    modes=$(grep 'NO_THINK_MODES' "$REPO/plugins/think-router.js" | head -1 | grep -oE "'[a-z-]+'" | tr -d "'")
    for mode in $modes; do
        if [ ! -f "$REPO/modes/${mode}.md" ]; then
            echo "think-router references mode '$mode' but no mode file exists"
            return 1
        fi
    done
}

@test "think-router NEUTRAL_MODES all have corresponding mode files" {
    modes=$(grep 'NEUTRAL_MODES' "$REPO/plugins/think-router.js" | head -1 | grep -oE "'[a-z-]+'" | tr -d "'")
    for mode in $modes; do
        if [ ! -f "$REPO/modes/${mode}.md" ]; then
            echo "think-router references mode '$mode' but no mode file exists"
            return 1
        fi
    done
}

@test "all mode files are referenced in think-router" {
    all_router_modes=$(grep -E '(THINK_MODES|NO_THINK_MODES|NEUTRAL_MODES)' "$REPO/plugins/think-router.js" | grep -oE "'[a-z-]+'" | tr -d "'" | sort -u)
    for mode_file in "$REPO/modes"/*.md; do
        mode=$(basename "$mode_file" .md)
        [ "$mode" = "_template" ] && continue
        if ! echo "$all_router_modes" | grep -q "^${mode}$"; then
            echo "Mode file '${mode}.md' not referenced in think-router.js"
            return 1
        fi
    done
}

# =========================================================================
# Cross-file consistency: token-budget read-only modes
# =========================================================================

@test "token-budget READ_ONLY_MODES are a subset of modes that exist" {
    modes=$(grep 'READ_ONLY_MODES' "$REPO/plugins/token-budget.js" | head -1 | grep -oE "'[a-z-]+'" | tr -d "'")
    for mode in $modes; do
        if [ ! -f "$REPO/modes/${mode}.md" ]; then
            echo "token-budget references mode '$mode' but no mode file exists"
            return 1
        fi
    done
}

# =========================================================================
# Documentation
# =========================================================================

@test "docs/manual.md exists" {
    [ -f "$REPO/docs/manual.md" ]
}

@test "docs/setup-reference.md exists" {
    [ -f "$REPO/docs/setup-reference.md" ]
}

# =========================================================================
# Git
# =========================================================================

@test "bin/crux CLI exists and is executable" {
    [ -f "$REPO/bin/crux" ]
    [ -x "$REPO/bin/crux" ]
}

@test "skills have SKILL.md files" {
    count=$(find "$REPO/skills" -name "SKILL.md" | wc -l | tr -d ' ')
    [ "$count" -ge 2 ]
}

# =========================================================================
# Git
# =========================================================================

@test ".gitignore exists" {
    [ -f "$REPO/.gitignore" ]
}

@test ".github directory exists" {
    [ -d "$REPO/.github" ]
}
