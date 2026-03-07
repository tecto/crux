# CRUX VIBE: SELF-SOVEREIGN CONTAINER PLATFORM SPECIFICATION

**Version:** 2.0 (Rewrite)
**Date:** March 2026
**Status:** Technical Specification (MVP Phase)
**Architecture:** User-Funded, Self-Sovereign Infrastructure Orchestration
**Document Classification:** Internal - Proprietary Commercial Product

---

## EXECUTIVE SUMMARY

Crux Vibe is a developer platform that orchestrates user-owned infrastructure rather than managing infrastructure itself. Users provision and control their own VPS instances (on Hetzner, Vultr, or any cloud provider), and Crux Vibe provides the tooling to deploy, manage, and scale applications on those instances.

**Core Value Proposition:**
- Users own their infrastructure (BYOS: Bring Your Own Server)
- Crux Vibe manages provisioning optionally (with transparent markup)
- All code, data, and secrets live on user containers only
- Platform provides orchestration, CI/CD, and developer experience
- No vendor lock-in; users can export and redeploy anytime

**Architecture Principle:** Crux Vibe is a **thin orchestration layer** that connects local development environments (OpenCode + Crux OS + Ollama) to user-controlled cloud containers (Docker + Crux OS + PostgreSQL + Caddy).

**Financial Model:**
- Platform subscription: $9-29/month (based on features)
- Optional managed provisioning: 10-30% markup on Hetzner/Vultr costs
- No per-container fees, no usage-based billing
- Users pay cloud providers directly for compute (BYOS model)

---

## 1. CORE ARCHITECTURE

### 1.1 System Overview Diagram

```
┌─────────────────────────────┐          ┌────────────────────────────────┐
│   LOCAL DEVELOPMENT         │          │   USER'S CLOUD CONTAINER       │
│                             │          │                                │
│ Developer Machine:          │ git push │ Hetzner/Vultr/AWS VPS:         │
│ ┌─────────────────────────┐ │ ──────→ │ ┌──────────────────────────┐   │
│ │ OpenCode CLI            │ │         │ │ Crux OS (Custom Linux)   │   │
│ │ + Crux MCP Server       │ │         │ │ Docker Runtime           │   │
│ │ + Crux OS (local)       │ │         │ │ PostgreSQL 16+           │   │
│ │ + Ollama (local LLM)    │ │         │ │ Caddy/Nginx (reverse     │   │
│ │ + Local git repo        │ │         │ │ proxy, SSL, domains)     │   │
│ │ + .env (API keys)       │ │         │ │ Docker Compose           │   │
│ └─────────────────────────┘ │         │ │ Git hooks (CI/CD)        │   │
│                             │         │ │ Prometheus node exporter │   │
│                             │         │ │ Crux Vibe agent          │   │
│  OR                         │         │ │ (WebSocket to platform)  │   │
│                             │         │ └──────────────────────────┘   │
│ ┌─────────────────────────┐ │         │                                │
│ │ Crux Vibe Web IDE       │ │ WS      │ App Containers:                │
│ │ (Monaco editor)         │ │ ←───→  │ ┌──────────────────────────┐   │
│ │ Terminal, file browser  │ │         │ │ main app container       │   │
│ │ Vibe coding mode        │ │         │ │ (Node/Python/Rust)       │   │
│ │ (runs on Crux Vibe      │ │         │ │ PORT 3000 (internal)     │   │
│ │  but executes on        │ │         │ │ ← Caddy (external)       │   │
│ │  user's container)      │ │         │ └──────────────────────────┘   │
│ └─────────────────────────┘ │         │ ┌──────────────────────────┐   │
│                             │         │ │ Additional app containers│   │
│  login.cruxvibe.dev         │         │ │ (for scaling)            │   │
└─────────────────────────────┘         └────────────────────────────────┘
```

### 1.2 Architecture Layers

