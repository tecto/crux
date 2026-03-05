#!/usr/bin/env bats
# Tests for setup.sh syntax correctness and structural integrity.
# These catch the kind of bugs like the line 76 parenthesis error.

SETUP_SH="/Users/user/personal/crux/setup.sh"

# =========================================================================
# Bash syntax validation
# =========================================================================

@test "setup.sh passes bash -n syntax check" {
    run bash -n "$SETUP_SH"
    if [ "$status" -ne 0 ]; then
        echo "Syntax errors found:"
        echo "$output"
    fi
    [ "$status" -eq 0 ]
}

@test "setup.sh has valid shebang" {
    head -1 "$SETUP_SH" | grep -q '^#!/bin/bash'
}

@test "setup.sh uses set -euo pipefail" {
    grep -q 'set -euo pipefail' "$SETUP_SH"
}

# =========================================================================
# Dangerous patterns detection
# =========================================================================

@test "no unquoted variables inside command substitution with echo -e" {
    # The bug: read -p "$(echo -e ${BOLD}...)" where parens in text break parsing
    # Safe form: read -p "$(echo -e "${BOLD}...")"
    # Check for: echo -e ${VAR} (unquoted var after echo -e inside $())
    problematic=$(grep -n 'echo -e \${' "$SETUP_SH" || true)
    if [ -n "$problematic" ]; then
        echo "Found unquoted variables in echo -e (potential syntax issue):"
        echo "$problematic"
    fi
    [ -z "$problematic" ]
}

@test "no unclosed parentheses in read -p arguments" {
    # Extract all read -p lines and check for balanced parens
    while IFS= read -r line; do
        # Count open and close parens
        opens=$(echo "$line" | tr -cd '(' | wc -c | tr -d ' ')
        closes=$(echo "$line" | tr -cd ')' | wc -c | tr -d ' ')
        if [ "$opens" -ne "$closes" ]; then
            echo "Unbalanced parentheses on line: $line"
            return 1
        fi
    done < <(grep 'read -p' "$SETUP_SH" || true)
}

@test "all heredocs are properly terminated" {
    # Extract unique heredoc delimiters and verify each has a matching terminator
    # Handles: << 'EOF', << EOF, <<'EOF', <<EOF
    delimiters=$(grep -oE "<<-?\s*'?[A-Z_]+'?" "$SETUP_SH" | sed "s/.*<<-*[[:space:]]*'*//;s/'*$//" | sort -u)
    for delimiter in $delimiters; do
        [ -z "$delimiter" ] && continue
        count=$(grep -c "^${delimiter}$" "$SETUP_SH" || true)
        if [ "$count" -lt 1 ]; then
            echo "Unterminated heredoc with delimiter: $delimiter"
            return 1
        fi
    done
}

# =========================================================================
# Function structure tests
# =========================================================================

@test "all expected functions are defined" {
    expected_functions=(
        header info success warn error explain
        ask_yn ask_choice
        state_mark state_done state_save state_read
        detect_hardware install_ollama
        select_model_quantization explain_quantization select_and_pull_models
        create_modelfiles tune_environment install_opencode configure_opencode
        create_modes create_agents_md create_commands create_tools
        create_skills create_plugins
        create_knowledge_base create_model_registry create_analytics
        optional_integrations verify_installation final_summary
        main
    )

    for func in "${expected_functions[@]}"; do
        if ! grep -q "^${func}()" "$SETUP_SH"; then
            echo "Missing function: $func"
            return 1
        fi
    done
}

@test "main calls all 18 setup steps" {
    expected_steps=(
        detect_hardware
        install_ollama
        select_and_pull_models
        create_modelfiles
        tune_environment
        install_opencode
        configure_opencode
        create_modes
        create_agents_md
        create_commands
        create_tools
        create_skills
        create_plugins
        create_knowledge_base
        create_model_registry
        create_analytics
        optional_integrations
        verify_installation
        final_summary
    )

    # Extract the main function body
    main_body=$(sed -n '/^main()/,/^}/p' "$SETUP_SH" | tail -n +2)

    for step in "${expected_steps[@]}"; do
        if ! echo "$main_body" | grep -q "$step"; then
            echo "main() missing call to: $step"
            return 1
        fi
    done
}

@test "all step functions check state_done for idempotency" {
    # These functions should all check state_done to be re-runnable
    idempotent_steps=(
        detect_hardware install_ollama select_and_pull_models
        create_modelfiles tune_environment install_opencode configure_opencode
        create_modes create_agents_md create_commands create_tools
        create_skills create_plugins
        create_knowledge_base create_model_registry create_analytics
    )

    for step in "${idempotent_steps[@]}"; do
        body=$(sed -n "/^${step}()/,/^}/p" "$SETUP_SH")
        if ! echo "$body" | grep -q 'state_done'; then
            echo "Function $step doesn't check state_done (not idempotent)"
            return 1
        fi
    done
}

# =========================================================================
# macOS guard
# =========================================================================

@test "main checks for macOS before proceeding" {
    main_body=$(sed -n '/^main()/,/^}/p' "$SETUP_SH")
    echo "$main_body" | grep -q 'OSTYPE.*darwin'
}
