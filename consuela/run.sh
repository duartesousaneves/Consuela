#!/usr/bin/with-contenv bashio

# Lê a API key das opções do add-on
export ANTHROPIC_API_KEY=$(bashio::config 'anthropic_api_key')

bashio::log.info "A iniciar Consuela..."

# Verifica se o token Google existe
if [ ! -f /data/token.pickle ]; then
    bashio::log.warning "token.pickle não encontrado em /data/"
    bashio::log.warning "Copia o token.pickle do teu PC para /data/ via SSH"
fi

# Verifica se credentials.json existe
if [ ! -f /data/credentials.json ]; then
    bashio::log.warning "credentials.json não encontrado em /data/"
fi

# Cria symlinks dos ficheiros auth para o diretório da app
ln -sf /data/token.pickle /app/token.pickle 2>/dev/null || true
ln -sf /data/credentials.json /app/credentials.json 2>/dev/null || true

cd /app
exec python3 consuela_server_v2.py
