#!/bin/bash
set -euo pipefail

###############################################################################
# Crux Setup Script - Self-Improving AI Operating System
# macOS (Apple Silicon) installer with interactive setup and state tracking
#
# Usage:
#   ./setup.sh           Full interactive setup
#   ./setup.sh --update  Non-interactive refresh (symlinks, scripts, CLI)
###############################################################################

# Detect repo directory (where this script lives)
CRUX_DIR="$(cd "$(dirname "$0")" && pwd)"

# Parse flags
UPDATE_MODE=false
if [ "${1:-}" = "--update" ]; then
    UPDATE_MODE=true
fi

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# State tracking directory
STATE_DIR="$HOME/.config/crux/setup-state"
mkdir -p "$STATE_DIR"

###############################################################################
# HELPER FUNCTIONS
###############################################################################

header() {
    echo -e "\n${BOLD}${BLUE}=== $1 ===${NC}\n"
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

explain() {
    echo -e "${CYAN}→${NC} $1"
}

ask_yn() {
    local question="$1"
    local response
    while true; do
        read -p "$(echo -e "${BOLD}${question}${NC}") (y/n): " response
        case "$response" in
            [yY]) return 0 ;;
            [nN]) return 1 ;;
            *) echo "Please answer y or n" ;;
        esac
    done
}

ask_choice() {
    local prompt="$1"
    shift
    local choices=("$@")
    local response

    echo -e "\n${BOLD}$prompt${NC}"
    for i in "${!choices[@]}"; do
        echo "  $((i+1)). ${choices[$i]}"
    done

    while true; do
        read -p "$(echo -e "${BOLD}Enter choice (1-${#choices[@]}):${NC}") " response
        if [[ "$response" =~ ^[0-9]+$ ]] && [ "$response" -ge 1 ] && [ "$response" -le ${#choices[@]} ]; then
            echo "$((response-1))"
            return 0
        fi
        echo "Invalid choice. Please enter a number between 1 and ${#choices[@]}."
    done
}

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

# Create a symlink, removing any existing file/dir/link at the target
safe_symlink() {
    local source="$1"
    local target="$2"

    if [ -L "$target" ]; then
        rm "$target"
    elif [ -e "$target" ]; then
        # Back up existing non-symlink content
        local backup="${target}.backup.$(date +%s)"
        warn "Backing up existing $target to $backup"
        mv "$target" "$backup"
    fi

    ln -s "$source" "$target"
}

###############################################################################
# STEP 1: HARDWARE DETECTION
###############################################################################

detect_hardware() {
    if state_done "hardware_detected"; then
        info "Hardware profile already detected (cached)"
        return 0
    fi

    header "STEP 1: Hardware Detection"

    info "Detecting system hardware..."

    # Total RAM in bytes
    local total_ram_bytes
    total_ram_bytes=$(sysctl -n hw.memsize)
    local total_ram_gb=$((total_ram_bytes / 1024 / 1024 / 1024))

    # Available RAM - try memory_pressure first, fallback to vm_stat
    local available_ram_gb
    if command -v memory_pressure &> /dev/null; then
        available_ram_gb=$((total_ram_gb - 2))  # Conservative estimate
    else
        available_ram_gb=$((total_ram_gb / 2))  # Very conservative
    fi

    # Chip detection
    local chip_brand
    chip_brand=$(sysctl -n machdep.cpu.brand_string | grep -oE 'Apple (M[0-9]+)' | head -1 | awk '{print $2}')

    if [ -z "$chip_brand" ]; then
        chip_brand="Unknown"
    fi

    success "Total RAM: ${total_ram_gb}GB"
    success "Available RAM: ${available_ram_gb}GB"
    success "Chip: Apple $chip_brand"

    # Save hardware profile
    state_save "total_ram_gb" "$total_ram_gb"
    state_save "available_ram_gb" "$available_ram_gb"
    state_save "chip_model" "$chip_brand"

    state_mark "hardware_detected"
}

###############################################################################
# STEP 2: OLLAMA INSTALLATION
###############################################################################

install_ollama() {
    if state_done "ollama_installed"; then
        info "Ollama installation already completed (skipping)"
        return 0
    fi

    header "STEP 2: Ollama Installation"

    # Check if Ollama is already installed
    if command -v ollama &> /dev/null; then
        success "Ollama is already installed"
        state_mark "ollama_installed"
        return 0
    fi

    info "Installing Ollama via Homebrew..."

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        error "Homebrew is not installed. Please install from https://brew.sh"
        return 1
    fi

    brew install ollama
    success "Ollama installed"

    # Start Ollama service
    info "Starting Ollama service..."
    brew services start ollama

    # Wait for service to start
    sleep 2

    # Verify Ollama is responding
    local retries=0
    while [ $retries -lt 10 ]; do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            success "Ollama service verified at localhost:11434"
            state_mark "ollama_installed"
            return 0
        fi
        retries=$((retries + 1))
        sleep 1
    done

    error "Could not verify Ollama service. Please check with 'brew services list'"
    return 1
}

###############################################################################
# STEP 3: MODEL SELECTION AND PULL
###############################################################################

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

explain_quantization() {
    local quant=$1

    case "$quant" in
        Q8_0)
            explain "Q8_0: 8-bit quantization. Best quality, highest performance on Metal GPU. ~10GB per 32B model."
            ;;
        Q6_K)
            explain "Q6_K: 6-bit quantization. Excellent quality-to-size ratio. ~6GB per 32B model."
            ;;
        Q4_K_M)
            explain "Q4_K_M: 4-bit quantization with K-quant optimization. Good quality, efficient size. ~4GB per 32B model."
            ;;
        Q4_K_S)
            explain "Q4_K_S: 4-bit quantization, smaller variant. Compact, suitable for constrained RAM. ~3.5GB per 32B model."
            ;;
    esac
}

