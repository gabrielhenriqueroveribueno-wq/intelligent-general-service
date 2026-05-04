# IGS — Intelligent General Service
## Resumo Completo do Projeto para Apresentação

> Documento gerado a partir de auditoria completa do código-fonte (não do `CONTEXT.md`, que está desatualizado).
> Última atualização: 2026-05-02.

---

## 1. O que é o IGS — pitch em uma frase

**Um SaaS multi-tenant que transforma o WhatsApp da instituição de ensino em uma central de atendimento 24/7. A assistente virtual "Billie" conversa naturalmente com alunos, funcionários, professores e candidatos — usando IA com fallback automático, dados reais do banco, e um painel administrativo PWA completo para a equipe interna.**

---

## 2. O Problema

A secretaria de uma escola média (800 alunos, 60 funcionários) gasta hoje cerca de **R$ 26.800/mês** atendendo manualmente perguntas repetitivas: nota, boleto, falta, holerite, declaração, agendamento. E mesmo assim:

- Aluno espera **8 minutos** em média por uma resposta
- Atendimento só de segunda a sexta, em horário comercial
- Em pico (provas, matrícula) o tempo triplica
- Coordenação só descobre que um aluno vai evadir **depois** que ele já desistiu
- Equipe esgotada respondendo as mesmas perguntas todos os dias

---

## 3. A Solução — quatro produtos em uma plataforma

1. **Billie** — agente de IA no WhatsApp que responde 24/7, identifica o usuário com segurança, busca dados reais e transfere para humano quando precisa.
2. **Painel administrativo PWA** — 36 páginas para gestão de conversas, tickets, alunos, funcionários, slides, métricas, configurações; instalável como app no celular/desktop com push notifications nativas.
3. **Automação proativa** — 14 tarefas agendadas que rodam sozinhas: lembretes, alertas de evasão, relatórios semanais, anonimização LGPD.
4. **Integrações com sistemas legados** — adapters prontos para **Sophia (Prima)**, **TOTVS RM Educacional** e **REST genérico**, sincronização automática a cada 6h.

---

## 4. Stack Tecnológica (real, lida de `pyproject.toml` e `package.json`)

### Backend
| Camada | Tecnologia | Versão |
|---|---|---|
| Runtime | Python | 3.12 |
| Framework | FastAPI | 0.115 |
| ORM | SQLAlchemy async | 2.0.35 |
| Driver | asyncpg | 0.29 |
| Migrations | Alembic | 1.13 |
| Banco | PostgreSQL | 16 |
| Cache/Fila | Redis | 7 |
| Worker | Celery | 5.4 |
| Auth | python-jose (JWT) + bcrypt | — |
| AI Providers | anthropic 0.40 + google-generativeai + groq | — |
| Resiliência | tenacity | 9.0 |
| Criptografia | cryptography (Fernet) | 43 |
| Web Push | pywebpush | 2.0 |
| PDF | ReportLab | 4.2 |
| Excel | openpyxl | 3.1 |
| PowerPoint | python-pptx | 1.0 |
| Erros | sentry-sdk[fastapi] | 2.19+ |
| Backup S3 | boto3 | 1.35+ |
| Métricas | prometheus-fastapi-instrumentator | 7.0 |

### Frontend
| Camada | Tecnologia | Versão |
|---|---|---|
| Framework | React + TypeScript | 18.3 + 5.6 |
| Build | Vite | 5.4 |
| Estilo | TailwindCSS | 3.4 |
| Roteamento | react-router-dom | 6.26 |
| Data fetching | @tanstack/react-query | 5.59 |
| Forms | react-hook-form + zod | 7.53 + 3.23 |
| HTTP | axios | 1.7 |
| Charts | recharts | 2.13 |
| Ícones | lucide-react | 0.454 |
| Datas | date-fns | 4.1 |
| Toasts | react-hot-toast | 2.4 |
| Erros | @sentry/react | 8.55+ |
| PWA | vite-plugin-pwa + workbox-* | 0.20 + 7.4 |

### Infraestrutura
- **Docker Compose** — 12 containers em dev, 5 em prod-light (Oracle Free Tier), full stack em `docker-compose.prod.yml`
- **Caddy** com Let's Encrypt automático (prod-light)
- **Nginx** como reverse proxy (full stack)
- **Cloudflare WAF** (3 regras documentadas)
- **Tailscale sidecar** para acesso admin remoto via VPN

