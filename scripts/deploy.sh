#!/usr/bin/env bash
# deploy.sh — Deploy da IGS API para o servidor de produção via SSH
# Uso: DEPLOY_HOST=user@137.131.151.205 DEPLOY_PATH=/opt/igs bash scripts/deploy.sh
#
# Variáveis de ambiente necessárias:
#   DEPLOY_HOST  — ex: ubuntu@137.131.151.205
#   DEPLOY_PATH  — ex: /opt/igs (padrão: /opt/igs)
#   SSH_KEY      — caminho para chave privada (padrão: ~/.ssh/id_rsa)

set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/igs}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
COMPOSE_FILE="docker-compose.prod.yml"

if [[ -z "$DEPLOY_HOST" ]]; then
  echo "ERRO: variável DEPLOY_HOST não definida."
  echo "Uso: DEPLOY_HOST=ubuntu@IP bash scripts/deploy.sh"
  exit 1
fi

echo "=== IGS Deploy → $DEPLOY_HOST:$DEPLOY_PATH ==="

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$DEPLOY_HOST" bash <<REMOTE
set -euo pipefail

echo "--- Entrando em $DEPLOY_PATH ---"
cd "$DEPLOY_PATH"

echo "--- Atualizando código ---"
git fetch origin master
git reset --hard origin/master

echo "--- Baixando imagens atualizadas ---"
docker compose -f $COMPOSE_FILE pull --quiet

echo "--- Rodando migrações ---"
docker compose -f $COMPOSE_FILE run --rm api alembic upgrade head

echo "--- Rolling restart da API (zero-downtime) ---"
docker compose -f $COMPOSE_FILE up -d --no-deps --scale api=2 api
sleep 10
docker compose -f $COMPOSE_FILE up -d --no-deps --scale api=1 api

echo "--- Reiniciando workers ---"
docker compose -f $COMPOSE_FILE up -d --no-deps celery_worker
docker compose -f $COMPOSE_FILE up -d --no-deps celery_beat
docker compose -f $COMPOSE_FILE up -d --no-deps nginx

echo "--- Limpando imagens antigas ---"
docker image prune -f

echo "--- Deploy concluído: \$(date) ---"
REMOTE

echo ""
echo "✓ Deploy finalizado com sucesso!"
