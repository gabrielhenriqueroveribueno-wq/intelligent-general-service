#!/usr/bin/env bash
# setup-cron.sh — Configura cron jobs no servidor:
#   - Backup diário do PostgreSQL às 2:30
#   - Limpeza de backups antigos (mantém 7)
#
# Uso: bash scripts/setup-cron.sh
# Executa automaticamente pelo first-start.sh

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$APP_DIR/backups"

mkdir -p "$BACKUP_DIR"

# Script wrapper que roda dentro do container postgres
BACKUP_WRAPPER="$APP_DIR/scripts/_backup_cron.sh"

cat > "$BACKUP_WRAPPER" << 'WRAPPER'
#!/usr/bin/env bash
# Executado pelo cron — não editar manualmente
set -euo pipefail

APP_DIR="/opt/igs"
BACKUP_DIR="$APP_DIR/backups"
KEEP=7

mkdir -p "$BACKUP_DIR"

# Carrega variáveis do .env
if [ -f "$APP_DIR/.env" ]; then
    export $(grep -E "^POSTGRES_(DB|USER|PASSWORD)=" "$APP_DIR/.env" | xargs)
fi

POSTGRES_DB="${POSTGRES_DB:-igs_db}"
POSTGRES_USER="${POSTGRES_USER:-igs_user}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="igs_backup_${TIMESTAMP}.sql.gz"
FILEPATH="$BACKUP_DIR/$FILENAME"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup: $FILENAME"

docker exec igs_postgres \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl \
    | gzip > "$FILEPATH"

SIZE=$(du -sh "$FILEPATH" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup concluído: $FILEPATH ($SIZE)"

# Rotação: mantém apenas os últimos N backups
ls -1t "$BACKUP_DIR"/igs_backup_*.sql.gz 2>/dev/null \
    | tail -n "+$((KEEP + 1))" \
    | xargs -r rm -v

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rotação aplicada. Backups mantidos: $KEEP"
WRAPPER

chmod +x "$BACKUP_WRAPPER"

# Instala cron job (idempotente)
CRON_LINE="30 2 * * * /bin/bash $BACKUP_WRAPPER >> $APP_DIR/backups/backup.log 2>&1"

# Remove linha antiga se existir, adiciona nova
(crontab -l 2>/dev/null | grep -v "_backup_cron.sh" ; echo "$CRON_LINE") | crontab -

echo "✓ Cron de backup configurado: todos os dias às 02:30"
echo "  Backups salvos em: $BACKUP_DIR"
echo "  Logs em: $BACKUP_DIR/backup.log"
echo "  Para executar agora: bash $BACKUP_WRAPPER"
