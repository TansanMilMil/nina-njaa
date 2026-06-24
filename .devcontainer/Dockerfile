# 要ダイジェスト固定: docker manifest inspect mcr.microsoft.com/devcontainers/javascript-node:1-24-bookworm --verbose
FROM mcr.microsoft.com/devcontainers/javascript-node:24-bookworm

# Python 3.13 + pip
RUN apt-get update && apt-get install -y \
    python3.13 python3.13-venv python3-pip \
    && ln -sf /usr/bin/python3.13 /usr/local/bin/python3 \
    && ln -sf /usr/local/bin/python3 /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/*

# Task CLI
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin
