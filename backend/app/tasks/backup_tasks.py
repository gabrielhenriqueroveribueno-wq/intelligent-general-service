import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/app/backups"))
BACKUP_KEEP = int(os.getenv("BACKUP_KEEP", "7"))


@celery_app.task(name="app.tasks.backup_tasks.backup_database_task")
def backup_database_task() -> str:
    """Executa pg_dump do banco e mantém os últimos N backups."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"igs_backup_{timestamp}.sql.gz"
    filepath = BACKUP_DIR / filename

    db_url = os.getenv("DATABASE_URL", "")
    # Extrai componentes da DATABASE_URL (postgresql+asyncpg://user:pass@host:port/db)
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
    gzip_cmd = ["gzip"]

    logger.info("Iniciando backup do banco: %s", filename)

    with open(filepath, "wb") as out_file:
        dump_proc = subprocess.Popen(dump_cmd, stdout=subprocess.PIPE, env=env)
        gzip_proc = subprocess.Popen(gzip_cmd, stdin=dump_proc.stdout, stdout=out_file)
        dump_proc.stdout.close()  # type: ignore[union-attr]
        gzip_proc.communicate()
        dump_proc.wait()

    if dump_proc.returncode != 0:
        filepath.unlink(missing_ok=True)
        raise RuntimeError(f"pg_dump falhou com código {dump_proc.returncode}")

    size_kb = filepath.stat().st_size // 1024
    logger.info("Backup concluído: %s (%d KB)", filepath, size_kb)

    # Rotação: remove backups antigos além de BACKUP_KEEP
    backups = sorted(BACKUP_DIR.glob("igs_backup_*.sql.gz"))
    for old in backups[: max(0, len(backups) - BACKUP_KEEP)]:
        old.unlink()
        logger.info("Backup antigo removido: %s", old.name)

    return str(filepath)
