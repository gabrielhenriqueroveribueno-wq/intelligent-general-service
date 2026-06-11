# IGS — Contexto Completo do Projeto

> Este arquivo serve como referencia para o Claude Code retomar o trabalho
> caso o historico de conversas seja perdido. Leia este documento inteiro
> antes de iniciar qualquer tarefa.
>
> **Ultima atualizacao:** 2026-06-10 (apos commits ate `f40d54b`; revisao de pendencias verificada contra o codigo)

---

## 1. O que e o IGS

**Intelligent General Service** — SaaS multi-tenant de atendimento inteligente via WhatsApp
para instituicoes de ensino. Atende alunos, funcionarios e professores com respostas
automaticas via IA (Groq/Gemini/Anthropic) + agente conversacional "Billie IGS".

**Repositorio:** `gabrielhenriqueroveribueno-wq/intelligent-general-service`
**Branch principal:** `master`
**CI:** GitHub Actions (`.github/workflows/ci.yml`) — 3 jobs: backend lint, backend tests, frontend build
**Deploy:** `.github/workflows/deploy.yml` (trigger por tag `v*`, com rollback automatico)

---

## 2. Stack Completa

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0 async, Alembic |
| Database | PostgreSQL 16 (asyncpg) com Row-Level Security |
| Cache/Queue | Redis 7 + Celery |
| Frontend | React 18 + TypeScript 5.6 + TailwindCSS 3.4 + Vite 5.4 |
| PWA | vite-plugin-pwa + Workbox + Web Push (VAPID) |
| WhatsApp | Meta Business Cloud API |
| IA | Multi-provider: Groq (llama-3.3-70b) **default**, Gemini (2.0-flash), Anthropic (claude-opus-4-6) |
| Pagamentos | Mercado Pago Checkout Pro (PIX + cartao + boleto) |
| Email | Resend API (preferido) com SMTP fallback |
| Monitoring | Prometheus + Grafana + Loki + Promtail + AlertManager + Sentry |
| Infra | Docker + Docker Compose (3 stacks: dev, prod, prod-light) |
| Auth | JWT (access 15min + refresh 7d), bcrypt, must_change_password flow |
| Proxy | Nginx (dev/prod), Caddy (prod-light, SSL automatico) |

**AI Provider ativo:** `AI_PROVIDER=groq` (default no config.py — mudou de anthropic em fases recentes para reduzir custo). Ainda configuravel via .env.
**Deploy ativo:** Oracle Cloud Free Tier — igs-anchieta.duckdns.org (`docker-compose.prod-light.yml`, 6 containers leves).

---

## 3. Estrutura de Arquivos

### 3.1 Backend Models (26 arquivos — `backend/app/models/`)

```
base.py                — Base, TimestampMixin, TenantMixin
tenant.py              — Tenant, TenantSettings
user.py                — User (super_admin, admin, manager, agent, teacher) + must_change_password
student.py             — Student (com evasion_risk_score/level/factors), Grade, AttendanceRecord
employee.py            — Employee, Payslip, VacationBalance, TimeRecord, HRRequest
billing.py             — Boleto (com pix_code/pix_txid), InstallmentPlan (parcelamento)
conversation.py        — Contact, Conversation, Message (com sentiment + sentiment_score)
ticket.py              — Ticket (protocol, SLA, category), TicketComment
ticket_learning.py     — TicketResolution (ML para sugerir respostas)
knowledge_base.py      — KBCategory, KBArticle, ClassMaterial (materiais do professor)
schedule.py            — ClassSchedule
notification.py        — MessageTemplate (HSM Meta), ScheduledNotification
satisfaction.py        — SatisfactionSurvey, OnboardingSession
service_request.py     — ServiceRequest
metrics.py             — ResponseTimeMetric, WhatsAppMonitoredAccount
audit.py               — AuditLog, FailedTask, SLAConfig
webhook.py             — WebhookEndpoint, WebhookDelivery
appointment.py         — Appointment (agendamento presencial)
library.py             — Book, Loan (biblioteca)
academic_integration.py — AcademicIntegration (Sophia/TOTVS/REST/SQL)
sync_log.py            — SyncLog (historico de syncs)
push_subscription.py   — PushSubscription (Web Push)
report_subscription.py — ReportSubscription (assinatura de relatorios)
lead.py                — Lead (CRM comercial)
slide.py               — SlideTemplate, SlidePresentation (DEPRECATED — tabelas dropadas, modelo mantido por compat)
```

