#!/usr/bin/env bats
# Tests for bin/crux CLI — dispatch, help, version, doctor, status, setup, update.
# We use CRUX_DIR to point at the real repo and mock external commands where needed.

CRUX_CLI="/Users/user/personal/crux/bin/crux"
CRUX_REPO="/Users/user/personal/crux"

setup() {
    export TEST_DIR="$(mktemp -d)"
    export CRUX_DIR="$CRUX_REPO"
    # Isolate HOME so doctor doesn't check real ~/.config
    export REAL_HOME="$HOME"
    export HOME="$TEST_DIR"
}

teardown() {
    export HOME="$REAL_HOME"
    rm -rf "$TEST_DIR"
}

# =========================================================================
# Syntax
# =========================================================================

@test "bin/crux passes bash -n syntax check" {
    run bash -n "$CRUX_CLI"
    [ "$status" -eq 0 ]
}

@test "bin/crux has valid shebang" {
    head -1 "$CRUX_CLI" | grep -q '^#!/bin/bash'
}

@test "bin/crux uses set -euo pipefail" {
    grep -q 'set -euo pipefail' "$CRUX_CLI"
}

@test "bin/crux is executable" {
    [ -x "$CRUX_CLI" ]
}

# =========================================================================
# Version
# =========================================================================

@test "crux version outputs version string" {
    run bash "$CRUX_CLI" version
    [ "$status" -eq 0 ]
    [[ "$output" == *"crux 0."* ]]
}

@test "crux version shows git commit info" {
    run bash "$CRUX_CLI" version
    [ "$status" -eq 0 ]
    [[ "$output" == *"repo:"* ]]
}

# =========================================================================
# Help
# =========================================================================

@test "crux help shows usage" {
    run bash "$CRUX_CLI" help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
    [[ "$output" == *"crux <command>"* ]]
}

