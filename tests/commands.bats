#!/usr/bin/env bats
# Tests for command definition files in commands/

COMMANDS_DIR="/Users/user/personal/crux/commands"

# All 11 commands from CLAUDE.md
COMMANDS=(promote scripts archive log init-project stats digest propose-mode review-knowledge review-community configure-api)

# =========================================================================
# File existence
# =========================================================================

@test "all 11 command files exist" {
    for cmd in "${COMMANDS[@]}"; do
        if [ ! -f "$COMMANDS_DIR/${cmd}.md" ]; then
            echo "Missing command file: ${cmd}.md"
            return 1
        fi
    done
}

@test "no unexpected command files exist" {
    actual_count=$(ls -1 "$COMMANDS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
    [ "$actual_count" -eq 11 ]
}

# =========================================================================
# Structure
# =========================================================================

@test "all commands have '# Command:' header" {
    for cmd in "${COMMANDS[@]}"; do
        if ! grep -q "^# Command: ${cmd}" "$COMMANDS_DIR/${cmd}.md"; then
            echo "Missing or wrong header in ${cmd}.md"
            return 1
        fi
    done
}

@test "all commands have Usage section" {
    for cmd in "${COMMANDS[@]}"; do
        if ! grep -q '## Usage' "$COMMANDS_DIR/${cmd}.md"; then
            echo "Missing Usage section in ${cmd}.md"
            return 1
        fi
    done
}

@test "all commands are non-empty" {
    for cmd in "${COMMANDS[@]}"; do
        size=$(wc -c < "$COMMANDS_DIR/${cmd}.md" | tr -d ' ')
        if [ "$size" -lt 50 ]; then
            echo "Command ${cmd}.md is too short (${size} bytes)"
            return 1
        fi
    done
}
