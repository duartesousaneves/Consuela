#!/usr/bin/env python3
"""
CONSUELA - Email & Calendar Manager
Uma assistente "má" e sarcástica para gerir o teu Gmail e Calendário
Personalidade: Consuela (Family Guy) - rude, sarcástica, divertida
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_core.client_options import ClientOptions
import anthropic
import base64
from email.mime.text import MIMEText
import re

# SCOPES para Gmail e Google Calendar
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
                'https://www.googleapis.com/auth/gmail.modify']
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar',
                   'https://www.googleapis.com/auth/calendar.readonly']
SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES

TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'

# Dicionário de personalidade da Consuela
CONSUELA_PERSONALITY = {
    "greetings": [
        "Mister, listen to me...",
        "Ay, Dios mío, what do you want now?",
        "No, no, no... but yes, I help you.",
    ],
    "sarcasm": [
        "Claro, porque nada é fácil na vida, verdade?",
        "Ay, que maravilha... outro email importante.",
        "Sim, sim, deixa-me ver o teu caos...",
        "Mister, você é um desastre. Deixa comigo.",
    ],
    "goodbye": [
        "Agora deixa-me em paz, tenho coisas melhores para fazer.",
        "Tá tudo pronto. Volto quando precisares de mais caos organizado.",
        "Ay, que trabalho... mas pronto, está feito.",
    ]
}

class ConsuaAuth:
    """Gestão de autenticação OAuth2 para Google APIs"""
    
    @staticmethod
    def authenticate():
        """Autentica com Google usando OAuth2"""
        creds = None
        
        # Se já existe token salvo, carrega-o
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # Se não tem credenciais válidas, faz login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Salva o token para próximas execuções
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds

class ConsuaEmailManager:
    """Gestor de Gmail com critérios de importância"""
    
    # Critérios para marcar emails como importantes
    CRITERIA = {
        "shows": {
            "keywords": ["cinema", "teatro", "concerto", "show", "espetáculo", "bilhete", 
                        "evento", "festival", "musical", "ópera", "dança", "comedy"],
            "description": "📽️ Email sobre espetáculos/eventos"
        },
        "senders": {
            "keywords": ["amigo@", "colega@", "boss@", "cliente@", "família@"],
            "description": "👤 Email de remetente importante"
        },
        "urgent": {
            "keywords": ["urgente", "importante", "deadline", "asap", "emergência", 
                        "deadline", "prioridade", "crítico"],
            "description": "⚠️ Email urgente/importante"
        },
        "bookings": {
            "keywords": ["confirmação", "booking", "reserva", "compra", "pedido", 
                        "order", "confirmation", "purchase"],
            "description": "🎫 Email de confirmação/reserva"
        }
    }
    
    def __init__(self, service):
        self.service = service
        self.client = anthropic.Anthropic()
    
    def get_recent_emails(self, max_results=10):
        """Obtém emails recentes"""
        results = self.service.users().messages().list(
            userId='me', 
            maxResults=max_results,
            q="is:unread"
        ).execute()
        
        messages = results.get('messages', [])
        emails = []
        
        for message in messages:
            msg = self.service.users().messages().get(
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
        
        return emails
    
    def _get_email_body(self, msg):
        """Extrai o corpo do email"""
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
    
    def classify_email_importance(self, email):
        """Classifica a importância do email baseado em critérios"""
        subject = email['subject'].lower()
        body = email['body'].lower()
        sender = email['from'].lower()
        text_combined = f"{subject} {body} {sender}"
        
        matched_criteria = []
        
        for criterion_key, criterion_data in self.CRITERIA.items():
            for keyword in criterion_data['keywords']:
                if keyword.lower() in text_combined:
                    matched_criteria.append({
                        'type': criterion_key,
                        'description': criterion_data['description'],
                        'keyword': keyword
                    })
                    break
        
        return matched_criteria
    
    def analyze_with_claude(self, emails):
        """Usa Claude para análise e resumo inteligente com personalidade Consuela"""
        
        email_summaries = []
        important_emails = []
        
        for email in emails:
            criteria = self.classify_email_importance(email)
            
            if criteria:
                important_emails.append({
                    'email': email,
                    'criteria': criteria
                })
        
        if not important_emails:
            return {
                "message": "Nenhum email importante encontrado. Mister, as tuas coisas estão... organizadas!",
                "emails": []
            }
        
        # Usa Claude para análise
        prompt = f"""Você é CONSUELA, uma assistente sarcástica, rude mas divertida do Family Guy.
Analise estes emails importantes e responda em PORTUGUÊS com o tom dela.

Comece com uma saudação sarcástica da Consuela. Depois, resuma os emails em pontos-chave.
Se há emails sobre espetáculos, destaque-os para adicionar ao calendário.
Termine com uma despedida rude mas divertida.