### 3.2 Backend Services (47 arquivos — `backend/app/services/`)

**Core IA:**
- `ai_client.py` — Cliente unificado com Circuit Breaker (3 falhas / 60s recovery) + failover automatico entre providers + Tenacity retry
- `ai_fallback.py` — Resposta offline (keyword matching + KB) quando todos os providers falham
- `ai_service.py` — Orquestracao RAG (contexto + historico + dados)
- `intent_classifier.py` — Classificacao de 41 intents (ver secao 4)
- `provider_health.py` — Estados: healthy / rate_limited / no_credits / auth_error / unreachable

**Mensageria & WhatsApp:**
- `whatsapp_service.py` — Envio (text, document, image) via Meta API
- `media_service.py` — Download de midia
- `transcription_service.py` — Audio → texto
- `task_executor.py` — Executor de acoes por intent
- `sentiment_service.py` — Analise de sentimento (positive/neutral/negative)

**Dados academicos:**
- `student_service.py`, `student_onboarding.py`, `employee_service.py`

**Integracoes externas (`services/integrations/`):**
- `base.py` — Protocol `AcademicSystemIntegrator`
- `registry.py` — Factory + `PROVIDER_CATALOG` (metadados para form dinamico)
- `sophia.py` — Prima Tecnologia (REST, token auth)
- `totvs.py` — TOTVS RM Educacional (REST/OData, basic auth)
- `generic_rest.py` — REST generico (bearer/basic/header)
- `generic_sql.py` — SQL direto (MSSQL/MySQL/PostgreSQL/Oracle)

**Atendimento:**
- `ticket_service.py`, `appointment_service.py`, `sla_service.py`, `learning_service.py`

**Conteudo:**
- `knowledge_service.py`, `tutor_service.py`, `document_ocr_service.py`, `hr_vision_service.py`
- `library_service.py` — emprestimos/renovacao/multas
- `boleto_pdf_service.py`, `report_service.py` (PDF + Excel via ReportLab/openpyxl)

**Comercial/SaaS:**
- `saas_billing_service.py` — Planos Starter (R$ 297) / Pro (R$ 497) / Enterprise via Mercado Pago
- `mercadopago_service.py` — Checkout Pro + webhook
- `payment_service.py` — PIX BR Code + negociacao de debitos
- `onboarding_service.py` — Onboarding step-by-step de novo tenant

**Notificacoes:**
- `email_service.py` (Resend + SMTP fallback), `email_templates.py`
- `push_notification_service.py` (Web Push VAPID)
- `executive_report_service.py` (relatorios PDF para gestores)

**Analytics:**
- `evasion_service.py` — Cruza faltas + notas + boletos vencidos → score de evasao
- `metrics_service.py` — Prometheus metrics

**Outros:** `auth_service.py`, `anonymization_service.py` (LGPD), `cache_service.py`, `ws_manager.py`, `webhook_delivery_service.py`

### 3.3 Backend API Routes (28 modulos — `backend/app/api/v1/`)

```
auth.py              — /login, /refresh, /logout, /forgot-password, /me
tenants.py           — CRUD tenants, settings, whatsapp/test
users.py             — Gestao de usuarios + must_change_password
students.py          — CRUD + import CSV + notas/freq/boletos/horarios
employees.py         — CRUD + holerites/ferias/ponto/RH
student_portal.py    — Portal publico do aluno (sem login painel)
conversations.py     — Listar, detalhar, atribuir agente, fechar
tickets.py           — CRUD tickets + comentarios + SLA
knowledge_base.py    — Categorias + artigos
templates.py         — Templates WhatsApp HSM
dashboard.py         — KPIs principais
reports.py           — Geracao PDF/Excel
report_subscriptions.py — Assinatura de relatorios por email
metrics.py           — Prometheus + custom stats
health.py            — /ping, /health, /health/ready, /health/detailed
ai_health.py         — Saude dos providers + circuit state
webhook.py           — Inbound WhatsApp + Mercado Pago
webhooks_config.py   — Webhooks outbound (HMAC)
ws.py                — WebSocket real-time
admin.py             — Operacoes administrativas
integrations.py      — Configurar Sophia/TOTVS/REST/SQL + test + sync now + logs
onboarding.py        — Progresso do onboarding por tenant
push_subscriptions.py — Web Push subscribe/unsubscribe + VAPID public key
evasion.py           — Riscos + fatores por aluno
billing.py           — Checkout SaaS + status + invoices
leads.py             — Captura de leads (landing page)
router.py            — Agregador
```