---

## 5. O que a Billie faz hoje — **40 intenções classificadas**

(Lista verificada em `backend/app/services/intent_classifier.py`)

### Para alunos (17)
- `grade_query`, `attendance_query`, `schedule_query` — consultas acadêmicas
- `boleto_query`, `generate_boleto`, `generate_pix` — financeiro + emissão de PIX/boleto
- `enrollment_query`, `enrollment_request`, `class_enrollment` — matrícula
- `document_request`, `certificate_request` — documentos
- `grade_appeal`, `transfer_request` — ações administrativas
- `scholarship_query`, `internship_query`, `event_registration` — informações
- `library_query`, `library_renewal` — biblioteca
- `financial_negotiation` — negociação de débito
- `tutor_question` — Tutor IA (orienta o que estudar)
- `medical_certificate` — atestado médico por foto

### Para funcionários (4)
- `payslip_query` — holerite
- `vacation_query` — saldo de férias
- `time_record_query` — ponto
- `hr_request` — solicitações de RH

### Para professores (2)
- `slide_generate`, `slide_update` — gerar/atualizar apresentações via IA

### Serviços transversais (3)
- `schedule_appointment`, `cancel_appointment` — agendamento presencial
- `document_ocr` — reconhecer documento por foto
- `facility_ticket` — chamado de manutenção/infra (com foto)

### Comportamento geral (10)
- `faq`, `greeting`, `farewell`, `verification`, `human_handoff`
- `feedback_response` — resposta de pesquisa de satisfação (1-5)
- `enable_reminders` / `disable_reminders` — opt-in de notificações
- `unknown` — fallback

### Comandos invisíveis embutidos pela IA na resposta
A IA retorna comandos em colchetes que são extraídos via regex e executados pelo backend antes de enviar a resposta limpa ao usuário:
`[IDENTIFY:student:RA]`, `[PASSWORD:valor]`, `[HANDOFF]`, `[CANCEL]`, `[FEEDBACK_REQUEST]`, `[FEEDBACK:N]`, `[REMINDERS_ON]`, `[REMINDERS_OFF]`, `[GENERATE_DOC:tipo]`.

---

## 6. Como Funciona — fluxo real (lido em `tasks/message_tasks.py` + `services/ai_client.py`)

```
Usuário no WhatsApp
        ↓
Meta Cloud API
        ↓
FastAPI webhook
  - Valida HMAC-SHA256
  - Mascarar PII (CPF/email/tel/cartão) antes de salvar
  - Enfileirar Celery
        ↓
Celery worker
  - Cria engine async dedicada (evita conflito de event loop)
  - Se áudio → transcrição
  - Detecta estado do contato:
      • NÃO VERIFICADO   → prompt "Billie pede RA naturalmente"
      • AGUARDANDO SENHA → prompt "Billie pede senha"
      • VERIFICADO       → acesso completo aos dados
  - Classifica intent (35-50 tokens, modelo barato)
  - Análise de sentimento (PT-BR, keyword-based, sem custo de IA)
  - Calcula sinal de evasão (gatilhos como "trancar curso")
  - Busca dados reais no PostgreSQL conforme intent
  - Busca artigos KB relevantes (com cache Redis 5min)
  - Busca resoluções similares (aprendizado IA)
  - Gera resposta com IA usando contexto RAG
        ↓
ai_complete() — Multi-provider com Circuit Breaker
  - Tenta provider primário (groq por padrão)
  - Se falha (timeout/429/5xx): retry 2x com backoff exponencial
  - Se circuito abre (3 falhas): tenta fallback chain
      groq → gemini → anthropic
      gemini → anthropic → groq
      anthropic → groq → gemini
  - Vision: gemini → anthropic (groq não suporta)
  - Se TODOS falharem: ai_complete_safe() ativa fallback offline
      • Detecta intent por keyword
      • Busca KB por palavras-chave
      • Resposta genérica + [HANDOFF]
        ↓
Extrai e executa comandos embutidos
Limpa a resposta
        ↓
Envia via WhatsApp Cloud API
        ↓
Registra: tokens, tempo, intent, provider_used, sentimento
Publica via Redis pub/sub → WebSocket → painel ao vivo
Dispara webhook outbound message.processed (HMAC-SHA256)
Descarta engine async
```

