#!/bin/bash
set -e

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