**Layer 1: Local Development (User's Machine)**
- OpenCode CLI with Crux MCP Server support
- Local Crux OS installation (safety modes, test framework)
- Ollama for local LLM inference (no API key required)
- Local git repository with `.crux/` configuration directory
- Developer workflows entirely offline-capable

**Layer 2: Crux Vibe Platform (SaaS Control Plane)**
- User authentication & account management
- Container provisioning orchestration (via Hetzner/Vultr API)
- Web IDE (Monaco-based, thin client)
- Dashboard for monitoring, logs, deployment history
- Webhook & notification routing
- DNS management for `.cruxvibe.dev` subdomains
- API for programmatic access
- Billing & plan management

**Layer 3: User's Cloud Container (User-Owned Infrastructure)**
- Crux OS running natively on a Linux container (CX22 or equivalent)
- Docker runtime for application containers
- PostgreSQL 16+ for persistent data
- Caddy/Nginx reverse proxy with automatic SSL
- Git repository with CI/CD hooks
- Metrics collection (Prometheus node exporter)
- Crux Vibe agent (lightweight daemon for real-time sync)

---

## 2. CONTAINER PROVISIONING SYSTEM

### 2.1 Two Provisioning Models

#### Model A: BYOS (Bring Your Own Server)

User has existing VPS instance and provides credentials to Crux Vibe.

**Workflow:**
```
1. User signs up for Crux Vibe
2. Goes to Settings → Add Container
3. Selects "I have a VPS" (BYOS mode)
4. Provides: SSH hostname, username, private key (or password)
5. Crux Vibe connects and runs bootstrap script
6. Container ready in 3-5 minutes
7. User gets web terminal access in Crux Vibe UI
```

**Security:**
- SSH credentials stored encrypted in user's Crux Vibe account
- Private key never transmitted; used only for initial provisioning
- After setup, Crux Vibe uses key-based auth; password deleted
- User can revoke Crux Vibe's SSH access anytime via container settings
- Alternative: User provides IP + port, manually runs bootstrap script locally

#### Model B: Managed Provisioning

Crux Vibe provisions container on behalf of user (10-30% markup on hosting cost).

**Workflow:**
```
1. User signs up for Crux Vibe
2. Goes to Settings → Add Container
3. Selects "Crux Vibe Managed" (managed provisioning)
4. Chooses cloud provider: Hetzner, Vultr, AWS (Phase 2)
5. Chooses server size: CX22 ($4.50/mo), CX31 ($13.50/mo), etc.
6. Crux Vibe calls Hetzner Cloud API with user's API key OR:
   - User pays through Crux Vibe (10% markup)
   - Crux Vibe provisions and owns the container; user has SSH+billing access
7. Container deployed and configured in <5 minutes
8. User can export container or transfer to BYOS anytime
```

**Hetzner Cloud API Integration:**
```python
# Pseudocode
def provision_container(user_id, provider, server_type, name):
    if provider == "hetzner":
        api_key = user.hetzner_api_key  # or Crux Vibe's key if managed
        client = HetznerCloudAPI(api_key)

        # Create server
        server = client.servers.create(
            name=f"{name}-{user_id}",
            server_type=server_type,  # "cx22", "cx31", etc.
            image="ubuntu-22.04",  # or custom Crux OS image
            labels={"crux_vibe_user": user_id},
            automount=True,
            networks=[crux_vibe_network_id]
        )

        # Wait for server to be running
        wait_for_status(server, "running")

        # Run bootstrap script via cloud-init or SSH
        ip = server.public_net.ipv4.ip
        run_bootstrap_script(ip, user_id)

        return {
            "container_id": server.id,
            "ip": ip,
            "status": "ready"
        }
```

**Pricing Model (Managed Mode):**
- CX22 (2 vCPU, 4GB RAM, 40GB disk): Hetzner $4.50/mo → Crux Vibe user $5.00/mo (+10%)
- CX31 (2 vCPU, 8GB RAM, 160GB disk): Hetzner $13.50/mo → Crux Vibe user $14.85/mo (+10%)
- CX51 (4 vCPU, 16GB RAM, 240GB disk): Hetzner $40.50/mo → Crux Vibe user $45.00/mo (+11%)
- Markup covers: API costs, support, infrastructure redundancy, billing overhead
- Transparent pricing: invoice shows Hetzner cost + Crux Vibe markup separately

### 2.2 Container Bootstrap Script

**Execution:**
- User (BYOS) or Crux Vibe (managed) runs a single shell script: `curl https://crux-vibe-cdn.com/bootstrap.sh | bash`
- Script requires: `sudo`, `curl`, Internet access
- Runtime: 3-5 minutes (depends on Internet speed and cloud provider's image loading)

**Bootstrap Script Responsibilities:**

```bash
#!/bin/bash
# Crux Vibe Container Bootstrap Script
# Installs and configures a complete Crux Vibe execution environment

set -e
CONTAINER_ID=$1  # Passed by Crux Vibe platform
USER_ID=$2

# Log to both console and file
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $@" | tee -a /var/log/crux-vibe-bootstrap.log
}

# Step 1: Update system and install base dependencies
log "Step 1: Updating system packages..."
apt-get update && apt-get upgrade -y
apt-get install -y curl wget git build-essential ca-certificates

# Step 2: Install Docker
log "Step 2: Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker root
systemctl enable docker
systemctl start docker

# Step 3: Install Docker Compose
log "Step 3: Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Step 4: Install Crux OS
log "Step 4: Installing Crux OS..."
# Clone Crux OS repo and install system-wide
git clone https://github.com/trinsiklabs/crux.git /opt/crux
cd /opt/crux
make install  # Installs crux command to /usr/local/bin

# Step 5: Configure system paths
log "Step 5: Configuring system paths..."
echo 'export PATH="/opt/crux/bin:$PATH"' >> /etc/profile.d/crux.sh
echo 'export CRUX_MODE="production"' >> /etc/profile.d/crux.sh

# Step 6: Install PostgreSQL
log "Step 6: Installing PostgreSQL 16..."
apt-get install -y postgresql-16 postgresql-contrib-16
systemctl enable postgresql
systemctl start postgresql

# Create Crux Vibe system user and database
sudo -u postgres psql <<EOF
CREATE USER crux_app WITH PASSWORD 'auto-generated-secure-password';
CREATE DATABASE crux_app_db OWNER crux_app;
GRANT ALL PRIVILEGES ON DATABASE crux_app_db TO crux_app;
EOF

# Step 7: Install Caddy (reverse proxy)
log "Step 7: Installing Caddy..."
apt-get install -y caddy
# Caddy config will be provisioned via Crux Vibe API later
systemctl enable caddy
systemctl start caddy

# Step 8: Install Node.js (for example app runtime)
log "Step 8: Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt-get install -y nodejs

# Step 9: Install Python (for example app runtime)
log "Step 9: Installing Python 3.11..."
apt-get install -y python3.11 python3.11-venv python3-pip

# Step 10: Install Rust (for example app runtime)
log "Step 10: Installing Rust..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable

# Step 11: Install monitoring & metrics
log "Step 11: Installing Prometheus node exporter..."
apt-get install -y prometheus-node-exporter
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

# Step 12: Create Crux Vibe directory structure
log "Step 12: Creating directory structure..."
mkdir -p /opt/crux-vibe
mkdir -p /opt/crux-vibe/apps
mkdir -p /opt/crux-vibe/config
mkdir -p /opt/crux-vibe/logs
mkdir -p /opt/crux-vibe/data

# Step 13: Install Crux Vibe agent (WebSocket listener)
log "Step 13: Installing Crux Vibe agent..."
mkdir -p /opt/crux-vibe/agent
cd /opt/crux-vibe/agent
git clone https://github.com/crux-vibe/agent.git .
npm install
npm run build

# Create systemd service for Crux Vibe agent
cat > /etc/systemd/system/crux-vibe-agent.service <<EOF
[Unit]
Description=Crux Vibe Container Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/crux-vibe/agent
ExecStart=/usr/bin/node /opt/crux-vibe/agent/dist/index.js
Environment="CONTAINER_ID=${CONTAINER_ID}"
Environment="USER_ID=${USER_ID}"
Environment="CRUX_VIBE_API=https://api.cruxvibe.dev"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable crux-vibe-agent
systemctl start crux-vibe-agent

# Step 14: Install Git hooks for CI/CD
log "Step 14: Setting up Git hooks..."
mkdir -p /opt/crux-vibe/git-hooks
cat > /opt/crux-vibe/git-hooks/post-receive <<'EOFHOOK'
#!/bin/bash
# Triggered on git push
# Runs CI/CD pipeline

cd /opt/crux-vibe/apps/$(cat /tmp/crux_app_name)
/opt/crux/bin/crux mode:pipeline --config .crux/pipeline.yml
EOFHOOK
chmod +x /opt/crux-vibe/git-hooks/post-receive

# Step 15: Configure firewall
log "Step 15: Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 5432/tcp  # PostgreSQL (internal only - restrict later)
ufw --force enable

# Step 16: Set timezone and NTP
log "Step 16: Configuring time..."
timedatectl set-timezone UTC
systemctl enable systemd-timesyncd
systemctl start systemd-timesyncd

# Step 17: Configure system limits
log "Step 17: Configuring system limits..."
cat >> /etc/security/limits.conf <<EOF
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
EOF

# Step 18: Notify Crux Vibe platform that bootstrap is complete
log "Step 18: Notifying Crux Vibe platform..."
curl -X POST https://api.cruxvibe.dev/containers/${CONTAINER_ID}/bootstrap-complete \
  -H "Authorization: Bearer $(cat /opt/crux-vibe/agent-token)" \
  -H "Content-Type: application/json" \
  -d '{"status": "ready", "ip": "'$(hostname -I | awk '{print $1}')'"}'

log "Bootstrap complete! Container ready for deployment."
```

**Bootstrap Script Input:**
- Passed via cloud-init (managed mode) or SSH (BYOS mode)
- Variables: `CONTAINER_ID`, `USER_ID`
- Idempotent: safe to re-run (won't reinstall existing components)

**Post-Bootstrap:**
- Crux Vibe platform receives "bootstrap-complete" webhook
- User sees container in UI with status "Ready"
- User can now deploy applications

---

## 3. CI/CD PIPELINE (ON-CONTAINER)

### 3.1 Pipeline Architecture

Unlike traditional CI/CD platforms (GitHub Actions, GitLab CI), Crux Vibe's pipeline runs **entirely on the user's container**. This means:

- No external service integration needed
- All source code stays on user's infrastructure
- Pipeline config lives in repo: `.crux/pipeline.yml`
- Pipeline triggered by git push via post-receive hook
- Same safety gates as local Crux OS

**Design Principle:** The container is self-contained and autonomous. It doesn't phone home to Crux Vibe for CI/CD execution; it only notifies Crux Vibe of results.

### 3.2 Pipeline Configuration Format

**.crux/pipeline.yml:**

```yaml
# Crux Vibe CI/CD Pipeline Configuration
version: "1.0"
name: "app-deployment-pipeline"

# Global environment variables
env:
  NODE_ENV: "production"
  LOG_LEVEL: "info"

# Pipeline stages (executed sequentially)
stages:
  - name: "fetch"
    description: "Fetch latest code from git"
    steps:
      - command: "git fetch origin"
      - command: "git reset --hard origin/main"

  - name: "install"
    description: "Install dependencies"
    steps:
      - command: "npm ci"  # or 'pip install -r requirements.txt', 'cargo build', etc.
        timeout: 600
        env:
          NPM_REGISTRY: "https://registry.npmjs.org"

  - name: "test"
    description: "Run test suite (TDD gate)"
    steps:
      - command: "npm run test"
        timeout: 1200
        fail_on_error: true  # Pipeline fails if tests fail
      - command: "npm run test:coverage"
        timeout: 300
        env:
          COVERAGE_THRESHOLD: "80"
    gate: true  # This stage must succeed for pipeline to continue

  - name: "lint"
    description: "Code quality checks"
    steps:
      - command: "npm run lint"
        timeout: 300
      - command: "npm run format:check"
        timeout: 300

  - name: "security"
    description: "Security audit (Crux OS recursive mode)"
    steps:
      - command: "/opt/crux/bin/crux mode:security --recursive --fail-on-high"
        timeout: 600
    gate: true  # Blocks deployment if security fails

  - name: "build"
    description: "Build application"
    steps:
      - command: "npm run build"
        timeout: 600
        env:
          BUILD_TARGET: "production"

  - name: "docker-build"
    description: "Build Docker image"
    steps:
      - command: "docker build -t app:${GIT_COMMIT_SHORT} -f Dockerfile ."
        timeout: 900
      - command: "docker tag app:${GIT_COMMIT_SHORT} app:latest"

  - name: "docker-push"
    description: "Push image to local Docker daemon"
    steps:
      - command: "docker tag app:latest localhost:5000/app:latest"
      - command: "docker push localhost:5000/app:latest"  # Local registry

  - name: "deploy"
    description: "Deploy to production"
    steps:
      - command: "docker-compose -f docker-compose.prod.yml up -d"
        timeout: 300
      - command: "sleep 10 && curl -f http://localhost:3000/health || exit 1"
        timeout: 30

  - name: "health-check"
    description: "Verify application health"
    steps:
      - command: |
          for i in {1..10}; do
            if curl -s -f http://localhost:3000/health > /dev/null; then
              echo "Health check passed"
              exit 0
            fi
            sleep 5
          done
          echo "Health check failed"
          exit 1
        timeout: 60
    gate: true

# Notifications
notifications:
  on_success:
    - type: "email"
      recipients: ["${DEPLOYMENT_EMAIL}"]
      template: "deployment_success"
  on_failure:
    - type: "email"
      recipients: ["${DEPLOYMENT_EMAIL}"]
      template: "deployment_failure"
    - type: "webhook"
      url: "${SLACK_WEBHOOK_URL}"
      payload:
        text: "Deployment failed on branch ${GIT_BRANCH}"

# Rollback configuration
rollback:
  enabled: true
  trigger: "health_check_failure"
  previous_image: "app:previous"
  notification: true
```

### 3.3 Pipeline Execution Flow

**Sequence Diagram:**

```
Developer                Container               Crux Vibe Platform
    │                        │                          │
    ├─────────git push───────→│                          │
    │                        │                          │
    │                        ├─ git post-receive hook  │
    │                        │  (trigger pipeline)     │
    │                        │                          │
    │                        ├─ Stage: fetch           │
    │                        │  git fetch origin       │
    │                        │                          │
    │                        ├─ Stage: install         │
    │                        │  npm ci                 │
    │                        │                          │
    │                        ├─ Stage: test (gate)     │
    │                        │  npm run test           │
    │                        │                          │
    │                        ├─ Stage: security (gate) │
    │                        │  crux mode:security     │
    │                        │                          │
    │                        ├─ Stage: build           │
    │                        │  npm run build          │
    │                        │                          │
    │                        ├─ Stage: docker-build    │
    │                        │  docker build .         │
    │                        │                          │
    │                        ├─ Stage: deploy          │
    │                        │  docker-compose up      │
    │                        │                          │
    │                        ├─ Stage: health-check    │
    │                        │  curl /health           │
    │                        │                          │
    │                        ├────deployment success──→│
    │←── notification (email) ────────────────────────┤
    │                        │                          │
```

### 3.4 Pipeline Runner Implementation

**Location:** `/opt/crux-vibe/pipeline-runner`

```python
#!/usr/bin/env python3
# Pipeline runner - executes stages defined in .crux/pipeline.yml

import yaml
import subprocess
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

class PipelineRunner:
    def __init__(self, config_path: str, container_id: str):
        self.config_path = config_path
        self.container_id = container_id
        self.start_time = datetime.now()
        self.results = []
        self.failed = False

    def load_config(self) -> Dict[str, Any]:
        """Load pipeline config from YAML"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def run_stage(self, stage: Dict[str, Any]) -> bool:
        """Execute a single pipeline stage"""
        stage_name = stage['name']
        print(f"\n{'='*60}")
        print(f"Stage: {stage_name}")
        print(f"{'='*60}\n")

        stage_result = {
            "name": stage_name,
            "start_time": datetime.now().isoformat(),
            "steps": []
        }

        for step in stage.get('steps', []):
            command = step['command']
            timeout = step.get('timeout', 300)
            env = step.get('env', {})
            fail_on_error = step.get('fail_on_error', True)

            print(f"  → Running: {command}")

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    timeout=timeout,
                    capture_output=True,
                    text=True,
                    env={**subprocess.os.environ, **env}
                )

                step_result = {
                    "command": command,
                    "returncode": result.returncode,
                    "stdout": result.stdout[-500:] if result.stdout else "",  # Last 500 chars
                    "stderr": result.stderr[-500:] if result.stderr else "",
                    "duration": time.time()
                }

                if result.returncode != 0:
                    print(f"    ✗ Failed (exit code {result.returncode})")
                    if fail_on_error:
                        step_result['status'] = 'failed'
                        stage_result['steps'].append(step_result)
                        stage_result['status'] = 'failed'
                        self.results.append(stage_result)
                        self.failed = True
                        return False
                else:
                    print(f"    ✓ Success")
                    step_result['status'] = 'success'

                stage_result['steps'].append(step_result)

            except subprocess.TimeoutExpired:
                print(f"    ✗ Timeout after {timeout}s")
                step_result = {
                    "command": command,
                    "status": "timeout",
                    "timeout": timeout
                }
                stage_result['steps'].append(step_result)
                stage_result['status'] = 'failed'
                self.results.append(stage_result)
                self.failed = True
                return False

        stage_result['status'] = 'success'
        stage_result['end_time'] = datetime.now().isoformat()
        self.results.append(stage_result)
        return True

    def run_pipeline(self):
        """Execute full pipeline"""
        config = self.load_config()

        print(f"Starting pipeline: {config['name']}")
        print(f"Pipeline version: {config['version']}")

        for stage in config.get('stages', []):
            is_gate = stage.get('gate', False)

            if not self.run_stage(stage):
                if is_gate:
                    print(f"\n✗ Pipeline failed at gate: {stage['name']}")
                    self.send_notification(config, 'failure')
                    return False
                else:
                    print(f"\n⚠ Stage failed (non-gating): {stage['name']}")
                    continue

        print(f"\n✓ Pipeline completed successfully!")
        self.send_notification(config, 'success')
        return True

    def send_notification(self, config: Dict, status: str):
        """Send notifications after pipeline completion"""
        notifications = config.get('notifications', {})

        if status == 'success':
            targets = notifications.get('on_success', [])
        else:
            targets = notifications.get('on_failure', [])

        for target in targets:
            if target['type'] == 'email':
                # Send email notification
                self.send_email(target, status)
            elif target['type'] == 'webhook':
                # Send webhook notification
                self.send_webhook(target, status)

    def send_email(self, config: Dict, status: str):
        """Send email notification"""
        # Implementation uses SendGrid or local MTA
        pass

    def send_webhook(self, config: Dict, status: str):
        """Send webhook notification (e.g., Slack)"""
        import requests
        payload = config.get('payload', {})
        payload['status'] = status
        requests.post(config['url'], json=payload)

if __name__ == '__main__':
    config_path = '.crux/pipeline.yml'
    container_id = sys.argv[1] if len(sys.argv) > 1 else 'unknown'

    runner = PipelineRunner(config_path, container_id)
    success = runner.run_pipeline()

    sys.exit(0 if success else 1)
```

### 3.5 Git Hook Setup

**File: `/opt/crux-vibe/git-hooks/post-receive`**

```bash
#!/bin/bash
# Git post-receive hook - triggered when user pushes to origin/main
# Runs on the container itself

set -e

# Parse pushed refs
while read oldrev newrev refname; do
  BRANCH=$(git rev-parse --symbolic --abbrev-ref "$refname")

  # Only run pipeline on main/master branch
  if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
    echo "────────────────────────────────────────"
    echo "Crux Vibe CI/CD Pipeline Triggered"
    echo "Branch: $BRANCH"
    echo "Commit: $newrev"
    echo "────────────────────────────────────────"

    # Change to app directory
    cd /opt/crux-vibe/apps/$(cat /tmp/crux_app_name)

    # Run pipeline runner
    /usr/bin/python3 /opt/crux-vibe/pipeline-runner/.crux/pipeline.yml $BRANCH

    PIPELINE_EXIT=$?

    if [ $PIPELINE_EXIT -eq 0 ]; then
      echo ""
      echo "✓ Pipeline succeeded. Application deployed."
      echo ""
    else
      echo ""
      echo "✗ Pipeline failed. See logs above."
      echo ""
      exit 1
    fi
  fi
done
```

**Hook Installation:**
```bash
# User runs during container setup
git config --global core.hooksPath /opt/crux-vibe/git-hooks
chmod +x /opt/crux-vibe/git-hooks/post-receive
```

---

## 4. LOCAL ↔ CLOUD WORKFLOW

### 4.1 Development Modes

**Mode 1: Pure Local Development (Offline)**
```
Developer → OpenCode + Crux OS (local) + Ollama
↓
`git commit` and test locally
↓
`git push` → Deploys to container via CI/CD
↓
Container sends deployment status back to Crux Vibe UI
```

**Mode 2: Web IDE (Vibe Coding)**
```
Developer logs into Crux Vibe (login.cruxvibe.dev)
↓
Opens Crux Vibe Web IDE (Monaco editor)
↓
Web IDE connects to user's container via WebSocket
↓
All commands execute on container (terminal, file ops, vibe coding)
↓
Changes appear in real-time on container
↓
User can commit and push from web IDE or local CLI
```

**Mode 3: Hybrid (Local + Web)**
```
Developer works locally in OpenCode + Crux OS
↓
Makes changes, commits
↓
Can optionally open Crux Vibe web IDE to deploy or monitor
↓
Seamless switching between local CLI and web IDE
↓
Git syncs both environments
```

### 4.2 Git-Based Sync Architecture

**Assumption:** User has git repository synced across local machine and container.

**Setup:**
```bash
# On local machine
git remote add origin git@container.ip:repos/app.git
git remote add upstream https://github.com/myrepo.git  # Optional

# On container
mkdir -p /opt/crux-vibe/repos
cd /opt/crux-vibe/repos
git init --bare app.git
cd app.git
# Set up post-receive hook for CI/CD (see Section 3.5)
```

**Push Workflow:**
```
Local machine:
  git add .
  git commit -m "Add user auth system"
  git push origin main

Container receives push → post-receive hook triggers → CI/CD pipeline
↓
Pipeline stages: test (gate) → security (gate) → build → deploy → health-check
↓
Pipeline completes: success/failure notification sent
↓
Crux Vibe platform receives webhook with status
↓
User sees deployment status in Crux Vibe dashboard
↓
If failed: rollback to previous container version automatically
```

**Pull Workflow (rare in this model):**
```
Developer wants to pull latest from container (e.g., after debugging via web IDE):
  git pull origin main
```

### 4.3 State Synchronization

**What stays on container:**
- Application code (git repo)
- `.env` file with API keys, database credentials, secrets
- PostgreSQL database
- Deployed Docker containers and volumes
- Application logs
- Metrics and monitoring data

**What stays on local machine:**
- Local `.env` (for local Ollama, local testing)
- Development dependencies (npm, Python, Rust toolchains)
- IDE configuration
- Local Crux OS installation

**What syncs via git:**
- Source code (obviously)
- `.crux/` configuration directory (pipeline.yml, modes, security rules)
- `docker-compose.yml` and `Dockerfile`
- Test specs
- Documentation

**What does NOT sync (security):**
- Production `.env` with API keys (developer imports manually via Crux Vibe UI)
- Database backups (managed by container automatically)
- Container SSH keys (generated and stored only on container)

### 4.4 Conflict Resolution

If developer and container have diverged:

```bash
# Local machine detects conflict on git push
# Crux Vibe platform rejects push and returns error

git status  # Shows diverged branches

# Option 1: Developer pulls and resolves
git pull origin main
# ... resolve conflicts ...
git push origin main

# Option 2: Developer resets to container version
git reset --hard origin/main

# Option 3: Developer uses Crux Vibe web IDE to resolve
# Opens Crux Vibe UI → Web Terminal → git merge/rebase
```

---

## 5. CRUX VIBE WEB IDE

### 5.1 Architecture & Design Principles

The Crux Vibe Web IDE is a **thin client** that connects to the user's container via **WebSocket**. It does NOT run any compute on Crux Vibe's servers.

**Key Principle:** All code execution happens on the user's container. The web IDE is purely a UI for interacting with that container.

**Tech Stack:**
- Frontend: React + Monaco Editor (VS Code's editor)
- Connection: WebSocket to Crux Vibe agent on container
- Backend: Crux Vibe API (authentication, billing, logs)

### 5.2 Web IDE Components

```
┌─────────────────────────────────────────────────────────┐
│ Crux Vibe Web IDE (login.cruxvibe.dev/ide/{app_id})     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────────────┬─────────────────────────────┐   │
│ │ File Browser        │                             │   │
│ │ ├─ src/             │ Monaco Editor               │   │
│ │ ├─ public/          │ ┌─────────────────────────┐ │   │
│ │ ├─ tests/           │ │ (Current file content)   │ │   │
│ │ ├─ .crux/           │ │                         │ │   │
│ │ │  ├─ pipeline.yml  │ │ Syntax highlighting,     │ │   │
│ │ │  └─ modes/        │ │ autocomplete, git diff   │ │   │
│ │ ├─ docker-compose   │ │                         │ │   │
│ │ ├─ Dockerfile       │ │                         │ │   │
│ │ └─ .env (hidden)    │ └─────────────────────────┘ │   │
│ │                     │                             │   │
│ └─────────────────────┴─────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Terminal (xterm.js)                                 │   │
│ │                                                     │   │
│ │ $ npm run test                                      │   │
│ │ > Running 45 tests...                              │   │
│ │ ✓ User authentication (234ms)                       │   │
│ │ ✓ API rate limiting (156ms)                         │   │
│ │ ...                                                 │   │
│ │ $                                                   │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                         │
│ ┌──────────────────────┬────────────────────────────┐   │
│ │ Logs                 │ Deployment History         │   │
│ │                      │                            │   │
│ │ [14:23:01] Deploy... │ ✓ v1.2.3 - 2 hours ago     │   │
│ │ [14:23:45] Test...   │ ✗ v1.2.2 - 5 hours ago     │   │
│ │ [14:24:30] Success   │ ✓ v1.2.1 - 1 day ago       │   │
│ │                      │                            │   │
│ └──────────────────────┴────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Git Integration                                     │   │
│ │ Branch: main | Status: 3 changes staged             │   │
│ │ [Commit Message] [Commit] [Push] [Pull]             │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Vibe Coding Mode (Natural Language)                 │   │
│ │ [Tell Crux what to build...]                        │   │
│ │ > "Add email verification to signup flow"           │   │
│ │ ✓ Analyzed requirements                             │   │
│ │ ✓ Generated test specs                              │   │
│ │ ✓ Implemented feature                               │   │
│ │ ✓ Security audit passed                             │   │
│ │ [Ready to deploy] [Review changes] [Discard]        │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 5.3 WebSocket Protocol

**Connection Handshake:**

```javascript
// Client (web IDE) connects
const ws = new WebSocket('wss://crux-vibe-agent.container-ip:9443/ws');

ws.onopen = () => {
  // Send authentication
  ws.send(JSON.stringify({
    type: 'auth',
    token: localStorage.getItem('crux_session_token'),
    container_id: location.pathname.split('/')[3]
  }));
};
```

**Message Types:**

```typescript
// File Operations
{
  "type": "file:read",
  "path": "src/index.js",
  "id": "msg_123"
}
→ Response:
{
  "type": "file:read:response",
  "id": "msg_123",
  "content": "import Express from 'express'...",
  "mtime": 1678953600000
}

// Terminal Commands
{
  "type": "terminal:exec",
  "command": "npm run test",
  "id": "msg_124"
}
→ Response (streaming):
{
  "type": "terminal:output",
  "id": "msg_124",
  "stdout": "✓ Test 1 passed\n",
  "stderr": ""
}

// Git Operations
{
  "type": "git:status",
  "id": "msg_125"
}
→ Response:
{
  "type": "git:status:response",
  "id": "msg_125",
  "branch": "main",
  "modified": ["src/app.js"],
  "staged": ["src/index.js"]
}

// Vibe Coding
{
  "type": "vibe:generate",
  "prompt": "Add user authentication",
  "id": "msg_126"
}
→ Response (streaming):
{
  "type": "vibe:progress",
  "id": "msg_126",
  "stage": "plan",
  "status": "Analyzing requirements..."
}
```

### 5.4 Vibe Coding via Web IDE

**Flow:**

```
User: "Add email verification to signup flow"
↓
Web IDE sends to container's Crux Vibe agent
↓
Agent routes to OpenCode + Crux OS modes (on container)
↓
Crux OS runs: plan → test → build → security
↓
Results streamed back to web IDE
↓
User sees code changes in editor
↓
User clicks "Ready to deploy" or "Discard"
↓
If deploy: git add + commit + push + CI/CD pipeline
↓
Notification sent to Crux Vibe platform
```

**Implementation (Crux Vibe Agent):**

```typescript
// /opt/crux-vibe/agent/src/handlers.ts

export async function handleVibeCoding(
  ws: WebSocket,
  message: VibeMessage
) {
  const { prompt, id } = message;
  const { app_id } = ws.auth_data;

  // Step 1: Plan mode
  ws.send(JSON.stringify({
    type: 'vibe:progress',
    id,
    stage: 'plan',
    status: 'Analyzing requirements...'
  }));

  const plan = await execCruxMode(app_id, 'plan', {
    prompt,
    context: 'new_feature'
  });

  // Step 2: Test mode
  ws.send(JSON.stringify({
    type: 'vibe:progress',
    id,
    stage: 'test',
    status: 'Writing test specs...'
  }));

  const tests = await execCruxMode(app_id, 'test', {
    plan,
    framework: 'jest'  // Auto-detected from package.json
  });

  // Step 3: Build mode
  ws.send(JSON.stringify({
    type: 'vibe:progress',
    id,
    stage: 'build',
    status: 'Implementing feature...'
  }));

  const implementation = await execCruxMode(app_id, 'build-js', {
    plan,
    tests,
    target_language: 'typescript'
  });

  // Step 4: Security audit
  ws.send(JSON.stringify({
    type: 'vibe:progress',
    id,
    stage: 'security',
    status: 'Running security audit...'
  }));

  const securityResult = await execCruxMode(app_id, 'security', {
    files: implementation.modified_files,
    recursive: true
  });

  if (securityResult.severity === 'high') {
    ws.send(JSON.stringify({
      type: 'vibe:error',
      id,
      message: 'Security audit found issues. Review and fix manually.'
    }));
    return;
  }

  // Step 5: Return results
  ws.send(JSON.stringify({
    type: 'vibe:complete',
    id,
    files_changed: implementation.modified_files,
    tests_added: tests.test_files,
    ready_to_deploy: securityResult.severity !== 'high'
  }));

  // Update file system with changes
  await fs.promises.writeFile(
    `/opt/crux-vibe/apps/${app_id}/${implementation.files[0]}`,
    implementation.content[0]
  );
}
```

---

## 6. CRUX MCP SERVER & OPENCODE INTEGRATION

### 6.1 What is Crux MCP?

**Crux MCP Server** is a Model Context Protocol (MCP) server that integrates Crux OS modes with OpenCode. It exposes Crux modes (plan, test, build, security, etc.) as MCP tools that OpenCode can call.

**MCP Spec:** https://spec.modelcontextprotocol.io/

### 6.2 MCP Server Architecture

**Location:** `/opt/crux/mcp-server`

```python
#!/usr/bin/env python3
# Crux MCP Server - provides Crux OS modes as MCP tools

import json
import sys
from typing import Any, Dict, List

class CruxMCPServer:
    def __init__(self):
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define MCP tools that OpenCode can call"""
        return [
            {
                "name": "mode:plan",
                "description": "Generate architecture and test specifications",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Feature request or problem description"
                        },
                        "language": {
                            "type": "string",
                            "description": "Target language (python, javascript, rust, go)",
                            "enum": ["python", "javascript", "rust", "go"]
                        },
                        "context": {
                            "type": "string",
                            "description": "Project context (new_project, existing_codebase, add_feature)"
                        }
                    },
                    "required": ["prompt", "language"]
                }
            },
            {
                "name": "mode:test",
                "description": "Generate comprehensive test specifications",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "string",
                            "description": "Output from mode:plan"
                        },
                        "framework": {
                            "type": "string",
                            "description": "Test framework (jest, pytest, vitest, etc.)",
                            "enum": ["jest", "pytest", "vitest", "unittest", "rspec"]
                        },
                        "coverage_target": {
                            "type": "number",
                            "description": "Minimum coverage threshold (0-100)",
                            "default": 80
                        }
                    },
                    "required": ["plan"]
                }
            },
            {
                "name": "mode:build-python",
                "description": "Generate Python implementation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "string",
                            "description": "Output from mode:plan"
                        },
                        "tests": {
                            "type": "string",
                            "description": "Output from mode:test"
                        },
                        "framework": {
                            "type": "string",
                            "description": "Web framework (fastapi, flask, django)",
                            "enum": ["fastapi", "flask", "django"]
                        }
                    },
                    "required": ["plan"]
                }
            },
            {
                "name": "mode:build-javascript",
                "description": "Generate JavaScript/TypeScript implementation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "string",
                            "description": "Output from mode:plan"
                        },
                        "tests": {
                            "type": "string",
                            "description": "Output from mode:test"
                        },
                        "framework": {
                            "type": "string",
                            "description": "Web framework (express, next, fastify)",
                            "enum": ["express", "next", "fastify", "remix"]
                        },
                        "typescript": {
                            "type": "boolean",
                            "description": "Use TypeScript",
                            "default": True
                        }
                    },
                    "required": ["plan"]
                }
            },
            {
                "name": "mode:security",
                "description": "Run security audit with recursive analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Files to audit"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Run recursive security analysis",
                            "default": True
                        },
                        "severity_level": {
                            "type": "string",
                            "description": "Report issues at this level and above",
                            "enum": ["low", "medium", "high", "critical"],
                            "default": "medium"
                        }
                    },
                    "required": ["files"]
                }
            },
            {
                "name": "mode:knowledge",
                "description": "Query knowledge base about Crux patterns",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'how to implement rate limiting')"
                        },
                        "category": {
                            "type": "string",
                            "description": "Knowledge category",
                            "enum": ["architecture", "security", "performance", "testing", "deployment"]
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "mode:correct",
                "description": "Detect and correct errors in code",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to analyze"
                        },
                        "error_message": {
                            "type": "string",
                            "description": "Error or failure message"
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "enum": ["python", "javascript", "rust", "go"]
                        }
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "name": "mode:sync",
                "description": "Sync knowledge base between local and container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "description": "Sync direction",
                            "enum": ["local_to_container", "container_to_local", "bidirectional"],
                            "default": "bidirectional"
                        }
                    }
                }
            }
        ]

    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process MCP tool call from OpenCode"""
        method = request.get('method')

        if method == 'tools/list':
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": self.tools
                }
            }

        elif method == 'tools/call':
            tool_name = request['params']['name']
            tool_input = request['params']['arguments']

            # Execute the corresponding Crux mode
            result = self._execute_mode(tool_name, tool_input)

            return {
                "jsonrpc": "2.0",
                "result": {
                    "type": "text",
                    "text": result
                }
            }

    def _execute_mode(self, tool_name: str, inputs: Dict) -> str:
        """Execute Crux OS mode"""
        import subprocess

        # Build command
        cmd = ['/opt/crux/bin/crux', f'mode:{tool_name.split(":")[1]}']

        # Add inputs as flags
        for key, value in inputs.items():
            if isinstance(value, bool):
                if value:
                    cmd.append(f'--{key}')
            elif isinstance(value, list):
                for item in value:
                    cmd.append(f'--{key}')
                    cmd.append(item)
            else:
                cmd.append(f'--{key}')
                cmd.append(str(value))

        # Execute
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"Crux mode failed: {result.stderr}")

def main():
    server = CruxMCPServer()

    # Read JSON-RPC requests from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = server.process_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }))

if __name__ == '__main__':
    main()
```

### 6.3 OpenCode Integration

**OpenCode Configuration (`.opencode/config.json`):**

```json
{
  "mcp_servers": [
    {
      "name": "crux",
      "command": "/opt/crux/bin/crux",
      "args": ["mcp-server"],
      "env": {
        "CRUX_MODE": "development"
      }
    }
  ],
  "default_modes": {
    "python": ["mode:plan", "mode:test", "mode:build-python", "mode:security"],
    "javascript": ["mode:plan", "mode:test", "mode:build-javascript", "mode:security"],
    "rust": ["mode:plan", "mode:test", "mode:build-rust", "mode:security"]
  }
}
```

**Example OpenCode Workflow:**

```
User: "Build a user authentication system with JWT tokens"

OpenCode calls Crux MCP:
1. mode:plan
   Input: { prompt: "...", language: "python", context: "existing_codebase" }
   Output: Architecture spec + test requirements

2. mode:test
   Input: { plan: "...", framework: "pytest", coverage_target: 90 }
   Output: Test file specifications

3. mode:build-python
   Input: { plan: "...", tests: "...", framework: "fastapi" }
   Output: Implementation (auth.py, models.py, routes.py, etc.)

4. mode:security
   Input: { files: ["auth.py", "models.py", "routes.py"], recursive: true }
   Output: Security audit report

OpenCode displays results and saves to local filesystem

User: git push origin main

Container receives push → CI/CD pipeline → deploys
```

### 6.4 Knowledge Base Sync

**Crux OS maintains a local knowledge base** of patterns, best practices, and solutions. This KB can sync between local and container environments.

**KB Structure:**

```
.crux/knowledge-base/
├── patterns/
│   ├── authentication.md
│   ├── api-design.md
│   ├── database-migrations.md
│   └── error-handling.md
├── security/
│   ├── owasp-top-10.md
│   ├── secrets-management.md
│   └── input-validation.md
├── performance/
│   ├── caching-strategies.md
│   ├── database-optimization.md
│   └── async-patterns.md
└── examples/
    ├── jwt-auth-fastapi/
    ├── rest-api-nodejs/
    └── websocket-realtime/
```

**Sync Mechanism:**

```bash
# Local machine
crux mode:sync --direction local_to_container

# Container
crux mode:sync --direction container_to_local

# Bidirectional (merge strategy for conflicts)
crux mode:sync --direction bidirectional --merge-strategy prefer_local
```

---

## 7. SELF-HOSTED POSTGRESQL

### 7.1 Default Installation

Every container automatically gets PostgreSQL 16 installed during bootstrap with:

- Single-node setup (Phase 1)
- `postgres` superuser (no password, trusted local connection)
- `crux_app` user (auto-generated password) for application use
- `crux_app_db` database

**Connection String (auto-generated):**
```
postgresql://crux_app:{password}@localhost:5432/crux_app_db
```

**Stored in:** `/opt/crux-vibe/config/database-url.env`

### 7.2 Backup & Recovery

**Automated Backup Script (runs daily via cron):**

```bash
#!/bin/bash
# Daily PostgreSQL backup

BACKUP_DIR="/opt/crux-vibe/data/backups"
DB_NAME="crux_app_db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Full database dump
pg_dump -U postgres $DB_NAME | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$TIMESTAMP.sql.gz"
```

**Cron Job:**
```
0 2 * * * /opt/crux-vibe/scripts/backup-postgres.sh >> /var/log/crux-vibe-backup.log 2>&1
```

**Recovery:**
```bash
gunzip < /opt/crux-vibe/data/backups/backup_20260305_020000.sql.gz | psql -U postgres crux_app_db
```

### 7.3 Monitoring & Performance

**Connection Pooling (via PgBouncer - Phase 1 optional):**

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
crux_app_db = host=localhost port=5432 dbname=crux_app_db

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
```

**Metrics Collection (Prometheus):**

```bash
# PostgreSQL exporter installation
apt-get install prometheus-postgres-exporter

# Systemd service configured to scrape PostgreSQL metrics
# Metrics available at: http://localhost:9187/metrics
```

---

## 8. DOMAIN & SSL MANAGEMENT

### 8.1 Domain Configuration

**Option 1: Crux Vibe-Managed Subdomain (Default)**

```
User's app gets: myapp.cruxvibe.dev
↓
Crux Vibe manages DNS A record → container IP
↓
Automatic SSL via Let's Encrypt
↓
User sees in Crux Vibe dashboard
```

**Option 2: Custom Domain (User-Owned)**

```
User has: myapp.example.com
↓
User points DNS to container IP via Crux Vibe UI instructions:
  A record: myapp.example.com → 1.2.3.4 (container IP)
↓
Caddy auto-detects and provisions SSL
↓
User's domain resolves to their app
```

### 8.2 SSL Certificate Management

**Tool:** Caddy (v2+) with automatic Let's Encrypt integration

**Caddy Configuration (auto-generated):**

```
# /etc/caddy/Caddyfile

{
  email admin@cruxvibe.dev
  storage file_system /opt/caddy-storage
}

myapp.cruxvibe.dev {
  reverse_proxy localhost:3000 {
    header_uri -x-forwarded-for
    header_uri x-forwarded-for {remote_host}
    header_uri x-forwarded-proto {scheme}
  }
}

example.com {
  reverse_proxy localhost:3000
}
```

**Certificate Renewal (automatic):**
- Caddy monitors certificate expiry
- Renews 30 days before expiration
- Zero downtime
- Metrics exposed to Prometheus

### 8.3 Wildcard SSL for Subdomains

**For apps with multiple subdomains** (e.g., `api.myapp.com`, `admin.myapp.com`):

```
# /etc/caddy/Caddyfile

*.example.com {
  tls {
    dns route53
  }
  reverse_proxy localhost:3000
}
```

Requires user to authorize Caddy to access DNS (e.g., AWS Route53 credentials).

---

## 9. USER API KEY MANAGEMENT

### 9.1 Local Development

**File:** `~/.crux-vibe/.env.local` (or project-level `.env`)

```bash
# ~/.crux-vibe/.env.local
ANTHROPIC_API_KEY=sk-xxx...
OLLAMA_API_KEY=  # (Empty if using local Ollama)
DATABASE_URL=postgresql://localhost/crux_app_db
```

**Security:**
- Never committed to git
- Added to `.gitignore`
- OpenCode loads from `~/.crux-vibe/.env.local` by default
- Crux OS modes use key for API calls locally

### 9.2 Container API Key Vault

**When using Vibe Coding via Web IDE:**

```
User logs into Crux Vibe Web IDE
↓
UI prompts: "Enter your Anthropic API key for AI-powered coding"
↓
Key transmitted via HTTPS to Crux Vibe API
↓
Crux Vibe forwards to Crux Vibe agent on container
↓
Agent stores key in encrypted vault: /opt/crux-vibe/secrets/vault.enc
↓
Vault accessed only by Crux Vibe agent + Crux OS on container
```

**Vault Implementation:**

```python
# /opt/crux-vibe/agent/vault.py

from cryptography.fernet import Fernet
import json
import os

class SecretVault:
    def __init__(self):
        # Load vault key from system (set during container bootstrap)
        self.cipher_key = os.environ.get('VAULT_KEY')
        if not self.cipher_key:
            raise Exception("VAULT_KEY not set")
        self.cipher = Fernet(self.cipher_key)
        self.vault_path = '/opt/crux-vibe/secrets/vault.json.enc'

    def set_secret(self, key: str, value: str):
        """Store encrypted secret"""
        data = self.load_vault()
        data[key] = value
        encrypted = self.cipher.encrypt(json.dumps(data).encode())
        with open(self.vault_path, 'wb') as f:
            f.write(encrypted)

    def get_secret(self, key: str) -> str:
        """Retrieve encrypted secret"""
        data = self.load_vault()
        return data.get(key)

    def load_vault(self) -> dict:
        """Load and decrypt vault"""
        if not os.path.exists(self.vault_path):
            return {}
        with open(self.vault_path, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
```

**Access Control:**
- Only Crux Vibe agent can read/write vault
- Vault key stored in container's secure boot environment (similar to cloud provider's instance metadata)
- User never sees plaintext key in logs
- Vault revoked when container is destroyed

