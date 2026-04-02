# IGS — Contexto Completo do Projeto

> Este arquivo serve como referencia para o Claude Code retomar o trabalho
> caso o historico de conversas seja perdido. Leia este documento inteiro
> antes de iniciar qualquer tarefa.

---

## 1. O que e o IGS

**Intelligent General Service** — SaaS de atendimento inteligente via WhatsApp
para instituicoes de ensino. Atende alunos e funcionarios com respostas
automaticas via IA (Groq/Gemini/Anthropic).

**Repositorio:** `gabrielhenriqueroveribueno-wq/intelligent-general-service`
**Branch principal:** `master`
**CI:** GitHub Actions (`.github/workflows/ci.yml`) — 3 jobs: Backend Lint, Backend Tests, Frontend Build

---

## 2. Stack Completa

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0 async, Alembic |
| Database | PostgreSQL 16 (asyncpg) |
| Cache/Queue | Redis 7 + Celery |
| Frontend | React 18 + TypeScript + TailwindCSS + Vite |
| WhatsApp | Meta Business Cloud API |
| AI | Multi-provider: Groq (llama-3.3-70b), Gemini (2.0-flash), Anthropic (claude-opus-4-6) |
| Monitoring | Prometheus + Grafana + Loki + Promtail |
| Infra | Docker + Docker Compose (12 containers) |
| Auth | JWT (access 15min + refresh 7d) |
| Proxy | Nginx |

**AI Provider ativo:** Groq (configuravel via `AI_PROVIDER` no .env)

---

## 3. Estrutura dos Arquivos Principais

### Backend Models (19 tabelas)
```
backend/app/models/
  base.py            — Base, TimestampMixin, TenantMixin
  tenant.py          — Tenant, TenantSettings
  user.py            — User (roles: super_admin, admin, manager, agent, teacher)
  student.py         — Student, Grade, AttendanceRecord
  employee.py        — Employee, Payslip, VacationBalance, TimeRecord, HRRequest
  billing.py         — Boleto
  conversation.py    — Contact, Conversation, Message
  ticket.py          — Ticket, TicketComment
  knowledge_base.py  — KBCategory, KBArticle
  slide.py           — SlideTemplate, SlidePresentation, SlideGenerationLog
  schedule.py        — ClassSchedule
  notification.py    — MessageTemplate, ScheduledNotification
  satisfaction.py    — SatisfactionSurvey, OnboardingSession
  service_request.py — ServiceRequest
  metrics.py         — ResponseTimeMetric, WhatsAppMonitoredAccount
  audit.py           — AuditLog, FailedTask, SLAConfig
  ticket_learning.py — TicketResolution
  webhook.py         — WebhookEndpoint, WebhookDelivery
```

### Backend Services (21 servicos)
```
backend/app/services/
  ai_client.py           — Cliente unificado IA (Groq/Gemini/Anthropic)
  ai_service.py          — Gera resposta RAG com dados reais + KB + historico
  intent_classifier.py   — Classifica intent da mensagem (28 intents)
  slide_service.py       — Gera/atualiza slides via IA com template institucional
  task_executor.py       — Executa acoes (boleto, matricula, docs, slides)
  student_service.py     — CRUD + queries de aluno
  employee_service.py    — CRUD + queries de funcionario
  ticket_service.py      — CRUD tickets, protocolos, SLA
  knowledge_service.py   — Busca artigos KB
  whatsapp_service.py    — Envia mensagens via Meta API
  learning_service.py    — Busca resolucoes similares (aprendizado IA)
  transcription_service.py — Transcricao de audio
  media_service.py       — Download de midia do WhatsApp
  auth_service.py        — JWT tokens
  metrics_service.py     — Metricas de tempo de resposta
  sla_service.py         — Verificacao de SLA
  report_service.py      — Relatorios e analytics
  student_onboarding.py  — Autocadastro de aluno via WhatsApp
  webhook_delivery_service.py — Despacho de eventos com HMAC
  ws_manager.py          — WebSocket via Redis pub/sub
  pptx_service.py        — Export de slides JSON para .pptx (python-pptx)
  boleto_pdf_service.py  — Geracao de boleto em PDF (ReportLab)
  anonymization_service.py — LGPD: anonimizacao de alunos/funcionarios (direito ao esquecimento)
```