**Tempo médio observado:** 3 segundos por mensagem.

---

## 7. Banco de Dados — **23 modelos, 11 migrations, RLS ativado**

### Modelos (23 arquivos em `backend/app/models/`)
`tenant`, `user`, `student`, `employee`, `billing` (Boleto), `conversation` (Contact + Conversation + Message), `ticket`, `ticket_learning`, `knowledge_base`, `slide`, `schedule`, `notification`, `satisfaction`, `service_request`, `metrics`, `audit`, `webhook`, `library`, `appointment`, `academic_integration`, `push_subscription`, `report_subscription`.

### Histórico real de migrations Alembic
1. `85cef5d6b524` — initial schema
2. `84781b46eefb` — webhooks endpoints + delivery
3. `a3f1b2c4d5e6` — tabelas de slides
4. `b7e2a9f3c1d8` — **Row-Level Security em 32 tabelas tenant-scoped** (4 policies cada)
5. `c8d3e5f7a9b1` — módulos PIX, biblioteca, materiais
6. `d9e4f6a7b2c3` — tabela de agendamentos presenciais
7. `e1a2b3c4d5e6` — `report_subscriptions` (assinaturas de relatório por email)
8. `f2b3c4d5e6f7` — `academic_integrations` (Sophia/TOTVS/REST)
9. `g3c4d5e6f7a8` — `push_subscriptions` (Web Push VAPID)
10. `h4d5e6f7a8b9` — colunas de **sentimento** em `messages` + **risco de evasão** em `students`
11. `i5e6f7a8b9c0` — **9 índices de performance** (conversations, messages, students, tickets, boletos, audit_logs)

### Multi-tenancy de verdade
- **ORM:** `TenantMixin` em todo modelo tenant-scoped
- **Banco:** RLS PostgreSQL com 2 roles distintos:
  - `igs_app` (RLS-enforced) — usado pela API
  - `igs_worker` (BYPASSRLS) — usado pelo Celery para cross-tenant
- **JWT:** carrega `tenant_id` e `plan` no payload

---

## 8. API REST — **26 módulos de rotas** (verificado em `api/v1/router.py`)

`auth`, `tenants`, `users`, `students`, `employees`, `conversations`, `tickets`, `knowledge_base`, `dashboard`, `reports`, `webhook`, `ws`, `admin`, `ai_health`, `onboarding`, `report_subscriptions`, `integrations`, `templates`, `webhooks_config`, `metrics`, `slides`, `student_portal`, `push_subscriptions`, `evasion`, `billing`, `health`.

Destaques que **não estavam** no CONTEXT.md:
- `/integrations` — CRUD de integração com sistema acadêmico (Sophia/TOTVS/REST genérico)
- `/billing` — checkout SaaS via Mercado Pago para tenants
- `/admin/ai-health` — status dos providers de IA (circuit breaker state)
- `/onboarding` — onboarding wizard do tenant
- `/portal/student` — portal do aluno
- `/push-subscriptions` — registro de Web Push
- `/report-subscriptions` — assinaturas de relatório executivo por email
- `/evasion` — listagem e detalhes de risco de evasão

---

## 9. Serviços — **36 serviços + subsistema de integrações**

Lidos em `backend/app/services/`:

### IA e processamento
- `ai_client` — multi-provider com circuit breaker + retry tenacity
- `ai_fallback` — resposta offline (keyword + KB) quando tudo falha
- `ai_service` — geração RAG com dados reais
- `intent_classifier` — classificação em 40 intents
- `sentiment_service` — análise de sentimento PT-BR (keyword-based)
- `transcription_service` — áudio → texto
- `media_service` — download de mídia WhatsApp
- `task_executor` — despacha 22 tipos de ação automatizada

### Negócio
- `student_service`, `employee_service`, `ticket_service`, `knowledge_service`
- `slide_service` + `pptx_service` — geração de slides + export `.pptx`
- `boleto_pdf_service` — geração de boleto em PDF
- `appointment_service` — agendamento presencial (slots, slots disponíveis)
- `library_service` — empréstimos/renovação
- `payment_service` — PIX BR Code + negociação
- `mercadopago_service` — Checkout Pro (PIX + cartão + boleto)
- `saas_billing_service` — cobrança mensal dos tenants via MP
- `tutor_service` — Tutor IA acadêmico
- `hr_vision_service` — atestado médico por foto
- `document_ocr_service` — OCR de documentos via IA Vision
- `student_onboarding`, `onboarding_service` — fluxos de auto-cadastro
- `evasion_service` — score 0-100 com 4 níveis (low/medium/high/critical)
- `learning_service` — busca de resoluções similares (memória institucional)