### 3.4 Celery Tasks (16 modulos — `backend/app/tasks/`)

```
celery_app.py             — Config + Beat schedule (15 jobs)
message_tasks.py          — Pipeline principal (Billie)
notification_tasks.py     — SLA, boletos, frequencia, notas, relatorio semanal, evasao, rematricula
report_tasks.py           — Geracao assincrona de relatorios
executive_report_tasks.py — Despacho de relatorios executivos
integration_sync_tasks.py — Sync com Sophia/TOTVS/REST/SQL (horaria)
evasion_tasks.py          — Compute evasion risks
anonymization_tasks.py    — Anonimizacao LGPD automatica
health_check_tasks.py     — Probe dos 3 providers IA (15min)
ai_budget_tasks.py        — Alerta de orcamento mensal IA (USD)
trial_tasks.py            — Verifica expiracao de trial
push_tasks.py             — Envio Web Push
backup_tasks.py           — Backup PostgreSQL diario
webhook_tasks.py          — Entrega de webhooks com retry exponencial
dlq_tasks.py              — Dead Letter Queue
```

**Beat Schedule (timezone: America/Sao_Paulo):**

| Job | Cron | Funcao |
|---|---|---|
| check-sla-breaches | `*/5 * * * *` | Alerta de SLA |
| send-boleto-reminders | `0 9 * * *` | Lembrete boletos vencendo |
| send-attendance-alerts | `0 10 * * *` | Alerta frequencia baixa |
| send-grade-notifications | `30 */6 * * *` | Notificacao de notas |
| daily-db-backup | `0 3 * * *` | Backup PostgreSQL |
| weekly-manager-report | `0 8 * * 1` | Relatorio semanal WhatsApp |
| weekly-pdf-report | `30 8 * * 1` | Relatorio PDF por email |
| check-evasion-risk | `0 7 * * *` | Alerta de evasao |
| reenrollment-campaign | `30 9 * * *` | Campanha rematricula (jun/jul/nov/dez) |
| ai-providers-health-check | `*/15 * * * *` | Probe IA |
| dispatch-scheduled-reports | `5 * * * *` | Relatorios executivos |
| dispatch-integration-syncs | `15 * * * *` | Sync sistemas academicos |
| compute-evasion-risks | `45 * * * *` | Calcula score por aluno |
| anonymization-auto | `0 2 1 * *` | LGPD mensal |
| ai-budget-check | `0 8 * * *` | Alerta de orcamento IA |
| trial-expiry-check | `0 6 * * *` | Trials expirando |

### 3.5 Frontend Pages (45 paginas — `frontend/src/pages/`)

**Publicas (sem login):**
`Landing`, `Pricing`, `PitchDeck`, `CaseStudy`, `Demo`, `Tour`, `Changelog`, `PublicStatus`, `Legal`

**Autenticacao:**
`Login`, `Signup`, `ForgotPassword`, `ResetPassword`, `ChangePassword`, `Onboarding`

**Dashboard (protegidas, prefixo /app):**
`Dashboard`, `Conversations`, `ConversationDetail`, `Tickets`, `Students`, `StudentDetail`, `Employees`, `EmployeeDetail`, `KnowledgeBase`

**Configuracao & Operacao:**
`Settings`, `WhatsAppSetup` (wizard visual passo-a-passo), `Templates`, `ImportData`, `Integrations`, `Slides` (UI mantida, backend dropado), `ReportSubscriptions`

**Analytics:**
`Reports`, `MetricsDashboard`, `LearningInsights`, `Billing`

**Admin:**
`UserManagement`, `Tenants`, `SuperAdmin`, `AuditLog`, `Status`, `Help`

**Erro:**
`NotFound`, `ServerError`, `Maintenance`, `Presentation` (slide deck fullscreen)

