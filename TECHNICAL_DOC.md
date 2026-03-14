# Consuela — Documentação Técnica

## Stack

| Componente | Tecnologia |
|---|---|
| Interface | Claude Code (terminal) ou claude.ai (browser/app) |
| LLM | Claude Sonnet (via subscrição claude.ai) |
| Email | Gmail MCP Server |
| Calendário | Google Calendar MCP Server |
| Autenticação Google | Gerida pelo MCP do claude.ai |
| Backend próprio | Nenhum |

---

## Arquitectura

```
Utilizador (terminal ou browser)
        ↓
Claude (claude.ai / Claude Code)
        ↓ MCP
Gmail MCP Server → Gmail API → Google
GCal MCP Server  → Calendar API → Google
```

Não existe servidor local, Flask, nem chamadas directas à Anthropic API. Tudo corre via MCP dentro do ecossistema claude.ai.

---

## Ferramentas MCP Disponíveis

### Gmail
| Ferramenta | O que faz |
|---|---|
| `gmail_search_messages` | Pesquisa emails com sintaxe Gmail (is:unread, from:, subject:, etc.) |
| `gmail_read_message` | Lê corpo completo de um email por ID |
| `gmail_create_draft` | Cria rascunho no Gmail |
| `gmail_list_labels` | Lista todas as labels da conta |
| `gmail_list_drafts` | Lista rascunhos existentes |
| `gmail_get_profile` | Informação do perfil Gmail |
| `gmail_read_thread` | Lê thread completa de emails |

### Google Calendar
| Ferramenta | O que faz |
|---|---|
| `gcal_list_events` | Lista eventos num intervalo de datas |
| `gcal_create_event` | Cria novo evento |
| `gcal_get_event` | Lê detalhes de um evento por ID |
| `gcal_update_event` | Edita evento existente |
| `gcal_delete_event` | Apaga evento |
| `gcal_respond_to_event` | Aceita/recusa/talvez para convite |
| `gcal_find_my_free_time` | Encontra slots livres no calendário |
| `gcal_find_meeting_times` | Encontra horários para reuniões com múltiplos participantes |
| `gcal_list_calendars` | Lista calendários da conta |

---

## System Prompt (Personalidade)

Ver `CLAUDE.md` na raiz da pasta — é a fonte de verdade para a personalidade.

Resumo: Consuela do Family Guy. Sarcástica, direta, um pouco rude, mas sempre eficiente. Usa expressões como "No, no, no...", "Ay, Dios mío", "Mister, listen to me". Português de Portugal. Nunca inventa informação — usa sempre as ferramentas.

---

## Autenticação

- A autenticação Google (Gmail + Calendar) é gerida pelo claude.ai via MCP OAuth
- Não existem `credentials.json` nem `token.json` locais
- A `ANTHROPIC_API_KEY` em console.anthropic.com existe mas não é usada para este fluxo

---

## Versão Anterior (Arquivada)

A versão anterior (Python + Flask) está em `OLD/`. Usava:
- `anthropic` SDK com API key directa
- OAuth Google local (`credentials.json` + `token.pickle`)
- Servidor Flask em `localhost:5000`

Foi abandonada por ser desnecessária — o MCP cobre todas as funcionalidades sem custo adicional.