### Backend API Routes (20 modulos)
```
backend/app/api/v1/
  auth.py           — POST /login, /refresh; GET /me
  students.py       — CRUD alunos, notas, frequencia, boletos, horarios
  employees.py      — CRUD funcionarios, holerites, ferias, ponto, RH
  conversations.py  — Listar, detalhar, atribuir agente, fechar
  tickets.py        — CRUD tickets, comentarios, SLA
  slides.py         — Templates CRUD, gerar/atualizar apresentacoes, historico
  knowledge_base.py — Categorias e artigos CRUD
  webhook.py        — Webhook WhatsApp (verify + incoming)
  dashboard.py      — Metricas overview
  reports.py        — Analytics
  users.py          — Gestao de usuarios
  tenants.py        — Gestao de tenants
  templates.py      — Templates de mensagem
  webhooks_config.py — Configuracao de webhooks outbound
  metrics.py        — Metricas da aplicacao
  health.py         — Health check
  admin.py          — Operacoes administrativas
  ws.py             — WebSocket real-time
```

### Frontend Pages (15 paginas)
```
frontend/src/pages/
  Login.tsx, Dashboard.tsx, Conversations.tsx, ConversationDetail.tsx,
  Tickets.tsx, Students.tsx, StudentDetail.tsx, Employees.tsx,
  EmployeeDetail.tsx, KnowledgeBase.tsx, Reports.tsx,
  MetricsDashboard.tsx, LearningInsights.tsx, UserManagement.tsx, Settings.tsx
```

### Celery Tasks
```
backend/app/tasks/
  celery_app.py        — Config + Beat schedule (SLA 5min, boletos 9h, backup seg 3h)
  message_tasks.py     — Processamento principal de mensagens WhatsApp
  notification_tasks.py — Notificacoes agendadas, checagem SLA
  webhook_tasks.py     — Entrega de webhooks com retries
  dlq_tasks.py         — Dead Letter Queue
  backup_tasks.py      — Backup do banco
  report_tasks.py      — Geracao de relatorios
```

---

## 4. Intents Classificados (28)

**Alunos:** grade_query, attendance_query, schedule_query, boleto_query, enrollment_query,
generate_boleto, enrollment_request, document_request, class_enrollment, grade_appeal,
transfer_request, scholarship_query, internship_query, event_registration, library_query,
financial_negotiation, certificate_request

**Funcionarios:** payslip_query, vacation_query, time_record_query, hr_request

**Professores:** slide_generate, slide_update

**Geral:** faq, greeting, verification, human_handoff, unknown

---

## 5. Fluxo de Mensagem WhatsApp (message_tasks.py)

```
1. Recebe message_id do Celery
2. Se audio → transcreve via transcription_service
3. Se contato nao verificado → envia msg de boas-vindas pedindo RA/matricula
4. Classifica intent via intent_classifier (ai_complete ~50 tokens)
5. Se human_handoff → cria ticket + transfere para agente
6. Busca dados conforme intent:
   - student: grades, attendance, boletos, schedules
   - employee: payslips, vacation, time_records, hr_requests
7. Se intent de acao → task_executor executa (boleto, matricula, slides, docs)
8. Busca artigos KB relevantes
9. Busca resolucoes similares (learning_service)
10. Gera resposta via ai_service (RAG com dados reais)
11. Envia resposta via WhatsApp API
12. Registra metricas (tokens, tempo, intent)
13. Publica evento via Redis pub/sub → WebSocket no painel
```

---

## 6. Sistema de Slides via IA

**Modelos:** SlideTemplate (padrao visual) → SlidePresentation (aula gerada) → SlideGenerationLog

