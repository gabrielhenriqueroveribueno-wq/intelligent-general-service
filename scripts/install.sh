#!/usr/bin/env bash
# IGS — Intelligent General Service
# Instalador para novos clientes (Ubuntu 22.04+ / Debian 12+)
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/SEU-USUARIO/intelligent-general-service/master/scripts/install.sh | bash
#   ou local: bash scripts/install.sh

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[IGS]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[AVISO]${NC} $*"; }
error()   { echo -e "${RED}[ERRO]${NC} $*" >&2; exit 1; }

REPO_URL="${IGS_REPO:-https://github.com/SEU-USUARIO/intelligent-general-service}"
INSTALL_DIR="${IGS_DIR:-/opt/igs}"
COMPOSE_FILE="docker-compose.prod-light.yml"

# ─── Pre-checks ────────────────────────────────────────────────────────────────

[ "$(id -u)" -eq 0 ] || error "Execute como root: sudo bash $0"

OS=$(. /etc/os-release 2>/dev/null && echo "$ID" || echo "unknown")
[[ "$OS" =~ ^(ubuntu|debian)$ ]] || warn "Sistema $OS nao testado. Continuando..."

# ─── Instalar dependencias ──────────────────────────────────────────────────────

install_docker() {
    if command -v docker &>/dev/null; then
        success "Docker ja instalado: $(docker --version)"
        return
    fi
    info "Instalando Docker..."
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg lsb-release git
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/"$OS"/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/$OS $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable --now docker
    success "Docker instalado"
}

# ─── Clonar / atualizar repo ───────────────────────────────────────────────────

clone_repo() {
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Repositorio ja existe em $INSTALL_DIR — atualizando..."
        git -C "$INSTALL_DIR" fetch origin master
        git -C "$INSTALL_DIR" reset --hard origin/master
    else
        info "Clonando repositorio em $INSTALL_DIR..."
        git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    fi
    success "Codigo atualizado"
}

# ─── Coletar configuracoes ─────────────────────────────────────────────────────

collect_config() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Configuração IGS — ${YELLOW}$(hostname)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Dominio
    DEFAULT_DOMAIN=$(curl -s --max-time 3 ifconfig.me 2>/dev/null || echo "localhost")
    read -rp "Domínio ou IP público [$DEFAULT_DOMAIN]: " DOMAIN
    DOMAIN="${DOMAIN:-$DEFAULT_DOMAIN}"

    # Email (para Let's Encrypt — só usado se domínio real)
    read -rp "Email do administrador [admin@${DOMAIN}]: " ADMIN_EMAIL
    ADMIN_EMAIL="${ADMIN_EMAIL:-admin@${DOMAIN}}"

    # Nome da instituição
    read -rp "Nome da instituição [Instituição]: " INSTITUTION_NAME
    INSTITUTION_NAME="${INSTITUTION_NAME:-Instituição}"

    # Admin inicial
    read -rp "Email do admin do sistema [admin@igs.local]: " ADMIN_SYSTEM_EMAIL
    ADMIN_SYSTEM_EMAIL="${ADMIN_SYSTEM_EMAIL:-admin@igs.local}"
    read -rsp "Senha do admin (min 12 chars): " ADMIN_PASSWORD
    echo ""
    [ ${#ADMIN_PASSWORD} -ge 12 ] || error "Senha muito curta (min 12 chars)"

    # Chaves de API
    read -rp "Groq API Key (sk-...) ou ENTER para pular: " GROQ_API_KEY
    read -rp "Anthropic API Key (sk-ant-...) ou ENTER para pular: " ANTHROPIC_API_KEY

    # WhatsApp (opcional agora, pode configurar depois na UI)
    warn "WhatsApp pode ser configurado depois em Configurações > Configurar WhatsApp"
    read -rp "WhatsApp Phone Number ID (ou ENTER para configurar depois): " WA_PHONE_ID
    read -rsp "WhatsApp Token (ou ENTER para configurar depois): " WA_TOKEN
    echo ""
    read -rp "WhatsApp Verify Token [igs_verify_$(head -c6 /dev/urandom | base64 | tr -d '/+=' | head -c8)]: " WA_VERIFY_TOKEN
    WA_VERIFY_TOKEN="${WA_VERIFY_TOKEN:-igs_verify_$(head -c6 /dev/urandom | base64 | tr -d '/+=' | head -c8)}"
}

# ─── Gerar .env ────────────────────────────────────────────────────────────────

generate_env() {
    info "Gerando .env..."

    JWT_SECRET=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null \
        || docker run --rm python:3.12-alpine python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    DB_PASSWORD=$(openssl rand -hex 16)

    cat > "$INSTALL_DIR/.env" <<EOF
# Gerado automaticamente por install.sh em $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Instituição: $INSTITUTION_NAME

DOMAIN=$DOMAIN
ADMIN_EMAIL=$ADMIN_EMAIL

# Database
DATABASE_URL=postgresql+asyncpg://igs:${DB_PASSWORD}@postgres:5432/igs
POSTGRES_USER=igs
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=igs

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Auth
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256

# Encryption (credenciais do tenant)
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# AI
AI_PROVIDER=groq
GROQ_API_KEY=${GROQ_API_KEY:-}
GROQ_MODEL=llama-3.3-70b-versatile
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=${WA_PHONE_ID:-}
WHATSAPP_TOKEN=${WA_TOKEN:-}
WHATSAPP_VERIFY_TOKEN=${WA_VERIFY_TOKEN}

# CORS
CORS_ORIGINS=["https://${DOMAIN}","http://${DOMAIN}"]

# Env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
EOF

    chmod 600 "$INSTALL_DIR/.env"
    success ".env gerado em $INSTALL_DIR/.env"
}

# ─── Subir containers ─────────────────────────────────────────────────────────

start_services() {
    info "Construindo e subindo containers (pode demorar 5-10min na primeira vez)..."
    cd "$INSTALL_DIR"
    docker compose -f "$COMPOSE_FILE" pull --quiet 2>/dev/null || true
    docker compose -f "$COMPOSE_FILE" build --quiet
    docker compose -f "$COMPOSE_FILE" up -d
    success "Containers rodando"
}

# ─── Migrações + seed ─────────────────────────────────────────────────────────

setup_database() {
    info "Aguardando banco de dados..."
    until docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U igs -q 2>/dev/null; do
        printf '.'
        sleep 2
    done
    echo ""

    info "Rodando migrações..."
    docker compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head

    info "Criando tenant inicial: $INSTITUTION_NAME"
    docker compose -f "$COMPOSE_FILE" exec -T api python scripts/create_tenant.py \
        --name "$INSTITUTION_NAME" \
        --slug "$(echo "$INSTITUTION_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 20)" \
        --admin-email "$ADMIN_SYSTEM_EMAIL" \
        --admin-password "$ADMIN_PASSWORD" \
        2>/dev/null || warn "Tenant pode ja existir — pulando"

    success "Banco configurado"
}