### 9.3 Alternative: Zero-Cost Ollama

**For users who don't want to provide an API key:**

```bash
# During container bootstrap, install Ollama
curl https://ollama.ai/install.sh | sh
ollama pull mistral:latest

# Crux OS uses Ollama locally (no API key needed)
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
```

**Trade-off:** Slower AI inference, but completely free and private.

---

## 10. MULTI-CONTAINER SCALING

### 10.1 Default: Single Container (Everything-in-One)

**Phase 1 Architecture:**
```
User's Container (CX22, $4.50/mo):
├─ App Container (Node/Python/Rust)
├─ PostgreSQL (embedded)
├─ Redis (optional, embedded)
├─ Caddy (reverse proxy)
└─ CI/CD Pipeline
```

**Sufficient for:** Up to 10k requests/day, typical MVP apps

### 10.2 Multi-Container Scaling (Phase 2)

**When user hits traffic limits:**

```
User clicks "Scale App" in Crux Vibe Dashboard
↓
Crux Vibe suggests: "Add 2 more app containers"
↓
Creates 2 new CX22 instances cloned from main container
↓
Sets up Hetzner Load Balancer ($5/mo)
↓
Architecture:

┌──────────────────────────────────┐
│   Hetzner Load Balancer          │
│   (myapp.com:443 → 3 containers) │
└──────────────────────────────────┘
         ↓         ↓         ↓
    ┌────────┬────────┬────────┐
    │        │        │        │
   [CX22]  [CX22]  [CX22]   [Database-only CX51]
   App1    App2    App3     (PostgreSQL)
   (Read-only)

All 3 app containers share PostgreSQL on DB container
```

