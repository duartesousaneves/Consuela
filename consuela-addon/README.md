# 🧹 Consuela — Add-on para Home Assistant OS

Assistente pessoal para Gmail e Google Calendar, a correr 24/7 no Raspberry Pi.

---

## Estrutura de Ficheiros

```
consuela-addon/
├── config.json          ← Configuração do add-on (HAOS)
├── Dockerfile           ← Imagem Docker
├── requirements.txt     ← Dependências Python
├── run.sh               ← Script de arranque
└── consuela/
    ├── consuela_server_v2.py    ← Servidor Flask + scheduler
    └── consuela_web_fixed.html  ← Interface web
```

---

## Instalação — Passo a Passo

### 1. Preparar o token.pickle no PC (Windows)

O `token.pickle` já existe no teu PC em:
`C:\Users\Duarte\OneDrive\Aplicações\Consuela\token.pickle`

### 2. Copiar o token.pickle para o Raspberry Pi via SSH

No terminal do teu PC (PowerShell ou CMD):

```bash
# Substitui <IP_DO_RASPBERRY> pelo IP do teu Pi (ex: 192.168.1.100)
# Podes ver o IP no Home Assistant: Settings > System > Network

scp "C:\Users\Duarte\OneDrive\Aplicações\Consuela\token.pickle" root@<IP_DO_RASPBERRY>:/root/token.pickle
scp "C:\Users\Duarte\OneDrive\Aplicações\Consuela\credentials.json" root@<IP_DO_RASPBERRY>:/root/credentials.json
```

A password SSH do HAOS é a que definiste na instalação (ou "root" se nunca alteraste).

### 3. Mover os ficheiros para /data/ via SSH

Liga via SSH ao Raspberry:
```bash
ssh root@<IP_DO_RASPBERRY>
```

Dentro do Raspberry:
```bash
# O /data/ do add-on fica em:
mkdir -p /mnt/data/supervisor/addons/data/consuela/

cp /root/token.pickle /mnt/data/supervisor/addons/data/consuela/token.pickle
cp /root/credentials.json /mnt/data/supervisor/addons/data/consuela/credentials.json
```

### 4. Adicionar o repositório ao Home Assistant

1. No Home Assistant, vai a: **Settings > Add-ons > Add-on Store**
2. Clica nos três pontos (⋮) no canto superior direito
3. Seleciona **Repositories**
4. Adiciona o URL do teu repositório GitHub:
   `https://github.com/duartesousaneves/consuela`
5. Clica **Add**

### 5. Instalar o add-on

1. Procura "Consuela" na lista de add-ons
2. Clica em **Install**
3. Vai a **Configuration** e preenche:
   - `anthropic_api_key`: a tua chave API da Anthropic
4. Clica **Start**

### 6. Verificar que está a funcionar

- Abre: `http://<IP_DO_RASPBERRY>:5000`
- Ou verifica o status: `http://<IP_DO_RASPBERRY>:5000/api/status`
- Para disparar o report agora (teste): 
  ```bash
  curl -X POST http://<IP_DO_RASPBERRY>:5000/api/report/now
  ```

---

## Report Diário

O report é enviado automaticamente todos os dias às **19:00** para `duartesousaneves@gmail.com`.

Para testar manualmente sem esperar pelas 19:00:
```bash
curl -X POST http://<IP_DO_RASPBERRY>:5000/api/report/now
```

---

## SSH no Home Assistant OS

O HAOS não tem SSH por defeito. Para ativar:

1. **Settings > Add-ons > Add-on Store**
2. Instala o add-on **"SSH & Web Terminal"** (add-on oficial)
3. Configura uma password e inicia o add-on
4. Liga via: `ssh root@<IP_DO_RASPBERRY>` na porta 22222

---

## Renovação do Token Google

O `token.pickle` renova-se automaticamente enquanto a Consuela estiver a correr.
Se o token expirar (raro), repete o passo 2 e 3.

---

## Repositório GitHub — Estrutura Recomendada

```
github.com/duartesousaneves/consuela/
└── consuela-addon/        ← esta pasta
    ├── config.json
    ├── Dockerfile
    ├── requirements.txt
    ├── run.sh
    └── consuela/
        ├── consuela_server_v2.py
        └── consuela_web_fixed.html
```

O `repository.json` na raiz do repo é necessário para o HAOS reconhecer o repositório:
```json
{
  "name": "Consuela Add-ons",
  "url": "https://github.com/duartesousaneves/consuela",
  "maintainer": "Duarte Sousa Neves"
}
```
