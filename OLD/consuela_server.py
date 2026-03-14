#!/usr/bin/env python3
"""
CONSUELA WEB SERVER
Servidor Flask que serve a interface web e processa comandos
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from flask import Flask, send_file, request, jsonify
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

class ConsuaBackend:
    """Backend para processar comandos da Consuela"""
    
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
    
    def _get_emails(self, max_results=20):
        """Obtém emails com cache"""
        if self.cached_emails and self.cached_emails_time:
            if datetime.now() - self.cached_emails_time < timedelta(minutes=5):
                return self.cached_emails
        
        results = self.gmail_service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q="is:unread"
        ).execute()
        
        messages = results.get('messages', [])
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
                'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), '(sem assunto)'),
                'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                'body': self._get_email_body(msg)
            }
            emails.append(email_data)
        
        self.cached_emails = emails
        self.cached_emails_time = datetime.now()
        return emails
    
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
    
    def _get_calendar_events(self, days=7):
        """Obtém eventos do calendário"""
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
        """Processa comando em linguagem natural"""
        
        try:
            emails = self._get_emails(max_results=15)
            events = self._get_calendar_events(days=7)
            
            emails_context = json.dumps([
                {
                    'from': e['from'],
                    'subject': e['subject'],
                    'date': e['date'],
                    'preview': e['body'][:200]
                }
                for e in emails
            ], ensure_ascii=False, indent=2)
            
            events_context = json.dumps([
                {
                    'title': e['summary'],
                    'start': e['start'].get('dateTime', e['start'].get('date')),
                    'description': e.get('description', '')[:100]
                }
                for e in events
            ], ensure_ascii=False, indent=2)
            
            prompt = f"""Você é CONSUELA, uma assistente sarcástica, rude mas divertida do Family Guy.
O utilizador está a conversar contigo sobre os seus emails e calendário.

CONTEXTO ATUAL:
- Emails não lidos: {len(emails)}
- Eventos próximos (7 dias): {len(events)}

EMAILS RECENTES:
{emails_context}

EVENTOS PRÓXIMOS:
{events_context}

COMANDO DO UTILIZADOR: "{user_input}"

Responde em PORTUGUÊS com o tom sarcástico e rude da Consuela.
- Se pedir para filtrar/buscar: procura nos emails e resume
- Se pedir para sugestões: dá ideias com sarcasmo
- Se pedir info sobre calendário: mostra eventos relevantes
- Se fizer perguntas: responde com personalidade
- Sempre com o tom "Ay, mister..." ou similar

Sê conciso (máx 5-10 linhas), mas divertido!"""
            
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            return f"❌ Ay, mister... algo correu mal: {str(e)}"

# Instancia backend
try:
    backend = ConsuaBackend()
except Exception as e:
    print(f"Erro ao inicializar backend: {e}")
    backend = None

@app.route('/')
def index():
    """Serve a página web"""
    return send_file('consuela_web_fixed.html', mimetype='text/html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API para processar mensagens"""
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
    """Status da aplicação"""
    return jsonify({
        'status': 'ok' if backend else 'error',
        'message': 'Consuela está pronta!' if backend else 'Erro ao inicializar'
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧹 CONSUELA WEB SERVER")
    print("="*60)
    print("\nServidor iniciado!")
    print("Abre em: http://localhost:5000")
    print("\nPara parar: CTRL+C\n")
    
    app.run(debug=False, host='localhost', port=5000)