### 3.6 Frontend Components (`frontend/src/components/`)

**Layout:** `Layout`, `Sidebar`, `Header`, `PublicLayout`
**Common:** `ProtectedRoute`, `ErrorBoundary`, `PageLoader`, `OnboardingWizard`, `TrialBanner`, `PaywallModal`, `InstallBanner`, `OfflineBanner`, `CookieBanner` (LGPD), `LeadForm`, `AnimatedCounter`

### 3.7 Frontend Hooks (`frontend/src/hooks/`)

- `useWebSocket` — Reconexao automatica com backoff
- `useNotifications` — Eventos real-time (new_message, conversation_waiting, conversation_closed)
- `usePWA` — Instalacao + standalone detection
- `usePushNotifications` — Inscricao Web Push (VAPID)
- `useTrial` — Status do trial via `/billing/status`

### 3.8 Migracoes Alembic (15 — `backend/alembic/versions/`)

```
85cef5d6b524 — initial_schema
84781b46eefb — add_webhook_endpoints_and_webhook_deliveries
a3f1b2c4d5e6 — add_slide_tables (depois dropado)
b7e2a9f3c1d8 — enable_rls_all_tenant_tables (Row-Level Security)
c8d3e5f7a9b1 — add_modules_pix_library_materials
d9e4f6a7b2c3 — add_appointments_table
e1a2b3c4d5e6 — add_report_subscriptions
f2b3c4d5e6f7 — add_academic_integrations
g3c4d5e6f7a8 — add_push_subscriptions
h4d5e6f7a8b9 — add_sentiment_evasion
i5e6f7a8b9c0 — add_performance_indexes
j6f7a8b9c0d1 — add_must_change_password
k7g8h9i0j1k2 — add_integration_sync_logs
l8h9i0j1k2l3 — drop_slide_tables
m9i0j1k2l3m4 — add_leads_table
```

---

## 4. Intents Classificados (41 — `intent_classifier.py`)

**Alunos:** `grade_query`, `attendance_query`, `schedule_query`, `boleto_query`, `enrollment_query`, `generate_boleto`, `generate_pix`, `enrollment_request`, `document_request`, `class_enrollment`, `grade_appeal`, `transfer_request`, `scholarship_query`, `internship_query`, `event_registration`, `library_query`, `library_renewal`, `financial_negotiation`, `certificate_request`, `tutor_question`

**Funcionarios:** `payslip_query`, `vacation_query`, `time_record_query`, `hr_request`, `medical_certificate`

**Professores:** `slide_generate`, `slide_update` *(funcionalidade deprecated mas intent mantido)*

**Servicos gerais:** `schedule_appointment`, `cancel_appointment`, `document_ocr`, `facility_ticket`, `open_ticket`

**Conversacionais:** `faq`, `greeting`, `verification`, `human_handoff`, `farewell`, `feedback_response`, `enable_reminders`, `disable_reminders`, `unknown`

---

## 5. Fluxo de Mensagem WhatsApp (Agente "Billie IGS")

**Arquitetura:** Todas as mensagens passam pela IA. Nao ha respostas hardcoded. A Billie conduz a conversa e inclui comandos embutidos que sao extraidos via regex.

```
1. Webhook Meta → /api/v1/webhook/whatsapp → valida HMAC → persiste msg
2. Enqueue Celery: process_incoming_message
3. Worker: cria async engine dedicada (evita conflito de event loop)
4. Determina estado do contato:
   a) NAO VERIFICADO     → system prompt BEHAVIOR_NEW_CONTACT
   b) AGUARDANDO SENHA   → system prompt BEHAVIOR_AWAITING_PASSWORD
   c) VERIFICADO         → system prompt BEHAVIOR_VERIFIED
5. Se audio → transcricao | se imagem → media_service + (OCR ou hr_vision)
6. Se verificado: busca dados (grades, boletos, schedules, payslips, books, etc.)
7. Envia mensagem + historico + dados para IA (com sentiment analysis em paralelo)
8. IA retorna resposta com comandos embutidos:
   [IDENTIFY:student:NUMERO] / [IDENTIFY:employee:CODIGO]
   [PASSWORD:valor]
   [HANDOFF]
   [CANCEL]
   [FEEDBACK_REQUEST] / [FEEDBACK:N]      (satisfacao 1-5)
   [REMINDERS_ON] / [REMINDERS_OFF]       (opt-in proativo)
   [GENERATE_DOC:tipo]                    (enrollment_declaration, academic_history)
9. Regex extrai comandos, executa acoes, remove da resposta
10. Envia resposta limpa via WhatsApp API
11. Registra metricas (tokens, tempo, intent, sentiment) → DB + Prometheus
12. Descarta engine async
```

