"""
Backup diário do PostgreSQL com upload opcional para S3/Backblaze B2.

Variáveis de ambiente:
  BACKUP_DIR        — pasta local para os arquivos (default: /app/backups)
  BACKUP_KEEP       — quantos backups locais manter (default: 7)
  BACKUP_S3_BUCKET  — nome do bucket S3/B2; se vazio, só salva local
  BACKUP_S3_PREFIX  — prefixo de pasta no bucket (default: igs-backups/)
  AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION — credenciais AWS
  BACKUP_S3_ENDPOINT_URL — endpoint alternativo (para B2: https://s3.us-west-001.backblazeb2.com)
"""

import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/app/backups"))
BACKUP_KEEP = int(os.getenv("BACKUP_KEEP", "7"))
S3_BUCKET = os.getenv("BACKUP_S3_BUCKET", "")
S3_PREFIX = os.getenv("BACKUP_S3_PREFIX", "igs-backups/")
S3_ENDPOINT = os.getenv("BACKUP_S3_ENDPOINT_URL", "")


def _upload_to_s3(filepath: Path, bucket: str, key: str) -> None:
    """Faz upload do arquivo para S3 ou B2 (endpoint compatível com S3 API)."""
    import boto3
    from botocore.config import Config

    kwargs: dict = {
        "service_name": "s3",
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region_name": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        "config": Config(signature_version="s3v4"),
    }
    if S3_ENDPOINT:
        kwargs["endpoint_url"] = S3_ENDPOINT

    s3 = boto3.client(**kwargs)
    s3.upload_file(str(filepath), bucket, key)
    logger.info("Backup enviado para s3://%s/%s", bucket, key)


@celery_app.task(name="app.tasks.backup_tasks.backup_database_task")
def backup_database_task() -> str:
    """Executa pg_dump, comprime, salva local e (opcional) envia para S3/B2."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"igs_backup_{timestamp}.sql.gz"
    filepath = BACKUP_DIR / filename

    db_url = os.getenv("DATABASE_URL", "")
    try:
        from urllib.parse import urlparse

        parsed = urlparse(db_url.replace("postgresql+asyncpg://", "postgresql://"))
        host = parsed.hostname or "localhost"
        port = str(parsed.port or 5432)
        user = parsed.username or "igs"
        password = parsed.password or ""
        database = (parsed.path or "/igs").lstrip("/")
    except Exception as exc:
        logger.error("Erro ao parsear DATABASE_URL: %s", exc)
        raise

    env = {**os.environ, "PGPASSWORD": password}

    dump_cmd = [
        "pg_dump",
        "-h",
        host,
        "-p",
        port,
        "-U",
        user,
        "-d",
        database,
        "--no-owner",
        "--no-acl",
        "--format=plain",
    ]

    logger.info("Iniciando backup do banco: %s", filename)

    with open(filepath, "wb") as out_file:
        dump_proc = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, env=env)
        gzip_proc = subprocess.Popen(["gzip"], stdin=dump_proc.stdout, stdout=out_file)
        dump_proc.stdout.close()  # type: ignore[union-attr]
        gzip_proc.communicate()
        dump_proc.wait()

    if dump_proc.returncode != 0:
        filepath.unlink(missing_ok=True)
        raise RuntimeError(f"pg_dump falhou com código {dump_proc.returncode}")

    size_kb = filepath.stat().st_size // 1024
    logger.info("Backup local concluído: %s (%d KB)", filepath, size_kb)

    # Upload para S3/B2 (apenas se BACKUP_S3_BUCKET configurado)
    if S3_BUCKET:
        try:
            s3_key = f"{S3_PREFIX.rstrip('/')}/{filename}"
            _upload_to_s3(filepath, S3_BUCKET, s3_key)
        except Exception as exc:
            logger.error("Falha no upload S3 (backup local mantido): %s", exc)

    # Rotação local: remove backups antigos além de BACKUP_KEEP
    backups = sorted(BACKUP_DIR.glob("igs_backup_*.sql.gz"))
    for old in backups[: max(0, len(backups) - BACKUP_KEEP)]:
        old.unlink()
        logger.info("Backup antigo removido: %s", old.name)

    return str(filepath)
