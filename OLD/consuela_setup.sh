#!/bin/bash

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Consuela welcome message
echo -e "${BLUE}"
echo "╔══════════════════════════════════════╗"
echo "║   🧹 CONSUELA - Email & Calendar    ║"
echo "║   Manager (Family Guy Edition)      ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# Função para imprimir com estilo
print_step() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check Python version
print_step "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 não encontrado. Instale Python 3.8 ou superior."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
print_success "Python $PYTHON_VERSION encontrado"

# Check if script exists
if [ ! -f "consuela_email_calendar.py" ]; then
    print_error "Script 'consuela_email_calendar.py' não encontrado na pasta atual!"
    exit 1
fi

# Main menu
show_menu() {
    echo ""
    echo -e "${YELLOW}=== MENU CONSUELA ===${NC}"
    echo "1) 📦 Instalar dependências"
    echo "2) 🔑 Configurar Google Cloud Credentials"
    echo "3) 📧 Executar - Verificar Emails"
    echo "4) 📅 Executar - Ver Calendário"
    echo "5) 🚀 Executar - Full Service (Emails + Calendário)"
    echo "6) ⏰ Agendar execução automática (cron)"
    echo "7) 🧹 Limpar logs e cache"
    echo "8) ❌ Sair"
    echo ""
    read -p "Escolhe uma opção (1-8): " choice
}

# Install dependencies
install_deps() {
    print_step "Instalando dependências Python..."
    pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client anthropic
    
    if [ $? -eq 0 ]; then
        print_success "Dependências instaladas com sucesso!"
    else
        print_error "Erro ao instalar dependências."
        exit 1
    fi
}

# Setup Google credentials
setup_credentials() {
    print_step "Setup de Google Cloud Credentials"
    echo ""
    echo "Siga estes passos:"
    echo "1. Ir a https://console.cloud.google.com/"
    echo "2. Criar um novo projeto chamado 'Consuela'"
    echo "3. Ativar Gmail API e Google Calendar API"
    echo "4. Ir para 'Credenciais' > 'Criar' > 'ID de cliente OAuth' > 'Desktop'"
    echo "5. Fazer download do ficheiro JSON"
    echo "6. Salvar como 'credentials.json' nesta pasta"
    echo ""
    
    if [ -f "credentials.json" ]; then
        print_success "credentials.json já existe!"
    else
        print_warning "credentials.json não encontrado. Espera o download..."
        read -p "Pressiona ENTER quando tiveres salvado credentials.json nesta pasta..."
        
        if [ ! -f "credentials.json" ]; then
            print_error "credentials.json ainda não encontrado!"
            exit 1
        else
            print_success "credentials.json encontrado!"
        fi
    fi
}

# Check API key
check_api_key() {
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        print_warning "Variável ANTHROPIC_API_KEY não está definida!"
        echo ""
        echo "Para definir:"
        echo "  export ANTHROPIC_API_KEY='tua-chave-aqui'"
        echo ""
        read -p "Quer definir agora? (s/n): " -r
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            read -p "Insere a tua chave API Anthropic: " api_key
            export ANTHROPIC_API_KEY="$api_key"
            print_success "API key definida temporariamente."
            echo "Para tornar permanente, adiciona ao ~/.bashrc ou ~/.zshrc:"
            echo "  export ANTHROPIC_API_KEY='$api_key'"
        fi
    else
        print_success "ANTHROPIC_API_KEY está definida"
    fi
}

# Run email check
run_emails() {
    check_api_key
    print_step "Executando verificação de emails..."
    python3 consuela_email_calendar.py check_emails
}

# Run calendar
run_calendar() {
    check_api_key
    print_step "Executando visualização de calendário..."
    python3 consuela_email_calendar.py calendar
}

# Run full service
run_full() {
    check_api_key
    print_step "Executando Full Service (Emails + Calendário)..."
    python3 consuela_email_calendar.py full_service
}

# Setup cron job
setup_cron() {
    print_step "Setup de agendamento automático (cron)"
    echo ""
    echo "Com que frequência?"
    echo "1) Diariamente às 9:00 AM"
    echo "2) A cada 2 horas"
    echo "3) De 2 em 2 dias às 9:00 AM"
    echo "4) Custom (digite a expressão cron)"
    read -p "Escolhe (1-4): " cron_choice
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
    CRON_CMD="cd $SCRIPT_DIR && /usr/bin/python3 $SCRIPT_DIR/consuela_email_calendar.py full_service >> $SCRIPT_DIR/consuela.log 2>&1"
    
    case $cron_choice in
        1) CRON_SCHEDULE="0 9 * * *" ;;
        2) CRON_SCHEDULE="0 */2 * * *" ;;
        3) CRON_SCHEDULE="0 9 */2 * *" ;;
        4) 
            read -p "Insere a expressão cron: " CRON_SCHEDULE
            ;;
        *)
            print_error "Opção inválida"
            return
            ;;
    esac
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_CMD") | crontab -
    
    print_success "Cron job agendado!"
    echo "Para verificar: crontab -l"
    echo "Para remover: crontab -e (e deleta a linha)"
}

# Clean cache
clean_cache() {
    print_step "Limpando cache e logs..."
    
    read -p "Remover token.pickle (vai obrigar a fazer login novamente)? (s/n): " -r
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -f token.pickle
        print_success "token.pickle removido"
    fi
    
    read -p "Limpar consuela.log? (s/n): " -r
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        > consuela.log
        print_success "consuela.log limpo"
    fi
    
    read -p "Limpar __pycache__? (s/n): " -r
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf __pycache__
        print_success "__pycache__ removido"
    fi
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1) install_deps ;;
        2) setup_credentials ;;
        3) run_emails ;;
        4) run_calendar ;;
        5) run_full ;;
        6) setup_cron ;;
        7) clean_cache ;;
        8) 
            print_success "Até logo! Consuela signing off... 👋"
            exit 0
            ;;
        *)
            print_error "Opção inválida. Tenta novamente."
            ;;
    esac
done