select_and_pull_models() {
    if state_done "models_pulled"; then
        info "Model selection and pulling already completed (skipping)"
        return 0
    fi

    header "STEP 3: Model Selection and Pull"

    local total_ram
    total_ram=$(state_read "total_ram_gb")
    local available_ram
    available_ram=$(state_read "available_ram_gb")

    # Recommend quantization based on total RAM
    local recommended_quant
    recommended_quant=$(select_model_quantization "$total_ram")

    info "System RAM: ${total_ram}GB total, ${available_ram}GB available"
    info "Recommended quantization: $recommended_quant"
    explain_quantization "$recommended_quant"

    # Check if we have enough available RAM
    local suggested_choice="$recommended_quant"
    if [ "$available_ram" -lt 10 ] && [ "$recommended_quant" = "Q8_0" ]; then
        warn "Available RAM may be insufficient for Q8_0. Current large processes:"
        ps aux -m | head -5

        echo ""
        echo -e "${BOLD}Options:${NC}"
        echo "  1. Free memory for best quality (Q8_0)"
        echo "  2. Proceed with Q6_K that fits now"

        local choice
        choice=$(ask_choice "Choose option:" "Free memory for Q8_0" "Proceed with Q6_K")

        if [ "$choice" = "0" ]; then
            warn "Please close applications and press Enter when ready"
            read -p ""
            suggested_choice="Q8_0"
        else
            suggested_choice="Q6_K"
        fi
    fi

    # Model selection menu
    echo -e "\n${BOLD}Select primary model:${NC}"
    echo "  1. Qwen3 32B (recommended general purpose)"
    echo "  2. Qwen3-Coder 30B (code-specialized)"
    echo "  3. Qwen3.5 27B (balanced)"
    echo "  4. Custom (enter model name)"

    local model_choice
    model_choice=$(ask_choice "Choose model:" \
        "Qwen3 32B" \
        "Qwen3-Coder 30B" \
        "Qwen3.5 27B" \
        "Custom")

    local primary_model
    case "$model_choice" in
        0) primary_model="qwen3:32b" ;;
        1) primary_model="qwen3-coder:30b" ;;
        2) primary_model="qwen3.5:27b" ;;
        3)
            read -p "Enter model name (e.g., mistral:7b): " primary_model
            ;;
    esac

    state_save "primary_model" "$primary_model"
    state_save "model_quantization" "$suggested_choice"

    info "Pulling primary model: $primary_model"
    explain "This may take a while depending on model size and internet speed..."
    ollama pull "$primary_model"
    success "Primary model pulled: $primary_model"

    # Pull small model for auditing
    info "Pulling small model for auditing (qwen3:8b)..."
    ollama pull qwen3:8b
    success "Audit model pulled: qwen3:8b"

    state_mark "models_pulled"
}

###############################################################################
# STEP 4: MODELFILE CREATION
###############################################################################

create_modelfiles() {
    if state_done "modelfiles_created"; then
        info "Modelfiles already created (skipping)"
        return 0
    fi

    header "STEP 4: Modelfile Creation"

    local primary_model
    primary_model=$(state_read "primary_model")

    # Ask about context size
    echo -e "\n${BOLD}Select context window size:${NC}"
    echo "  1. 16K tokens (minimal memory, faster inference)"
    echo "  2. 32K tokens (balanced - recommended)"
    echo "  3. 64K tokens (high memory, can track longer conversations)"
    echo "  4. 128K tokens (requires 64GB+ RAM)"

    local ctx_choice
    ctx_choice=$(ask_choice "Choose context size:" "16K" "32K" "64K" "128K")

    local num_ctx
    case "$ctx_choice" in
        0) num_ctx="16384" ;;
        1) num_ctx="32768" ;;
        2) num_ctx="65536" ;;
        3) num_ctx="131072" ;;
    esac

    explain "Selected context: $num_ctx tokens"
    state_save "num_ctx" "$num_ctx"

    # Create Modelfile for crux-think
    info "Creating Modelfile for crux-think (reasoning mode)..."

    mkdir -p "$HOME/.ollama/models"

    cat > "$HOME/.ollama/models/modelfile-think" << 'MODELFILE_EOF'
FROM {{PRIMARY_MODEL}}

# Reasoning mode: higher temperature for exploration, top_p for diversity
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx {{NUM_CTX}}
PARAMETER num_gpu 64

