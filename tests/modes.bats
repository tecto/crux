#!/usr/bin/env bats
# Tests for mode files: structure, content rules, and consistency.

MODES_DIR="/Users/user/personal/crux/modes"

# All 22 modes
MODES=(build-py build-ex plan infra-architect review debug explain analyst writer psych legal strategist ai-infra mac docker test security design-ui design-review design-system design-responsive design-accessibility)

# Think routing from think-router.js
THINK_MODES=(debug plan infra-architect review legal strategist psych security design-review design-accessibility)
NO_THINK_MODES=(build-py build-ex writer analyst mac docker explain test design-ui design-system design-responsive)
NEUTRAL_MODES=(ai-infra)

# =========================================================================
# File existence
# =========================================================================

@test "all 22 mode files exist" {
    for mode in "${MODES[@]}"; do
        if [ ! -f "$MODES_DIR/${mode}.md" ]; then
            echo "Missing mode file: ${mode}.md"
            return 1
        fi
    done
}

@test "mode template file exists" {
    [ -f "$MODES_DIR/_template.md" ]
}

# =========================================================================
# Structure: each mode has required sections
# =========================================================================

@test "all modes have Core Rules (First Position) section" {
    for mode in "${MODES[@]}"; do
        if ! grep -Fq '## Core Rules (First Position)' "$MODES_DIR/${mode}.md"; then
            echo "Missing 'Core Rules (First Position)' in ${mode}.md"
            return 1
        fi
    done
}

@test "all modes have Core Rules (Last Position) section" {
    for mode in "${MODES[@]}"; do
        if ! grep -Fq '## Core Rules (Last Position)' "$MODES_DIR/${mode}.md"; then
            echo "Missing 'Core Rules (Last Position)' in ${mode}.md"
            return 1
        fi
    done
}

@test "all modes have Response Format section" {
    for mode in "${MODES[@]}"; do
        if ! grep -q '## Response Format' "$MODES_DIR/${mode}.md"; then
            echo "Missing 'Response Format' in ${mode}.md"
            return 1
        fi
    done
}

@test "all modes have Scope section" {
    for mode in "${MODES[@]}"; do
        if ! grep -q '## Scope' "$MODES_DIR/${mode}.md"; then
            echo "Missing 'Scope' in ${mode}.md"
            return 1
        fi
    done
}

@test "all modes start with '# Mode: name' header" {
    for mode in "${MODES[@]}"; do
        first_line=$(head -1 "$MODES_DIR/${mode}.md")
        if [[ "$first_line" != "# Mode: ${mode}" ]]; then
            echo "Wrong header in ${mode}.md: got '$first_line', expected '# Mode: ${mode}'"
            return 1
        fi
    done
}

# =========================================================================
# Content quality rules (from CLAUDE.md design decisions)
# =========================================================================

@test "mode prompts use positive framing (no 'don't' or 'never' or 'avoid')" {
    for mode in "${MODES[@]}"; do
        # Check for negative framing in rule lines (lines starting with -)
        negative=$(grep '^-' "$MODES_DIR/${mode}.md" | grep -iE '\b(don.t|never|avoid|do not)\b' || true)
        if [ -n "$negative" ]; then
            echo "Negative framing found in ${mode}.md:"
            echo "$negative"
            return 1
        fi
    done
}

@test "all think modes are listed in THINK_MODES" {
    # Every mode listed in CLAUDE.md as "think" should be in THINK_MODES
    for mode in "${THINK_MODES[@]}"; do
        if [[ ! " ${MODES[*]} " =~ " $mode " ]]; then
            echo "Think mode '$mode' not in MODES list"
            return 1
        fi
    done
}

@test "all no_think modes are listed in NO_THINK_MODES" {
    for mode in "${NO_THINK_MODES[@]}"; do
        if [[ ! " ${MODES[*]} " =~ " $mode " ]]; then
            echo "No-think mode '$mode' not in MODES list"
            return 1
        fi
    done
}

@test "every mode is classified as think, no_think, or neutral" {
    all_classified=("${THINK_MODES[@]}" "${NO_THINK_MODES[@]}" "${NEUTRAL_MODES[@]}")
    for mode in "${MODES[@]}"; do
        if [[ ! " ${all_classified[*]} " =~ " $mode " ]]; then
            echo "Mode '$mode' not classified in any think category"
            return 1
        fi
    done
}

@test "no mode is in multiple think categories" {
    all_classified=("${THINK_MODES[@]}" "${NO_THINK_MODES[@]}" "${NEUTRAL_MODES[@]}")
    for mode in "${MODES[@]}"; do
        count=0
        for m in "${all_classified[@]}"; do
            [ "$m" = "$mode" ] && count=$((count + 1))
        done
        if [ "$count" -gt 1 ]; then
            echo "Mode '$mode' appears in multiple think categories"
            return 1
        fi
    done
}

# =========================================================================
# Template compliance
# =========================================================================

@test "template documents positive instruction rule" {
    grep -q 'positive' "$MODES_DIR/_template.md"
}

@test "template documents prime positions rule" {
    grep -q 'prime' "$MODES_DIR/_template.md" || grep -q 'First Position.*Last Position' "$MODES_DIR/_template.md"
}

@test "template documents 150-200 word target" {
    grep -q '150.*200' "$MODES_DIR/_template.md"
}
