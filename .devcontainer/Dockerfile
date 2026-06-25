# 要ダイジェスト固定: docker manifest inspect mcr.microsoft.com/devcontainers/javascript-node:1-24-bookworm --verbose
FROM mcr.microsoft.com/devcontainers/javascript-node:24-bookworm

# Python + pip
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip python3-full \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/*

# Task CLI
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin
