# IGS — Runbook de Incidentes

> Versão: 2026-05  
> Guia de diagnóstico e resolução para os problemas mais comuns em produção.

---

## Acesso rápido ao servidor

```bash
ssh -i ~/.ssh/igs_key ubuntu@137.131.151.205
cd /opt/igs
```

---

## Comandos de diagnóstico geral

```bash
# Status de todos os containers
docker compose -f docker-compose.prod-light.yml ps

# Logs em tempo real
docker compose -f docker-compose.prod-light.yml logs -f --tail=100

# Logs de um serviço específico
docker compose -f docker-compose.prod-light.yml logs api --tail=200
docker compose -f docker-compose.prod-light.yml logs celery-worker --tail=200
docker compose -f docker-compose.prod-light.yml logs caddy --tail=100

# Uso de recursos
docker stats --no-stream
free -h
df -h
```

---

## Incidentes por severidade

---

### CRÍTICO — API retorna 500 ou 502

**Sintomas:** Frontend exibe "Erro interno" / WhatsApp não responde.

**Diagnóstico:**
```bash
docker compose -f docker-compose.prod-light.yml logs api --tail=100
```

**Causas comuns:**

| Causa | Solução |
|-------|---------|
| Banco fora do ar | Ver seção PostgreSQL abaixo |
| Redis fora do ar | Ver seção Redis abaixo |
| Variável de ambiente faltando | `docker compose ... exec api env | grep -i key` |
| Memória esgotada | `free -h` → reiniciar serviços menos críticos |

**Reinício rápido:**
```bash
docker compose -f docker-compose.prod-light.yml restart api
```

---

### CRÍTICO — WhatsApp não responde mensagens

**Sintomas:** Usuários enviam mensagens mas não recebem resposta.

**Diagnóstico:**
```bash
# Verificar se o Celery está processando tasks
docker compose -f docker-compose.prod-light.yml logs celery-worker --tail=50

# Verificar fila do Redis
docker compose -f docker-compose.prod-light.yml exec redis redis-cli llen celery
```

**Causas comuns:**

| Causa | Solução |
|-------|---------|
| Celery worker caído | `docker compose ... restart celery-worker` |
| Chave GROQ/AI inválida | Conferir `GROQ_API_KEY` no `.env` e no painel |
| Fila travada | Ver seção DLQ abaixo |
| Webhook não configurado | Reconfigurar no Meta for Developers |

**Teste manual do webhook:**
```bash
curl -X POST https://igs-anchieta.duckdns.org/api/v1/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account"}'
```
Deve retornar `{"status":"ok"}`.

---

### ALTO — Frontend em branco ou 404

**Diagnóstico:**
```bash
docker compose -f docker-compose.prod-light.yml logs frontend --tail=30
docker compose -f docker-compose.prod-light.yml logs caddy --tail=30
```

**Causas comuns:**

| Causa | Solução |
|-------|---------|
| Build do frontend não atualizado | `docker compose ... build frontend && docker compose ... up -d frontend` |
| Caddy não conseguiu obter SSL | Ver logs Caddy — verificar DNS do domínio |
| Container frontend caído | `docker compose ... restart frontend` |

---

### ALTO — PostgreSQL fora do ar

**Diagnóstico:**
```bash
docker compose -f docker-compose.prod-light.yml logs postgres --tail=50
docker compose -f docker-compose.prod-light.yml exec postgres pg_isready -U igs_user
```

**Recuperação:**
```bash
# Reiniciar
docker compose -f docker-compose.prod-light.yml restart postgres

# Verificar integridade
docker compose -f docker-compose.prod-light.yml exec postgres \
  psql -U igs_user -d igs_db -c "SELECT count(*) FROM users;"
```

**Disco cheio (causa frequente):**
```bash
df -h
# Liberar logs antigos do Docker
docker system prune -f --volumes  # CUIDADO: não remove volumes nomeados
# Ver tamanho dos volumes
docker system df
```

---

### ALTO — Redis fora do ar

**Diagnóstico:**
```bash
docker compose -f docker-compose.prod-light.yml logs redis --tail=30
docker compose -f docker-compose.prod-light.yml exec redis redis-cli ping
```

**Recuperação:**
```bash
docker compose -f docker-compose.prod-light.yml restart redis
# Aguardar 10s e testar
docker compose -f docker-compose.prod-light.yml exec redis redis-cli ping
```

