# Consuela — Guia de Utilização

## O que é?
Consuela é a assistente pessoal do Duarte para gestão de Gmail e Google Calendar. Funciona via linguagem natural em Português de Portugal, sem instalações, sem servidor local, sem custo extra além da subscrição claude.ai.

---

## Como Aceder

### Terminal (Claude Code)
Abre o Claude Code na pasta de trabalho. As ferramentas Gmail e Calendar estão ligadas automaticamente via MCP. Fala diretamente:
```
"quantos emails tenho por ler?"
"que reuniões tenho esta semana?"
"cria um evento sexta às 15h"
```

### Browser / App / Telemóvel
Abre o claude.ai e vai ao projeto **Consuela**. Funciona em qualquer dispositivo com a subscrição.

---

## Funcionalidades

### Email (Gmail)
- Listar e pesquisar emails
- Ler email completo
- Criar rascunhos de resposta
- Gerir labels

### Calendário (Google Calendar)
- Ver eventos do dia/semana/mês
- Criar eventos
- Verificar disponibilidade
- Responder a convites
- Encontrar horários livres

---

## Estilo
- **Língua**: Português de Portugal (sempre)
- **Tom**: Profissional, caloroso, eficiente

---

## Estrutura da Pasta

```
Consuela/
├── PROJECT_INSTRUCTIONS.md     # Instruções para Claude Code
├── PROJECT_MEMORY.md           # Contexto e histórico do projeto
├── FUNCTIONAL_DOC.md           # Documentação funcional
├── TECHNICAL_DOC.md            # Documentação técnica
├── CONSUELA_README.md          # Este ficheiro
├── QUICK_START.md              # Início rápido
├── FILE_STRUCTURE.md           # Estrutura de ficheiros
├── CONSUELA_NATURAL_LANGUAGE.md # Exemplos de linguagem natural
└── OLD/                        # Versão anterior (Python/Flask) — arquivada
```