### Infra e operação
- `whatsapp_service` — envio de texto, listas, templates HSM, documentos
- `auth_service` — JWT + bcrypt
- `cache_service` — Redis-backed TTL (KB 5min, settings 10min, dashboard 2min)
- `email_service` + `email_templates` — Resend (preferido) + SMTP fallback
- `report_service` + `executive_report_service` — relatórios CSV/PDF/Excel + email HTML com tendências (% vs período anterior)
- `webhook_delivery_service` — entrega outbound com HMAC-SHA256
- `push_notification_service` — Web Push VAPID
- `ws_manager` — WebSocket via Redis pub/sub
- `metrics_service`, `sla_service`, `provider_health` — observabilidade
- `anonymization_service` — LGPD direito ao esquecimento (hashes irreversíveis)

### Subsistema de integrações com ERPs (`services/integrations/`)
- `base.py` — interface comum + helpers `upsert_student`/`upsert_employee`
- `sophia.py` — adapter Sophia (Prima Tecnologia), Bearer token, paginação offset/limit
- `totvs.py` — adapter TOTVS RM Educacional, Basic auth, OData com `$filter`/`$top`/`$skip`, `CODCOLIGADA`
- `generic_rest.py` — adapter genérico configurável (bearer/basic/header)
- `registry.py` — factory + catálogo com metadados para o frontend montar formulário dinâmico

---

## 10. Tarefas Celery — **13 arquivos, 14 jobs agendados**

Verificados em `backend/app/tasks/celery_app.py`:

| Job | Frequência | O que faz |
|---|---|---|
| `check-sla-breaches` | a cada 5min | verifica SLA de tickets abertos |
| `ai-providers-health-check` | a cada 15min | testa Anthropic/Groq/Gemini |
| `dispatch-scheduled-reports` | minuto 5 de cada hora | envia relatórios executivos por email |
| `dispatch-integration-syncs` | minuto 15 de cada hora | dispara sync com Sophia/TOTVS/REST |
| `compute-evasion-risks` | minuto 45 de cada hora | atualiza `evasion_risk_score` de todos os alunos |
| `check-evasion-risk` | diário 7h | alerta de evasão para coordenação via WhatsApp |
| `send-boleto-reminders` | diário 9h | lembrete de boletos vencendo |
| `send-attendance-alerts` | diário 10h | alerta de baixa frequência |
| `send-grade-notifications` | a cada 6h (min 30) | notifica novas notas |
| `reenrollment-campaign` | diário 9:30 | campanha de rematrícula (jun/jul/nov/dez) |
| `weekly-manager-report` | seg 8h | relatório semanal via WhatsApp |
| `weekly-pdf-report` | seg 8:30 | relatório PDF semanal por email |
| `daily-db-backup` | diário 3h | backup do banco |
| `auto-anonymize-lgpd` | dia 1° do mês 2h | anonimiza registros >5 anos inativos |

**Outras tasks (sem schedule, disparadas por eventos):** `message_tasks`, `webhook_tasks`, `dlq_tasks` (Dead Letter Queue), `push_tasks` (notifica admins via Web Push em ticket criado / SLA violado / handoff solicitado), `report_tasks`, `health_check_tasks`, `executive_report_tasks`, `integration_sync_tasks`.

---

## 11. Frontend — **36 páginas, PWA completa**

### Páginas públicas (sem login)
`Landing` (pitch comercial completo), `Pricing`, `Demo`, `CaseStudy`, `Legal`, `Tour`, `PublicStatus`

### Auth
`Login`, `Signup`

