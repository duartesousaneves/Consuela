#!/bin/sh
set -e

echo "A iniciar Consuela..."

if [ -f /data/.env ]; then
    set -a
    . /data/.env
    set +a
    echo "Variáveis de ambiente carregadas de /data/.env"
fi

if [ ! -f /data/token.pickle ]; then
    echo "AVISO: token.pickle não encontrado em /data/"
fi

ln -sf /data/token.pickle /app/token.pickle 2>/dev/null || true
ln -sf /data/credentials.json /app/credentials.json 2>/dev/null || true

cd /app
exec python3 consuela_server_v2.py
