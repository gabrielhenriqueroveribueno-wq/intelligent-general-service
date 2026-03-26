#!/usr/bin/env bash
# init-letsencrypt.sh
# Obtém certificado Let's Encrypt pela primeira vez usando certbot webroot.
# Uso: ./scripts/init-letsencrypt.sh yourdomain.com admin@yourdomain.com
#
# Pré-requisitos:
#   - Docker Compose rodando (ao menos nginx na porta 80)
#   - Domínio apontando para o servidor
#   - .env com DOMAIN definido (ou passar como arg)

set -euo pipefail

DOMAIN="${1:-${DOMAIN:-}}"
EMAIL="${2:-${CERTBOT_EMAIL:-}}"

if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "Uso: $0 <dominio> <email>"
  echo "  ou defina DOMAIN e CERTBOT_EMAIL no .env"
  exit 1
fi

CERTBOT_DIR="./certbot"
WEBROOT_DIR="${CERTBOT_DIR}/www"
CONF_DIR="${CERTBOT_DIR}/conf"

mkdir -p "${WEBROOT_DIR}" "${CONF_DIR}"

echo ">>> Gerando certificado para ${DOMAIN} (email: ${EMAIL})"

# Garante que nginx está rodando para o challenge webroot
docker compose -f docker-compose.prod.yml up -d nginx

# Aguarda nginx ficar pronto
echo ">>> Aguardando nginx..."
sleep 5

# Solicita certificado
docker run --rm \
  -v "${CONF_DIR}:/etc/letsencrypt" \
  -v "${WEBROOT_DIR}:/var/www/certbot" \
  certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email \
    -d "${DOMAIN}"

echo ""
echo ">>> Certificado obtido com sucesso!"
echo ">>> Reiniciando nginx com TLS..."

docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

echo ""
echo ">>> Pronto! Configure a renovação automática no cron do host:"
echo "    0 3 * * * cd $(pwd) && docker compose -f docker-compose.prod.yml run --rm certbot renew && docker compose -f docker-compose.prod.yml exec nginx nginx -s reload"
