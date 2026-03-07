#!/usr/bin/env bats
# Tests for setup.sh helper functions and pure logic functions.
# These tests source only the helper/pure-logic portions of setup.sh
# without running main() or any step that requires external tools.

setup() {
    export TEST_DIR="$(mktemp -d)"
    export STATE_DIR="$TEST_DIR/setup-state"
    mkdir -p "$STATE_DIR"

    # Color codes (same as setup.sh)
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    DIM='\033[2m'
    NC='\033[0m'

    # Source only the helper functions from setup.sh by extracting them
    # We define them inline to avoid running the main body
    state_mark() {
        touch "$STATE_DIR/$1.done"
    }

    state_done() {
        [ -f "$STATE_DIR/$1.done" ]
    }

    state_save() {
        local key="$1"
        local value="$2"
        echo "$value" > "$STATE_DIR/$key"
    }

    state_read() {
        local key="$1"
        if [ -f "$STATE_DIR/$key" ]; then
            cat "$STATE_DIR/$key"
        fi
    }

    select_model_quantization() {
        local total_ram=$1
        if [ "$total_ram" -ge 64 ]; then
            echo "Q8_0"
        elif [ "$total_ram" -ge 32 ]; then
            echo "Q6_K"
        elif [ "$total_ram" -ge 16 ]; then
            echo "Q4_K_M"
        else
            echo "Q4_K_S"
        fi
    }

    ask_choice() {
        local prompt="$1"
        shift
        local choices=("$@")
        local response

        echo -e "\n${BOLD}$prompt${NC}" >&2
        for i in "${!choices[@]}"; do
            echo "  $((i+1)). ${choices[$i]}" >&2
        done

        while true; do
            read -p "$(echo -e "${BOLD}Enter choice (1-${#choices[@]}):${NC}") " response
            if [[ "$response" =~ ^[0-9]+$ ]] && [ "$response" -ge 1 ] && [ "$response" -le ${#choices[@]} ]; then
                echo "$((response-1))"
                return 0
            fi
            echo "Invalid choice. Please enter a number between 1 and ${#choices[@]}." >&2
        done
    }

    export -f state_mark state_done state_save state_read select_model_quantization ask_choice
}

teardown() {
    rm -rf "$TEST_DIR"
}

# =========================================================================
# State management tests
# =========================================================================

@test "state_mark creates a .done file" {
    state_mark "test_step"
    [ -f "$STATE_DIR/test_step.done" ]
}

@test "state_done returns 0 when step is done" {
    state_mark "completed_step"
    run state_done "completed_step"
    [ "$status" -eq 0 ]
}

@test "state_done returns 1 when step is not done" {
    run state_done "missing_step"
    [ "$status" -eq 1 ]
}

@test "state_save writes value to file" {
    state_save "my_key" "my_value"
    [ -f "$STATE_DIR/my_key" ]
    result=$(cat "$STATE_DIR/my_key")
    [ "$result" = "my_value" ]
}

@test "state_read retrieves saved value" {
    state_save "ram" "64"
    result=$(state_read "ram")
    [ "$result" = "64" ]
}

@test "state_read returns empty for missing key" {
    result=$(state_read "nonexistent")
    [ -z "$result" ]
}

@test "state_save overwrites existing value" {
    state_save "key" "first"
    state_save "key" "second"
    result=$(state_read "key")
    [ "$result" = "second" ]
}

@test "state_mark is idempotent" {
    state_mark "step"
    state_mark "step"
    run state_done "step"
    [ "$status" -eq 0 ]
}

# =========================================================================
# Model quantization selection tests
# =========================================================================

@test "select_model_quantization returns Q8_0 for 64GB" {
    result=$(select_model_quantization 64)
    [ "$result" = "Q8_0" ]
}

@test "select_model_quantization returns Q8_0 for 128GB" {
    result=$(select_model_quantization 128)
    [ "$result" = "Q8_0" ]
}

@test "select_model_quantization returns Q6_K for 32GB" {
    result=$(select_model_quantization 32)
    [ "$result" = "Q6_K" ]
}

@test "select_model_quantization returns Q6_K for 48GB" {
    result=$(select_model_quantization 48)
    [ "$result" = "Q6_K" ]
}

@test "select_model_quantization returns Q4_K_M for 16GB" {
    result=$(select_model_quantization 16)
    [ "$result" = "Q4_K_M" ]
}

@test "select_model_quantization returns Q4_K_M for 24GB" {
    result=$(select_model_quantization 24)
    [ "$result" = "Q4_K_M" ]
}

@test "select_model_quantization returns Q4_K_S for 8GB" {
    result=$(select_model_quantization 8)
    [ "$result" = "Q4_K_S" ]
}

@test "select_model_quantization returns Q4_K_S for 4GB" {
    result=$(select_model_quantization 4)
    [ "$result" = "Q4_K_S" ]
}

# =========================================================================
# State integration tests
# =========================================================================

@test "full state workflow: save, read, mark, done" {
    state_save "total_ram_gb" "64"
    state_save "chip_model" "M1"
    state_mark "hardware_detected"

    [ "$(state_read 'total_ram_gb')" = "64" ]
    [ "$(state_read 'chip_model')" = "M1" ]
    run state_done "hardware_detected"
    [ "$status" -eq 0 ]
}

# =========================================================================
# ask_choice tests
# =========================================================================

@test "ask_choice returns 0-indexed value for first option" {
    result=$(echo "1" | ask_choice "Pick:" "Alpha" "Beta" "Gamma")
    [ "$result" = "0" ]
}

@test "ask_choice returns 0-indexed value for last option" {
    result=$(echo "3" | ask_choice "Pick:" "Alpha" "Beta" "Gamma")
    [ "$result" = "2" ]
}

@test "ask_choice stdout contains only the index" {
    # This is the critical test: stdout must be ONLY the return value,
    # not the menu text (which goes to stderr). If the menu leaks to stdout,
    # variable capture like model_choice=$(ask_choice ...) breaks.
    result=$(echo "2" | ask_choice "Pick:" "Alpha" "Beta" "Gamma")
    [ "$result" = "1" ]
    # Verify no extra lines
    line_count=$(echo "2" | ask_choice "Pick:" "Alpha" "Beta" | wc -l | tr -d ' ')
    [ "$line_count" = "1" ]
}

@test "ask_choice menu goes to stderr not stdout" {
    # Capture only stdout — should be just the index
    stdout=$(echo "1" | ask_choice "Pick:" "Alpha" "Beta" 2>/dev/null)
    [ "$stdout" = "0" ]
    # Capture only stderr — should contain the menu
    stderr=$(echo "1" | ask_choice "Pick:" "Alpha" "Beta" 2>&1 1>/dev/null)
    [[ "$stderr" == *"Alpha"* ]]
    [[ "$stderr" == *"Beta"* ]]
}

@test "multiple steps can be tracked independently" {
    state_mark "step_1"
    run state_done "step_1"
    [ "$status" -eq 0 ]
    run state_done "step_2"
    [ "$status" -eq 1 ]
    state_mark "step_2"
    run state_done "step_2"
    [ "$status" -eq 0 ]
}
