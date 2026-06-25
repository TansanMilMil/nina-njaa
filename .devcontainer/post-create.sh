#!/bin/bash
set -e

# Tools
sudo apt-get update -qq && sudo apt-get install -y -qq rsync

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
