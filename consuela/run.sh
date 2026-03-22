#!/bin/bash

# Load optional local env override
if [ -f /data/.env ]; then
    set -a
    . /data/.env
    set +a
fi

# Read ANTHROPIC_API_KEY from HAOS options.json if not already in environment
if [ -z "${ANTHROPIC_API_KEY}" ] && [ -f /data/options.json ]; then
    ANTHROPIC_API_KEY=$(python3 -c "import json; d=json.load(open('/data/options.json')); print(d.get('anthropic_api_key',''))" 2>/dev/null)
    export ANTHROPIC_API_KEY
fi

ln -sf /data/token.pickle /app/token.pickle 2>/dev/null || true
ln -sf /data/credentials.json /app/credentials.json 2>/dev/null || true

cd /app
exec python3 consuela_server_v2.py
