#!/usr/bin/env bats
# Tests for setup.sh step functions that create files.
# We source the functions with a temp HOME and mock external commands,
# pre-seed state, then call each step and verify files were created.

SETUP_SH="/Users/user/personal/crux/setup.sh"

setup() {
    export REAL_HOME="$HOME"
    export TEST_HOME="$(mktemp -d)"
    export HOME="$TEST_HOME"
    export STATE_DIR="$TEST_HOME/.config/crux/setup-state"
    mkdir -p "$STATE_DIR"

    # Color codes (needed by sourced functions)
    export RED='\033[0;31m'
    export GREEN='\033[0;32m'
    export YELLOW='\033[1;33m'
    export BLUE='\033[0;34m'
    export CYAN='\033[0;36m'
    export BOLD='\033[1m'
    export DIM='\033[2m'
    export NC='\033[0m'

    # Source only the function definitions from setup.sh (not main or the `mkdir -p` at line 21)
    # We use a trick: define functions by evaluating the file with main() and the final line neutralized
    eval "$(sed -n '
        # Skip the shebang and set -euo pipefail
        /^#!/d
        /^set -euo pipefail/d
        # Skip the mkdir at line 21
        /^mkdir -p "\$STATE_DIR"/d
        # Skip the final "main" call at the very end
        /^main "\$@"/d
        # Print everything else
        p
    ' "$SETUP_SH")"
}

teardown() {
    export HOME="$REAL_HOME"
    rm -rf "$TEST_HOME"
}

# =========================================================================
# Helper function tests
# =========================================================================

@test "header outputs formatted text" {
    run header "Test Header"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Test Header"* ]]
}

@test "info outputs info text" {
    run info "Test info"
    [ "$status" -eq 0 ]
}

@test "success outputs success text" {
    run success "Test success"
    [ "$status" -eq 0 ]
}

@test "warn outputs warning text" {
    run warn "Test warning"
    [ "$status" -eq 0 ]
}

@test "error outputs error text" {
    run error "Test error"
    [ "$status" -eq 0 ]
}

@test "explain outputs explanation text" {
    run explain "Test explanation"
    [ "$status" -eq 0 ]
}

@test "explain_quantization handles Q8_0" {
    run explain_quantization "Q8_0"
    [ "$status" -eq 0 ]
    [[ "$output" == *"8-bit"* ]]
}

@test "explain_quantization handles Q6_K" {
    run explain_quantization "Q6_K"
    [ "$status" -eq 0 ]
    [[ "$output" == *"6-bit"* ]]
}

@test "explain_quantization handles Q4_K_M" {
    run explain_quantization "Q4_K_M"
    [ "$status" -eq 0 ]
    [[ "$output" == *"4-bit"* ]]
}

@test "explain_quantization handles Q4_K_S" {
    run explain_quantization "Q4_K_S"
    [ "$status" -eq 0 ]
    [[ "$output" == *"4-bit"* ]]
}

# =========================================================================
# Step 7: configure_opencode - writes opencode.json
# =========================================================================

@test "configure_opencode creates opencode.json" {
    run configure_opencode
    [ "$status" -eq 0 ]
    [ -f "$TEST_HOME/.config/opencode/opencode.json" ]
}

@test "configure_opencode json is valid JSON" {
    configure_opencode
    # Validate JSON with node
    node -e "JSON.parse(require('fs').readFileSync('$TEST_HOME/.config/opencode/opencode.json','utf8'))"
}

@test "configure_opencode json has expected keys" {
    configure_opencode
    local json="$TEST_HOME/.config/opencode/opencode.json"
    node -e "
        const j = JSON.parse(require('fs').readFileSync('$json','utf8'));
        if (!j.models) throw 'missing models';
        if (!j.models.primary) throw 'missing primary model';
        if (!j.lsp) throw 'missing lsp';
        if (!j.pluginPath) throw 'missing pluginPath';
        if (!j.commandPath) throw 'missing commandPath';
        if (!j.toolPath) throw 'missing toolPath';
    "
}

@test "configure_opencode is idempotent" {
    configure_opencode
    run configure_opencode
    [ "$status" -eq 0 ]
    [[ "$output" == *"already completed"* ]]
}