**Container Cloning:**

```bash
#!/bin/bash
# Clone app container from master image

HN_API_KEY=$1
SOURCE_IMAGE_ID=$2

# Create new server from image
hcloud server create \
  --type cx22 \
  --image $SOURCE_IMAGE_ID \
  --name app-replica-$(date +%s) \
  --labels role=app-server

# All files, configs, Docker images present
# Only needs to connect to shared database
```

**Load Balancing Configuration:**

```
Hetzner Load Balancer HTTP(S) settings:
├─ Frontend: 0.0.0.0:80, 0.0.0.0:443 (public)
├─ Backend Service: "app-servers"
│  └─ Targets: [app1-ip:3000, app2-ip:3000, app3-ip:3000]
│  └─ Health Check: GET /health (3s interval)
│  └─ Algorithm: Round-Robin
└─ SSL Certificate: Let's Encrypt (auto-managed)
```

**Sticky Sessions (if needed):**

```
# Caddy configuration for session affinity
app.example.com {
  lb_policy least_conn  # Route to least-busy server
  lb_try_duration 2000ms
  lb_try_interval 250ms

  reverse_proxy backend1:3000 backend2:3000 backend3:3000 {
    policy random_choose 2  # Probabilistic load balancing
  }
}
```

---

## 11. MONITORING & BILLING

