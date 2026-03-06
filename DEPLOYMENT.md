# Deployment: runcrux.io

## Settings

```
SERVER="runcrux.io"
USER="runcrux.io"
DEST_DIR="/home/runcrux.io/public_html/"
SRC_DIR="site/_site"
```

## Quick Deploy

```bash
./deploy-runcrux.io.sh
```

Or via npm: `npm run deploy` (from site/ directory)

## Manual Build & Deploy

### Build
```bash
cd site
npm install
npm run build
```
Output: `site/_site/`

### Deploy
```bash
./deploy-runcrux.io.sh --build    # build first, then deploy
./deploy-runcrux.io.sh --dry-run  # preview what would be deployed
```

## SSH Key Setup (First Time)

### 1. Generate SSH key (if needed)
```bash
ssh-keygen -t ed25519 -C "crux@runcrux.io" -f ~/.ssh/runcrux_ed25519
```

### 2. Add to SSH config
```bash
cat >> ~/.ssh/config << 'EOF'
Host runcrux.io
  HostName runcrux.io
  User runcrux.io
  IdentityFile ~/.ssh/runcrux_ed25519
  IdentitiesOnly yes
EOF
```

### 3. Copy key to server
```bash
ssh-copy-id -i ~/.ssh/runcrux_ed25519 runcrux.io@runcrux.io
```

### 4. Test connection
```bash
ssh runcrux.io@runcrux.io "echo 'Connected'"
```

## Server Requirements

- SSH access with key-based auth
- Web root: `/home/runcrux.io/public_html/`
- Nginx/Apache serving from that directory
- SSL/TLS handled at proxy/load balancer level

## Deploy Script Options

| Flag | Description |
|------|-------------|
| `--build` | Run build before deploy |
| `--dry-run` | Preview changes without uploading |
| `--verbose` | Show rsync progress |
| `--force` | Skip confirmation prompt |

## Git Hook (Optional)

To auto-deploy on git push:
```bash
# Add to .git/hooks/post-receive
#!/bin/bash
while read oldrev newrev refname; do
  if [ "$refname" = "refs/heads/main" ]; then
    ./deploy-runcrux.io.sh --build
  fi
done
```

## CI/CD (Future)

- GitHub Actions for automated deploys
- Netlify/Vercel as alternative hosting
- Cloudflare Pages
