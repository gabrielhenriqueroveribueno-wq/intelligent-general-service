# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **IMPORTANTE:** Leia `docs/CONTEXT.md` para o historico completo do projeto,
> decisoes tomadas, estado atual e proximos passos. Esse arquivo e mantido
> atualizado para que o contexto nao se perca entre conversas.

## Project Overview

**IGS — Intelligent General Service**
SaaS de atendimento inteligente via WhatsApp para instituições de ensino.
Atende alunos (notas, frequência, boletos, horários) e funcionários (holerite, férias, ponto, solicitações RH) com respostas automáticas via Claude API.

## Architecture

```
WhatsApp User → Meta Cloud API → FastAPI (webhook) → Celery Worker → Claude API → WhatsApp reply
                                        ↕
                              PostgreSQL + Redis
                                        ↕
                                React Admin Panel
                                        ↕
                         Prometheus + Grafana + Loki
```

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 + Celery |
| Frontend | React 18 + TypeScript + TailwindCSS + Vite |
| WhatsApp | Meta Business Cloud API |
| AI | Claude API (claude-opus-4-6) |
| Monitoring | Prometheus + Grafana + Loki + Promtail |
| Infra | Docker + Docker Compose |
| Auth | JWT (access 15min + refresh 7d) |
| Proxy | Nginx |

## Project Structure

```
intelligent-general-service/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory
│   │   ├── config.py            # Pydantic Settings
│   │   ├── dependencies.py      # DI: get_db, get_current_user
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response
│   │   ├── api/v1/              # REST endpoints
│   │   ├── services/            # Business logic
│   │   ├── tasks/               # Celery async tasks
│   │   ├── middleware/          # Logging, metrics, tenant
│   │   └── utils/               # Security, exceptions, pagination
│   ├── alembic/                 # DB migrations
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── pages/               # Dashboard, Conversations, Tickets, etc.
│       ├── components/          # Layout, common components
│       ├── context/             # AuthContext
│       └── api/                 # axios client
├── monitoring/                  # Prometheus, Grafana, Loki, Promtail
├── nginx/                       # Reverse proxy config
├── scripts/                     # seed_db, create_tenant, import_*
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── Makefile
```

## Commands

```bash
# Copiar e configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves (ANTHROPIC_API_KEY, WHATSAPP_APP_SECRET, etc.)

# Subir todos os serviços
make up
# ou: docker compose up -d

# Rodar migrações
make migrate

# Popular banco com dados iniciais
make seed

# Rodar testes
make test

# Ver logs
make logs

# Abrir shell no container da API
make shell

# Criar novo tenant
make create-tenant

# Importar alunos via CSV
make import-students file=alunos.csv

# Importar funcionários via CSV
make import-employees file=funcionarios.csv
```

## Access URLs (development)

| Service | URL |
|---|---|
| API (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Grafana | http://localhost:3001 (admin/admin123) |
| Prometheus | http://localhost:9090 |
| API Health | http://localhost:8000/api/v1/health |

## Default Credentials (after seed)

| Role | Email | Password |
|---|---|---|
| Super Admin | admin@igs.com | Admin@123456 |
| Admin Tenant | gestor@anchieta.edu.br | Gestor@2026 |

## Multi-tenancy

Strategy: shared database + `tenant_id` column on all tenant-scoped tables.
Enforcement: ORM-level via `TenantMixin` + JWT payload carries `tenant_id`.

## WhatsApp Message Flow

1. User sends WhatsApp message
2. Meta webhook POST → `/api/v1/webhook/whatsapp`
3. FastAPI validates HMAC signature, persists message
4. Celery task enqueued: `process_incoming_message`
5. Worker: identify contact (verify by RA/employee number on first message)
6. Worker: classify intent via Claude (grade_query, boleto_query, payslip_query, etc.)
7. Worker: query database for relevant data
8. Worker: generate response with Claude (RAG pattern — only uses real data)
9. Worker: send reply via WhatsApp Cloud API
10. Log tokens, intent, resolution type to DB + Prometheus metrics

## Key Design Decisions

- **Celery for async processing**: webhook must return 200 fast; Claude calls can take 2-5s
- **Two-step AI**: classify intent (cheap ~50 tokens) → generate response (with real data context)
- **Contact verification**: user must send RA or employee number on first contact for security
- **KB full-text search**: PostgreSQL ILIKE — sufficient for hundreds of articles without vector DB
- **Per-tenant API keys**: each tenant can have own Claude/WhatsApp keys stored encrypted

## Environment Variables (required)

See `.env.example` for full list. Critical variables:
- `DATABASE_URL` — PostgreSQL connection string
- `ANTHROPIC_API_KEY` — Claude API key (or set per-tenant in DB)
- `WHATSAPP_APP_SECRET` — Meta app secret for webhook signature verification
- `WHATSAPP_VERIFY_TOKEN` — Token for Meta webhook verification challenge
- `JWT_SECRET_KEY` — JWT signing key (change in production!)
- `ENCRYPTION_KEY` — Fernet key for encrypting CPF/tokens in DB

---

## Skills & Plugins Configurados

### Skills Globais Disponíveis (~/.claude/skills/)
- `backend-patterns` — Padrões de API, banco, cache para os 23 serviços
- `postgres-patterns` — Otimização das 19 tabelas, queries async, índices
- `docker-patterns` — Docker Compose 12 containers, networking, volumes
- `api-design` — Design dos 20 módulos de rotas REST
- `deployment-patterns` — CI/CD GitHub Actions, rolling restart
- `security-review` — HMAC, JWT, multi-tenancy, OWASP Top 10
- `python-patterns` — Python 3.12, async/await, SQLAlchemy 2.0
- `tdd-workflow` — Pytest com asyncio, PostgreSQL de teste
- `database-migrations` — Alembic migrations com SQLAlchemy async
- `cost-aware-llm-pipeline` — Otimizar custo Groq/Gemini/Anthropic
- `frontend-patterns` — React 18, TypeScript, TailwindCSS
- `security-trailofbits` — Auditoria de segurança profissional (CodeQL, Semgrep)

### Agents Globais Disponíveis (~/.claude/agents/)
- `python-reviewer` — Code review especializado em Python/FastAPI
- `database-reviewer` — Review de queries, models, migrations
- `security-reviewer` — Auditoria de segurança (OWASP, injection, auth)
- `tdd-guide` — Enforcer de TDD (RED-GREEN-REFACTOR)
- `planner` — Feature planning com planos detalhados
- `build-error-resolver` — Resolver erros de build/lint/test

### Rules Globais (~/.claude/rules/)
- `common` — Regras de código linguagem-agnóstica
- `python` — Regras específicas Python/FastAPI

### Skills Locais do Projeto (.claude/skills/)
- `igs-context` — Contexto arquitetural completo do IGS (carregar sempre)

### Commands Locais do Projeto (.claude/commands/)
- `/review-intent <nome>` — Revisar implementação completa de um intent
- `/add-intent <nome>` — Adicionar novo intent seguindo o padrão existente
- `/debug-celery <problema>` — Debugar problemas no pipeline Celery
