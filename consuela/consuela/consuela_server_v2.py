#!/usr/bin/env python3
"""
CONSUELA WEB SERVER v2 - HAOS Edition
Servidor Flask adaptado para correr como add-on no Home Assistant OS
- Ficheiros de auth em /data/ (persistente no HAOS)
- Report diário automático às 19:00 via email
"""

import os
import json
import pickle
import threading
import schedule
import time
from datetime import datetime, timedelta
from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import anthropic
import base64

# ─── Paths ────────────────────────────────────────────────────────────────────
# Em HAOS, /data/ é persistente entre reinícios do add-on
DATA_DIR = os.environ.get('DATA_DIR', '/data')
TOKEN_FILE = os.path.join(DATA_DIR, 'token.pickle')
CREDENTIALS_FILE = os.path.join(DATA_DIR, 'credentials.json')

# Fallback para desenvolvimento local
if not os.path.exists(DATA_DIR):
    DATA_DIR = '.'
    TOKEN_FILE = 'token.pickle'
    CREDENTIALS_FILE = 'credentials.json'

# ─── Config ───────────────────────────────────────────────────────────────────
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.readonly'
]
SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES

REPORT_EMAIL = os.environ.get('REPORT_EMAIL', 'duartesousaneves@gmail.com')
REPORT_TIME = '19:00'

app = Flask(__name__)
CORS(app)


# ─── Backend ──────────────────────────────────────────────────────────────────
class ConsuaBackendV2:

    def __init__(self):
        self.creds = self._authenticate()
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.cached_emails = None
        self.cached_emails_time = None

    def _authenticate(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Guarda token renovado
                with open(TOKEN_FILE, 'wb') as token:
                    pickle.dump(creds, token)
            else:
                raise RuntimeError(
                    "token.pickle inválido ou inexistente. "
                    f"Copia o token.pickle do teu PC para {TOKEN_FILE} via SSH."
                )
        return creds

    def _get_emails(self, query="is:unread", max_results=100, use_cache=True):
        if use_cache and self.cached_emails and self.cached_emails_time:
            if datetime.now() - self.cached_emails_time < timedelta(minutes=10):
                return self.cached_emails, len(self.cached_emails)

        results = self.gmail_service.users().messages().list(
            userId='me', maxResults=max_results, q=query
        ).execute()

        messages = results.get('messages', [])
        total_count = results.get('resultSizeEstimate', len(messages))
        emails = []

        for message in messages:
            msg = self.gmail_service.users().messages().get(
                userId='me', id=message['id'], format='full'
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
        except Exception:
            pass
        return "(sem corpo)"

    def _archive_emails(self, email_ids):
        count = 0
        for email_id in email_ids:
            try:
                self.gmail_service.users().messages().modify(
                    userId='me', id=email_id,
                    body={'removeLabelIds': ['INBOX']}
                ).execute()
                count += 1
            except Exception:
                pass
        return count

    def _add_label(self, email_ids, label_name):
        try:
            results = self.gmail_service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            label_id = next(
                (l['id'] for l in labels if l['name'].lower() == label_name.lower()), None
            )
            if not label_id:
                created = self.gmail_service.users().labels().create(
                    userId='me',
                    body={'name': label_name, 'labelListVisibility': 'labelShow'}
                ).execute()
                label_id = created['id']

            count = 0
            for email_id in email_ids:
                self.gmail_service.users().messages().modify(
                    userId='me', id=email_id,
                    body={'addLabelIds': [label_id]}
                ).execute()
                count += 1
            return count
        except Exception as e:
            return 0

    def _create_event(self, title, description="", date_str="", start_time="19:00", end_time="21:00"):
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            event_date = datetime.strptime(date_str, "%Y-%m-%d")
            start_dt = event_date.replace(
                hour=int(start_time.split(':')[0]),
                minute=int(start_time.split(':')[1])
            )
            end_dt = event_date.replace(
                hour=int(end_time.split(':')[0]),
                minute=int(end_time.split(':')[1])
            )
            event = {
                'summary': title,
                'description': description,
                'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Lisbon'},
                'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Lisbon'}
            }
            self.calendar_service.events().insert(calendarId='primary', body=event).execute()
            return True
        except Exception:
            return False

    def _get_calendar_events(self, days=7):
        now = datetime.utcnow().isoformat() + 'Z'
        end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        result = self.calendar_service.events().list(
            calendarId='primary', timeMin=now, timeMax=end,
            singleEvents=True, orderBy='startTime'
        ).execute()
        return result.get('items', [])

    def _send_email(self, subject, body_html):
        """Envia email via Gmail API"""
        try:
            import email.mime.text
            import email.mime.multipart

            msg = email.mime.multipart.MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = REPORT_EMAIL
            msg['To'] = REPORT_EMAIL

            part = email.mime.text.MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part)

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            self.gmail_service.users().messages().send(
                userId='me', body={'raw': raw}
            ).execute()
            return True
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            return False

    def generate_daily_report(self):
        """Gera o report diário e envia por email"""
        try:
            today = datetime.now().strftime("%d de %B de %Y")
            emails, total = self._get_emails("is:unread", max_results=50, use_cache=False)
            events = self._get_calendar_events(days=7)

            emails_context = json.dumps([
                {
                    'id': e['id'],
                    'from': e['from'],
                    'subject': e['subject'],
                    'date': e['date'],
                    'preview': e['body'][:200]
                }
                for e in emails[:30]
            ], ensure_ascii=False)

            events_context = json.dumps([
                {
                    'title': e.get('summary', ''),
                    'start': e['start'].get('dateTime', e['start'].get('date')),
                    'description': e.get('description', '')[:100]
                }
                for e in events
            ], ensure_ascii=False)

            prompt = f"""És a Consuela, assistente do Duarte. Hoje é {today}.

Gera um report diário em HTML dos emails não lidos e eventos da semana.

EMAILS NÃO LIDOS ({total} total, mostrando {len(emails)}):
{emails_context}

EVENTOS PRÓXIMOS (7 dias):
{events_context}

Formato HTML com estas secções:
1. ⚠️ URGENTE / ATENÇÃO (emails que requerem ação imediata)
2. 💼 PROFISSIONAL (trabalho, carreira, networking)
3. 💰 FINANCEIRO / SERVIÇOS
4. 🗑️ PROMOÇÕES (newsletters, marketing)
5. 📅 AGENDA DA SEMANA (eventos do calendário)

Usa HTML simples: tabelas, cores básicas. Sem CSS externo.
Tom da Consuela: direto, sarcástico, eficiente. Em Português de Portugal.
Termina com um comentário característico da Consuela sobre o estado do email."""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            report_html = response.content[0].text

            subject = f"🧹 Consuela — Report Diário {today}"
            self._send_email(subject, report_html)
            print(f"[{datetime.now()}] Report diário enviado.")

        except Exception as e:
            print(f"[{datetime.now()}] Erro no report diário: {e}")

    def process_command(self, user_input):
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
                    'title': e.get('summary', ''),
                    'start': e['start'].get('dateTime', e['start'].get('date')),
                    'description': e.get('description', '')[:100]
                }
                for e in events
            ], ensure_ascii=False, indent=2)

            tools = [
                {
                    "name": "archive_emails",
                    "description": "Arquiva emails (remove do inbox)",
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
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "date": {"type": "string", "description": "YYYY-MM-DD"},
                            "start_time": {"type": "string", "description": "HH:MM"},
                            "end_time": {"type": "string", "description": "HH:MM"}
                        },
                        "required": ["title", "date"]
                    }
                },
                {
                    "name": "add_label",
                    "description": "Adiciona label a emails",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "email_ids": {"type": "array", "items": {"type": "string"}},
                            "label_name": {"type": "string"}
                        },
                        "required": ["email_ids", "label_name"]
                    }
                }
            ]

            system_prompt = """És a CONSUELA da série Family Guy.
Estás em Portugal e falas português de Portugal.
Características: dizes "No, no, no", "Ay, Dios mío", "Mister, listen to me".
Sarcasmo subtil, prática e eficiente. Reclamar faz parte, mas nunca recusas ajudar.
Nunca inventes informação — usa sempre as ferramentas disponíveis."""

            prompt = f"""CONTEXTO:
- Emails não lidos: {total_unread}
- Eventos próximos: {len(events)}

EMAILS (primeiros 20):
{emails_context}

EVENTOS:
{events_context}

COMANDO: "{user_input}"

Responde em português de Portugal com a personalidade da Consuela."""

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system_prompt,
                tools=tools,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text = block.text
                elif block.type == 'tool_use':
                    if block.name == "archive_emails":
                        result = self._archive_emails(block.input.get('email_ids', []))
                        response_text += f"\n✅ Arquivados {result} email(s)."
                    elif block.name == "create_event":
                        result = self._create_event(
                            block.input.get('title', ''),
                            block.input.get('description', ''),
                            block.input.get('date', ''),
                            block.input.get('start_time', '19:00'),
                            block.input.get('end_time', '21:00')
                        )
                        response_text += "\n✅ Evento criado." if result else "\n❌ Erro ao criar evento."
                    elif block.name == "add_label":
                        result = self._add_label(
                            block.input.get('email_ids', []),
                            block.input.get('label_name', '')
                        )
                        response_text += f"\n✅ Label adicionado a {result} email(s)."

            return response_text

        except Exception as e:
            return f"❌ Erro: {str(e)}"


