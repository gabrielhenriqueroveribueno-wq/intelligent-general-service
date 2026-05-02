#!/usr/bin/env bash
# tunnel.sh — Inicia o Cloudflare Tunnel junto com o IGS
#
# Modo rápido (sem conta, URL muda ao reiniciar):
#   bash scripts/tunnel.sh
#
# Modo permanente (com token do Cloudflare Zero Trust):
#   CLOUDFLARE_TUNNEL_TOKEN=eyJ... bash scripts/tunnel.sh

set -euo pipefail

TOKEN="${CLOUDFLARE_TUNNEL_TOKEN:-}"

echo "════════════════════════════════════════"
echo "  IGS + Cloudflare Tunnel"
echo "════════════════════════════════════════"

# Sobe IGS (se não estiver rodando)
if ! docker compose ps api | grep -q "running"; then
  echo "▶ Subindo IGS..."
  docker compose up -d api celery-worker postgres redis
  sleep 5
fi

# Sobe o tunnel
if [ -n "$TOKEN" ]; then
  echo "▶ Iniciando tunnel permanente (token configurado)..."
  docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d cloudflared
  echo ""
  echo "  Tunnel permanente ativo."
  echo "  A URL está configurada no painel Cloudflare Zero Trust."
else
  echo "▶ Iniciando tunnel temporário (sem token)..."
  echo "  A URL aparecerá nos logs em ~5 segundos..."
  echo ""
  docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d cloudflared
  sleep 4
  echo "  ┌─────────────────────────────────────────────────────────────┐"
  echo "  │  URL do webhook (copie para o Meta Developer):              │"
  docker compose logs cloudflared 2>/dev/null | grep -o 'https://[^ ]*\.trycloudflare\.com' | tail -1 | xargs -I{} echo "  │  {}/api/v1/webhook/whatsapp                              │" || echo "  │  (aguarde mais alguns segundos e rode: docker compose logs cloudflared) │"
  echo "  └─────────────────────────────────────────────────────────────┘"
fi

echo ""
echo "  Para ver a URL: docker compose logs cloudflared | grep trycloudflare"
echo "  Para parar:     docker compose stop cloudflared"
echo ""
