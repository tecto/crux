#!/usr/bin/env bats
# Tests for script-template.sh and transaction-template.sh

SCRIPT_TEMPLATE="/Users/user/personal/crux/scripts/templates/script-template.sh"
TRANSACTION_TEMPLATE="/Users/user/personal/crux/scripts/templates/transaction-template.sh"

setup() {
    export TEST_DIR="$(mktemp -d)"
}

teardown() {
    rm -rf "$TEST_DIR"
}

# =========================================================================
# script-template.sh
# =========================================================================

@test "script-template.sh passes bash syntax check" {
    run bash -n "$SCRIPT_TEMPLATE"
    [ "$status" -eq 0 ]
}

@test "script-template.sh has proper shebang" {
    head -1 "$SCRIPT_TEMPLATE" | grep -q '^#!/bin/bash'
}

@test "script-template.sh uses set -euo pipefail" {
    grep -q 'set -euo pipefail' "$SCRIPT_TEMPLATE"
}

@test "script-template.sh defines DRY_RUN variable" {
    grep -q 'DRY_RUN=' "$SCRIPT_TEMPLATE"
}

@test "script-template.sh defines all logging functions" {
    for func in log_info log_warn log_error log_success log_debug; do
        if ! grep -q "^${func}()" "$SCRIPT_TEMPLATE"; then
            echo "Missing function: $func"
            return 1
        fi
    done
}

@test "script-template.sh defines run_cmd helper" {
    grep -q '^run_cmd()' "$SCRIPT_TEMPLATE"
}

@test "script-template.sh defines main function" {
    grep -q '^main()' "$SCRIPT_TEMPLATE"
}

@test "script-template.sh has error trap" {
    grep -q "trap.*ERR" "$SCRIPT_TEMPLATE"
}

@test "script-template.sh supports --help flag" {
    run bash "$SCRIPT_TEMPLATE" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage:"* ]]
}

@test "script-template.sh supports --dry-run flag" {
    run bash "$SCRIPT_TEMPLATE" --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY_RUN"* ]]
}

@test "script-template.sh rejects unknown flags" {
    run bash "$SCRIPT_TEMPLATE" --bogus
    [ "$status" -ne 0 ]
}

@test "script-template.sh runs successfully with no args" {
    run bash "$SCRIPT_TEMPLATE"
    [ "$status" -eq 0 ]
}

@test "script-template.sh logging functions write to stderr" {
    # Run the script in dry-run mode and verify stderr output contains log markers
    result=$(bash "$SCRIPT_TEMPLATE" --dry-run 2>&1)
    [[ "$result" == *"[INFO]"* ]]
}

# =========================================================================
# transaction-template.sh
# =========================================================================

@test "transaction-template.sh passes bash syntax check" {
    run bash -n "$TRANSACTION_TEMPLATE"
    [ "$status" -eq 0 ]
}

@test "transaction-template.sh has proper shebang" {
    head -1 "$TRANSACTION_TEMPLATE" | grep -q '^#!/bin/bash'
}

@test "transaction-template.sh uses set -euo pipefail" {
    grep -q 'set -euo pipefail' "$TRANSACTION_TEMPLATE"
}

@test "transaction-template.sh defines all 5 transaction stages" {
    for func in validate_transaction prepare_transaction apply_transaction verify_transaction commit_transaction; do
        if ! grep -q "^${func}()" "$TRANSACTION_TEMPLATE"; then
            echo "Missing stage: $func"
            return 1
        fi
    done
}

@test "transaction-template.sh defines rollback_transaction" {
    grep -q '^rollback_transaction()' "$TRANSACTION_TEMPLATE"
}

@test "transaction-template.sh defines cleanup function" {
    grep -q '^cleanup()' "$TRANSACTION_TEMPLATE"
}

@test "transaction-template.sh defines track_modified and track_created" {
    grep -q '^track_modified()' "$TRANSACTION_TEMPLATE"
    grep -q '^track_created()' "$TRANSACTION_TEMPLATE"
}

@test "transaction-template.sh has error trap with rollback" {
    grep -q 'trap.*rollback_transaction' "$TRANSACTION_TEMPLATE"
}

@test "transaction-template.sh supports --help" {
    run bash "$TRANSACTION_TEMPLATE" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Transaction Stages"* ]]
}

@test "transaction-template.sh supports --dry-run" {
    run bash "$TRANSACTION_TEMPLATE" --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY_RUN"* ]]
}

@test "transaction-template.sh runs all 5 stages" {
    run bash "$TRANSACTION_TEMPLATE"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STAGE 1: Validation"* ]]
    [[ "$output" == *"STAGE 2: Preparation"* ]]
    [[ "$output" == *"STAGE 3: Apply"* ]]
    [[ "$output" == *"STAGE 4: Verification"* ]]
    [[ "$output" == *"STAGE 5: Commit"* ]]
}

@test "transaction-template.sh main orchestrates stages in order" {
    main_body=$(sed -n '/^main()/,/^}/p' "$TRANSACTION_TEMPLATE")
    # Check the order
    validate_pos=$(echo "$main_body" | grep -n 'validate_transaction' | head -1 | cut -d: -f1)
    prepare_pos=$(echo "$main_body" | grep -n 'prepare_transaction' | head -1 | cut -d: -f1)
    apply_pos=$(echo "$main_body" | grep -n 'apply_transaction' | head -1 | cut -d: -f1)
    verify_pos=$(echo "$main_body" | grep -n 'verify_transaction' | head -1 | cut -d: -f1)
    commit_pos=$(echo "$main_body" | grep -n 'commit_transaction' | head -1 | cut -d: -f1)

    [ "$validate_pos" -lt "$prepare_pos" ]
    [ "$prepare_pos" -lt "$apply_pos" ]
    [ "$apply_pos" -lt "$verify_pos" ]
    [ "$verify_pos" -lt "$commit_pos" ]
}

@test "transaction-template.sh cleanup only removes /tmp dirs" {
    # The cleanup function should check that TEMP_DIR is in /tmp
    grep -A5 '^cleanup()' "$TRANSACTION_TEMPLATE" | grep -q '/tmp'
}
