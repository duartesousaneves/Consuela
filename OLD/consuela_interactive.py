#!/usr/bin/env python3
"""
CONSUELA INTERACTIVE - Chat em Linguagem Natural
Uma assistente "má" e sarcástica para gerir Gmail e Calendário
Personalidade: Consuela (Family Guy) - rude, sarcástica, divertida
Interface: Chat interativo em português natural
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import anthropic
import base64
from email.mime.text import MIMEText

# SCOPES
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
                'https://www.googleapis.com/auth/gmail.modify']
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar',
                   'https://www.googleapis.com/auth/calendar.readonly']
SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES

TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'

class ConsuaInteractive:
    """Consuela com interface conversacional em linguagem natural"""
    
    def __init__(self):
        self.creds = self._authenticate()
        from googleapiclient.discovery import build
        
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.client = anthropic.Anthropic()
        
        # Cache de emails para não fazer muitas requests
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
    
    def _get_emails(self, max_results=20, refresh=False):
        """Obtém emails com cache"""
        if self.cached_emails and not refresh:
            # Se cache tem menos de 5 minutos, usa cache
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
        """Processa comando em linguagem natural usando Claude"""
        
        # Obtém contexto: emails e eventos
        emails = self._get_emails(max_results=15)
        events = self._get_calendar_events(days=7)
        
        # Prepara contexto para Claude
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
        
        # Cria prompt para Claude
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
    
    def run_interactive(self):
        """Loop interativo de chat"""
        print("\n" + "="*60)
        print("🧹 CONSUELA - Chat Interativo")
        print("="*60)
        print("\nAy, mister... aqui estou. O que queres?")
        print("(Digita 'sair' para acabar)\n")
        
        while True:
            try:
                user_input = input("Você: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print("\nConsuela: Ay, finalmente! Agora deixa-me em paz. 👋")
                    break
                
                print("\nConsuela: ", end="", flush=True)
                response = self.process_command(user_input)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\n\nConsuela: Ay! Desligas-me assim? Mister, isto é desrespeitoso!")
                break
            except Exception as e:
                print(f"\n❌ Erro: {str(e)}")
                print("Tenta novamente...\n")

def main():
    """Função principal"""
    import sys
    
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ ERRO: Ficheiro 'credentials.json' não encontrado!")
        print("Coloca o ficheiro na mesma pasta do script.")
        return
    
    try:
        consuela = ConsuaInteractive()
        consuela.run_interactive()
    except Exception as e:
        print(f"❌ Erro ao inicializar: {str(e)}")
        print("Verifica se tens credenciais e conexão à internet.")

if __name__ == "__main__":
    main()