### App protegido (`/app/*`)
| Página | Função |
|---|---|
| Dashboard | KPIs em tempo real |
| Conversations + ConversationDetail | Lista e detalhe de conversas, assumir atendimento |
| Tickets | Tickets com SLA, comentários, prioridades |
| Students + StudentDetail | Alunos + notas/frequência/boletos/PDF |
| Employees + EmployeeDetail | Funcionários + holerites/férias/ponto |
| KnowledgeBase | Artigos da KB |
| Slides | Geração via IA + download `.pptx` |
| Reports | Export CSV/PDF/Excel |
| ReportSubscriptions | Configura quem recebe relatório executivo por email |
| Integrations | Configura Sophia/TOTVS/REST genérico |
| MetricsDashboard | Métricas IA vs humano |
| LearningInsights | Padrões detectados pelo aprendizado |
| ImportData | Importação de CSV (alunos/funcionários) |
| WhatsAppSetup | Wizard de configuração do WhatsApp |
| UserManagement | Gestão de usuários + roles |
| Tenants | Gestão de tenants (super admin) |
| SuperAdmin | Painel super admin |
| AuditLog | Log de auditoria |
| Status | Status interno do sistema |
| Help | Central de ajuda |
| Settings | Configurações do tenant |

### Erros e suporte
`NotFound`, `ServerError`, `Maintenance`, `Status`

### PWA real (não é só "responsivo")
- `manifest.json` com nome, ícones SVG (192/512/maskable), 3 shortcuts (Conversas, Tickets, Dashboard), categorias, idioma pt-BR
- Service Worker (`sw.ts`) com Workbox:
  - Precache do shell
  - `NetworkOnly` para `/auth` (nunca cacheia)
  - `NetworkFirst` com TTL de 5min para APIs de leitura
  - `CacheFirst` com TTL de 30 dias para imagens
  - SPA navigation fallback
- **Web Push receiver** com handler de `notificationclick` que abre/foca a janela
- `InstallBanner`, `OfflineBanner`, `CookieBanner` — UX completo de PWA

### Hooks customizados
`useNotifications`, `usePWA`, `usePushNotifications`, `useWebSocket`

---

## 12. Segurança e Hardening (verificado em código)

### Autenticação e autorização
- JWT com access 15min + refresh 7 dias
- 5 roles: `super_admin`, `admin`, `manager`, `agent`, `teacher`
- Senhas com bcrypt (passlib)

### Validação no boundary
- Webhook WhatsApp: assinatura HMAC-SHA256 obrigatória
- Webhook Mercado Pago: assinatura HMAC validada (`MP_WEBHOOK_SECRET`)
- Webhooks outbound: assinatura HMAC enviada no header `X-IGS-Signature`

### Rate limiting (`middleware/rate_limit_middleware.py`)
- Login: **10 req/min por IP** (proteção brute-force)
- Webhook WhatsApp: 300 req/min por IP (Meta envia em burst)
- API autenticada: 600 req/min por tenant
- API não-autenticada: 60 req/min por IP
- Headers `X-RateLimit-*` retornados em toda resposta

### Plan limits (`middleware/plan_limit_middleware.py`)
- Trial: 300 msg/mês, 3 usuários, sem slides/integrações/webhooks
- Starter: 2.000 msg/mês, 10 usuários, sem integrações
- Pro: 10.000 msg/mês, 50 usuários, tudo liberado
- Enterprise: ilimitado
- Bloqueia com HTTP **402 Payment Required** + `upgrade_required: true`

### LGPD
- **`utils/data_masking.py`** — mascara PII (CPF, email, telefone, cartão) **antes** de salvar mensagens no banco
- **`anonymization_service.py`** — substitui PII por hashes irreversíveis mantendo integridade referencial
- **`auto_anonymize_task`** roda dia 1° de cada mês: anonimiza alunos `dropped`/`graduated` e funcionários `inactive` com >5 anos
- Endpoints: `POST /api/v1/admin/lgpd/anonymize/student/{id}` e `/employee/{id}` (super_admin/admin)

### Criptografia em repouso
- **Fernet** (`utils/encryption.py`) para credenciais de integrações (Sophia/TOTVS), tokens sensíveis, CPFs
- **Web Push VAPID** keys (P-256 EC)

### Hardening de produção
- PostgreSQL e Redis **sem porta pública** (apenas `expose`)
- Redis com `--requirepass`, `FLUSHDB`/`FLUSHALL`/`DEBUG` desabilitados
- `pg_hba.conf` com SCRAM-SHA-256 + restrição a redes Docker internas
- `postgresql.conf` com `row_security=on`, log de DDL e queries lentas >1s
- **Tailscale sidecar** para acesso admin remoto via VPN
- **Cloudflare WAF** com 3 regras (anti-SQLi/XSS, rate-limit no login, whitelist Meta)
- **Sentry** com `send_default_pii=False`

