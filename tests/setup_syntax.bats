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
        install_modes install_agents_md install_commands install_tools
        install_skills install_plugins
        create_knowledge_base create_model_registry create_analytics
        install_python_scripts install_crux_cli
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

@test "main calls all setup steps" {
    expected_steps=(
        detect_hardware
        install_ollama
        select_and_pull_models
        create_modelfiles
        tune_environment
        install_opencode
        configure_opencode
        install_modes
        install_agents_md
        install_commands
        install_tools
        install_skills
        install_plugins
        create_knowledge_base
        create_model_registry
        create_analytics
        install_python_scripts
        install_crux_cli
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

# =========================================================================
# Model name validation
# =========================================================================

@test "model names in case statement are valid Ollama registry names" {
    # Extract model names from the case statement in select_and_pull_models
    models=$(grep -oE 'primary_model="[^"]*"' "$SETUP_SH" | sed 's/primary_model="//;s/"//' | grep -v '^\$' | sort -u)
    for model in $models; do
        # Model name must match pattern: name:tag (alphanumeric, dots, hyphens)
        if ! echo "$model" | grep -qE '^[a-z][a-z0-9._-]*:[a-z0-9._-]+$'; then
            echo "Invalid model name format: $model"
            return 1
        fi
    done
}

@test "audit model name is valid format" {
    audit=$(grep 'audit_model=' "$SETUP_SH" | head -1 | grep -oE '"[^"]*"' | tr -d '"')
    echo "$audit" | grep -qE '^[a-z][a-z0-9._-]*:[a-z0-9._-]+$'
}

# =========================================================================
# Idempotent self-healing: state-guarded steps verify artifacts
# =========================================================================

@test "create_modelfiles verifies models exist before skipping" {
    func_body=$(sed -n '/^create_modelfiles()/,/^}/p' "$SETUP_SH")
    # Must check ollama list for all model variants, not just state_done
    echo "$func_body" | grep -q 'ollama list.*crux-think'
    echo "$func_body" | grep -q 'ollama list.*crux-code'
}

@test "install_opencode verifies binary exists before skipping" {
    func_body=$(sed -n '/^install_opencode()/,/^}/p' "$SETUP_SH")
    # Must check command -v opencode even in the state_done branch
    # The state_done block should verify the artifact
    echo "$func_body" | grep -A5 'state_done.*opencode_installed' | grep -q 'command -v opencode'
}

@test "select_and_pull_models verifies models exist before skipping" {
    func_body=$(sed -n '/^select_and_pull_models()/,/^}/p' "$SETUP_SH")
    # Must read saved model AND check it exists in ollama
    echo "$func_body" | grep -q 'state_read.*primary_model'
    echo "$func_body" | grep -q 'ollama list.*saved_model'
}

@test "optional_integrations has state guard to avoid re-asking" {
    func_body=$(sed -n '/^optional_integrations()/,/^}/p' "$SETUP_SH")
    echo "$func_body" | grep -q 'state_done'
}

@test "verify_installation auto-fixes missing node_modules" {
    func_body=$(sed -n '/^verify_installation()/,/^}/p' "$SETUP_SH")
    # Must actually run npm install as a fix, not just mention it in an error message
    echo "$func_body" | grep -qE '\(cd.*npm install|npm install.*\&'
}

@test "final_summary dynamically counts modes" {
    func_body=$(sed -n '/^final_summary()/,/^}/p' "$SETUP_SH")
    # Should count from filesystem, not hardcode "15 total"
    echo "$func_body" | grep -qE 'mode_count|ls.*modes'
}

# =========================================================================
# Existing checks
# =========================================================================

@test "npm install does not use --production flag" {
    # zod is a devDependency — --production skips it
    func_body=$(sed -n '/^install_tools()/,/^}/p' "$SETUP_SH")
    ! echo "$func_body" | grep -q '\-\-production'
}

@test "mode count check uses >= not ==" {
    # The repo grows — verification should accept at least 15, not exactly 15
    func_body=$(sed -n '/^verify_installation()/,/^}/p' "$SETUP_SH")
    echo "$func_body" | grep -q 'mode_count.*-ge 15'
}

@test "create_modelfiles runs ollama create for all three variants" {
    func_body=$(sed -n '/^create_modelfiles()/,/^}/p' "$SETUP_SH")
    echo "$func_body" | grep -q 'ollama create crux-think'
    echo "$func_body" | grep -q 'ollama create crux-chat'
    echo "$func_body" | grep -q 'ollama create crux-code'
}

@test "install_opencode does not duplicate menu before ask_choice" {
    func_body=$(sed -n '/^install_opencode()/,/^}/p' "$SETUP_SH")
    # There should be no manual echo of numbered options — ask_choice handles that
    ! echo "$func_body" | grep -qE 'echo.*1\.'
}

@test "install_opencode refreshes PATH before verifying" {
    # The curl installer adds opencode to ~/.zshrc but the running shell
    # doesn't have it on PATH yet. The function must handle this.
    func_body=$(sed -n '/^install_opencode()/,/^}/p' "$SETUP_SH")
    # Must either source shell config or add known install paths to PATH
    echo "$func_body" | grep -qE 'PATH=.*opencode|source.*zshrc|\.opencode/bin'
}

@test "opencode.json template has no invalid keys" {
    # Extract the heredoc content for opencode.json
    config_block=$(sed -n '/cat.*opencode\.json.*EOF/,/^EOF$/p' "$SETUP_SH")
    # These keys are not in OpenCode's schema
    ! echo "$config_block" | grep -q '"lsp"'
    ! echo "$config_block" | grep -q '"timeout"'
}

@test "opencode.json template includes schema reference" {
    config_block=$(sed -n '/cat.*opencode\.json.*EOF/,/^EOF$/p' "$SETUP_SH")
    echo "$config_block" | grep -q 'opencode.ai/config.json'
}

@test "install_modes symlinks to both modes and agents directories" {
    func_body=$(sed -n '/^install_modes()/,/^}/p' "$SETUP_SH")
    echo "$func_body" | grep -q 'safe_symlink.*config_dir/modes'
    echo "$func_body" | grep -q 'safe_symlink.*config_dir/agents'
}

@test "ask_choice outputs menu to stderr not stdout" {
    # Verify that ask_choice in setup.sh uses >&2 for menu output
    func_body=$(sed -n '/^ask_choice()/,/^}/p' "$SETUP_SH")
    # The echo lines for menu items must go to stderr
    echo "$func_body" | grep 'echo.*\$prompt' | grep -q '>&2'
    echo "$func_body" | grep 'echo.*choices\[' | grep -q '>&2'
}
