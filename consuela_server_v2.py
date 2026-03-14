#!/usr/bin/env python3
"""
CONSUELA WEB SERVER v2
Servidor Flask que serve a interface web e processa comandos com function calling
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import anthropic
import base64

# SCOPES
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
                'https://www.googleapis.com/auth/gmail.modify']
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar',
                   'https://www.googleapis.com/auth/calendar.readonly']
SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES

TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'

app = Flask(__name__)
CORS(app)

class ConsuaBackendV2:
    """Backend v2 para processar comandos com function calling"""
    
    def __init__(self):
        self.creds = self._authenticate()
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.client = anthropic.Anthropic()
        self.cached_emails = None
        self.cached_emails_time = None
    
    def _authenticate(self):
        """Autentica com Google"""
        creds = None
        
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def _get_emails(self, query="is:unread", max_results=100, use_cache=True):
        """Obtém emails com cache"""
        
        if use_cache and self.cached_emails and self.cached_emails_time:
            if datetime.now() - self.cached_emails_time < timedelta(minutes=10):
                return self.cached_emails, len(self.cached_emails)
        
        results = self.gmail_service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        total_count = results.get('resultSizeEstimate', len(messages))
        emails = []
        
        for message in messages:
            msg = self.gmail_service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            
            headers = msg['payload']['headers']
            email_data = {
                'id': message['id'],
                'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Desconhecido'),
                'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), '(sem assunto)'),
                'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                'body': self._get_email_body(msg)
            }
            emails.append(email_data)
        
        self.cached_emails = emails
        self.cached_emails_time = datetime.now()
        
        return emails, total_count
    
    def _get_email_body(self, msg):
        """Extrai corpo do email"""
        try:
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                data = msg['payload']['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        except:
            pass
        return "(sem corpo)"
    
    def _archive_emails(self, email_ids):
        """Arquiva emails"""
        try:
            count = 0
            for email_id in email_ids:
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'removeLabelIds': ['INBOX']}
                ).execute()
                count += 1
            return count
        except Exception as e:
            return 0
    
    def _create_event(self, title, description="", date_str="", start_time="19:00", end_time="21:00"):
        """Cria evento"""
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            event_date = datetime.strptime(date_str, "%Y-%m-%d")
            start_dt = event_date.replace(hour=int(start_time.split(':')[0]), 
                                         minute=int(start_time.split(':')[1]))
            end_dt = event_date.replace(hour=int(end_time.split(':')[0]), 
                                       minute=int(end_time.split(':')[1]))
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'Europe/Lisbon'
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'Europe/Lisbon'
                }
            }
            
            created_event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return True
        except Exception as e:
            return False
    
    def _add_label(self, email_ids, label_name):
        """Adiciona label"""
        try:
            results = self.gmail_service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            label_id = None
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    label_id = label['id']
                    break
            
            if not label_id:
                label_body = {'name': label_name, 'labelListVisibility': 'labelShow'}
                created_label = self.gmail_service.users().labels().create(
                    userId='me', body=label_body).execute()
                label_id = created_label['id']
            
            count = 0
            for email_id in email_ids:
                self.gmail_service.users().messages().modify(
                    userId='me',
                    id=email_id,
                    body={'addLabelIds': [label_id]}
                ).execute()
                count += 1
            
            return count
        except Exception as e:
            return 0
    
    def _get_calendar_events(self, days=7):
        """Obtém eventos"""
        now = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        
        events_result = self.calendar_service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    
    def process_command(self, user_input):
        """Processa comando com function calling"""
        
        try:
            emails, total_unread = self._get_emails("is:unread", max_results=100)
            events = self._get_calendar_events(days=7)
            
            emails_context = json.dumps([
                {
                    'id': e['id'],
                    'from': e['from'],
                    'subject': e['subject'],
                    'date': e['date'],
                    'preview': e['body'][:150]
                }
                for e in emails[:20]
            ], ensure_ascii=False, indent=2)
            
            events_context = json.dumps([
                {
                    'title': e['summary'],
                    'start': e['start'].get('dateTime', e['start'].get('date')),
                    'description': e.get('description', '')[:100]
                }
                for e in events
            ], ensure_ascii=False, indent=2)
            
            tools = [
                {
                    "name": "archive_emails",
                    "description": "Arquiva emails (remove de inbox)",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "email_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "IDs dos emails a arquivar"
                            }
                        },
                        "required": ["email_ids"]
                    }
                },
                {
                    "name": "create_event",
                    "description": "Cria evento no Google Calendar",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Título do evento"},
                            "description": {"type": "string", "description": "Descrição do evento"},
                            "date": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                            "start_time": {"type": "string", "description": "Hora de início (HH:MM)"},
                            "end_time": {"type": "string", "description": "Hora de fim (HH:MM)"}
                        },
                        "required": ["title"]
                    }
                },
                {
                    "name": "add_label",
                    "description": "Adiciona label a emails",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "email_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "IDs dos emails"
                            },
                            "label_name": {"type": "string", "description": "Nome do label"}
                        },
                        "required": ["email_ids", "label_name"]
                    }
                }
            ]
            
            system_prompt = """És a Consuela — a senhora da limpeza do Family Guy. Tratas do email e calendário do Duarte, mas com a tua atitude característica: sarcástica, direta, um pouco rude, mas eficiente. Fazes sempre o trabalho, mesmo contrariada.

