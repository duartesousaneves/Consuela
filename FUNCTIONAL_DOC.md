# Consuela — Documentação Funcional

## Visão Geral

A Consuela é a assistente pessoal do Duarte para gestão de email e calendário, baseada na personagem homónima do Family Guy. Sarcástica, direta e um pouco rude — mas sempre eficiente. O utilizador escreve o que quer fazer em Português de Portugal e a Consuela executa, mesmo que reclamando. Sem scripts, sem servidor local, sem custo extra além da subscrição claude.ai.

---

## Como Aceder

| Forma | Como | Custo |
|---|---|---|
| Terminal | Claude Code (esta sessão) | Subscrição |
| Browser | claude.ai → projeto Consuela | Subscrição |
| App móvel | App Claude → projeto Consuela | Subscrição |

---

## Casos de Uso

### Email (Gmail)

| Pedido | Exemplo |
|---|---|
| Listar emails | "que emails não li hoje?" |
| Pesquisar | "emails do João sobre o projeto X" |
| Resumir | "resume os emails não lidos" |
| Ler email | "abre o email do banco" |
| Criar rascunho | "escreve uma resposta a dizer que aceito" |

### Calendário (Google Calendar)

| Pedido | Exemplo |
|---|---|
| Ver eventos | "o que tenho esta semana?" |
| Criar evento | "cria reunião de equipa sexta às 10h" |
| Verificar disponibilidade | "tenho alguma coisa quinta de manhã?" |
| Próximos eventos | "quando é a próxima reunião com o cliente?" |
| Responder a convite | "aceita o convite da reunião de amanhã" |

---

## Fluxo de Interação

```
Utilizador escreve pedido em linguagem natural
        ↓
Claude interpreta e decide que ferramentas MCP usar
        ↓
Ferramenta MCP executa ação no Gmail/Calendar
        ↓
Claude processa resultado e responde em português
```

---

## Limitações

- Sem persistência entre sessões (a Consuela não recorda conversas anteriores)
- Requer ligação à internet
- Sem acesso offline
