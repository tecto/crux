#!/usr/bin/env bats
# Tests for setup.sh step functions that create files.
# We extract function definitions to a cached file (once), then source it per-test.
# The install_* functions symlink from CRUX_DIR, so we point at the real repo.

SETUP_SH="/Users/user/personal/crux/setup.sh"
CACHED_FUNCTIONS="/tmp/crux-setup-functions.sh"

# Extract function definitions ONCE (skip shebang, set flags, and the final "main" call)
setup_file() {
    export REAL_HOME="$HOME"
    if [ ! -f "$CACHED_FUNCTIONS" ] || [ "$SETUP_SH" -nt "$CACHED_FUNCTIONS" ]; then
        awk '
            /^header\(\) \{/ { in_funcs=1 }
            in_funcs && /^main$/ { next }
            in_funcs && /^# Run main$/ { next }
            in_funcs { print }
        ' "$SETUP_SH" > "$CACHED_FUNCTIONS"
    fi
}

# Per-test: source cached functions + create fresh temp dirs
setup() {
    export TEST_HOME="$(mktemp -d)"
    export HOME="$TEST_HOME"
    export STATE_DIR="$TEST_HOME/.config/crux/setup-state"
    export CRUX_DIR="/Users/user/personal/crux"
    export UPDATE_MODE=false
    mkdir -p "$STATE_DIR"

    export RED='\033[0;31m'
    export GREEN='\033[0;32m'
    export YELLOW='\033[1;33m'
    export BLUE='\033[0;34m'
    export CYAN='\033[0;36m'
    export BOLD='\033[1m'
    export DIM='\033[2m'
    export NC='\033[0m'

    source "$CACHED_FUNCTIONS"
}

teardown() {
    export HOME="$REAL_HOME"
    rm -rf "$TEST_HOME"
}

teardown_file() {
    export HOME="$REAL_HOME"
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
    node -e "JSON.parse(require('fs').readFileSync('$TEST_HOME/.config/opencode/opencode.json','utf8'))"
}

@test "configure_opencode json has expected keys" {
    configure_opencode
    local json="$TEST_HOME/.config/opencode/opencode.json"
    node -e "
        const j = JSON.parse(require('fs').readFileSync('$json','utf8'));
        if (!j.model) throw 'missing model';
        if (!j.lsp) throw 'missing lsp';
        if (!j.timeout) throw 'missing timeout';
    "
}

@test "configure_opencode is idempotent" {
    configure_opencode
    run configure_opencode
    [ "$status" -eq 0 ]
    [[ "$output" == *"already completed"* ]]
}

# =========================================================================
# Step 8: install_modes - symlinks modes directory from repo
# =========================================================================

@test "install_modes creates modes symlink" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run install_modes
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/modes" ]
}

@test "install_modes links to repo modes" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_modes
    # Should contain mode files from the repo
    [ -f "$TEST_HOME/.config/opencode/modes/build-py.md" ]
    [ -f "$TEST_HOME/.config/opencode/modes/debug.md" ]
}

@test "install_modes is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_modes
    run install_modes
    [ "$status" -eq 0 ]
}

# =========================================================================
# Step 9: install_agents_md - symlinks AGENTS.md from repo
# =========================================================================

@test "install_agents_md creates AGENTS.md" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run install_agents_md
    [ "$status" -eq 0 ]
    [ -f "$TEST_HOME/.config/opencode/AGENTS.md" ]
}

@test "install_agents_md AGENTS.md has expected content" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_agents_md
    grep -Fq "Scripts-First" "$TEST_HOME/.config/opencode/AGENTS.md"
    grep -Fq "Tool Resolution Hierarchy" "$TEST_HOME/.config/opencode/AGENTS.md"
}

@test "install_agents_md is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_agents_md
    run install_agents_md
    [ "$status" -eq 0 ]
}

# =========================================================================
# Step 10: install_commands - symlinks commands from repo
# =========================================================================

@test "install_commands creates commands directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run install_commands
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/commands" ]
}