---

## 6. Provedores de IA & Circuit Breaker

**Padrao (config.py):** `AI_PROVIDER=groq`

| Provider | Modelo | Vision | Notas |
|---|---|---|---|
| Groq | `llama-3.3-70b-versatile` | nao | rapido/barato, default |
| Gemini | `gemini-2.0-flash` | sim | fallback de vision |
| Anthropic | `claude-opus-4-6` | sim | melhor qualidade, mais caro |

**Circuit Breaker:** 3 falhas consecutivas → OPEN por 60s → HALF_OPEN para teste.
**Retry:** Tenacity, 2 tentativas por provider, backoff exponencial 1-4s, retryavel em timeout/429/5xx.
**Fallback chain:**
- `groq → gemini → anthropic`
- `gemini → anthropic → groq`
- `anthropic → groq → gemini`
- Vision (foto): `gemini → anthropic` (groq nao suporta)

**Quando tudo falha:** `ai_fallback.py` faz keyword matching + busca KB + mensagem generica.

---

## 7. Integracoes Academicas (4 providers)

**Localizacao:** `backend/app/services/integrations/`

| Provider | Tipo | Auth | Uso |
|---|---|---|---|
| Sophia | REST | Token | Prima Tecnologia |
| TOTVS RM | REST/OData | Basic Auth | TOTVS Educacional |
| Generic REST | REST | bearer/basic/header | Qualquer JSON |
| Generic SQL | SQL direto | username/password | MSSQL/MySQL/PostgreSQL/Oracle |

**Configuracao:**
- UI: `/app/integrations` → form dinamico baseado em `PROVIDER_CATALOG` do `registry.py`
- Credenciais armazenadas encrypted (Fernet) em `AcademicIntegration.credentials_encrypted`
- Sync periodico via `integration_sync_tasks` (cron por integration)
- Historico em `SyncLog`: records_synced, students/employees created/updated, errors, duration_ms

**Interface comum:** `test_connection`, `sync_students`, `sync_employees`, `sync_grades`, `sync_boletos`, `sync_all`

---

## 8. Funcionalidades SaaS / Comercial

- **Trial Period:** controlado por `trial_tasks.check_trial_expiry_task` (06:00 diario)
- **Billing:** `saas_billing_service` cria checkout MP com planos Starter/Pro/Enterprise
- **Leads:** captura via `LeadForm` (landing page) → `/api/v1/leads` com UTM tracking
- **Pitch Deck:** `/pitch` (fullscreen) + `Presentation.tsx`
- **Onboarding:** wizard visual em `WhatsAppSetup.tsx` (passo-a-passo para admin de TI)
- **Cookie Banner:** consentimento LGPD em todas paginas publicas
- **PWA:** instalavel em mobile, offline cache, push notifications

---

## 9. Estado do WhatsApp (atualizado)

- **Bot em producao:** Billie IGS respondendo mensagens reais
- **Servidor:** Oracle Cloud Free Tier (137.131.151.205), Oracle Linux, regiao Sao Paulo
- **Stack producao:** `docker-compose.prod-light.yml` (6 containers: caddy, frontend, api, celery-worker, postgres, redis)
- **Memoria total:** 1GB RAM + 2GB swap → limites por container (api 256MB, celery 256MB, postgres 192MB, redis 96MB)
- **Dominio:** `igs-anchieta.duckdns.org` (DuckDNS gratuito)
- **HTTPS:** Caddy com Let's Encrypt automatico (sem certbot separado)
- **Webhook:** `https://igs-anchieta.duckdns.org/api/v1/webhook/whatsapp`
- **Verify Token:** `igs-verify-token-2026`
- **Phone Number ID:** 1142668418921479
- **Numero do bot:** 92679-8094
- **Access Token:** ainda usando token temporario (System User Token pendente)