# ─── Backup cron ──────────────────────────────────────────────────────────────

setup_backup() {
    info "Configurando backup automático..."
    bash "$INSTALL_DIR/scripts/setup-cron.sh" "$INSTALL_DIR"
    success "Backup agendado para 02:30 diário"
}

# ─── Verificação final ────────────────────────────────────────────────────────

health_check() {
    info "Verificando saúde do sistema (aguardando 15s)..."
    sleep 15

    HTTP=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/api/v1/health/ping" 2>/dev/null || echo "000")

    if [ "$HTTP" = "200" ]; then
        success "API respondendo (HTTP $HTTP)"
    else
        warn "API retornou HTTP $HTTP — pode ainda estar iniciando. Verifique: docker compose -f $INSTALL_DIR/$COMPOSE_FILE logs api"
    fi
}

# ─── Resumo final ─────────────────────────────────────────────────────────────

print_summary() {
    IS_IP=false
    [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] && IS_IP=true

    if $IS_IP; then
        PANEL_URL="http://$DOMAIN"
    else
        PANEL_URL="https://$DOMAIN"
    fi

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  IGS instalado com sucesso!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  Painel admin:   ${YELLOW}${PANEL_URL}${NC}"
    echo -e "  API (Swagger):  ${YELLOW}${PANEL_URL}/api/docs${NC}"
    echo -e "  Email:          ${ADMIN_SYSTEM_EMAIL}"
    echo -e "  Senha:          ${YELLOW}(a que você digitou)${NC}"
    echo ""
    echo -e "  Logs:    ${BLUE}docker compose -f $INSTALL_DIR/$COMPOSE_FILE logs -f${NC}"
    echo -e "  Status:  ${BLUE}docker compose -f $INSTALL_DIR/$COMPOSE_FILE ps${NC}"
    echo -e "  Restart: ${BLUE}docker compose -f $INSTALL_DIR/$COMPOSE_FILE restart${NC}"
    echo ""
    if $IS_IP; then
        warn "Usando IP direto — sem HTTPS. Para SSL, configure um domínio e edite DOMAIN no .env"
    fi
    echo -e "  Próximo passo: configure o WhatsApp em ${YELLOW}${PANEL_URL}/app/whatsapp-setup${NC}"
    echo ""
}

# ─── Main ─────────────────────────────────────────────────────────────────────

main() {
    echo ""
    echo -e "${BLUE}  ██╗ ██████╗ ███████╗${NC}"
    echo -e "${BLUE}  ██║██╔════╝ ██╔════╝${NC}"
    echo -e "${BLUE}  ██║██║  ███╗███████╗${NC}"
    echo -e "${BLUE}  ██║██║   ██║╚════██║${NC}"
    echo -e "${BLUE}  ██║╚██████╔╝███████║${NC}"
    echo -e "${BLUE}  ╚═╝ ╚═════╝ ╚══════╝  Intelligent General Service${NC}"
    echo ""

    install_docker
    clone_repo
    collect_config
    generate_env
    start_services
    setup_database
    setup_backup
    health_check
    print_summary
}

main "$@"