# =========================================================================
# Step 8: create_modes - writes 15 mode files
# =========================================================================

@test "create_modes creates modes directory" {
    run create_modes
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/modes" ]
}

@test "create_modes creates all 15 mode files" {
    create_modes
    local count
    count=$(ls -1 "$TEST_HOME/.config/opencode/modes"/*.md 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 15 ]
}

@test "create_modes mode files have correct headers" {
    create_modes
    local modes_dir="$TEST_HOME/.config/opencode/modes"
    for mode in build-py build-ex plan infra-architect review debug explain analyst writer psych legal strategist ai-infra mac docker; do
        if [ ! -f "$modes_dir/${mode}.md" ]; then
            echo "Missing mode: $mode"
            return 1
        fi
        head -1 "$modes_dir/${mode}.md" | grep -Fq "# Mode: ${mode}" || {
            echo "Wrong header in $mode"
            return 1
        }
    done
}

@test "create_modes is idempotent" {
    create_modes
    run create_modes
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 9: create_agents_md - writes AGENTS.md
# =========================================================================

@test "create_agents_md creates AGENTS.md" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run create_agents_md
    [ "$status" -eq 0 ]
    [ -f "$TEST_HOME/.config/opencode/AGENTS.md" ]
}

@test "create_agents_md AGENTS.md has expected content" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_agents_md
    grep -Fq "Scripts-First" "$TEST_HOME/.config/opencode/AGENTS.md"
    grep -Fq "Tool Resolution Hierarchy" "$TEST_HOME/.config/opencode/AGENTS.md"
}

@test "create_agents_md is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_agents_md
    run create_agents_md
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 10: create_commands - writes 11 command files
# =========================================================================

@test "create_commands creates commands directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run create_commands
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/commands" ]
}

@test "create_commands creates all 11 command files" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_commands
    local count
    count=$(ls -1 "$TEST_HOME/.config/opencode/commands"/*.md 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 11 ]
}

@test "create_commands is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_commands
    run create_commands
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 11: create_tools - writes 7 tool files
# =========================================================================

@test "create_tools creates tools directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run create_tools
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/tools" ]
}

@test "create_tools creates all 7 tool files" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_tools
    local count
    count=$(ls -1 "$TEST_HOME/.config/opencode/tools"/*.js 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 7 ]
}

@test "create_tools files import zod" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_tools
    for f in "$TEST_HOME/.config/opencode/tools"/*.js; do
        grep -q "from 'zod'" "$f" || {
            echo "$(basename "$f") missing zod import"
            return 1
        }
    done
}

@test "create_tools is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_tools
    run create_tools
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 12: create_skills - writes skill files
# =========================================================================

@test "create_skills creates skills directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run create_skills
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/skills" ]
}

@test "create_skills is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_skills
    run create_skills
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 13: create_plugins - writes 5 plugin files
# =========================================================================

@test "create_plugins creates plugins directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run create_plugins
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/plugins" ]
}

@test "create_plugins creates at least 5 plugin files" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_plugins
    local count
    count=$(ls -1 "$TEST_HOME/.config/opencode/plugins"/*.js 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -ge 5 ]
}

@test "create_plugins is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_plugins
    run create_plugins
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 14: create_knowledge_base
# =========================================================================

@test "create_knowledge_base creates knowledge directories" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run create_knowledge_base
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/knowledge" ]
    [ -d "$TEST_HOME/.config/opencode/knowledge/shared" ]
}

@test "create_knowledge_base creates template" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_knowledge_base
    [ -f "$TEST_HOME/.config/opencode/knowledge/_template.md" ]
}

@test "create_knowledge_base is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_knowledge_base
    run create_knowledge_base
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 15: create_model_registry
# =========================================================================

@test "create_model_registry creates registry.json" {
    mkdir -p "$TEST_HOME/.config/opencode"
    # Pre-seed required state
    state_save "primary_model" "qwen3:32b"
    state_save "model_quantization" "Q8_0"
    run create_model_registry
    [ "$status" -eq 0 ]
    [ -f "$TEST_HOME/.config/opencode/models/registry.json" ]
}

@test "create_model_registry json is valid JSON" {
    mkdir -p "$TEST_HOME/.config/opencode"
    state_save "primary_model" "qwen3:32b"
    state_save "model_quantization" "Q8_0"
    create_model_registry
    node -e "JSON.parse(require('fs').readFileSync('$TEST_HOME/.config/opencode/models/registry.json','utf8'))"
}

@test "create_model_registry is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    state_save "primary_model" "qwen3:32b"
    state_save "model_quantization" "Q8_0"
    create_model_registry
    run create_model_registry
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 16: create_analytics
# =========================================================================

@test "create_analytics creates analytics directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run create_analytics
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/analytics" ]
}

@test "create_analytics creates digest template" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_analytics
    [ -f "$TEST_HOME/.config/opencode/analytics/digest-template.md" ]
}

@test "create_analytics is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_analytics
    run create_analytics
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]]
}

# =========================================================================
# Step 5: tune_environment - writes to shell profile
# =========================================================================

@test "tune_environment adds OLLAMA vars to zshrc" {
    export SHELL="/bin/zsh"
    touch "$TEST_HOME/.zshrc"
    run tune_environment
    [ "$status" -eq 0 ]
    grep -q "OLLAMA_KEEP_ALIVE" "$TEST_HOME/.zshrc"
    grep -q "OLLAMA_MAX_LOADED_MODELS" "$TEST_HOME/.zshrc"
}

@test "tune_environment is idempotent" {
    export SHELL="/bin/zsh"
    touch "$TEST_HOME/.zshrc"
    tune_environment
    run tune_environment
    [ "$status" -eq 0 ]
    [[ "$output" == *"already completed"* ]]
}

@test "tune_environment skips if vars already present" {
    export SHELL="/bin/zsh"
    echo "OLLAMA_KEEP_ALIVE=24h" > "$TEST_HOME/.zshrc"
    # Clear state so it doesn't skip from state_done
    rm -f "$STATE_DIR/environment_tuned.done"
    run tune_environment
    [ "$status" -eq 0 ]
    [[ "$output" == *"already configured"* ]]
}

# =========================================================================
# final_summary - purely output, just verify it runs
# =========================================================================

@test "final_summary runs without error" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run final_summary
    [ "$status" -eq 0 ]
    [[ "$output" == *"Setup Complete"* ]]
    [[ "$output" == *"build-py"* ]]
    [[ "$output" == *"/promote"* ]]
}

# =========================================================================
# detect_hardware - uses sysctl (available on macOS)
# =========================================================================

@test "detect_hardware saves hardware profile" {
    run detect_hardware
    [ "$status" -eq 0 ]
    [ -f "$STATE_DIR/total_ram_gb" ]
    [ -f "$STATE_DIR/available_ram_gb" ]
    [ -f "$STATE_DIR/chip_model" ]
    run state_done "hardware_detected"
    [ "$status" -eq 0 ]
}

@test "detect_hardware is idempotent" {
    detect_hardware
    run detect_hardware
    [ "$status" -eq 0 ]
    [[ "$output" == *"already detected"* ]]
}

# =========================================================================
# verify_installation - checks files that were created
# =========================================================================

@test "verify_installation checks file presence" {
    # Mock external commands
    curl() { return 1; }
    ollama() { return 1; }
    opencode() { return 1; }
    export -f curl ollama opencode

    mkdir -p "$TEST_HOME/.config/opencode"
    run verify_installation
    # Should run to completion even if checks fail
    [ "$status" -eq 0 ]
    [[ "$output" == *"Verification Results"* ]]
}

@test "verify_installation counts correct files after full setup" {
    # Mock external commands to succeed
    curl() { return 0; }
    ollama() { echo "crux-think"; echo "crux-chat"; }
    opencode() { return 0; }
    export -f curl ollama opencode

    # Run all file-creating steps
    configure_opencode
    create_modes
    create_agents_md
    create_commands
    create_tools
    create_skills
    create_plugins
    state_save "primary_model" "qwen3:32b"
    state_save "model_quantization" "Q8_0"
    create_knowledge_base
    create_model_registry
    create_analytics

    run verify_installation
    [ "$status" -eq 0 ]
    [[ "$output" == *"All 15 modes"* ]]
    [[ "$output" == *"All 11 custom commands"* ]]
    [[ "$output" == *"All 7 custom tools"* ]]
}