---

## 10. CI/CD

### Workflow `ci.yml` (push em master/main/develop, PR para master/main)

1. **test-backend** — PostgreSQL 16 + Redis 7, `ruff check`, `pytest --cov` (unit + integration), coverage upload artifact + Codecov
2. **lint-backend** — `ruff check app/` + `ruff format --check app/`
3. **test-frontend** — Node 20, `tsc --noEmit`, `npm run build` (Vite)

**Ruff config:** line-length=100, py312, select=["E","F","I","N","W"], ignore=["E501","N818"]

### Workflow `deploy.yml` (trigger: tag `v*`)

1. **build** — Login GHCR, build & push imagem API com semver tags
2. **deploy** — SSH para `/opt/igs`, git pull, pull imagem, **salva imagem anterior**, `alembic upgrade head`, rolling restart (api + celery-worker + celery-beat), `curl /api/v1/health` para validar, **rollback automatico** se falhar
3. **notify** — Markdown summary com status, tag, commit, build, deploy

---

## 11. Monitoring

### Prometheus alerts (`monitoring/prometheus/rules/igs-alerts.yml`)

- **igs_bot_performance:** BotResponseTimeHigh (P95 > 8s warn), BotResponseTimeCritical (P95 > 15s)
- **igs_sla:** SLABreachRateHigh (>5% em 10m), SLABreachSpike (>5 em 5m)
- **igs_ai_costs:** HighTokenConsumption (>100k/h), ExcessiveTokenConsumption (>500k/h)
- **igs_infrastructure:** APIDown, RedisDown, HighHTTPErrorRate (>5% 5xx), NoMessagesProcessed (zero em 15m)

### AlertManager
- Receiver: `http://api:8000/api/v1/internal/alerts`
- Critical: 0s group_wait, repeat 1h
- Inhibit: suprime warnings se ha critical para mesmo tenant

### Sentry
- DSN configuravel, traces 10%, profiles 5%
- Habilitado em backend (Python SDK) e frontend (@sentry/react)

### Health endpoints
- `/api/v1/ping` (uptime checks)
- `/api/v1/health` (basico)
- `/api/v1/health/ready` (db ok)
- `/api/v1/health/detailed` (postgres + redis + celery + AI providers) → 200/207/503
- `/api/v1/ai-health` (cacheado 60s)

---

## 12. Seguranca

- **Row-Level Security (RLS):** 32 tabelas tenant-scoped, dual roles (`igs_app` RLS-enforced + `igs_worker` BYPASSRLS para tarefas cross-tenant). Toggle via `RLS_ENABLED`.
- **Data Masking (LGPD):** `utils/data_masking.py` mascara CPF/email/telefone/cartao em mensagens salvas
- **Direito ao Esquecimento:** `anonymization_service.py` substitui PII por hashes irreversiveis
- **HMAC-SHA256:** verificacao em webhook WhatsApp + assinatura de webhooks outbound
- **Encryption:** Fernet (CPF, tokens, credenciais de integracao)
- **JWT:** access 15min + refresh 7d, must_change_password flow
- **Cloudflare WAF:** 3 regras (SQLi/XSS, rate limit login, whitelist Meta no webhook)
- **Cookie Banner:** consentimento LGPD ativo

---

## 13. Variaveis de Ambiente Criticas (.env.example)

```
DATABASE_URL              # PostgreSQL asyncpg
REDIS_URL                 # Cache
CELERY_BROKER_URL         # Redis db1
CELERY_RESULT_BACKEND     # Redis db2
JWT_SECRET_KEY            # JWT signing
ANTHROPIC_API_KEY         # Claude
GROQ_API_KEY              # Groq (default)
GOOGLE_API_KEY            # Gemini
AI_PROVIDER=groq          # Provider default
WHATSAPP_APP_SECRET       # HMAC verification
WHATSAPP_VERIFY_TOKEN     # Meta webhook challenge
MP_ACCESS_TOKEN           # Mercado Pago
MP_WEBHOOK_SECRET         # MP webhook signature
ENCRYPTION_KEY            # Fernet (CPF, tokens)
VAPID_PUBLIC_KEY          # Web Push
VAPID_PRIVATE_KEY         # Web Push
RESEND_API_KEY            # Email (preferido)
SMTP_*                    # Email fallback
SENTRY_DSN                # Error tracking
RLS_ENABLED               # false em dev, true em prod
RLS_APP_PASSWORD          # Senha role igs_app
RLS_WORKER_PASSWORD       # Senha role igs_worker
FRONTEND_URL              # Para links de reset
AI_MONTHLY_BUDGET_USD=50  # Alerta de orcamento
SAAS_BILLING_NOTIFICATION_URL  # Webhook MP do plano SaaS
VITE_GA_MEASUREMENT_ID    # Google Analytics frontend
```

