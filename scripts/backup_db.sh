#!/usr/bin/env bash
# backup_db.sh
# Faz pg_dump do banco IGS, comprime e mantém os últimos 7 backups.
# Suporte opcional a upload via rclone (S3, GCS, etc.)
#
# Uso direto no host:  ./scripts/backup_db.sh
# Uso via Makefile:    make backup
# Uso via Docker:      docker compose exec postgres bash /backup_db.sh
#
# Variáveis de ambiente (herda do .env ou pode exportar antes):
#   POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#   BACKUP_DIR   — onde salvar (padrão: ./backups)
#   BACKUP_KEEP  — quantos backups manter (padrão: 7)
#   RCLONE_DEST  — destino rclone, ex: "s3:meu-bucket/igs-backups" (opcional)

set -euo pipefail

# ── Configurações ──────────────────────────────────────────────────
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-igs}"
POSTGRES_USER="${POSTGRES_USER:-igs}"
export PGPASSWORD="${POSTGRES_PASSWORD:-}"

BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/../backups}"
BACKUP_KEEP="${BACKUP_KEEP:-7}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="igs_backup_${TIMESTAMP}.sql.gz"
FILEPATH="${BACKUP_DIR}/${FILENAME}"

mkdir -p "${BACKUP_DIR}"

# ── Dump ──────────────────────────────────────────────────────────
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup: ${FILENAME}"

pg_dump \
  -h "${POSTGRES_HOST}" \
  -p "${POSTGRES_PORT}" \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  --no-owner \
  --no-acl \
  --format=plain \
  | gzip > "${FILEPATH}"

SIZE=$(du -sh "${FILEPATH}" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup concluído: ${FILEPATH} (${SIZE})"

# ── Upload remoto via rclone (opcional) ──────────────────────────
if [[ -n "${RCLONE_DEST:-}" ]]; then
  if command -v rclone &>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Enviando para ${RCLONE_DEST}..."
    rclone copy "${FILEPATH}" "${RCLONE_DEST}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Upload concluído."
  else
    echo "[WARN] rclone não encontrado, pulando upload remoto."
  fi
fi

# ── Rotação: mantém apenas os últimos N backups ───────────────────
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rotação: mantendo últimos ${BACKUP_KEEP} backups..."
ls -1t "${BACKUP_DIR}"/igs_backup_*.sql.gz 2>/dev/null | tail -n "+$((BACKUP_KEEP + 1))" | xargs -r rm -v

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup finalizado."