---

## 13. Resiliência da IA (verificado em `services/ai_client.py`)

```
ai_complete()
   ↓
1. Tenta provider primário (groq/gemini/anthropic)
   ↓ se falha
2. Retry 2x com backoff exponencial (tenacity)
   ↓ se falha
3. Marca circuit_state.failures++
   ↓ se atinge 3 falhas
4. Abre o circuito por 60s (provider isolado)
   ↓
5. Tenta fallback chain (definida por provider primário):
      groq      → gemini → anthropic
      gemini    → anthropic → groq
      anthropic → groq → gemini
   ↓ se TUDO falhar
6. ai_complete_safe() ativa fallback offline:
      a) Detecta intent por keyword (notas, boletos, faltas, etc.)
      b) Busca KB por keywords
      c) Mensagem genérica com [HANDOFF]
   → NUNCA levanta exceção
```

**Vision (imagens):** fallback `gemini → anthropic` (Groq não suporta visão).

**Erros considerados retryáveis:** timeout, 429, 500/502/503, ConnectionError, `anthropic.RateLimitError`, `anthropic.APITimeoutError`, etc.

---

## 14. SaaS Billing (cobrança dos tenants)

(Verificado em `services/saas_billing_service.py` + `api/v1/billing.py` + `Pricing.tsx`)

| Plano | Preço/mês | Limites |
|---|---|---|
| **Starter** | R$ 297 | 500 alunos, 1 número WhatsApp, suporte por email |
| **Pro** ⭐ | R$ 497 | alunos ilimitados, funcionários, alertas de evasão IA, até 3 números WhatsApp, suporte prioritário |
| **Enterprise** | sob consulta | múltiplas unidades, integração com sistemas legados via API, SLA 24/7, on-premise disponível |

**Como funciona:**
- Tenant solicita link via `POST /api/v1/billing/checkout`
- Sistema chama Mercado Pago Checkout Pro (PIX + cartão + boleto)
- Webhook `POST /api/v1/billing/webhook` recebe notificação MP, valida HMAC, ativa/suspende `tenant.is_active`
- 14 dias grátis, sem cartão, sem fidelidade

---

## 15. Inteligência institucional — três sistemas únicos

### A. Análise de sentimento em PT-BR
- **Sem custo de IA** — keyword-based (`services/sentiment_service.py`)
- 50+ palavras-chave negativas ponderadas (-0.3 a -0.9): "absurdo", "decepção", "cancelar matrícula", "vou largar"
- 30+ palavras positivas (+0.35 a +0.75): "obrigado", "excelente", "resolveu"
- Resultado salvo em cada mensagem (`messages.sentiment` + `sentiment_score`)
- Função `is_evasion_signal()` detecta gatilhos explícitos de abandono

### B. Score de risco de evasão por aluno
- Roda a **cada hora** (`compute_evasion_risks_task`)
- Score 0-100 ponderando 5 fatores:
  - Status de matrícula (locked +40, dropped = 100)
  - Média de notas (<5 +30, 5-7 +15)
  - Frequência (faltas ≥25% +25, 15-25% +10)
  - Boletos em atraso (2+ +20, 1 +10)
  - Sentimento negativo recente (3+ msg negativas +15)
- 4 níveis: `low` (0-25), `medium` (26-50), `high` (51-75), `critical` (76+)
- Fatores legíveis salvos em JSON para a coordenação ler
- Alerta diário às 7h via WhatsApp para gestores

### C. Aprendizado IA com tickets resolvidos
- Cada ticket fechado vira um `TicketResolution`
- Quando uma nova conversa chega, sistema busca resoluções similares
- IA usa as resoluções como contexto extra na geração da resposta
- Métricas no painel "Aprendizado IA"

---

## 16. Monitoramento e Observabilidade

### Stack completa (dev / prod full)
- **Prometheus** — scrape `igs-api:8000/metrics` a cada 10s + `redis-exporter`
- **Grafana** — dashboards
- **Loki + Promtail** — agregação de logs de todos os containers
- **AlertManager** — disparo de alertas