**Impacto:** Sem Redis, o Celery para de processar tarefas e o rate limiting falha (retorna 500). A API fica inoperante para WhatsApp.

---

### MÉDIO — Certificado SSL expirado / renovação falhou

**Diagnóstico:**
```bash
docker compose -f docker-compose.prod-light.yml logs caddy | grep -i "certificate\|acme\|tls"
```

**Forçar renovação:**
```bash
# Parar Caddy, limpar dados do Let's Encrypt, reiniciar
docker compose -f docker-compose.prod-light.yml stop caddy
docker volume rm igs_caddy_data
docker compose -f docker-compose.prod-light.yml up -d caddy
```

**Nota:** Caddy renova automaticamente ~30 dias antes do vencimento. Falhas de renovação geralmente são causadas por DNS incorreto ou porta 80/443 bloqueada.

---

### MÉDIO — Celery DLQ (Dead Letter Queue) com tarefas falhas

**Diagnóstico:**
```bash
# Tarefas na DLQ
docker compose -f docker-compose.prod-light.yml exec redis \
  redis-cli llen celery.dead.queue

# Verificar logs
docker compose -f docker-compose.prod-light.yml logs celery-worker | grep "ERROR\|FAILURE"
```

**Limpar DLQ (com cautela):**
```bash
docker compose -f docker-compose.prod-light.yml exec redis \
  redis-cli del celery.dead.queue
```

---

### BAIXO — Emails não estão sendo enviados

**Diagnóstico:**
```bash
# Verificar configuração
docker compose -f docker-compose.prod-light.yml exec api env | grep -E "SMTP|RESEND"

# Testar envio manual
docker compose -f docker-compose.prod-light.yml exec api python3 -c "
import asyncio
from app.services.email_service import send_email_async
asyncio.run(send_email_async('teste@gmail.com', 'Teste IGS', '<h1>Teste</h1>'))
"
```

---

## Procedimentos de manutenção

### Atualizar o sistema

```bash
cd /opt/igs
git pull origin master
docker compose -f docker-compose.prod-light.yml build api celery-worker
docker compose -f docker-compose.prod-light.yml up -d --no-deps api celery-worker
docker compose -f docker-compose.prod-light.yml exec api alembic upgrade head
# Verificar que a API voltou
curl https://igs-anchieta.duckdns.org/api/v1/health
```

### Backup manual do banco

```bash
docker compose -f docker-compose.prod-light.yml exec postgres \
  pg_dump -U igs_user -Fc igs_db > /tmp/igs_backup_$(date +%Y%m%d_%H%M).dump
# Copiar para fora do servidor
scp -i ~/.ssh/igs_key ubuntu@137.131.151.205:/tmp/igs_backup_*.dump ./backups/
```

### Restore do banco

```bash
# ATENÇÃO: Vai sobrescrever dados existentes
docker compose -f docker-compose.prod-light.yml exec -T postgres \
  pg_restore -U igs_user -d igs_db --clean < backup.dump
```

### Verificar uso de memória dos containers

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"
```

Se o total ultrapassar ~900 MB, o kernel pode matar containers (OOM). Reiniciar o servidor de VM resolve.

### Reiniciar tudo (último recurso)

```bash
docker compose -f docker-compose.prod-light.yml down
docker compose -f docker-compose.prod-light.yml up -d
# Aguardar postgres e redis ficarem healthy (~30s)
sleep 30
# Verificar saúde
docker compose -f docker-compose.prod-light.yml ps
curl https://igs-anchieta.duckdns.org/api/v1/health
```

---

## Logs importantes

| Serviço | Localização |
|---------|------------|
| API | `docker compose logs api` |
| Celery | `docker compose logs celery-worker` |
| Caddy | `/var/log/caddy/caddy.log` (dentro do container) e `docker compose logs caddy` |
| PostgreSQL | `docker compose logs postgres` |

### Ver logs do Caddy no arquivo

```bash
docker compose -f docker-compose.prod-light.yml exec caddy \
  tail -f /var/log/caddy/caddy.log
```

---

## Contatos de emergência

| Situação | Contato |
|----------|---------|
| Problema crítico na API | Gabriel Roveri — gabriel.henrique.roveri.bueno@gmail.com |
| Problema no Meta/WhatsApp | [Meta Business Support](https://business.facebook.com/support) |
| Problema na Groq API | [Groq Status](https://status.groq.com) |
| Oracle Cloud VM | [Oracle Support](https://support.oracle.com) |