**Fluxo via API:**
- POST `/api/v1/slides/generate` — gera apresentacao com prompt + disciplina
- PATCH `/api/v1/slides/presentations/{id}` — atualiza com novo prompt
- GET `/api/v1/slides/presentations` — lista apresentacoes do professor

**Fluxo via WhatsApp:**
- Professor envia mensagem pedindo slides → intent `slide_generate`
- task_executor chama slide_service.generate_slides()
- IA gera JSON com slides seguindo template institucional (cores, fontes, layout)
- Resposta confirma criacao e orienta a ver no painel

**Templates configurados:**
- "Padrao Anchieta" — cores #1B3A5C/#E8B931, Montserrat/Open Sans
- "Minimalista" — cores #2C3E50/#3498DB, Roboto

---

## 7. Dados de Demo (seed_demo.py)

Script: `scripts/seed_demo.py` | Comando: `make seed-demo`

Cria dados completos para demonstracao/pitch deck:
- 1 super admin + 1 tenant (Faculdade Anchieta)
- 1 admin, 2 agentes, 3 professores (com credenciais)
- 8 alunos com notas, frequencia, boletos, horarios
- 5 funcionarios com holerites, ferias, ponto, solicitacoes RH
- 14 contatos WhatsApp (alunos + funcionarios + visitante)
- 6 conversas com mensagens realistas
- 5 tickets com comentarios (diferentes status/prioridades)
- 2 templates de slides + 3 apresentacoes completas
- 14 artigos KB em 5 categorias
- 4 templates de mensagem WhatsApp
- 4 pesquisas de satisfacao (media 4.5/5)
- 2 resolucoes de aprendizado IA
- Metricas de resposta e logs de auditoria

**Credenciais de demo:**
| Role | Email | Senha |
|---|---|---|
| Super Admin | admin@igs.com | Admin@123456 |
| Admin | gestor@anchieta.edu.br | Gestor@2026 |
| Agente | suporte1@anchieta.edu.br | Suporte@2026 |
| Professor | prof.andre@anchieta.edu.br | Prof@2026 |

---

## 8. Estado do WhatsApp (marco 2026)

- WHATSAPP_APP_SECRET configurado no .env
- Meta WhatsApp Phone Number ID configurado
- **Problema:** envio de mensagens retorna erro de SPAM
- **Acao:** aguardar 48h (a partir de 30/03/2026) e testar novamente (~01/04/2026)
- Webhook de recebimento funciona (verificacao HMAC ok)

---

## 9. CI/CD

### GitHub Actions (ci.yml)
3 jobs paralelos em push para master/main/develop:

1. **Backend Tests** — PostgreSQL 16 + Redis 7, `pip install -e ".[dev]"`, `ruff check`, `pytest`
2. **Backend Lint** — `ruff check app/` + `ruff format --check app/`
3. **Frontend Build** — `npm ci`, `tsc --noEmit`, `npm run build`

**Ruff config:** line-length=100, py312, select=["E","F","I","N","W"], ignore=["E501","N818"]

### Deploy (deploy.yml)
Trigger: push de tag `v*` → SSH para servidor → `docker compose pull` + `alembic upgrade head` + rolling restart

---

## 10. Historico de Evolucao

### Fase 1 — Estrutura Base
- Setup Docker (12 containers), PostgreSQL, Redis, Celery
- Models base com multi-tenancy (TenantMixin)
- Auth JWT, RBAC com roles
- API REST completa (auth, students, employees, tickets, KB, dashboard)
- Frontend React com todas as paginas
- Webhook WhatsApp com verificacao HMAC
- CI/CD com GitHub Actions

### Fase 2 — IA e Automacao
- Cliente IA unificado (Groq/Gemini/Anthropic)
- Classificador de intents (26 intents iniciais)
- Servico de resposta RAG (dados reais + KB + historico)
- Processamento assincrono de mensagens (Celery)
- Task executor para acoes automatizadas
- Transcricao de audio
- Sistema de aprendizado IA (TicketResolution)
- Metricas IA vs Humano