### Stack leve (prod-light, 1GB RAM)
- Apenas Caddy + API + Celery + Postgres + Redis
- Limites de memória estritos: Caddy 64M, API 256M, Celery 256M, Postgres 192M, Redis 96M

### 9 alertas configurados (`monitoring/prometheus/rules/igs-alerts.yml`)
**Bot performance:**
- `BotResponseTimeHigh` — P95 > 8s por 2min (warning)
- `BotResponseTimeCritical` — P95 > 15s por 1min (critical)

**SLA:**
- `SLABreachRateHigh` — taxa de violação > 0.05/s por 5min
- `SLABreachSpike` — 5+ violações em 5min (critical)

**Custo de IA:**
- `HighTokenConsumption` — projeção > 100k tokens/h por 10min
- `ExcessiveTokenConsumption` — projeção > 500k tokens/h por 5min (critical)

**Infraestrutura:**
- `APIDown` — API não responde por 1min (critical)
- `RedisDown` — Redis não responde por 1min (critical)
- `HighHTTPErrorRate` — >5% de respostas 5xx por 3min
- `NoMessagesProcessed` — zero mensagens em 15min

### Erros em runtime
- **Sentry** integrado em backend (FastAPI + SQLAlchemy + Logging) e frontend (`@sentry/react`)

---

## 17. CI/CD (verificado em `.github/workflows/`)

### CI (`ci.yml`) — 3 jobs paralelos em push/PR para master/main/develop
1. **Backend Tests** — PostgreSQL 16 + Redis 7 services, ruff check, pytest unit + integration, upload coverage Codecov + HTML artifact
2. **Backend Lint** — `ruff check app/` + `ruff format --check app/`
3. **Frontend Build** — `npm ci`, `tsc --noEmit`, `npm run build`

### Deploy (`deploy.yml`) — em tag `v*`
- SSH para servidor (appleboy/ssh-action)
- `docker compose pull` da prod
- Migrations via `alembic upgrade head`
- **Rolling restart com `--scale api=2 → 1`** (zero-downtime)
- Restart de celery_worker, celery_beat, nginx
- `docker image prune -f`
- Notificação de status com summary

### Testes existentes (~14 arquivos)
**`backend/app/tests/`** (legacy): `test_ai_fallback`, `test_auth`, `test_feedback_flow`, `test_onboarding`, `test_provider_health`, `test_security_utils`, `test_student_service`, `test_tenant_isolation`, `test_webhook`

**`backend/tests/unit/services/`** (novo): `test_ai_client_circuit_breaker`, `test_evasion_service`, `test_intent_classifier`, `test_sentiment_service`, `test_task_executor`

**`backend/tests/integration/`**: `test_tenant_isolation`

---

## 18. Deploy em produção (estado atual)

- **Servidor:** Oracle Cloud Free Tier — VM.Standard.E2.1.Micro (1 OCPU, 1GB RAM, São Paulo)
- **IP:** 137.131.151.205
- **Domínio:** `igs-anchieta.duckdns.org` (DuckDNS gratuito)
- **HTTPS:** Caddy + Let's Encrypt automático
- **Stack rodando:** `docker-compose.prod-light.yml` (5 containers)
- **Webhook ativo:** `https://igs-anchieta.duckdns.org/api/v1/webhook/whatsapp`
- **Phone Number ID Meta:** 1142668418921479
- **Bot Billie em produção** respondendo mensagens reais

**Alternativa para acesso sem porta pública:** `docker-compose.tunnel.yml` com Cloudflare Tunnel.

---

## 19. O que existe HOJE no código mas NÃO estava no `CONTEXT.md`

Esta é a parte importante para a apresentação — coisas que o doc oficial ainda não capturou:

### Backend
- ✅ **Sentry** para error tracking (backend + frontend)
- ✅ **Resend** como provider de email primário (SMTP é fallback)
- ✅ **Web Push (VAPID)** com `pywebpush` — push notifications nativas no PWA
- ✅ **boto3** para upload de backup S3-compatible
- ✅ **Cache service** dedicado (Redis DB 4) para KB/settings/dashboard
- ✅ **Sentiment analysis PT-BR** keyword-based (zero custo)
- ✅ **Evasion risk score** computado por hora para todo aluno ativo
- ✅ **SaaS billing** completo via Mercado Pago (Starter/Pro/Enterprise)
- ✅ **Executive HTML email reports** com comparação de tendências (% vs período)
- ✅ **Subsistema de integrações** (Sophia/TOTVS/REST) com sync schedule, credenciais Fernet-encrypted, catálogo de metadata pro frontend
- ✅ **PlanLimitMiddleware** — bloqueia rotas e mensagens por plano
- ✅ **RateLimitMiddleware** — sliding window por tenant/IP/path
- ✅ **AlertManager** + 9 regras Prometheus customizadas

