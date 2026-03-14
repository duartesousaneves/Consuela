ARG BUILD_FROM
FROM $BUILD_FROM

# Instalar Python e dependências do sistema
RUN apk add --no-cache python3 py3-pip gcc musl-dev python3-dev libffi-dev

# Diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copiar código da Consuela
COPY consuela/ .

# Copiar script de arranque
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