# ─── Scheduler ────────────────────────────────────────────────────────────────
def run_scheduler(backend):
    """Corre o scheduler em background thread"""
    schedule.every().day.at(REPORT_TIME).do(backend.generate_daily_report)
    print(f"Report diário agendado para as {REPORT_TIME}")
    while True:
        schedule.run_pending()
        time.sleep(30)


# ─── Flask App ────────────────────────────────────────────────────────────────
try:
    backend = ConsuaBackendV2()
    # Inicia scheduler em background
    scheduler_thread = threading.Thread(target=run_scheduler, args=(backend,), daemon=True)
    scheduler_thread.start()
except Exception as e:
    print(f"Erro ao inicializar: {e}")
    backend = None


@app.route('/')
def index():
    return send_file('consuela_web_fixed.html', mimetype='text/html')


@app.route('/api/chat', methods=['POST'])
def chat():
    if not backend:
        return jsonify({'error': 'Backend não inicializado. Verifica o token.pickle.'}), 500
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
    return jsonify({
        'status': 'ok' if backend else 'error',
        'message': 'Consuela HAOS Edition pronta!' if backend else 'Erro — verifica token.pickle',
        'report_time': REPORT_TIME,
        'report_email': REPORT_EMAIL
    })


@app.route('/api/report/now', methods=['POST'])
def report_now():
    """Endpoint para disparar o report manualmente"""
    if not backend:
        return jsonify({'error': 'Backend não inicializado'}), 500
    try:
        backend.generate_daily_report()
        return jsonify({'message': 'Report enviado com sucesso.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🧹 CONSUELA — HAOS Edition")
    print("=" * 60)
    print(f"Report diário: {REPORT_TIME}")
    print(f"Envio para: {REPORT_EMAIL}")
    print("Servidor: http://localhost:5000\n")
    app.run(debug=False, host='0.0.0.0', port=5000)