### 11.1 Container Metrics Collection

**Prometheus Node Exporter** (installed by default):

```bash
# Metrics endpoint: http://localhost:9100/metrics

# Key metrics collected:
- CPU usage (%)
- Memory usage (bytes, %)
- Disk I/O (read/write bytes)
- Network I/O (bytes sent/received)
- Process count
- System load average
```

**Lightweight Monitoring UI (Phase 1):**

Crux Vibe Dashboard shows:

```
Container: myapp (CX22)
├─ Uptime: 45 days
├─ CPU: 12% (4 cores)
├─ Memory: 2.1 GB / 4 GB (52%)
├─ Disk: 18 GB / 40 GB (45%)
├─ Network: ↓ 2.3 MB/s ↑ 1.2 MB/s
├─ Requests/day: 8,234
├─ Error rate: 0.3%
└─ Last deployment: 2 hours ago
```

**API for Metrics:**

```
GET https://api.cruxvibe.dev/containers/{id}/metrics?range=24h

Response:
{
  "container_id": "cx22-abc123",
  "metrics": {
    "cpu_usage_percent": [12, 14, 11, 13, ...],
    "memory_usage_bytes": [2100000000, 2200000000, ...],
    "network_in_bytes": [1024000, 1124000, ...],
    "network_out_bytes": [512000, 612000, ...],
    "disk_usage_bytes": [18000000000, ...],
    "request_count": 342,
    "error_count": 1
  },
  "timestamp": "2026-03-05T14:30:00Z"
}
```

