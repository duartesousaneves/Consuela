# Consuela — Project Memory

## Sobre o Projeto
A Consuela é a assistente pessoal do Duarte para gestão de Gmail e Google Calendar. É um projeto ativo.

## Localização
`C:\Users\Duarte\OneDrive\Aplicações\Consuela`

## Estado Atual (Março 2026)
- Funciona via Claude Code (terminal) com ferramentas MCP do Gmail e Google Calendar
- Funciona via Claude.ai (browser/app/telemóvel) através do projeto Consuela
- **Sem servidor Python**: a abordagem Flask/API key foi abandonada — os MCP servers cobrem todas as funcionalidades
- Os scripts Python originais estão arquivados em `OLD/`

## Decisões Técnicas
- **Abordagem anterior (OLD)**: Python + Flask + Anthropic API key ($5 de crédito) — abandonada por ser desnecessária
- **Abordagem atual**: Claude Code + MCP servers (Gmail, Google Calendar) — usa subscrição claude.ai, sem custo extra
- **Língua**: Português de Portugal (sempre)
- **Auth Google**: Gerida pelo MCP do Claude.ai, sem credentials locais

## Contexto de Uso
- Duarte usa a Consuela para gerir o seu email e calendário do dia-a-dia
- Acesso via terminal (Claude Code) ou browser/app Claude.ai
- A API key da Anthropic em console.anthropic.com tem $5 de crédito mas não é necessária para uso normal

## Próximas Funcionalidades
- Resumo diário de emails
- Criação de rascunhos
- Google Tasks
- Notificações de reuniões
