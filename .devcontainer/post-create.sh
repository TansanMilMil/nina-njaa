#!/bin/bash
set -e

# Tools
sudo apt-get update -qq && sudo apt-get install -y -qq rsync sqlite3

# Claude Code CLI
npm install -g @anthropic-ai/claude-code
node $(npm root -g)/@anthropic-ai/claude-code/install.cjs

# SSH known hosts
mkdir -p ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

# Frontend
cd /workspaces/nina-njaa/frontend
npm install

# Backend
cd /workspaces/nina-njaa/backend
python3 -m venv --clear .venv
.venv/bin/pip install -r requirements.txt

echo "Post-create setup complete!"