---

## 14. Comandos Uteis (Makefile)

```bash
make up              # docker compose up -d (stack completa dev)
make down            # docker compose down
make logs            # logs de todos os servicos
make migrate         # alembic upgrade head
make seed            # seed_db.py (basico)
make seed-demo       # seed_demo.py (8 alunos, 5 funcs, 6 conversas, etc.)
make seed-pitch      # seed_pitch.py (dados de pitch deck)
make test            # pytest
make lint            # ruff check
make format          # ruff format
make shell           # bash no container api
make create-tenant   # scripts/create_tenant.py interativo
make import-students file=alunos.csv
make import-employees file=funcionarios.csv
```

---

## 15. URLs de Acesso (desenvolvimento local)

| Servico | URL |
|---|---|
| API (Swagger) | http://localhost:8000/docs (tambem `/api/docs` em prod) |
| API (ReDoc) | http://localhost:8000/redoc |
| Frontend | http://localhost:3000 |
| Grafana | http://localhost:3001 (admin/admin123) |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |
| Loki | http://localhost:3100 |
| Health | http://localhost:8000/api/v1/health |
| AI Health | http://localhost:8000/api/v1/ai-health |
| Metrics | http://localhost:8000/api/v1/metrics/prometheus |

---

## 16. Credenciais Demo (apos `make seed-demo`)

| Role | Email | Senha |
|---|---|---|
| Super Admin | admin@igs.com | Admin@123456 |
| Admin Tenant | gestor@anchieta.edu.br | Gestor@2026 |
| Agente | suporte1@anchieta.edu.br | Suporte@2026 |
| Professor | prof.andre@anchieta.edu.br | Prof@2026 |

---

## 17. Documentacao Adicional (`docs/`)

| Arquivo | Conteudo |
|---|---|
| `CONTEXT.md` | **Este arquivo** — contexto completo |
| `IGS_Project_Overview.md` | Visao geral, target, problema, USPs |
| `ADMIN_MANUAL.md` | Manual do administrador do painel |
| `RUNBOOK.md` | Runbook de incidentes (API 5xx, Celery hung, DB full, Redis OOM) |
| `SETUP_GUIDE.md` | Instalacao do zero (Oracle Free Tier) |
| `WEBHOOK_CONFIG.md` | Configuracao Meta webhook + tokens |
| `RESUMO_APRESENTACAO.md` | Resumo executivo (pitch) |
| `CONTRATO_SAAS.md` | Contrato SaaS modelo |
| `sales/one-pager.md` | One-pager comercial |
| `site/` | Site de apresentacao Vite/Vercel |

---

## 18. Claude Code Customizations (`.claude/`)

**Skills:** `igs-context/SKILL.md` (carrega contexto arquitetural automaticamente)

**Commands (slash):**
- `/add-intent <nome>` — Adicionar novo intent (classifier + handler + task_executor + tests)
- `/review-intent <nome>` — Revisar implementacao completa de um intent
- `/debug-celery <problema>` — Debugar pipeline Celery

**Agents globais usados:** planner, code-reviewer, security-reviewer, tdd-guide, python-reviewer, database-reviewer, build-error-resolver

---

## 19. Pendencias / Proximos Passos

> Revisado em 2026-06-10 contra o codigo. Legenda: 🔴 critico p/ apresentar ·
> 🟡 importante · 🟢 opcional/decisao · ✅ concluido.

### Concluido desde 2026-05-22 (sprint de seguranca + anti-leak, NAO estava no CONTEXT antigo)
- ✅ **Hardening de seguranca** (`6033603`): rate-limits, replay protection, output
  guardrail, audit logs.
