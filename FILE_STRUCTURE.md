# Consuela — Estrutura de Ficheiros

```
C:\Users\Duarte\OneDrive\Aplicações\Consuela\
│
├── PROJECT_INSTRUCTIONS.md       # Instruções principais para Claude Code
├── PROJECT_MEMORY.md             # Histórico de decisões e estado do projeto
├── FUNCTIONAL_DOC.md             # O que a Consuela faz e como usar
├── TECHNICAL_DOC.md              # Arquitectura técnica (MCP)
├── CONSUELA_README.md            # Guia geral
├── QUICK_START.md                # Início rápido
├── CONSUELA_NATURAL_LANGUAGE.md  # Exemplos de linguagem natural
├── FILE_STRUCTURE.md             # Este ficheiro
│
└── OLD/                          # Versão anterior arquivada (Python/Flask)
    ├── consuela_v2.py
    ├── consuela_server_v2.py
    ├── consuela_email_calendar.py
    ├── consuela_interactive.py
    ├── consuela_server.py
    ├── consuela_setup.sh
    ├── consuela_web.html
    ├── consuela_web_fixed.html
    ├── credentials.json
    ├── token.pickle
    └── CONSUELA_V2_GUIA.md
```

## Notas

- Não existe código executável activo — a Consuela corre inteiramente via Claude Code + MCP
- A pasta `OLD/` contém a versão anterior (Python + Flask + Anthropic API key) — arquivada mas não apagada
- Não há `requirements.txt`, `.env`, nem credenciais Google locais — a autenticação é gerida pelo MCP do claude.ai
