# 🧹 CONSUELA v2 - Guia Completo

## O que é novo?

✨ **Function Calling Inteligente** — Consuela executa ações automaticamente
✨ **Cache Inteligente** — Busca 100+ emails, mas com cache para reduzir custos
✨ **Português de Portugal** — Linguagem correcta + expressões reais da série
✨ **Roast Subtil** — Menos exagerado, mais natural
✨ **Confirmações Inteligentes** — Delete pede confirmação, criar eventos é automático

---

## 🚀 Como Usar

### **Terminal**

**COPIAR PARA: PowerShell/Antigravity**
```powershell
python consuela_v2.py
```

Depois digita comandos como:

```
Você: Mostra-me os emails importantes
Consuela: [Analisa e lista]

Você: Elimina emails de spam
Consuela: [Mostra quais vai eliminar]
⚠️  Consuela quer eliminar 5 email(s)
   Razão: Spam
Confirmas? (s/n): s
✅ Eliminados 5 email(s).

Você: Cria um evento para ir ao cinema dia 20
Consuela: [Cria automaticamente]
✅ Evento criado: Cinema - 20/03/2026

Você: Sair
Consuela: Ay, Dios mío... finalmente! 👋
```

---

## 📋 Comandos Que Entende

### **Leitura de Emails**
```
"Mostra-me os emails"
"Quantos emails tenho não lidos?"
"Tenho algo importante?"
"Emails sobre filmes"
```

### **Eliminação (com confirmação)**
```
"Elimina emails de spam"
"Apaga emails antigos de 2024"
"Remove emails deste remetente"
```

### **Arquivo**
```
"Arquiva estes emails"
"Move para arquivo"
"Organiza isto"
```

### **Organização com Labels**
```
"Marca com label 'Importante'"
"Organiza com 'Trabalho'"
"Categoriza como 'Pessoal'"
```

### **Calendário**
```
"Cria um evento para amanhã"
"Adiciona ao calendário: cinema dia 20"
"Que eventos tenho?"
```

### **Geral**
```
"Que fazer com isto?"
"Preciso de ajuda"
"Como está tudo?"
```

---

## 🎯 Funcionalidades

### ✅ **1. Buscar Emails (100+)**
- Carrega até 100 emails não lidos
- Cache de 10 minutos (não re-busca constantemente)
- Mostra total real de não lidos
- Análise com Claude

### ✅ **2. Eliminar Emails**
- Entende o comando
- Mostra quais vai eliminar
- **Pede confirmação** (segurança)
- Executa após confirmação

### ✅ **3. Arquivar Emails**
- Move de inbox automaticamente
- Sem confirmação (menos "destrutivo")
- Mantém os emails

### ✅ **4. Criar Eventos**
- Entende datas naturais ("amanhã", "dia 20")
- Cria automaticamente no calendário
- Sem confirmação (menos intrusivo)

### ✅ **5. Organizar com Labels**
- Cria novo label se não existir
- Aplica a múltiplos emails
- Automático

---

## 💰 Custos Estimados

### **Estrutura de Custos:**

| Operação | Custo | Notas |
|----------|-------|-------|
| Ler emails (com cache) | $0.002-0.01 | Cache reduz 70% |
| Eliminar (com confirmação) | $0.001-0.005 | Por email |
| Arquivar | $0.001-0.005 | Por email |
| Criar evento | $0.002-0.005 | Automático |
| Organizar labels | $0.002-0.01 | Por email |

### **Uso Típico Diário:**
```
Manhã: Lê emails (com cache) = $0.005
Meio: Organiza/arquivo = $0.01
Noite: Cria evento = $0.003
────────────────────────
TOTAL/dia = ~$0.02
TOTAL/mês = ~$0.60
```

**Tens $5 em créditos = ~8 meses de uso!** ✅

---

## 🔧 Personalizações

### **Mudar Número de Emails Carregados**

Linha ~70 em `consuela_v2.py`:
```python
emails, total_unread = self._get_emails("is:unread", max_results=100)
```

Substitui `100` pelo número que quiseres.

### **Mudar Tempo de Cache**

Linha ~60:
```python
if datetime.now() - self.cache_time < timedelta(minutes=10):
```

Substitui `minutes=10` pelo que preferires.

### **Adicionar Mais Expressões da Consuela**

Edita o prompt (linha ~320) e adiciona mais frases naturais dela.

---

## ⚙️ Como Funciona (Técnico)

```
Utilizador: "Elimina emails de spam"
    ↓
Claude analisa com function calling
    ↓
Identifica: "delete_emails" com IDs dos emails
    ↓
Consuela mostra: "Vou eliminar 5 emails"
    ↓
Pede confirmação: "Confirmas? (s/n):"
    ↓
Se "s": Executa via Gmail API
    ↓
Responde: "✅ Eliminados 5 email(s)"
```

---

## 🎨 Linguagem da Consuela v2

### **Expressões Reais da Série:**
- "No, no, no..."
- "Mister, listen to me"
- "Ay, Dios mío"
- "But yes, I help you"
- Sotaque português/espanhol misturado

### **Tom:**
- Sarcasmo subtil (não exagerado)
- Eficiente e prática
- Com atitude, mas ajuda sempre
- Português de Portugal correto

**Exemplo:**
```
Antes (v1): "Ay, que maravilha... outro email importante."
Depois (v2): "Tens 5 emails novos. Quer que organize isto?"
```

---

## 🚨 Troubleshooting

### "NameError: name 'build' is not defined"
```bash
pip install google-api-python-client
```

### "FileNotFoundError: credentials.json"
Certifica-te de que está na mesma pasta.

### "Não reconhece a ação"
- Tenta ser mais claro: "Elimina emails com assunto 'teste'"
- Em vez de: "Apaga isto"

### "Demasiados custos"
- Reduz `max_results` de 100 para 50
- Cache já ajuda bastante (70% menos custos)

---

## 📊 Roadmap Futuro

- 🤖 Respostas automáticas a padrões
- 📧 Síntese de emails longos
- 📅 Agendamento automático de eventos
- 🔔 Notificações prioritárias
- 🤝 Integração com Slack/Teams

---

## 🎯 Dicas

1. **Usa o cache** — Não refaz busca a cada 10 minutos
2. **Confirma deletes** — Sempre pede confirmação para eliminação
3. **Sê específico** — "Emails de spam antigos" em vez de "Apaga"
4. **Aproveita labels** — Melhor que deletar é organizar

---

**Pronto? Testa agora!** 🚀

```bash
python consuela_v2.py
```

Dúvidas? Avisa! 💜