- ✅ **39 testes de regressao** de isolamento de dados/seguranca (`ae67119`).
- ✅ **Topic pre-gate** — bloqueia mensagens off-topic antes do LLM principal (`fe10471`).
- ✅ **Prompt da Billie externalizado** para arquivos gitignored em `backend/prompts/`
  (`6e14846`) — `billie_agent.txt` / `billie_behaviors.txt` / `billie_classifier.txt`.
- ✅ **Anti-leak cooldown + super_admin cross-tenant** (tenant_id=NULL no JWT) (`9487087`).
- ✅ **Demo mock desligado em producao** — painel admin usa API real (`c7192cc`).
- ✅ Fixes de producao (`0caf77b`, `e616a42`, `f40d54b`): billing platform_admin p/
  super_admin, `audit_logs.tenant_id` nullable, conversation detail `messages` None→[].

### Tecnicas (verificado — ainda PENDENTE)
1. 🔴 **Token permanente Meta WhatsApp** — System User Token ainda pendente; o token
   atual e temporario (expira em 1-2h). **Risco #1 para uma demo ao vivo.** Verificar/trocar
   no servidor antes de qualquer apresentacao.
2. 🟢 **Evolution API** — apenas mencionada; sem codigo. Decisao de migracao em aberto.
3. 🟢 **Slides feature** — confirmado: `models/slide.py` mantido, `pages/Slides.tsx` ainda
   existe, intents `slide_generate/slide_update` no classifier, mas tabelas dropadas
   (`l8h9i0j1k2l3`). Decidir: remover UI ou reativar backend.
4. 🟡 **Templates HSM Meta** — infra existe (`MessageTemplate`, `api/v1/templates.py`,
   `notification_tasks`), mas **templates aprovados na Meta** (boleto/frequencia/rematricula)
   ainda nao criados. Necessario para outbound proativo.
5. 🟡 **Monitoring no prod-light** — confirmado ausente no `docker-compose.prod-light.yml`
   (sem uptime-kuma/monitoring). Falta solucao leve.
6. 🟡 **Integracao com sistema academico real** — testar em piloto (TOTVS RM via `generic_sql`).
7. 🔴 **Drift de migracao no prod** — prod em `k7g8h9i0j1k2`, head do repo `n0j1k2l3m4n5`.
   `l8`/`m9`/`n0` NAO aplicadas; tabela `leads` ausente no prod. Rodar `alembic upgrade head`
   (n0 e idempotente). **Nao** usar `alembic stamp` (esconderia o drift).

### Comerciais
8. 🟡 **Pitch deck final** — preparar demo end-to-end com Billie + dados de `seed_pitch`.
9. 🟢 **Site de apresentacao** — `docs/site/` (Vite + Vercel) existe; divulgar.
10. 🟢 **Leads pipeline** — follow-up automatico (email sequence?) — depende do item 7 (tabela `leads`).

### Concluido (produto)
- ✅ **Visual demo improvements** (`a9ece69`), **WhatsApp setup wizard** (`c47f38e`),
  **SEO + changelog** (`2146164`).

---

## 20. Regras para o Claude

1. **NAO remova arquivos existentes** sem confirmacao — apenas adicione ou edite
2. **Rode `ruff check` e `ruff format`** antes de commitar
3. **Testes devem passar** com SQLite (conftest usa aiosqlite) e PostgreSQL (CI)
4. **Multi-tenancy:** todo model com dados de tenant DEVE ter `tenant_id` + usar TenantMixin
5. **AI calls:** use `ai_client.ai_complete()` — NUNCA chame APIs de IA diretamente
6. **Intents novos:** adicionar em `intent_classifier.VALID_INTENTS` + prompt + `task_executor.py` se for acao
7. **Migrations:** sempre via `alembic revision --autogenerate -m "..."` e revisar manualmente
8. **Commits:** mensagens em ingles, prefixos feat/fix/refactor/docs/chore/test/perf/ci
9. **PRs:** analisar TODOS os commits do branch (nao so o ultimo) e gerar test plan
10. **Comunicacao com o usuario:** sempre em portugues brasileiro
11. **Skills/Agents:** delegar para subagents quando tarefa for paralelizavel ou consumir contexto