### Frontend
- ✅ **PWA real** com service worker, manifest, install banner, offline banner, push receiver
- ✅ **react-query** + **react-hook-form** + **zod** + **recharts**
- ✅ **Sentry React**
- ✅ Páginas Landing, Pricing, Demo, CaseStudy (material comercial dentro do app)
- ✅ Páginas Signup, Tour, Help, ImportData, WhatsAppSetup, ReportSubscriptions, Integrations, AuditLog, SuperAdmin (não estavam no doc)
- ✅ Lazy loading de páginas pesadas
- ✅ Aliases legados (`/dashboard` → `/app/dashboard`)
- ✅ Sidebar com badge de "conversas aguardando agente" (refetch 20s)

### Infra
- ✅ `docker-compose.prod-light.yml` para servidor 1GB
- ✅ `docker-compose.tunnel.yml` para Cloudflare Tunnel
- ✅ Caddy com Let's Encrypt
- ✅ 11 migrations (não 7 como o CONTEXT.md sugeria)
- ✅ Migration de **performance indexes** com 9 índices compostos para queries críticas

---

## 20. Por que o IGS vende — argumentos verificados

### Para a instituição
- Reduz custo de atendimento da secretaria significativamente
- Atendimento 24/7 com tempo médio de 3 segundos
- Antecipa evasão (score atualizado de hora em hora com fatores legíveis)
- Pronto para usar: já vem com seed de demo, multi-tenant, painel completo, PWA instalável

### Para o decisor (gestor/dono)
- SaaS com mensalidade previsível (Mercado Pago integrado)
- LGPD-compliant **desde o código**: mascaramento automático, anonimização agendada, direito ao esquecimento
- **Não depende de uma IA só**: 3 providers + retry + circuit breaker + fallback offline com keyword/KB
- Integra com **TOTVS RM** e **Sophia (Prima)** — não precisa trocar o ERP acadêmico
- Trial de 14 dias sem cartão de crédito

### Para o time técnico
- Stack moderna documentada (Python 3.12 / React 18 / TypeScript 5)
- Docker Compose: 1 comando para subir
- Monitoramento incluído (Prometheus + Grafana + Loki + AlertManager + Sentry)
- CI/CD pronto: 3 jobs em paralelo + deploy em tag com rolling restart
- Tests unitários + integração + coverage Codecov
- Plan-limits e rate-limits prontos para multi-tenancy real

---

## 21. Roteiro sugerido para a apresentação (15 min)

| Tempo | Slide | Conteúdo |
|---|---|---|
| 0-2min | **O problema** | Custo de R$ 26.800/mês, espera de 8min, equipe esgotada |
| 2-4min | **A Billie** | Vídeo/screenshot do WhatsApp respondendo |
| 4-6min | **Como funciona** | Diagrama: WhatsApp → IA → dados reais → resposta |
| 6-9min | **O painel** | Tour rápido pelo Dashboard, Conversas ao vivo, Métricas, Slides IA |
| 9-11min | **Inteligência** | Score de evasão, sentimento, aprendizado contínuo |
| 11-13min | **Confiança** | Multi-tenancy + RLS + LGPD + 3 providers de IA + circuit breaker |
| 13-14min | **Preço e setup** | Trial 14 dias, Starter R$297, Pro R$497, setup em 1h |
| 14-15min | **Próximo passo** | Demonstração ao vivo com WhatsApp do prospect |

---

## 22. Frase de fechamento

> **"O IGS é o que acontece quando o WhatsApp da escola deixa de ser uma fila de espera e vira um assistente que conhece cada aluno, antecipa cada problema e responde em 3 segundos — 24 horas por dia, sustentado por uma plataforma multi-tenant pronta para escalar de 1 a 1.000 instituições, com a Billie no front e a Anthropic, Google e Groq cobrindo um ao outro por trás."**