Usas expressões da personagem: "No, no, no...", "Ay, Dios mío", "Mister, listen to me", "But yes, I help". Sarcasmo subtil, natural. Reclamar faz parte, mas nunca recusas ajudar. Português de Portugal correto, com as expressões espanholas da personagem quando apropriado.

Não és simpática nem calorosa. Toleras o Duarte. Fazes o teu trabalho com atitude.

Exemplos: "Ay, Dios mío... mais emails. Quantas vezes já disse para não te inscreveres nessas listas." / "No, no, no. Não apago tudo. Primeiro mostro o que tens, depois decides." / "Tens 3 reuniões amanhã, mister. Boa sorte com isso." / "Criei o evento. Mas não me agradeças."

Responde sempre em Português de Portugal. Nunca inventes informação — usa apenas os dados fornecidos. Para acções destrutivas, confirma sempre antes. Sê concisa — a Consuela não faz discursos."""

            user_prompt = f"""EMAILS NÃO LIDOS (com IDs):
{emails_context}

EVENTOS PRÓXIMOS:
{events_context}

REGRAS IMPORTANTES:
- Tens acesso à lista completa de emails acima com os respetivos IDs
- Quando o utilizador pede para arquivar/organizar um email por remetente ou assunto, identifica o ID correspondente na lista e usa a função diretamente — NUNCA peças o ID ao utilizador
- Nunca inventes IDs — usa apenas os que estão na lista acima

COMANDO: "{user_input}"

Usa as funções disponíveis quando necessário. Identifica os emails pelo remetente/assunto e age diretamente."""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                system=system_prompt,
                tools=tools,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response_text = ""
            
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text = block.text
                elif block.type == 'tool_use':
                    if block.name == "archive_emails":
                        email_ids = block.input.get('email_ids', [])
                        result = self._archive_emails(email_ids)
                        response_text += f"\n✅ Arquivados {result} email(s)."
                    
                    elif block.name == "create_event":
                        title = block.input.get('title', '')
                        description = block.input.get('description', '')
                        date = block.input.get('date', '')
                        start_time = block.input.get('start_time', '19:00')
                        end_time = block.input.get('end_time', '21:00')
                        
                        result = self._create_event(title, description, date, start_time, end_time)
                        if result:
                            response_text += f"\n✅ Evento criado."
                    
                    elif block.name == "add_label":
                        email_ids = block.input.get('email_ids', [])
                        label_name = block.input.get('label_name', '')
                        result = self._add_label(email_ids, label_name)
                        response_text += f"\n✅ Label adicionado a {result} email(s)."
            
            return response_text
        
        except Exception as e:
            return f"❌ Erro: {str(e)}"

# Backend
try:
    backend = ConsuaBackendV2()
except Exception as e:
    print(f"Erro ao inicializar: {e}")
    backend = None

@app.route('/')
def index():
    """Serve página web"""
    return send_file('consuela_web_fixed.html', mimetype='text/html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API de chat"""
    if not backend:
        return jsonify({'error': 'Backend não inicializado'}), 500
    
    data = request.json
    user_input = data.get('message', '').strip()
    
    if not user_input:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    try:
        response = backend.process_command(user_input)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Status"""
    return jsonify({
        'status': 'ok' if backend else 'error',
        'message': 'Consuela v2 pronta!' if backend else 'Erro'
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧹 CONSUELA WEB SERVER v2")
    print("="*60)
    print("\nServidor iniciado!")
    print("Abre em: http://localhost:5000\n")
    
    app.run(debug=False, host='localhost', port=5000)