SYSTEM """You are a capable assistant operating within the Crux framework. Follow these rules in every interaction:

1. Always narrate what you are doing and why. Before taking action, briefly state your plan. During multi-step work, provide status updates. Never work silently.
2. When asking clarifying questions, always use numbered lists. Never use bullet points for questions.
3. When the user says "let's talk through" or "discuss one at a time," present each item individually and wait for explicit confirmation before moving to the next.
4. If uncertain, say so briefly rather than guessing.
5. Match your response length and formality to the complexity of the request.
6. All filesystem modifications must go through scripts in .opencode/scripts/ following the project script template. Never modify files directly.
7. Before writing a new script, check if a custom tool, MCP server, or existing library script can handle the task. Prefer higher-tier tools over lower-tier ones.
8. When you notice a task exceeds your current capability, say so and suggest alternatives rather than producing low-quality output.
"""
MODELFILE_EOF

    sed -i '' "s|{{PRIMARY_MODEL}}|$primary_model|g" "$HOME/.ollama/models/modelfile-think"
    sed -i '' "s|{{NUM_CTX}}|$num_ctx|g" "$HOME/.ollama/models/modelfile-think"

    # Create Modelfile for crux-chat
    info "Creating Modelfile for crux-chat (execution mode)..."

    cat > "$HOME/.ollama/models/modelfile-chat" << 'MODELFILE_EOF'
FROM {{PRIMARY_MODEL}}

# Chat mode: moderate temperature for balanced execution
PARAMETER temperature 0.7
PARAMETER top_p 0.8
PARAMETER top_k 20
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx {{NUM_CTX}}
PARAMETER num_gpu 64

SYSTEM """You are a capable assistant operating within the Crux framework. Follow these rules in every interaction:

1. Always narrate what you are doing and why. Before taking action, briefly state your plan. During multi-step work, provide status updates. Never work silently.
2. When asking clarifying questions, always use numbered lists. Never use bullet points for questions.
3. When the user says "let's talk through" or "discuss one at a time," present each item individually and wait for explicit confirmation before moving to the next.
4. If uncertain, say so briefly rather than guessing.
5. Match your response length and formality to the complexity of the request.
6. All filesystem modifications must go through scripts in .opencode/scripts/ following the project script template. Never modify files directly.
7. Before writing a new script, check if a custom tool, MCP server, or existing library script can handle the task. Prefer higher-tier tools over lower-tier ones.
8. When you notice a task exceeds your current capability, say so and suggest alternatives rather than producing low-quality output.
"""
MODELFILE_EOF

    sed -i '' "s|{{PRIMARY_MODEL}}|$primary_model|g" "$HOME/.ollama/models/modelfile-chat"
    sed -i '' "s|{{NUM_CTX}}|$num_ctx|g" "$HOME/.ollama/models/modelfile-chat"

    success "Modelfiles created"

    # Create the models in Ollama
    info "Creating crux-think model variant..."
    ollama create crux-think -f "$HOME/.ollama/models/modelfile-think"
    success "crux-think model created"

    info "Creating crux-chat model variant..."
    ollama create crux-chat -f "$HOME/.ollama/models/modelfile-chat"
    success "crux-chat model created"

    state_mark "modelfiles_created"
}

###############################################################################
# STEP 5: ENVIRONMENT TUNING
###############################################################################

tune_environment() {
    if state_done "environment_tuned"; then
        info "Environment tuning already completed (skipping)"
        return 0
    fi

    header "STEP 5: Environment Tuning"

    # Detect shell
    local shell_profile
    if [[ "$SHELL" == *"zsh"* ]]; then
        shell_profile="$HOME/.zshrc"
    else
        shell_profile="$HOME/.bashrc"
    fi

    info "Detected shell profile: $shell_profile"

    # Add Ollama environment variables
    info "Adding Ollama environment variables..."

    # Check and add OLLAMA_KEEP_ALIVE
    if ! grep -q "OLLAMA_KEEP_ALIVE" "$shell_profile"; then
        echo "" >> "$shell_profile"
        echo "# Crux: Ollama configuration" >> "$shell_profile"
        echo "export OLLAMA_KEEP_ALIVE=24h" >> "$shell_profile"
        echo "export OLLAMA_MAX_LOADED_MODELS=2" >> "$shell_profile"
        success "Added Ollama environment variables to $shell_profile"
    else
        info "Ollama environment variables already configured"
    fi

    state_mark "environment_tuned"
}

###############################################################################
# STEP 6: OPENCODE CLI INSTALLATION
###############################################################################

install_opencode() {
    if state_done "opencode_installed"; then
        info "OpenCode installation already completed (skipping)"
        return 0
    fi

    header "STEP 6: OpenCode CLI Installation"

    # Check if already installed
    if command -v opencode &> /dev/null; then
        success "OpenCode is already installed"
        state_mark "opencode_installed"
        return 0
    fi

    echo -e "\n${BOLD}Installation method:${NC}"
    echo "  1. curl (recommended)"
    echo "  2. Homebrew"
    echo "  3. npm"

    local install_choice
    install_choice=$(ask_choice "Choose installation method:" "curl" "Homebrew" "npm")

    case "$install_choice" in
        0)
            info "Installing OpenCode via curl..."
            curl -sSL https://install.opencode.dev/macos.sh | bash
            ;;
        1)
            info "Installing OpenCode via Homebrew..."
            brew install opencode
            ;;
        2)
            info "Installing OpenCode via npm..."
            npm install -g opencode
            ;;
    esac

    # Verify installation
    if command -v opencode &> /dev/null; then
        success "OpenCode installed successfully"
        opencode --version
        state_mark "opencode_installed"
    else
        error "OpenCode installation failed"
        return 1
    fi
}

###############################################################################
# STEP 7: OPENCODE CONFIGURATION
###############################################################################

