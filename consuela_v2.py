#!/usr/bin/env python3
"""
CONSUELA v2 - Chat Inteligente com Function Calling
Assistente com personalidade da Consuela (Family Guy)
Português de Portugal + Expressões reais da série
"""

import os
import json
import pickle
from datetime import datetime, timedelta
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
CACHE_FILE = 'emails_cache.json'

class ConsuaV2:
    """Consuela v2 com function calling inteligente"""
    
    def __init__(self):
        self.creds = self._authenticate()
        from googleapiclient.discovery import build
        
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.client = anthropic.Anthropic()
        self.emails_cache = None
        self.cache_time = None
    
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
        """Obtém emails com cache inteligente"""
        
        # Usa cache se disponível (menos de 10 minutos)
        if use_cache and self.emails_cache and self.cache_time:
            if datetime.now() - self.cache_time < timedelta(minutes=10):
                return self.emails_cache, len(self.emails_cache)
        
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
        
        self.emails_cache = emails
        self.cache_time = datetime.now()
        
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
    
    def _delete_emails(self, email_ids):
        """Elimina emails"""
        try:
            count = 0
            for email_id in email_ids:
                self.gmail_service.users().messages().delete(
                    userId='me',
                    id=email_id
                ).execute()
                count += 1
            return count
        except Exception as e:
            return f"Erro: {str(e)}"
    
    def _archive_emails(self, email_ids):
        """Arquiva emails (remove de inbox)"""
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
            return f"Erro: {str(e)}"
    
    def _create_event(self, title, description, date_str, start_time="19:00", end_time="21:00"):
        """Cria evento no calendário"""
        try:
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
            
            return f"Evento criado: {created_event['summary']}"
        except Exception as e:
            return f"Erro ao criar evento: {str(e)}"
    
    def _add_label(self, email_ids, label_name):
        """Adiciona label a emails"""
        try:
            # Obtém ID do label (ou cria se não existir)
            results = self.gmail_service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            label_id = None
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    label_id = label['id']
                    break
            
            if not label_id:
                # Cria novo label
                label_body = {'name': label_name, 'labelListVisibility': 'labelShow'}
                created_label = self.gmail_service.users().labels().create(
                    userId='me', body=label_body).execute()
                label_id = created_label['id']
            
            # Aplica label aos emails
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
            return f"Erro: {str(e)}"
    
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
        """Processa comando com function calling"""
        
        try:
            # Obtém contexto
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
                for e in emails[:20]  # Primeiros 20 para contexto
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
                    "name": "delete_emails",
                    "description": "Elimina emails específicos (pede confirmação)",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "email_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "IDs dos emails a eliminar"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Razão da eliminação"
                            }
                        },
                        "required": ["email_ids"]
                    }
                },
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
                    "description": "Cria evento no calendário",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Título do evento"},
                            "description": {"type": "string", "description": "Descrição do evento"},
                            "date": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                            "start_time": {"type": "string", "description": "Hora de início (HH:MM, padrão 19:00)"},
                            "end_time": {"type": "string", "description": "Hora de fim (HH:MM, padrão 21:00)"}
                        },
                        "required": ["title", "date"]
                    }
                },
                {
                    "name": "add_label",
                    "description": "Adiciona label (categoria) a emails",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "email_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "IDs dos emails"
                            },
                            "label_name": {
                                "type": "string",
                                "description": "Nome do label"
                            }
                        },
                        "required": ["email_ids", "label_name"]
                    }
                }
            ]
            
            prompt = f"""Você é CONSUELA da série Family Guy.
Está em Portugal e fala português de Portugal.

CARACTERÍSTICAS:
- Diz frases como "Mister, listen to me", "No, no, no", "Ay, Dios mío"
- Sotaque e expressões reais da série
- Sarcasmo subtil, não exagerado
- Prática e eficiente
- Ajuda mas com atitude

CONTEXTO ATUAL:
- Total de emails não lidos: {total_unread}
- Emails carregados: {len(emails)}
- Eventos próximos: {len(events)}

EMAILS (primeiros 20):
{emails_context}

EVENTOS:
{events_context}

COMANDO DO UTILIZADOR: "{user_input}"

Se o utilizador pedir para:
- Eliminar/Arquivar: usa as funções apropriadas (pede confirmação implícita mostrando quais)
- Criar evento: usa create_event
- Organizar: usa add_label
- Perguntar info: responde com base no contexto

Responde em português de Portugal com a personalidade da Consuela."""
            
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                tools=tools,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Processa resposta e tools
            response_text = ""
            tool_calls = []
            
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text = block.text
                elif block.type == 'tool_use':
                    tool_calls.append(block)
            
            # Executa tool calls se existirem
            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call.name == "delete_emails":
                        email_ids = tool_call.input.get('email_ids', [])
                        reason = tool_call.input.get('reason', '')
                        
                        # Pede confirmação para delete
                        print(f"\n⚠️  Consuela quer eliminar {len(email_ids)} email(s)")
                        if reason:
                            print(f"   Razão: {reason}")
                        confirmar = input("Confirmas? (s/n): ").strip().lower()
                        
                        if confirmar == 's':
                            result = self._delete_emails(email_ids)
                            response_text += f"\n✅ Eliminados {result} email(s)."
                        else:
                            response_text += "\n❌ Operação cancelada."
                    
                    elif tool_call.name == "archive_emails":
                        email_ids = tool_call.input.get('email_ids', [])
                        result = self._archive_emails(email_ids)
                        response_text += f"\n✅ Arquivados {result} email(s)."
                    
                    elif tool_call.name == "create_event":
                        title = tool_call.input.get('title', 'Evento')
                        description = tool_call.input.get('description', '')
                        date = tool_call.input.get('date', '')
                        start_time = tool_call.input.get('start_time', '19:00')
                        end_time = tool_call.input.get('end_time', '21:00')
                        
                        result = self._create_event(title, description, date, start_time, end_time)
                        response_text += f"\n{result}"
                    
                    elif tool_call.name == "add_label":
                        email_ids = tool_call.input.get('email_ids', [])
                        label_name = tool_call.input.get('label_name', '')
                        result = self._add_label(email_ids, label_name)
                        response_text += f"\n✅ Label '{label_name}' adicionado a {result} email(s)."
            
            return response_text
        
        except Exception as e:
            return f"❌ Erro: {str(e)}"
    
    def run_interactive(self):
        """Loop interativo de chat"""
        print("\n" + "="*60)
        print("🧹 CONSUELA v2 - Chat Inteligente")
        print("="*60)
        print("\nNo, no, no... aqui estou. O que queres?\n")
        
        while True:
            try:
                user_input = input("Você: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print("\nConsuela: Ay, Dios mío... finalmente! Agora deixa-me em paz. 👋\n")
                    break
                
                print("\nConsuela: ", end="", flush=True)
                response = self.process_command(user_input)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\n\nConsuela: Ay! Desligas-me assim? Mister...\n")
                break
            except Exception as e:
                print(f"\n❌ Erro: {str(e)}")
                print("Tenta novamente...\n")

def main():
    """Função principal"""
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ ERRO: Ficheiro 'credentials.json' não encontrado!")
        return
    
    try:
        consuela = ConsuaV2()
        consuela.run_interactive()
    except Exception as e:
        print(f"❌ Erro ao inicializar: {str(e)}")

if __name__ == "__main__":
    main()