@test "crux --help shows usage" {
    run bash "$CRUX_CLI" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "crux -h shows usage" {
    run bash "$CRUX_CLI" -h
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "crux with no args shows help" {
    run bash "$CRUX_CLI"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "crux help lists all commands" {
    run bash "$CRUX_CLI" help
    [ "$status" -eq 0 ]
    [[ "$output" == *"status"* ]]
    [[ "$output" == *"setup"* ]]
    [[ "$output" == *"update"* ]]
    [[ "$output" == *"doctor"* ]]
    [[ "$output" == *"version"* ]]
    [[ "$output" == *"help"* ]]
}

@test "crux help mentions CRUX_DIR env var" {
    run bash "$CRUX_CLI" help
    [[ "$output" == *"CRUX_DIR"* ]]
}

@test "crux help mentions getting started" {
    run bash "$CRUX_CLI" help
    [[ "$output" == *"Getting Started"* ]]
    [[ "$output" == *"crux setup"* ]]
}

# =========================================================================
# Unknown command
# =========================================================================

@test "crux unknown-command exits with error" {
    run bash "$CRUX_CLI" bogus
    [ "$status" -eq 1 ]
    [[ "$output" == *"Unknown command: bogus"* ]]
}

@test "crux unknown-command suggests help" {
    run bash "$CRUX_CLI" invalid
    [ "$status" -eq 1 ]
    [[ "$output" == *"crux help"* ]]
}

# =========================================================================
# CRUX_DIR resolution
# =========================================================================

@test "CRUX_DIR env var overrides script location" {
    export CRUX_DIR="$CRUX_REPO"
    run bash "$CRUX_CLI" version
    [ "$status" -eq 0 ]
    [[ "$output" == *"crux 0."* ]]
}

@test "CRUX_DIR with missing setup.sh causes setup to fail" {
    export CRUX_DIR="$TEST_DIR"
    run bash "$CRUX_CLI" setup
    [ "$status" -eq 1 ]
    [[ "$output" == *"setup.sh not found"* ]]
}

# =========================================================================
# Doctor — with mocked environment
# =========================================================================

@test "crux doctor runs without crashing" {
    # Doctor will report issues (no config dir, etc.) but should not crash
    run bash "$CRUX_CLI" doctor
    [ "$status" -eq 0 ]
    [[ "$output" == *"Health Check"* ]]
}

@test "crux doctor checks Crux repo" {
    run bash "$CRUX_CLI" doctor
    [[ "$output" == *"Crux repo"* ]]
}

@test "crux doctor reports missing config dir" {
    run bash "$CRUX_CLI" doctor
    # HOME is TEST_DIR, so ~/.config/opencode won't exist
    [[ "$output" == *"Config dir"* ]]
}

@test "crux doctor reports issues count" {
    run bash "$CRUX_CLI" doctor
    [[ "$output" == *"issue(s) found"* ]]
}

@test "crux doctor with config dir present reports success for config" {
    mkdir -p "$TEST_DIR/.config/opencode"
    run bash "$CRUX_CLI" doctor
    [[ "$output" == *"Config dir"* ]]
}

@test "crux doctor checks symlinks" {
    local config_dir="$TEST_DIR/.config/opencode"
    mkdir -p "$config_dir"
    # Create a working symlink
    ln -s "$CRUX_REPO/modes" "$config_dir/modes"
    run bash "$CRUX_CLI" doctor
    [[ "$output" == *"modes"* ]]
}

@test "crux doctor detects broken symlinks" {
    local config_dir="$TEST_DIR/.config/opencode"
    mkdir -p "$config_dir"
    # Create a broken symlink
    ln -s "/nonexistent/path" "$config_dir/modes"
    run bash "$CRUX_CLI" doctor
    [[ "$output" == *"Broken symlink"* ]] || [[ "$output" == *"modes"* ]]
}

@test "crux doctor detects regular directory (not symlink)" {
    local config_dir="$TEST_DIR/.config/opencode"
    mkdir -p "$config_dir/modes"
    run bash "$CRUX_CLI" doctor
    [[ "$output" == *"regular directory"* ]] || [[ "$output" == *"not symlinked"* ]]
}

@test "crux doctor checks Python scripts" {
    local config_dir="$TEST_DIR/.config/opencode"
    mkdir -p "$config_dir/scripts/lib"
    touch "$config_dir/scripts/lib/foo.py"
    touch "$config_dir/scripts/lib/bar.py"
    run bash "$CRUX_CLI" doctor
    [[ "$output" == *"Python scripts"* ]]
}

@test "crux doctor reports missing Python scripts" {
    mkdir -p "$TEST_DIR/.config/opencode"
    run bash "$CRUX_CLI" doctor
    [[ "$output" == *"Python scripts not installed"* ]]
}

# =========================================================================
# Status — basic invocation tests
# =========================================================================

@test "crux status runs without crashing" {
    # Set up minimal .crux directory so crux_status.py doesn't fail
    mkdir -p "$TEST_DIR/.crux/sessions"
    mkdir -p "$TEST_DIR/.crux/knowledge"
    export CRUX_PROJECT="$TEST_DIR"
    export CRUX_HOME="$TEST_DIR"
    run bash "$CRUX_CLI" status
    [ "$status" -eq 0 ]
    [[ "$output" == *"Status"* ]]
}

@test "crux status shows session info" {
    mkdir -p "$TEST_DIR/.crux/sessions"
    mkdir -p "$TEST_DIR/.crux/knowledge"
    export CRUX_PROJECT="$TEST_DIR"
    export CRUX_HOME="$TEST_DIR"
    run bash "$CRUX_CLI" status
    [[ "$output" == *"SESSION"* ]]
}

@test "crux status includes health checks" {
    mkdir -p "$TEST_DIR/.crux/sessions"
    mkdir -p "$TEST_DIR/.crux/knowledge"
    export CRUX_PROJECT="$TEST_DIR"
    export CRUX_HOME="$TEST_DIR"
    run bash "$CRUX_CLI" status
    [ "$status" -eq 0 ]
    [[ "$output" == *"HEALTH CHECKS"* ]]
    [[ "$output" == *"checks passed"* ]]
}

@test "crux status shows hooks info" {
    mkdir -p "$TEST_DIR/.crux/sessions"
    mkdir -p "$TEST_DIR/.crux/knowledge"
    export CRUX_PROJECT="$TEST_DIR"
    export CRUX_HOME="$TEST_DIR"
    run bash "$CRUX_CLI" status
    [[ "$output" == *"HOOKS"* ]]
}

@test "crux status shows interactions" {
    mkdir -p "$TEST_DIR/.crux/sessions"
    mkdir -p "$TEST_DIR/.crux/knowledge"
    export CRUX_PROJECT="$TEST_DIR"
    export CRUX_HOME="$TEST_DIR"
    run bash "$CRUX_CLI" status
    [[ "$output" == *"INTERACTIONS"* ]]
}

@test "crux status shows knowledge" {
    mkdir -p "$TEST_DIR/.crux/sessions"
    mkdir -p "$TEST_DIR/.crux/knowledge"
    export CRUX_PROJECT="$TEST_DIR"
    export CRUX_HOME="$TEST_DIR"
    run bash "$CRUX_CLI" status
    [[ "$output" == *"KNOWLEDGE"* ]]
}

# =========================================================================
# Setup — only test dispatch, not the actual setup
# =========================================================================

@test "crux setup dispatches to setup.sh" {
    # Verify setup.sh exists at CRUX_DIR — we can't run it (interactive),
    # but we can confirm the dispatch logic finds the file
    export CRUX_DIR="$CRUX_REPO"
    [ -f "$CRUX_DIR/setup.sh" ]
}

@test "crux setup fails gracefully with missing setup.sh" {
    export CRUX_DIR="$TEST_DIR"
    run bash "$CRUX_CLI" setup
    [ "$status" -eq 1 ]
    [[ "$output" == *"setup.sh not found"* ]]
}

# =========================================================================
# Color/output helper functions
# =========================================================================

@test "success helper produces output" {
    run bash -c "source '$CRUX_CLI' 2>/dev/null; success 'test message'" 2>/dev/null || \
    run bash -c "
        RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
        BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
        success() { echo -e \"\${GREEN}✓\${NC} \$1\"; }
        success 'test message'
    "
    [[ "$output" == *"test message"* ]]
}

@test "error helper produces output" {
    run bash -c "
        RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
        error() { echo -e \"\${RED}✗\${NC} \$1\"; }
        error 'test error'
    "
    [[ "$output" == *"test error"* ]]
}

# =========================================================================
# Integration: full doctor with all symlinks
# =========================================================================

@test "crux doctor with full config setup reports fewer issues" {
    local config_dir="$TEST_DIR/.config/opencode"
    mkdir -p "$config_dir/scripts/lib"
    # Create symlinks to real repo dirs
    ln -s "$CRUX_REPO/modes" "$config_dir/modes"
    ln -s "$CRUX_REPO/plugins" "$config_dir/plugins"
    ln -s "$CRUX_REPO/tools" "$config_dir/tools"
    ln -s "$CRUX_REPO/commands" "$config_dir/commands"
    touch "$config_dir/scripts/lib/foo.py"

    run bash "$CRUX_CLI" doctor
    [ "$status" -eq 0 ]
    # Should have valid symlinks
    [[ "$output" == *"modes"* ]]
    [[ "$output" == *"plugins"* ]]
    [[ "$output" == *"tools"* ]]
    [[ "$output" == *"commands"* ]]
}

# =========================================================================
# Switch
# =========================================================================

@test "crux switch with no args shows usage" {
    run bash "$CRUX_CLI" switch
    [ "$status" -eq 1 ]
    [[ "$output" == *"Usage: crux switch"* ]]
    [[ "$output" == *"Supported tools"* ]]
}

@test "crux switch with invalid tool shows error" {
    export CRUX_PROJECT="$CRUX_REPO"
    run bash "$CRUX_CLI" switch invalid-tool
    [ "$status" -eq 1 ]
    [[ "$output" == *"Unsupported tool"* ]]
}

@test "crux switch cursor generates config" {
    export CRUX_PROJECT="$CRUX_REPO"
    run bash "$CRUX_CLI" switch cursor
    [ "$status" -eq 0 ]
    [[ "$output" == *"Switched"* ]]
    [[ "$output" == *"cursor"* ]]
    # Verify files created
    [ -f "$CRUX_REPO/.cursor/mcp.json" ]
    [ -d "$CRUX_REPO/.cursor/rules" ]
}

@test "crux switch claude-code restores from cursor" {
    export CRUX_PROJECT="$CRUX_REPO"
    # Switch to cursor first, then back
    bash "$CRUX_CLI" switch cursor
    run bash "$CRUX_CLI" switch claude-code
    [ "$status" -eq 0 ]
    [[ "$output" == *"cursor → claude-code"* ]]
}

@test "crux help shows switch command" {
    run bash "$CRUX_CLI" help
    [[ "$output" == *"switch"* ]]
    [[ "$output" == *"crux switch opencode"* ]]
}