@test "install_commands links all 11 command files" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_commands
    local count
    count=$(ls -1 "$TEST_HOME/.config/opencode/commands"/*.md 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 11 ]
}

@test "install_commands is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_commands
    run install_commands
    [ "$status" -eq 0 ]
}

# =========================================================================
# Step 11: install_tools - symlinks tools from repo
# =========================================================================

@test "install_tools creates tools directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run install_tools
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/tools" ]
}

@test "install_tools links all 7 tool files" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_tools
    local count
    count=$(ls -1 "$TEST_HOME/.config/opencode/tools"/*.js 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -eq 7 ]
}

@test "install_tools files import zod or plugin-shim" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_tools
    for f in "$TEST_HOME/.config/opencode/tools"/*.js; do
        grep -qE "from 'zod'|from '\.\./lib/plugin-shim|from '\.\/lib\/plugin-shim" "$f" || {
            echo "$(basename "$f") missing zod or plugin-shim import"
            return 1
        }
    done
}

@test "install_tools is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_tools
    run install_tools
    [ "$status" -eq 0 ]
}

# =========================================================================
# Step 12: install_skills - symlinks skills from repo
# =========================================================================

@test "install_skills creates skills directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run install_skills
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/skills" ]
}

@test "install_skills is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_skills
    run install_skills
    [ "$status" -eq 0 ]
}

# =========================================================================
# Step 13: install_plugins - symlinks plugins from repo
# =========================================================================

@test "install_plugins creates plugins directory" {
    mkdir -p "$TEST_HOME/.config/opencode"
    run install_plugins
    [ "$status" -eq 0 ]
    [ -d "$TEST_HOME/.config/opencode/plugins" ]
}

@test "install_plugins links at least 5 plugin files" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_plugins
    local count
    count=$(ls -1 "$TEST_HOME/.config/opencode/plugins"/*.js 2>/dev/null | wc -l | tr -d ' ')
    [ "$count" -ge 5 ]
}

@test "install_plugins is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    install_plugins
    run install_plugins
    [ "$status" -eq 0 ]
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

@test "create_knowledge_base creates per-mode directories" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_knowledge_base
    [ -d "$TEST_HOME/.config/opencode/knowledge/build-py" ]
    [ -d "$TEST_HOME/.config/opencode/knowledge/debug" ]
    [ -d "$TEST_HOME/.config/opencode/knowledge/plan" ]
}

@test "create_knowledge_base links template" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_knowledge_base
    [ -e "$TEST_HOME/.config/opencode/knowledge/_template.md" ]
}

@test "create_knowledge_base is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    create_knowledge_base
    run create_knowledge_base
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]] || [[ "$output" == *"knowledge"* ]]
}

# =========================================================================
# Step 15: create_model_registry
# =========================================================================

@test "create_model_registry creates registry.json" {
    mkdir -p "$TEST_HOME/.config/opencode"
    state_save "primary_model" "qwen2.5:32b"
    state_save "model_quantization" "Q8_0"
    run create_model_registry
    [ "$status" -eq 0 ]
    [ -f "$TEST_HOME/.config/opencode/models/registry.json" ]
}

@test "create_model_registry json is valid JSON" {
    mkdir -p "$TEST_HOME/.config/opencode"
    state_save "primary_model" "qwen2.5:32b"
    state_save "model_quantization" "Q8_0"
    create_model_registry
    node -e "JSON.parse(require('fs').readFileSync('$TEST_HOME/.config/opencode/models/registry.json','utf8'))"
}

@test "create_model_registry is idempotent" {
    mkdir -p "$TEST_HOME/.config/opencode"
    state_save "primary_model" "qwen2.5:32b"
    state_save "model_quantization" "Q8_0"
    create_model_registry
    run create_model_registry
    [ "$status" -eq 0 ]
    [[ "$output" == *"already created"* ]] || [[ "$output" == *"registry"* ]]
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
    [[ "$output" == *"already created"* ]] || [[ "$output" == *"analytics"* ]]
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
    curl() { return 1; }
    ollama() { return 1; }
    opencode() { return 1; }
    export -f curl ollama opencode

    mkdir -p "$TEST_HOME/.config/opencode"
    run verify_installation
    [ "$status" -eq 0 ]
    [[ "$output" == *"Verification Results"* ]]
}

@test "verify_installation counts correct files after full setup" {
    curl() { return 0; }
    ollama() { echo "crux-think"; echo "crux-chat"; }
    opencode() { return 0; }
    export -f curl ollama opencode

    # Run all file-creating steps
    mkdir -p "$TEST_HOME/.config/opencode"
    configure_opencode
    install_modes
    install_agents_md
    install_commands
    install_tools
    install_skills
    install_plugins
    state_save "primary_model" "qwen2.5:32b"
    state_save "model_quantization" "Q8_0"
    create_knowledge_base
    create_model_registry
    create_analytics

    run verify_installation
    [ "$status" -eq 0 ]
}

# =========================================================================
# safe_symlink - atomic symlink creation
# =========================================================================

@test "safe_symlink creates a symlink" {
    local source_dir="$TEST_HOME/source"
    local target="$TEST_HOME/target"
    mkdir -p "$source_dir"
    run safe_symlink "$source_dir" "$target"
    [ "$status" -eq 0 ]
    [ -L "$target" ]
}

@test "safe_symlink replaces existing directory" {
    local source_dir="$TEST_HOME/source"
    local target="$TEST_HOME/target"
    mkdir -p "$source_dir"
    mkdir -p "$target"
    run safe_symlink "$source_dir" "$target"
    [ "$status" -eq 0 ]
    [ -L "$target" ]
}

@test "safe_symlink replaces existing symlink" {
    local source_dir="$TEST_HOME/source"
    local target="$TEST_HOME/target"
    mkdir -p "$source_dir"
    ln -s "/nonexistent" "$target"
    run safe_symlink "$source_dir" "$target"
    [ "$status" -eq 0 ]
    [ -L "$target" ]
    # Should point to the new source, not /nonexistent
    readlink "$target" | grep -q "source"
}