### Fase 3 — Slides + Demo
- Sistema de slides via IA (models, schemas, routes, service)
- 2 intents novos: slide_generate, slide_update
- Handlers de slides no task_executor (gerar/atualizar via WhatsApp)
- Handlers de schedule_query, time_record_query, hr_request no fluxo de mensagens
- Formatacao de dados para schedule, time_record, hr_request no ai_service
- Seed completo para demo/pitch deck (seed_demo.py)
- CI verde em todos os 3 jobs

### Fase 4 — Completude para Pitch Deck (atual)
- **PPTX Export:** python-pptx para gerar .pptx a partir do JSON de slides (pptx_service.py)
- **Endpoint download:** GET /api/v1/slides/presentations/{id}/download retorna .pptx
- **Pagina de Slides no Frontend:** Slides.tsx com listagem, preview, geracao via IA, download PPTX
- **Dashboard KPIs expandidos:** satisfacao media, total alunos/funcionarios, mensagens/mes, tokens IA, economia estimada
- **Boleto PDF:** boleto_pdf_service.py gera PDF via ReportLab; endpoint GET /students/{id}/boletos/{id}/pdf
- **send_document_message:** nova funcao no whatsapp_service para envio de documentos via WhatsApp
- **Notificacoes Proativas:** tasks de alerta de frequencia (diario 10h), notificacao de notas (a cada 6h), alem do lembrete de boleto ja existente
- **Onboarding via WhatsApp:** integracao do student_onboarding.py no message_tasks.py; contatos nao verificados que pedem inscricao/cadastro entram no fluxo step-by-step
- **Settings funcional:** API GET/PUT /tenants/settings/current; Settings.tsx com state management e chamadas API reais; salva bot_name, horarios, mensagens, chaves de integracao
- **Relatorios PDF/Excel:** rows_to_pdf (ReportLab) e rows_to_excel (openpyxl) no report_service; endpoints /reports/{conversations,tickets}/{pdf,excel}
- **Webhook Outbound funcional:** dispatch_event chamado ao criar ticket (ticket.created) e ao processar mensagem (message.processed); entrega via Celery com HMAC-SHA256

### Fase 5 — Security Hardening (Enterprise)
- **Row-Level Security (RLS):** migration Alembic (b7e2a9f3c1d8) habilita RLS em 32 tabelas tenant-scoped; 4 policies por tabela (SELECT/INSERT/UPDATE/DELETE) usando current_setting('app.current_tenant', true)
- **Dual Database Roles:** igs_app (RLS-enforced, usado pela API FastAPI) e igs_worker (BYPASSRLS, usado pelo Celery para tarefas cross-tenant como SLA e notificacoes)
- **dependencies.py reescrito:** dois engines (engine + worker_engine), dois session factories (AsyncSessionLocal + WorkerSessionLocal); _set_tenant_context() injeta tenant_id via set_config no PostgreSQL antes de cada query
- **Celery tasks migrados:** dlq_tasks, message_tasks, notification_tasks, report_tasks, webhook_tasks usam WorkerSessionLocal (BYPASSRLS) em vez de AsyncSessionLocal
- **config.py:** adicionados RLS_ENABLED (bool), RLS_APP_PASSWORD, RLS_WORKER_PASSWORD
- **Docker hardening (docker-compose.prod.yml):** PostgreSQL e Redis com ZERO portas publicadas (expose only); Redis com --requirepass, comandos perigosos renomeados/desabilitados (FLUSHDB, FLUSHALL, DEBUG); Tailscale sidecar para acesso admin remoto via VPN; Nginx como unico servico public-facing (80/443); Certbot para renovacao SSL automatica; resource limits em todos os containers
- **PostgreSQL hardening:** pg_hba.conf com SCRAM-SHA-256, acesso restrito a redes Docker internas (172.16.0.0/12, 10.0.0.0/8), reject total para IPs externos; postgresql.conf com row_security=on, logging de DDL e queries lentas >1s
- **Cloudflare WAF (3 regras free tier):** Regra 1 bloqueia SQLi/XSS em /api/ (exceto webhook para evitar falso-positivo da Meta); Regra 2 rate-limit + challenge no POST /auth/login (10 req/min/IP); Regra 3 whitelist de IPs Meta (AS32934) no webhook WhatsApp
- **Novos arquivos:** infra/pg_hba.conf, infra/postgresql.conf, infra/cloudflare-waf-rules.md, .env.prod.example