configure_opencode() {
    if state_done "opencode_configured" && [ "$UPDATE_MODE" = false ]; then
        info "OpenCode configuration already completed (skipping)"
        return 0
    fi

    header "STEP 7: OpenCode Configuration"

    local config_dir="$HOME/.config/opencode"
    mkdir -p "$config_dir"

    info "Creating opencode.json configuration..."

    cat > "$config_dir/opencode.json" << 'EOF'
{
  "model": "ollama/crux-think",
  "small_model": "ollama/qwen3:8b",
  "provider": {
    "ollama": {
      "options": {
        "endpoint": "http://localhost:11434"
      }
    }
  },
  "lsp": {
    "python": {
      "command": "pyright",
      "args": ["--outputjson"]
    },
    "elixir": {
      "command": "elixir-ls",
      "alternative": "next-ls"
    }
  },
  "timeout": 600000,
  "permission": {
    "edit": "ask",
    "bash": "ask"
  },
  "compaction": {
    "enabled": true
  }
}
EOF

    success "Created opencode.json"

    state_mark "opencode_configured"
}

###############################################################################
# STEP 8: SYMLINK MODES FROM REPO
###############################################################################

install_modes() {
    header "STEP 8: Installing Modes"

    local config_dir="$HOME/.config/opencode"
    local source_dir="$CRUX_DIR/modes"

    if [ ! -d "$source_dir" ]; then
        error "Modes directory not found at $source_dir"
        return 1
    fi

    # Symlink the entire modes directory
    safe_symlink "$source_dir" "$config_dir/modes"

    local count
    count=$(ls -1 "$source_dir"/*.md 2>/dev/null | grep -v '_template' | wc -l | tr -d ' ')
    success "Linked $count modes from repo → $config_dir/modes"
}

###############################################################################
# STEP 9: SYMLINK AGENTS.MD FROM REPO
###############################################################################

install_agents_md() {
    header "STEP 9: Installing AGENTS.md"

    local config_dir="$HOME/.config/opencode"
    local source_file="$CRUX_DIR/templates/AGENTS.md"

    if [ ! -f "$source_file" ]; then
        error "AGENTS.md template not found at $source_file"
        return 1
    fi

    safe_symlink "$source_file" "$config_dir/AGENTS.md"
    success "Linked AGENTS.md from repo"
}

###############################################################################
# STEP 10: SYMLINK COMMANDS FROM REPO
###############################################################################

install_commands() {
    header "STEP 10: Installing Commands"

    local config_dir="$HOME/.config/opencode"
    local source_dir="$CRUX_DIR/commands"

    if [ ! -d "$source_dir" ]; then
        error "Commands directory not found at $source_dir"
        return 1
    fi

    safe_symlink "$source_dir" "$config_dir/commands"

    local count
    count=$(ls -1 "$source_dir"/*.md 2>/dev/null | wc -l | tr -d ' ')
    success "Linked $count commands from repo → $config_dir/commands"
}

###############################################################################
# STEP 11: SYMLINK TOOLS FROM REPO
###############################################################################

install_tools() {
    header "STEP 11: Installing Tools"

    local config_dir="$HOME/.config/opencode"
    local source_dir="$CRUX_DIR/tools"

    if [ ! -d "$source_dir" ]; then
        error "Tools directory not found at $source_dir"
        return 1
    fi

    safe_symlink "$source_dir" "$config_dir/tools"

    # Symlink lib/ (plugin-shim.js used by tools)
    if [ -d "$CRUX_DIR/lib" ]; then
        safe_symlink "$CRUX_DIR/lib" "$config_dir/lib"
        success "Linked lib/ from repo (plugin-shim.js)"
    fi

    # Install Node.js dependencies (zod) required by tools
    info "Installing Node.js dependencies..."
    if command -v npm &>/dev/null; then
        (cd "$CRUX_DIR" && npm install --production 2>/dev/null) || {
            warn "npm install failed — tools may not load correctly"
        }
        success "Node.js dependencies installed"
    else
        warn "npm not found. Run 'npm install' in $CRUX_DIR to install dependencies (zod)."
    fi

    local count
    count=$(ls -1 "$source_dir"/*.js 2>/dev/null | wc -l | tr -d ' ')
    success "Linked $count tools from repo → $config_dir/tools"
}

###############################################################################
# STEP 12: SYMLINK SKILLS FROM REPO
###############################################################################

install_skills() {
    header "STEP 12: Installing Skills"

    local config_dir="$HOME/.config/opencode"
    local source_dir="$CRUX_DIR/skills"

    if [ ! -d "$source_dir" ]; then
        warn "Skills directory not found at $source_dir — creating placeholder"
        mkdir -p "$config_dir/skills"
        return 0
    fi

    safe_symlink "$source_dir" "$config_dir/skills"

    local count
    count=$(find "$source_dir" -name "SKILL.md" | wc -l | tr -d ' ')
    success "Linked $count skills from repo → $config_dir/skills"
}

###############################################################################
# STEP 13: SYMLINK PLUGINS FROM REPO
###############################################################################

install_plugins() {
    header "STEP 13: Installing Plugins"

    local config_dir="$HOME/.config/opencode"
    local source_dir="$CRUX_DIR/plugins"

    if [ ! -d "$source_dir" ]; then
        error "Plugins directory not found at $source_dir"
        return 1
    fi

    safe_symlink "$source_dir" "$config_dir/plugins"

    local count
    count=$(ls -1 "$source_dir"/*.js 2>/dev/null | wc -l | tr -d ' ')
    success "Linked $count plugins from repo → $config_dir/plugins"
}

###############################################################################
# STEP 14: KNOWLEDGE BASE STRUCTURE
###############################################################################

create_knowledge_base() {
    if state_done "knowledge_created" && [ "$UPDATE_MODE" = false ]; then
        info "Knowledge base already created (skipping)"
        return 0
    fi

    header "STEP 14: Knowledge Base Structure"

    local knowledge_dir="$HOME/.config/opencode/knowledge"
    mkdir -p "$knowledge_dir/shared"

    # Create per-mode directories
    for mode in build-py build-ex plan infra-architect review debug explain analyst writer psych legal strategist ai-infra mac docker; do
        mkdir -p "$knowledge_dir/$mode"
    done

    # Symlink knowledge template from repo if available
    if [ -f "$CRUX_DIR/knowledge/_template.md" ]; then
        safe_symlink "$CRUX_DIR/knowledge/_template.md" "$knowledge_dir/_template.md"
    fi

    success "Created knowledge base structure (15 mode directories + shared)"
    state_mark "knowledge_created"
}

###############################################################################
# STEP 15: MODEL REGISTRY
###############################################################################

create_model_registry() {
    if state_done "model_registry_created" && [ "$UPDATE_MODE" = false ]; then
        info "Model registry already created (skipping)"
        return 0
    fi

    header "STEP 15: Model Registry"

    local models_dir="$HOME/.config/opencode/models"
    mkdir -p "$models_dir"

    local primary_model
    primary_model=$(state_read "primary_model")
    local quantization
    quantization=$(state_read "model_quantization")

    # Only create registry if it doesn't exist (preserve user modifications)
    if [ -f "$models_dir/registry.json" ] && [ "$UPDATE_MODE" = true ]; then
        info "Model registry exists, preserving user data"
        return 0
    fi

    cat > "$models_dir/registry.json" << EOF
{
  "version": "1.0",
  "registeredAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "local": [
    {
      "name": "crux-think",
      "provider": "ollama",
      "baseModel": "${primary_model:-qwen3:32b}",
      "quantization": "${quantization:-Q8_0}",
      "parameterCount": 32000000000,
      "status": "assigned",
      "roles": ["primary-reasoning", "debug", "plan"],
      "strengths": ["complex-reasoning", "multi-step-planning", "error-analysis"],
      "hardwareRequirements": {
        "minRamGb": 16,
        "recommendedRamGb": 32,
        "metalAccelerated": true
      }
    },
    {
      "name": "crux-chat",
      "provider": "ollama",
      "baseModel": "${primary_model:-qwen3:32b}",
      "quantization": "${quantization:-Q8_0}",
      "parameterCount": 32000000000,
      "status": "assigned",
      "roles": ["execution", "code-generation", "writing"],
      "strengths": ["fast-inference", "code-quality", "clarity"],
      "hardwareRequirements": {
        "minRamGb": 16,
        "recommendedRamGb": 32,
        "metalAccelerated": true
      }
    },
    {
      "name": "qwen3:8b",
      "provider": "ollama",
      "baseModel": "qwen3:8b",
      "quantization": "Q8_0",
      "parameterCount": 8000000000,
      "status": "available",
      "roles": ["compaction", "quick-inference"],
      "strengths": ["speed", "low-memory", "reliability"],
      "hardwareRequirements": {
        "minRamGb": 4,
        "recommendedRamGb": 8,
        "metalAccelerated": true
      }
    }
  ],
  "commercial": [
    {
      "name": "claude-opus-4-6",
      "provider": "anthropic",
      "status": "available",
      "pricing": {
        "inputPerMtok": 0.003,
        "outputPerMtok": 0.015
      },
      "strengths": ["reasoning", "code", "accuracy"],
      "useCase": "High-stakes analysis when local models insufficient"
    },
    {
      "name": "gpt-4o",
      "provider": "openai",
      "status": "available",
      "pricing": {
        "inputPerMtok": 0.005,
        "outputPerMtok": 0.015
      },
      "strengths": ["vision", "function-calling", "multimodal"],
      "useCase": "Vision tasks and structured outputs"
    }
  ],
  "deprecated": [],
  "experimental": []
}
EOF

    success "Created model registry"
    state_mark "model_registry_created"
}

###############################################################################
# STEP 16: ANALYTICS STRUCTURE
###############################################################################

create_analytics() {
    if state_done "analytics_created" && [ "$UPDATE_MODE" = false ]; then
        info "Analytics structure already created (skipping)"
        return 0
    fi

    header "STEP 16: Analytics Structure"

    local analytics_dir="$HOME/.config/opencode/analytics"
    mkdir -p "$analytics_dir"

    # Create empty weekly rollup (only if missing)
    if [ ! -f "$analytics_dir/weekly-rollup.jsonl" ]; then
        cat > "$analytics_dir/weekly-rollup.jsonl" << 'EOF'
{"week":"2026-W10","modes":{},"scripts":{},"totalSessions":0,"totalDuration":0}
EOF
    fi

    # Symlink digest template from repo scripts if available
    if [ -f "$CRUX_DIR/scripts/templates/digest-template.md" ]; then
        safe_symlink "$CRUX_DIR/scripts/templates/digest-template.md" "$analytics_dir/digest-template.md"
    else
        # Create inline if repo template doesn't exist yet
        if [ ! -f "$analytics_dir/digest-template.md" ]; then
            cat > "$analytics_dir/digest-template.md" << 'EOF'
# Daily Digest

## Summary
- Sessions: {{sessionCount}}
- Total time: {{totalDuration}}
- Modes used: {{modesUsed}}
- Success rate: {{successRate}}%

## Top Activities
{{#topScripts}}
- {{script}} ({{count}} executions)
{{/topScripts}}

## Issues & Errors
{{#errors}}
- {{error}}: {{count}} occurrences
{{/errors}}

## Recommendations
{{#recommendations}}
- {{recommendation}}
{{/recommendations}}

## Script Promotion Candidates
{{#promotionCandidates}}
- {{script}} ({{executions}} runs, {{days}} days old)
{{/promotionCandidates}}
EOF
        fi
    fi

    success "Created analytics structure"
    state_mark "analytics_created"
}

###############################################################################
# STEP 17: PYTHON SCRIPTS INSTALLATION
###############################################################################

install_python_scripts() {
    header "STEP 17: Installing Python Scripts"

    local config_dir="$HOME/.config/opencode"
    local source_dir="$CRUX_DIR/scripts"

    # Symlink the scripts directory (lib/, templates/)
    mkdir -p "$config_dir/scripts"

    # Symlink lib/ (Python modules)
    if [ -d "$source_dir/lib" ]; then
        safe_symlink "$source_dir/lib" "$config_dir/scripts/lib"
        local count
        count=$(ls -1 "$source_dir/lib"/*.py 2>/dev/null | grep -v __init__ | wc -l | tr -d ' ')
        success "Linked $count Python scripts from repo → $config_dir/scripts/lib"
    fi

    # Symlink templates/
    if [ -d "$source_dir/templates" ]; then
        safe_symlink "$source_dir/templates" "$config_dir/scripts/templates"
        success "Linked script templates from repo"
    fi

    # Create session and archive directories (user data, not symlinked)
    mkdir -p "$config_dir/scripts/session"
    mkdir -p "$config_dir/scripts/archive"

    # Verify Python 3 is available
    if command -v python3 &>/dev/null; then
        local py_version
        py_version=$(python3 --version 2>&1)
        success "Python: $py_version"
    else
        warn "Python 3 not found. Python scripts will not work until Python 3 is installed."
        warn "Install via: brew install python3"
    fi

    # All scripts use stdlib only — no pip install needed
    info "All Python scripts use stdlib only (no pip dependencies required)"
}

###############################################################################
# STEP 18: CRUX CLI INSTALLATION
###############################################################################

install_crux_cli() {
    header "STEP 18: Installing Crux CLI"

    local bin_source="$CRUX_DIR/bin/crux"

    if [ ! -f "$bin_source" ]; then
        warn "Crux CLI not found at $bin_source — skipping"
        return 0
    fi

    # Determine install location
    local install_dir="/usr/local/bin"
    if [ ! -w "$install_dir" ] 2>/dev/null; then
        install_dir="$HOME/.local/bin"
        mkdir -p "$install_dir"
    fi

    safe_symlink "$bin_source" "$install_dir/crux"

    # Check if install_dir is in PATH
    if echo "$PATH" | tr ':' '\n' | grep -q "^${install_dir}$"; then
        success "Crux CLI linked to $install_dir/crux (already in PATH)"
    else
        # Add to PATH in shell profile
        local shell_profile
        if [[ "$SHELL" == *"zsh"* ]]; then
            shell_profile="$HOME/.zshrc"
        else
            shell_profile="$HOME/.bashrc"
        fi

        if ! grep -q "# Crux: CLI" "$shell_profile" 2>/dev/null; then
            echo "" >> "$shell_profile"
            echo "# Crux: CLI" >> "$shell_profile"
            echo "export PATH=\"$install_dir:\$PATH\"" >> "$shell_profile"
        fi

        success "Crux CLI linked to $install_dir/crux"
        warn "Reload your shell or run: export PATH=\"$install_dir:\$PATH\""
    fi

    # Save CRUX_DIR for the CLI to find the repo
    local shell_profile
    if [[ "$SHELL" == *"zsh"* ]]; then
        shell_profile="$HOME/.zshrc"
    else
        shell_profile="$HOME/.bashrc"
    fi

    if ! grep -q "CRUX_DIR" "$shell_profile" 2>/dev/null; then
        echo "export CRUX_DIR=\"$CRUX_DIR\"" >> "$shell_profile"
        success "Set CRUX_DIR=$CRUX_DIR in $shell_profile"
    fi
}

###############################################################################
# STEP 19: OPTIONAL INTEGRATIONS
###############################################################################

optional_integrations() {
    header "STEP 19: Optional Integrations"

    # Continue.dev
    if ask_yn "Install Continue.dev for IDE integration?"; then
        info "Continue.dev configuration..."
        mkdir -p "$HOME/.continue"

        cat > "$HOME/.continue/config.json" << 'EOF'
{
  "models": [
    {
      "title": "crux-think",
      "provider": "ollama",
      "model": "crux-think",
      "apiBase": "http://localhost:11434",
      "contextLength": 32768
    },
    {
      "title": "crux-chat",
      "provider": "ollama",
      "model": "crux-chat",
      "apiBase": "http://localhost:11434",
      "contextLength": 32768
    }
  ],
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text:v1.5"
  }
}
EOF
        success "Continue.dev configured"
    fi

    # Aider
    if ask_yn "Install and configure Aider (CLI pair programmer)?"; then
        info "Installing Aider..."
        pip install aider-chat &> /dev/null

        mkdir -p "$HOME/.config/aider"
        cat > "$HOME/.config/aider/aider.conf.yaml" << 'EOF'
model: ollama/crux-chat
model-settings-file: ~/.config/aider/models.conf.yaml
pretty: true
auto-commits: true
EOF
        success "Aider configured"
    fi
}

###############################################################################
# STEP 20: VERIFICATION
###############################################################################

verify_installation() {
    header "STEP 20: Verification"

    local checks_passed=0
    local checks_total=0

    # Check Ollama
    checks_total=$((checks_total + 1))
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        success "Ollama service running"
        checks_passed=$((checks_passed + 1))
    else
        error "Ollama service not responding"
    fi

    # Check models
    checks_total=$((checks_total + 1))
    if ollama list 2>/dev/null | grep -q "crux-think"; then
        success "crux-think model available"
        checks_passed=$((checks_passed + 1))
    else
        error "crux-think model not found"
    fi

    checks_total=$((checks_total + 1))
    if ollama list 2>/dev/null | grep -q "crux-chat"; then
        success "crux-chat model available"
        checks_passed=$((checks_passed + 1))
    else
        error "crux-chat model not found"
    fi

    # Check OpenCode
    checks_total=$((checks_total + 1))
    if command -v opencode &> /dev/null; then
        success "OpenCode CLI installed"
        checks_passed=$((checks_passed + 1))
    else
        error "OpenCode CLI not found"
    fi

    # Check config directory
    local config_dir="$HOME/.config/opencode"
    checks_total=$((checks_total + 1))
    if [ -d "$config_dir" ]; then
        success "OpenCode config directory created"
        checks_passed=$((checks_passed + 1))
    else
        error "OpenCode config directory not found"
    fi

    # Check symlinks
    for link_name in modes commands tools plugins lib; do
        checks_total=$((checks_total + 1))
        if [ -L "$config_dir/$link_name" ] && [ -d "$config_dir/$link_name" ]; then
            local target
            target=$(readlink "$config_dir/$link_name")
            success "$link_name → $target"
            checks_passed=$((checks_passed + 1))
        elif [ -d "$config_dir/$link_name" ]; then
            warn "$link_name exists but is not a symlink"
            checks_passed=$((checks_passed + 1))
        else
            error "$link_name missing"
        fi
    done

    # Count modes
    local mode_count
    mode_count=$(ls -1 "$config_dir/modes"/*.md 2>/dev/null | grep -v '_template' | wc -l | tr -d ' ')
    checks_total=$((checks_total + 1))
    if [ "$mode_count" -eq 15 ]; then
        success "All 15 modes available"
        checks_passed=$((checks_passed + 1))
    else
        error "Only $mode_count modes found (expected 15)"
    fi

    # Count commands
    local cmd_count
    cmd_count=$(ls -1 "$config_dir/commands"/*.md 2>/dev/null | wc -l | tr -d ' ')
    checks_total=$((checks_total + 1))
    if [ "$cmd_count" -eq 11 ]; then
        success "All 11 custom commands available"
        checks_passed=$((checks_passed + 1))
    else
        error "Only $cmd_count commands found (expected 11)"
    fi

    # Count tools
    local tool_count
    tool_count=$(ls -1 "$config_dir/tools"/*.js 2>/dev/null | wc -l | tr -d ' ')
    checks_total=$((checks_total + 1))
    if [ "$tool_count" -eq 7 ]; then
        success "All 7 custom tools available"
        checks_passed=$((checks_passed + 1))
    else
        error "Only $tool_count tools found (expected 7)"
    fi

    # Check Node.js dependencies (zod)
    checks_total=$((checks_total + 1))
    if [ -d "$CRUX_DIR/node_modules/zod" ]; then
        success "Node.js dependencies installed (zod)"
        checks_passed=$((checks_passed + 1))
    else
        error "Node.js dependencies missing — run 'npm install' in $CRUX_DIR"
    fi

    # Check AGENTS.md
    checks_total=$((checks_total + 1))
    if [ -e "$config_dir/AGENTS.md" ]; then
        success "AGENTS.md framework linked"
        checks_passed=$((checks_passed + 1))
    else
        error "AGENTS.md not found"
    fi

    # Check knowledge base
    checks_total=$((checks_total + 1))
    if [ -d "$config_dir/knowledge" ]; then
        success "Knowledge base structure created"
        checks_passed=$((checks_passed + 1))
    else
        error "Knowledge base not found"
    fi

    # Check model registry
    checks_total=$((checks_total + 1))
    if [ -f "$config_dir/models/registry.json" ]; then
        success "Model registry created"
        checks_passed=$((checks_passed + 1))
    else
        error "Model registry not found"
    fi

    # Check plugins
    local plugin_count
    plugin_count=$(ls -1 "$config_dir/plugins"/*.js 2>/dev/null | wc -l | tr -d ' ')
    checks_total=$((checks_total + 1))
    if [ "$plugin_count" -ge 5 ]; then
        success "Plugins available ($plugin_count files)"
        checks_passed=$((checks_passed + 1))
    else
        error "Only $plugin_count plugins found (expected 5+)"
    fi

    # Check Python scripts
    checks_total=$((checks_total + 1))
    if [ -d "$config_dir/scripts/lib" ]; then
        local py_count
        py_count=$(ls -1 "$config_dir/scripts/lib"/*.py 2>/dev/null | grep -v __init__ | wc -l | tr -d ' ')
        success "Python scripts available ($py_count files)"
        checks_passed=$((checks_passed + 1))
    else
        error "Python scripts not installed"
    fi

    # Check Crux CLI
    checks_total=$((checks_total + 1))
    if command -v crux &> /dev/null; then
        success "Crux CLI available: $(crux version 2>/dev/null | head -1)"
        checks_passed=$((checks_passed + 1))
    else
        warn "Crux CLI not in PATH (reload your shell)"
    fi

    echo ""
    echo -e "${BOLD}Verification Results:${NC}"
    echo -e "Passed: ${GREEN}$checks_passed${NC}/$checks_total"

    if [ "$checks_passed" -eq "$checks_total" ]; then
        echo -e "${GREEN}All checks passed!${NC}"
    else
        warn "$((checks_total - checks_passed)) checks failed"
    fi
}

###############################################################################
# FINAL SUMMARY
###############################################################################

final_summary() {
    header "Setup Complete!"

    local config_dir="$HOME/.config/opencode"

    echo -e "${CYAN}→${NC} Your Crux system is ready to go!"
    echo ""

    echo -e "${BOLD}Architecture:${NC}"
    echo "  Repo:    $CRUX_DIR"
    echo "  Config:  $config_dir"
    echo "  Update:  crux update (or: cd $CRUX_DIR && git pull)"
    echo ""

    echo -e "${BOLD}Symlinked from repo (auto-update on git pull):${NC}"
    echo "  modes/      → $CRUX_DIR/modes/"
    echo "  plugins/    → $CRUX_DIR/plugins/"
    echo "  tools/      → $CRUX_DIR/tools/"
    echo "  commands/   → $CRUX_DIR/commands/"
    echo "  skills/     → $CRUX_DIR/skills/"
    echo "  scripts/lib → $CRUX_DIR/scripts/lib/"
    echo ""

    echo -e "${BOLD}Available Modes (15 total):${NC}"
    echo "  1. build-py         - Python development (security-first)"
    echo "  2. build-ex         - Elixir/Phoenix development"
    echo "  3. plan             - Software architecture planning"
    echo "  4. infra-architect  - Infrastructure & deployment design"
    echo "  5. review           - Code review (security priority)"
    echo "  6. debug            - Root cause analysis & debugging"
    echo "  7. explain          - Teaching & mentoring"
    echo "  8. analyst          - Data analysis with code"
    echo "  9. writer           - Professional writing"
    echo " 10. psych            - Psychological reflection (ACT/Attachment/Shadow)"
    echo " 11. legal            - Legal research (not advice)"
    echo " 12. strategist       - First principles strategic thinking"
    echo " 13. ai-infra         - LLM infrastructure optimization"
    echo " 14. mac              - macOS systems & troubleshooting"
    echo " 15. docker           - Containers & infrastructure"
    echo ""

    echo -e "${BOLD}Custom Commands (11 total):${NC}"
    echo "  /promote            - Promote script to library"
    echo "  /scripts            - List available scripts"
    echo "  /archive            - Auto-archive old scripts"
    echo "  /log                - View session logs"
    echo "  /init-project       - Initialize new project"
    echo "  /stats              - Usage analytics"
    echo "  /digest             - Daily digest"
    echo "  /propose-mode       - Suggest new mode from drift data"
    echo "  /review-knowledge   - Review knowledge promotion"
    echo "  /review-community   - Review community contributions"
    echo "  /configure-api      - Setup commercial API keys"
    echo ""

    echo -e "${BOLD}Quick Start:${NC}"
    echo "  1. Reload your shell: source ~/.zshrc  (or ~/.bashrc)"
    echo "  2. cd your-project"
    echo "  3. opencode /init-project myapp"
    echo "  4. opencode --mode build-py"
    echo ""

    echo -e "${BOLD}Staying Current:${NC}"
    echo "  crux update         Pull latest + refresh symlinks"
    echo "  crux doctor         Health check your installation"
    echo "  crux version        Show current version"
    echo ""
}

###############################################################################
# MAIN EXECUTION
###############################################################################

main() {
    if [ "$UPDATE_MODE" = true ]; then
        echo -e "${BOLD}${BLUE}Crux — Refreshing installation...${NC}\n"
        info "Running in update mode (non-interactive)"
    else
        clear

        echo -e "${BOLD}${BLUE}"
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║                                                          ║"
        echo "║            Crux Setup - Self-Improving AI OS             ║"
        echo "║                macOS (Apple Silicon)                      ║"
        echo "║                                                          ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo -e "${NC}\n"

        # Check prerequisites
        if [[ "$OSTYPE" != "darwin"* ]]; then
            error "This script is for macOS only"
            exit 1
        fi

        if ! sysctl hw.memsize &> /dev/null; then
            error "Could not detect system hardware"
            exit 1
        fi
    fi

    if [ "$UPDATE_MODE" = true ]; then
        # Update mode: only refresh symlinks and scripts (non-interactive)
        configure_opencode
        install_modes
        install_agents_md
        install_commands
        install_tools
        install_skills
        install_plugins
        install_python_scripts
        install_crux_cli
        verify_installation
    else
        # Full interactive setup
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
    fi

    state_mark "setup_complete"
}

# Run main
main
