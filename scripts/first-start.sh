#!/usr/bin/env bash
# first-start.sh — Primeiro boot do IGS após configurar o .env
# Execute dentro de /opt/igs após editar o .env:
#   cd /opt/igs && bash scripts/first-start.sh

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="docker compose -f docker-compose.prod-light.yml"

echo "════════════════════════════════════════"
echo "  IGS — Primeiro start"
echo "  $(date)"
echo "════════════════════════════════════════"

cd "$APP_DIR"

# Valida .env mínimo
check_var() {
  local val
  val=$(grep -E "^${1}=" .env | cut -d= -f2-)
  if [ -z "$val" ] || [[ "$val" == *"CHANGE_ME"* ]]; then
    echo "ERRO: $1 não configurado em .env"
    exit 1
  fi
}
check_var "ANTHROPIC_API_KEY"
check_var "JWT_SECRET_KEY"
check_var "ENCRYPTION_KEY"
check_var "POSTGRES_PASSWORD"
echo "▶ .env validado."

# Build das imagens
echo ""
echo "▶ Build das imagens Docker (pode levar 3-5 min na primeira vez)..."
$COMPOSE build --no-cache

# Sobe banco e redis primeiro
echo ""
echo "▶ Subindo banco e Redis..."
$COMPOSE up -d postgres redis
echo "  Aguardando banco ficar saudável..."
sleep 10

# Migrações
echo ""
echo "▶ Rodando migrações Alembic..."
$COMPOSE run --rm api alembic upgrade head

# Seed inicial
echo ""
echo "▶ Rodando seed inicial (super admin + tenant demo)..."
$COMPOSE run --rm api python scripts/seed_db.py || echo "  Seed já executado anteriormente."

# Sobe tudo
echo ""
echo "▶ Subindo todos os serviços..."
$COMPOSE up -d

echo ""
echo "▶ Status dos containers:"
$COMPOSE ps

DOMAIN=$(grep -E "^DOMAIN=" .env | cut -d= -f2- | tr -d '"' || echo "")
IP=$(curl -s ifconfig.me 2>/dev/null || echo "seu-ip")

echo ""
echo "════════════════════════════════════════"
echo "  IGS rodando!"
echo ""
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "localhost" ]; then
  echo "  API:     https://$DOMAIN"
  echo "  Docs:    https://$DOMAIN/docs"
  echo "  Webhook: https://$DOMAIN/api/v1/webhook/whatsapp"
else
  echo "  API:     http://$IP:8000  (configure DOMAIN= para HTTPS)"
  echo "  Docs:    http://$IP:8000/docs"
fi
echo ""
echo "  Credenciais padrão:"
echo "    Super Admin: admin@igs.com / Admin@123456"
echo ""
echo "  Para ver logs: docker compose -f docker-compose.prod-light.yml logs -f"
echo "════════════════════════════════════════"