### Fase 6 — LGPD + Resiliencia IA
- **Data Masking (LGPD):** utils/data_masking.py com funcoes mask_cpf, mask_email, mask_phone, mask_credit_card, mask_pii; integrado no webhook (salvamento de mensagens do usuario) e em _save_bot_message (respostas do bot); todas as mensagens salvas no banco ja tem PII mascarado
- **Direito ao Esquecimento (LGPD Art. 18):** services/anonymization_service.py com anonymize_student() e anonymize_employee(); substitui PII por hashes irreversiveis mantendo integridade referencial; anonimiza student/employee, contacts, messages (sender_type=user), boletos, hr_requests, payslips; registra audit log com detalhes da operacao
- **Endpoints de anonimizacao:** POST /api/v1/admin/lgpd/anonymize/student/{id} e /employee/{id}; requer role super_admin ou admin; recebe motivo da solicitacao
- **Circuit Breaker (ai_client.py):** tenacity retry (2 tentativas com backoff exponencial) em cada provider; CircuitState por provider (threshold=3 falhas, recovery=60s); fallback automatico entre providers (groq→gemini→anthropic); detecta timeout, 429, 500/502/503; AIResponse agora inclui provider_used para rastreabilidade
- **Novos arquivos:** utils/data_masking.py, services/anonymization_service.py
- **Dependencia adicionada:** tenacity==9.0.0

---

## 11. Proximos Passos Sugeridos

1. **WhatsApp:** testar envio apos 48h do bloqueio de spam (~01/04/2026)
2. **Deploy:** configurar servidor de producao e primeiro deploy com docker-compose.prod.yml
3. **Pitch Deck:** preparar demonstracao end-to-end com dados do seed_demo
4. **Frontend Slides:** adicionar preview visual estilo PowerPoint (render HTML dos slides)
5. **Notificacoes:** criar templates HSM na Meta para boleto_lembrete, frequencia_alerta
6. **Relatorios agendados:** envio automatico de relatorios semanais via Celery Beat
7. **Seguranca adicional:** criptografar tokens do tenant em repouso (Fernet), audit logging de acessos RLS

---

## 12. Comandos Uteis

```bash
make up              # Subir todos os servicos
make migrate         # Rodar migracoes Alembic
make seed            # Seed basico
make seed-demo       # Seed completo para demo/pitch
make test            # Rodar testes
make lint            # Ruff check
make format          # Ruff format
make logs            # Ver logs de todos os servicos
make shell           # Shell no container da API
```

---

## 13. Regras para o Claude

1. **NAO remova arquivos existentes** — apenas adicione ou edite
2. **Rode `ruff check` e `ruff format`** antes de commitar (disponivel em `$HOME/.local/bin/ruff`)
3. **Testes devem passar** com SQLite (conftest usa aiosqlite) e PostgreSQL (CI)
4. **Multi-tenancy:** todo model com dados de tenant DEVE ter `tenant_id`
5. **AI Provider:** use `ai_client.ai_complete()` — NUNCA chame APIs de IA diretamente
6. **Intents novos:** adicionar em `intent_classifier.py` (VALID_INTENTS + prompt) E no `task_executor.py` se for acao
7. **Commits:** mensagens em ingles, prefixos feat/fix/refactor/docs
8. **O usuario prefere comunicacao em portugues brasileiro**