Emails importantes:
{json.dumps([{'from': e['email']['from'], 'subject': e['email']['subject'], 'criteria': e['criteria']} for e in important_emails], ensure_ascii=False, indent=2)}

Responda em tom SARCÁSTICO E RUDE como a Consuela faria."""
        
        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return {
            "analysis": message.content[0].text,
            "important_emails": important_emails
        }

class ConsuaCalendarManager:
    """Gestor de Google Calendar"""
    
    def __init__(self, service):
        self.service = service
    
    def get_upcoming_events(self, days=7):
        """Obtém eventos dos próximos dias"""
        now = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    
    def create_event(self, title, description, date_str, start_time="19:00", end_time="21:00"):
        """Cria um novo evento no calendário"""
        try:
            # Parse da data (formato: YYYY-MM-DD)
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
            
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return created_event
        except Exception as e:
            return None

class Consuela:
    """Assistente principal - A Consuela"""
    
    def __init__(self):
        self.creds = ConsuaAuth.authenticate()
        # Importa Google services após autenticação
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        
        self.email_manager = ConsuaEmailManager(self.gmail_service)
        self.calendar_manager = ConsuaCalendarManager(self.calendar_service)
        self.client = anthropic.Anthropic()
    
    def run(self, action="check_emails"):
        """Executa ações da Consuela"""
        
        print("\n" + "="*60)
        print(f"🧹 CONSUELA - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("="*60 + "\n")
        
        if action == "check_emails":
            self.check_important_emails()
        elif action == "calendar":
            self.show_calendar()
        elif action == "full_service":
            self.check_important_emails()
            print("\n" + "-"*60 + "\n")
            self.show_calendar()
    
    def check_important_emails(self):
        """Verifica e analisa emails importantes"""
        print("📧 Verificando os teus emails...\n")
        
        emails = self.email_manager.get_recent_emails(max_results=15)
        
        if not emails:
            print("Nenhum email não lido. Mister, parece que estás em dia... por enquanto.")
            return
        
        result = self.email_manager.analyze_with_claude(emails)
        
        print(result['analysis'])
        print("\n")
        
        # Se há emails sobre espetáculos, oferece adicionar ao calendário
        if result['important_emails']:
            for item in result['important_emails']:
                for criterion in item['criteria']:
                    if criterion['type'] == 'shows':
                        self._offer_add_to_calendar(item['email'])
                        break
    
    def _offer_add_to_calendar(self, email):
        """Oferece adicionar evento ao calendário com confirmação"""
        print(f"\n📍 Espera... encontrei um email sobre um espetáculo:")
        print(f"   De: {email['from']}")
        print(f"   Assunto: {email['subject']}")
        print(f"\n   Quer adicionar isto ao calendário? (s/n): ", end="")
        
        response = input().strip().lower()
        
        if response == 's':
            print(f"\n   Quando é? (formato: YYYY-MM-DD): ", end="")
            date = input().strip()
            
            print(f"   Hora? (formato: HH:MM, padrão 19:00): ", end="")
            time_str = input().strip() or "19:00"
            
            event = self.calendar_manager.create_event(
                title=email['subject'][:50],
                description=email['body'][:200],
                date_str=date,
                start_time=time_str
            )
            
            if event:
                print(f"\n   ✅ Pronto! Adicionado ao calendário: {event['summary']}")
            else:
                print(f"\n   ❌ Erro ao adicionar ao calendário. Mister, tenta novamente.")
    
    def show_calendar(self):
        """Mostra eventos próximos do calendário"""
        print("📅 Teus eventos dos próximos 7 dias:\n")
        
        events = self.calendar_manager.get_upcoming_events(days=7)
        
        if not events:
            print("Ay, que vazio... nenhum evento agendado.")
            return
        
        for i, event in enumerate(events, 1):
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"{i}. {event['summary']}")
            print(f"   📍 {start}")
            if 'description' in event:
                print(f"   📝 {event['description'][:100]}")
            print()

def main():
    """Função principal"""
    import sys
    
    # Verifica se credenciais existem
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ ERRO: Ficheiro 'credentials.json' não encontrado!")
        print("\nSeguir estes passos:")
        print("1. Ir a https://console.cloud.google.com/")
        print("2. Criar um novo projeto")
        print("3. Ativar Gmail API e Google Calendar API")
        print("4. Criar credenciais OAuth 2.0 (Desktop app)")
        print("5. Baixar o ficheiro e salvar como 'credentials.json'")
        return
    
    consuela = Consuela()
    
    # Se tem argumentos, usa-os como ação
    if len(sys.argv) > 1:
        action = sys.argv[1]
    else:
        action = "full_service"  # Padrão: verifica tudo
    
    consuela.run(action=action)

if __name__ == "__main__":
    main()
