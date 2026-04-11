# Consuela — System Documentation

## Objetivo

Assistente pessoal do Duarte para gestão de Gmail e Google Calendar via linguagem natural em Português de Portugal. Personagem baseada na Consuela do Family Guy — direta, sarcástica, eficiente. Sem servidor próprio, sem gestão de credenciais locais.

---

## Arquitetura Atual (MCP)

```
Input do Utilizador (Claude Code terminal / claude.ai)
    ↓
Claude Sonnet (processa linguagem natural)
    ↓ via MCP
Gmail MCP Server ←→ Gmail API ←→ Google
GCal MCP Server  ←→ Calendar API ←→ Google
    ↓
Claude responde em Português de Portugal com personalidade Consuela
```

**Sem backend próprio.** Toda a autenticação OAuth gerida pelo claude.ai. Sem `credentials.json` ou tokens locais necessários na versão atual.

---

## APIs Google Utilizadas

### Gmail API
| Ferramenta MCP | Ação |
|---|---|
| `gmail_search_messages` | Pesquisar emails (sintaxe Gmail: is:unread, from:, subject:) |
| `gmail_read_message` | Ler email completo por ID |
| `gmail_read_thread` | Ler thread completa |
| `gmail_create_draft` | Criar rascunho |
| `gmail_list_labels` | Listar labels |
| `gmail_list_drafts` | Listar rascunhos |
| `gmail_get_profile` | Info do perfil Gmail |

**Scopes:** `https://www.googleapis.com/auth/gmail.readonly`, `gmail.modify`

### Google Calendar API
| Ferramenta MCP | Ação |
|---|---|
| `gcal_list_events` | Listar eventos num intervalo |
| `gcal_create_event` | Criar evento |
| `gcal_get_event` | Detalhes de evento por ID |
| `gcal_update_event` | Editar evento existente |
| `gcal_delete_event` | Apagar evento |
| `gcal_respond_to_event` | Aceitar/recusar/talvez convite |
| `gcal_find_my_free_time` | Encontrar slots livres |
| `gcal_find_meeting_times` | Horários para múltiplos participantes |
| `gcal_list_calendars` | Listar calendários |

**Timezone:** Europe/Lisbon (hardcoded)

---

## Fluxos Principais

### Email
```
"Quantos emails tenho por ler?"
  → gmail_search_messages(is:unread)
  → Claude conta e resume
  → Resposta Consuela em PT

"Cria rascunho a responder ao Pedro"
  → gmail_read_message (contexto)
  → gmail_create_draft
  → Confirmação Consuela
```

### Calendário
```
"O que tenho esta semana?"
  → gcal_list_events(range: semana atual)
  → Claude processa eventos
  → Resposta Consuela em PT

"Cria almoço com Ana sexta às 13h"
  → gcal_create_event(...)
  → Confirmação Consuela
```

### Organização de Email
```
"Arquiva os newsletters"
  → gmail_search_messages(filtro relevante)
  → Mostra lista antes de executar
  → Confirmação do utilizador
  → Ação executada
```

---

## Estrutura de Ficheiros

```
Consuela/
├── PROJECT_INSTRUCTIONS.md     — Instruções para Claude Code
├── PROJECT_MEMORY.md           — Histórico e decisões do projeto
├── FUNCTIONAL_DOC.md           — O que Consuela faz e como usar
├── TECHNICAL_DOC.md            — Arquitetura MCP detalhada
├── CONSUELA_README.md          — Guia do utilizador (PT)
├── CONSUELA_NATURAL_LANGUAGE.md — Exemplos linguagem natural
├── QUICK_START.md              — Quick start
├── FILE_STRUCTURE.md           — Organização de ficheiros
├── CLAUDE.md                   — Definição de personalidade
│
├── [LEGACY - não usar]
│   ├── consuela_v2.py          — CLI interativo Python (arquivado)
│   ├── consuela_server_v2.py   — Flask server (arquivado)
│   ├── consuela_web_fixed.html — Web UI (arquivado)
│   ├── consuela_app.html       — Web UI alternativa (arquivado)
│   ├── credentials.json        — OAuth Google (NUNCA commitar)
│   ├── token.pickle            — Token OAuth binário (NUNCA commitar)
│   └── token_b64.txt           — Token base64
│
├── consuela/                   — Home Assistant add-on (legacy)
│   ├── config.json
│   ├── consuela_server_v2.py
│   └── consuela_web_fixed.html
│
└── OLD/                        — Versões anteriores arquivadas
```

---

## Ambientes de Execução

| Ambiente | Como usar | Estado |
|---|---|---|
| **Claude Code terminal** | Linguagem natural via MCP | **Ativo** |
| **claude.ai web/app** | Projeto "Consuela" no claude.ai | **Ativo** |
| **Home Assistant OS (RPi)** | Add-on Docker + Flask | Legacy |
| **Python local** | `python consuela_v2.py` | Arquivado |

---

## Personalidade (Consuela)

Baseada na personagem do Family Guy. Definida em `CLAUDE.md`.

- Expressões características: "No, no, no...", "Ay, Dios mío", "Mister, listen to me", "But yes, I help"
- Sarcasmo subtil, nunca exagerado
- Reclamar faz parte — nunca recusa ajudar
- Responde sempre em Português de Portugal
- **Nunca inventa informação** — usa sempre as ferramentas MCP
- Para ações destrutivas (apagar emails): **confirma sempre antes**

---

## Decisões Técnicas

| Decisão | Razão |
|---|---|
| MCP em vez de Python/Flask | Elimina backend, gestão de tokens, deployment |
| Sem servidor próprio | Usa subscrição claude.ai existente — sem custos API adicionais |
| OAuth via claude.ai | Sem credentials locais para gerir ou commitar acidentalmente |
| Sem persistência entre sessões | By design — privacidade, simplicidade |
| Português de Portugal | Utilizador PT, experiência mais natural |

---

## Histórico de Versões

| Versão | Stack | Estado |
|---|---|---|
| v1 | Python + Flask + Google OAuth + Anthropic SDK | Arquivado (OLD/) |
| v2 | Python + Flask + function calling + web UI | Arquivado (root) |
| **Atual** | Claude Code + MCP servers | **Ativo** |

---

## Segurança

- `credentials.json` e `token.pickle` **nunca commitar** (verificar `.gitignore`)
- Versão MCP não tem credenciais locais — OAuth no claude.ai
- Sem `.env` necessário na versão atual
- Ações destrutivas (delete) sempre com confirmação explícita do utilizador

---

## Funcionalidades Planeadas

- [ ] Resumo diário automático de email
- [ ] Integração Google Tasks
- [ ] Lembretes de reuniões
- [ ] Filtros e regras personalizadas
- [ ] Síntese de emails longos
- [ ] Agendamento automático de eventos
- [ ] Notificações prioritárias
