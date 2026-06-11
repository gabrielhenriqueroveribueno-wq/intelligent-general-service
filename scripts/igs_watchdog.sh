#!/usr/bin/env bash
# IGS watchdog — roda no HOST via cron (a cada 5 min).
# Checa a saude da API; apos 2 falhas consecutivas reinicia api+celery-worker.
# Sem custo de RAM (a caixa Oracle tem 1GB — nao cabe stack de monitoring).
#
# Instalacao (no servidor):
#   sudo cp scripts/igs_watchdog.sh /usr/local/bin/igs_watchdog.sh
#   sudo chmod +x /usr/local/bin/igs_watchdog.sh
#   (crontab root) */5 * * * * /usr/local/bin/igs_watchdog.sh >> /var/log/igs-watchdog.log 2>&1
set -u

COMPOSE_DIR="/opt/igs"
COMPOSE_FILE="docker-compose.prod-light.yml"
HEALTH_URL="https://igs-anchieta.duckdns.org/api/v1/health"
STATE_FILE="/tmp/igs_watchdog_failcount"
MAX_FAILS=2

ts() { date '+%Y-%m-%d %H:%M:%S'; }

code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 20 "$HEALTH_URL" 2>/dev/null || echo 000)

if [ "$code" = "200" ]; then
    if [ -f "$STATE_FILE" ]; then
        echo "$(ts) RECOVERED health=200 (apos falhas anteriores)"
        rm -f "$STATE_FILE"
    fi
    exit 0
fi

fails=$(cat "$STATE_FILE" 2>/dev/null || echo 0)
fails=$((fails + 1))
echo "$fails" > "$STATE_FILE"
echo "$(ts) FAIL health=$code consecutivas=$fails"

if [ "$fails" -ge "$MAX_FAILS" ]; then
    echo "$(ts) RESTART api + celery-worker (fails=$fails)"
    cd "$COMPOSE_DIR" || exit 1
    docker compose -f "$COMPOSE_FILE" restart api celery-worker
    rm -f "$STATE_FILE"
    sleep 30
    after=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 20 "$HEALTH_URL" 2>/dev/null || echo 000)
    echo "$(ts) POS-RESTART health=$after"
fi