### 11.2 Billing Model

**Crux Vibe Platform Subscription:**

```
Tier 1: Starter     - $9/month
├─ 1 container
├─ 5 GB storage
├─ Basic metrics
├─ Email support

Tier 2: Professional - $19/month
├─ Up to 3 containers
├─ 50 GB storage
├─ Advanced metrics + alerting
├─ Slack/webhook integrations
├─ Priority email support

Tier 3: Teams - $49/month
├─ Unlimited containers
├─ Unlimited storage
├─ All features
├─ Team management (10 users)
├─ 24/7 support
```

**Infrastructure Costs (BYOS Mode):**

User pays cloud provider directly:
- Hetzner CX22: $4.50/month (user's bill)
- Hetzner Load Balancer: $5/month (if scaling)
- Domains: varies (user registrar)

**Infrastructure Costs (Managed Mode):**

Crux Vibe charges markup:
```
Hetzner CX22 ($4.50) → Crux Vibe user ($5.00) [+10% markup]
Hetzner LB ($5.00) → Crux Vibe user ($5.50) [+10% markup]

Breakdown:
├─ Hetzner actual cost: $4.50
├─ Crux Vibe processing: $0.30
├─ Crux Vibe infra/support: $0.20
└─ Crux Vibe profit: $0.00 (neutral on low tiers, profit on premium)
```

**Transparent Invoicing:**

```
Crux Vibe Invoice (March 2026)
====================================
Platform subscription (Tier 2): $19.00
Container "myapp" (CX22): $5.00
Load balancer: $5.50
Estimated charges: $29.50
```

### 11.3 Cost Optimization

**Auto-scaling Recommendations:**

```
Crux Vibe detects traffic pattern:
- 8am-6pm: 15k requests/day (5 containers needed)
- 6pm-8am: 2k requests/day (1 container sufficient)

Recommendation: Scale down at 6pm, scale up at 8am
Expected savings: $15/month
```

---

## 12. PHASE 2: MANAGED DATABASE SERVICE (SUPABASE COMPETITOR)

### 12.1 Overview

**Phase 1** (Current): Self-hosted PostgreSQL on user's container

**Phase 2** (Roadmap): Managed PostgreSQL offering similar to Supabase

**Architecture:**

```
User's Container         Crux Vibe Managed DB
(App containers only)    (Dedicated DB cluster)
        │                        │
        ├── app:3000             │
        ├── app:3000             │
        │                        │
        └── Connection Pool ────→ │
                                 ├─ PostgreSQL Primary
                                 ├─ PostgreSQL Replica 1
                                 ├─ PostgreSQL Replica 2
                                 └─ Automated Backups
```

### 12.2 Managed Database Pricing

```
Base Tier: $10/month
├─ PostgreSQL 16
├─ 50 GB storage
├─ 100 concurrent connections
├─ Daily backups

Pro Tier: $29/month
├─ 200 GB storage
├─ 500 concurrent connections
├─ Hourly backups

HA Tier: $79/month
├─ 500 GB storage
├─ 1000 concurrent connections
├─ Real-time replication
├─ Automatic failover
├─ Point-in-time recovery (30 days)
├─ Read replicas (add $20 each)
```

### 12.3 Features

**Connection Pooling (PgBouncer):**
```
Connection pool: 100 → 5 server connections
Reduces overhead per app
```

**Automated Backups:**
```
Daily snapshots → Hetzner Snapshots API
Retention: 30 days (configurable)
Restore time: <5 minutes
```

**Point-in-Time Recovery:**
```
"Restore database to 2 hours ago"
Crux Vibe UI: one-click recovery
```

**Read Replicas:**
```
Primary (write): primary.db.cruxvibe.dev
Replica 1: replica1.db.cruxvibe.dev (read-only)
Replica 2: replica2.db.cruxvibe.dev (read-only)

App uses read replicas for analytics queries
```

**REST API (PostgREST-like):**
```
GET  /api/tables/users
GET  /api/tables/users/{id}
POST /api/tables/users
PUT  /api/tables/users/{id}
DELETE /api/tables/users/{id}

Auto-generated from database schema
```

**Edge Functions (Phase 2.1):**
```
Deploy serverless functions near your database

Function: /api/functions/process-signup
├─ Runs in Hetzner DC
├─ Direct database access
├─ Scales automatically
└─ Charged per invocation

Pricing: $0.001 per function invocation
```

**Realtime Subscriptions (Phase 2.2):**
```
WebSocket-based real-time updates

client.subscribe('users', { event: 'INSERT' }, callback)
// Notified immediately when new user inserted
```

### 12.4 Migration from Self-Hosted

**Process:**

```
1. User clicks "Upgrade to Managed DB"
2. Crux Vibe creates managed DB instance
3. Crux Vibe does pg_dump from self-hosted → managed DB
4. Crux Vibe updates app's DATABASE_URL
5. Health check: app connects to managed DB
6. Old self-hosted DB data archived (30 days retention)
7. Self-hosted PostgreSQL can be uninstalled (saves ~$2/month)

Zero downtime migration
```

---

## APPENDIX: QUICK START FOR DEVELOPERS

### A.1 Install Crux Vibe Locally

```bash
# 1. Sign up for Crux Vibe
open login.cruxvibe.dev

# 2. Download OpenCode + Crux MCP
curl -sSL https://crux-vibe-cdn.com/install-opencode.sh | bash

# 3. Provision a container (Managed or BYOS)
opencode provision --provider hetzner --size cx22

# Container ready in <5 minutes
```

### A.2 First Deploy

```bash
# 1. Clone your project (or create new)
git clone https://github.com/myrepo/myapp
cd myapp

# 2. Create Crux Vibe config
mkdir -p .crux
cat > .crux/pipeline.yml <<EOF
stages:
  - name: test
    steps:
      - command: npm test
    gate: true
  - name: build
    steps:
      - command: npm run build
  - name: deploy
    steps:
      - command: docker-compose up -d
EOF

# 3. Commit and push
git add .crux/pipeline.yml
git commit -m "Add CI/CD pipeline"
git push origin main  # Triggers container's CI/CD

# 4. Monitor in Crux Vibe UI
open https://crux-vibe.dev/dashboard
```

### A.3 Vibe Coding Example

```bash
# Use Crux Vibe Web IDE

User: "Add Redis caching to user lookups"

Crux OS + Claude execute:
1. Plan: Architecture for Redis integration
2. Test: Write cache tests
3. Build: Implement RedisClient + cache decorator
4. Security: Audit cache invalidation logic
5. Deploy: Rolling update with zero downtime

Result: Feature deployed in 2 minutes, no code written manually
```

---

## DOCUMENT VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | March 2026 | Complete rewrite: self-sovereign architecture, container provisioning, on-container CI/CD, Web IDE, Crux MCP integration |
| 1.0 | Feb 2026 | Platform-owned infrastructure model (archived) |

---

**End of Specification**
