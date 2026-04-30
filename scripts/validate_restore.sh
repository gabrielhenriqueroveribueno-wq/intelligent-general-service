#!/usr/bin/env bash
# validate_restore.sh — Valida se o último backup pode ser restaurado com sucesso
#
# Uso: bash scripts/validate_restore.sh [/caminho/para/backup.sql.gz]
#
# Se nenhum arquivo for passado, usa o backup mais recente em /backups/
# Requer: pg_restore/psql, acesso ao PostgreSQL configurado via env vars ou .env

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TEST_DB="igs_restore_test_$$"
PGHOST="${PGHOST:-postgres}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-igs_user}"
PGPASSWORD="${PGPASSWORD:-}"
POSTGRES_SUPERUSER="${POSTGRES_SUPERUSER:-postgres}"

# Carrega .env se existir
if [[ -f .env ]]; then
  export $(grep -E '^(POSTGRES_|PGPASSWORD)' .env | xargs) 2>/dev/null || true
fi

# Determina arquivo de backup
if [[ -n "${1:-}" ]]; then
  BACKUP_FILE="$1"
else
  BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -n1)
  if [[ -z "$BACKUP_FILE" ]]; then
    echo "ERRO: Nenhum backup encontrado em $BACKUP_DIR"
    echo "Uso: $0 /caminho/backup.sql.gz"
    exit 1
  fi
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "ERRO: Arquivo não encontrado: $BACKUP_FILE"
  exit 1
fi

echo "=== IGS Validate Restore ==="
echo "Backup: $BACKUP_FILE"
echo "DB teste: $TEST_DB"
echo ""

export PGPASSWORD

cleanup() {
  echo "--- Removendo banco de teste ---"
  psql -h "$PGHOST" -p "$PGPORT" -U "$POSTGRES_SUPERUSER" -c "DROP DATABASE IF EXISTS $TEST_DB;" 2>/dev/null || true
}
trap cleanup EXIT

echo "--- Criando banco temporário ---"
psql -h "$PGHOST" -p "$PGPORT" -U "$POSTGRES_SUPERUSER" -c "CREATE DATABASE $TEST_DB;"

echo "--- Restaurando backup ---"
if [[ "$BACKUP_FILE" == *.gz ]]; then
  gunzip -c "$BACKUP_FILE" | psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TEST_DB" -v ON_ERROR_STOP=0 -q
else
  psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TEST_DB" -f "$BACKUP_FILE" -v ON_ERROR_STOP=0 -q
fi

echo "--- Verificando tabelas críticas ---"
TABLES=("tenants" "users" "students" "employees" "conversations" "tickets" "kb_articles")

MISSING=0
for table in "${TABLES[@]}"; do
  count=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TEST_DB" -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='$table';" 2>/dev/null || echo "0")
  if [[ "$count" == "1" ]]; then
    rows=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$TEST_DB" -tAc "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "?")
    echo "  ✓ $table ($rows rows)"
  else
    echo "  ✗ $table — AUSENTE"
    MISSING=$((MISSING + 1))
  fi
done

echo ""
if [[ "$MISSING" -eq 0 ]]; then
  echo "✓ Restore validado com sucesso! Todas as $((${#TABLES[@]})) tabelas críticas presentes."
  echo "  Backup: $BACKUP_FILE"
  echo "  Data:   $(date)"
  exit 0
else
  echo "✗ Restore FALHOU: $MISSING tabela(s) ausente(s)."
  exit 1
fi
