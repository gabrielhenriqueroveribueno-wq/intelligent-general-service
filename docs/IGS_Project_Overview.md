# IGS — Intelligent General Service: Documento de Contexto Completo

## Visao Geral

O IGS (Intelligent General Service) e um SaaS multi-tenant de atendimento inteligente via WhatsApp, projetado para instituicoes de ensino. O sistema recebe mensagens de alunos e funcionarios pelo WhatsApp, classifica a intencao da mensagem usando IA, busca dados reais no banco de dados e gera respostas contextualizadas automaticamente. O projeto utiliza um padrao RAG (Retrieval-Augmented Generation) onde a IA nunca inventa dados — ela apenas formata informacoes reais consultadas no banco.

Alem do atendimento automatico, o sistema oferece: painel administrativo completo em React, sistema de tickets com SLA, base de conhecimento, geracao de slides via IA para professores, exportacao de relatorios em CSV/PDF/Excel, notificacoes proativas (lembretes de boleto, alertas de frequencia, notas), onboarding de alunos via WhatsApp, metricas de desempenho IA vs humano, webhooks outbound, e monitoramento completo via Prometheus + Grafana + Loki.

Repositorio: github.com/gabrielhenriqueroveribueno-wq/intelligent-general-service. Branch principal: master. Linguagem principal: Python 3.12 (backend) e TypeScript/React 18 (frontend).

## Arquitetura

O fluxo principal e: Usuario WhatsApp envia mensagem para a Meta Cloud API, que faz POST no webhook do FastAPI. O FastAPI valida a assinatura HMAC, persiste a mensagem no PostgreSQL e enfileira uma tarefa no Celery via Redis. O worker Celery processa a mensagem: identifica o contato, classifica a intencao via IA (~50 tokens), busca dados relevantes no banco, gera a resposta via IA com contexto real, e envia a resposta de volta pelo WhatsApp Cloud API. Todo o processamento e assincrono para que o webhook retorne 200 rapidamente (requisito da Meta).

A stack completa inclui: FastAPI com SQLAlchemy 2.0 async e Alembic para o backend; PostgreSQL 16 com asyncpg como banco de dados; Redis 7 com Celery para filas e cache; React 18 com TypeScript, TailwindCSS e Vite para o frontend; Meta Business Cloud API para integracao WhatsApp; multi-provider de IA (Groq com llama-3.3-70b como ativo, mais Gemini e Anthropic); Prometheus, Grafana, Loki e Promtail para monitoramento; Docker e Docker Compose com 12 containers; JWT com access token de 15 minutos e refresh de 7 dias para autenticacao; e Nginx como proxy reverso.

O provider de IA ativo e o Groq (llama-3.3-70b-versatile), configuravel via variavel de ambiente AI_PROVIDER. O sistema suporta troca transparente entre Groq, Google Gemini e Anthropic Claude atraves do ai_client.py unificado.

## Multi-tenancy

O sistema usa estrategia de banco compartilhado com coluna tenant_id em todas as tabelas escopadas. O isolamento e garantido a nivel ORM pelo TenantMixin e pelo JWT que carrega o tenant_id do usuario autenticado. Cada tenant pode ter suas proprias chaves de API (WhatsApp, Claude), configuracoes de bot, horarios de funcionamento e SLA customizados. Os roles disponiveis sao: super_admin (acesso total), admin (gestao do tenant), manager (supervisao), agent (atendimento) e teacher (professor com acesso a slides).

## Modelos de Dados (19 tabelas)

O banco possui 19 tabelas organizadas em grupos: Tenant/Auth (Tenant, TenantSettings, User com 5 roles); Academico (Student, Grade, AttendanceRecord, ClassSchedule); RH (Employee, Payslip, VacationBalance, TimeRecord, HRRequest); Financeiro (Boleto); Atendimento (Contact, Conversation, Message, Ticket, TicketComment); Conhecimento (KBCategory, KBArticle); Slides IA (SlideTemplate, SlidePresentation, SlideGenerationLog); Notificacoes (MessageTemplate, ScheduledNotification); Satisfacao (SatisfactionSurvey, OnboardingSession); Operacional (ServiceRequest, ResponseTimeMetric, AuditLog, FailedTask, SLAConfig); Aprendizado (TicketResolution); e Webhooks (WebhookEndpoint, WebhookDelivery).

## Sistema de Classificacao de Intents (28 intents)

O sistema usa um classificador de intents em duas etapas. Primeiro, uma chamada barata a IA (~50 tokens) classifica a mensagem do usuario em um dos 28 intents. Depois, com base no intent, o sistema busca os dados relevantes no banco e faz uma segunda chamada a IA para gerar a resposta formatada com os dados reais.

Os intents de alunos (17) sao: grade_query, attendance_query, schedule_query, boleto_query, enrollment_query, generate_boleto, enrollment_request, document_request, class_enrollment, grade_appeal, transfer_request, scholarship_query, internship_query, event_registration, library_query, financial_negotiation e certificate_request. Os intents de funcionarios (4) sao: payslip_query, vacation_query, time_record_query e hr_request. Os intents de professores (2) sao: slide_generate e slide_update. Os intents gerais (5) sao: faq, greeting, verification, human_handoff e unknown.

## Fluxo Completo de Processamento de Mensagem

O processamento de cada mensagem segue 18 etapas: (1) Meta Cloud API recebe mensagem do usuario e envia POST para /api/v1/webhook/whatsapp. (2) FastAPI valida assinatura HMAC-SHA256, identifica tenant, persiste mensagem no banco. (3) Tarefa Celery process_incoming_message e enfileirada no Redis. (4) Worker carrega mensagem, conversa, contato e configuracoes do tenant. (5) Se mensagem de audio, transcreve via transcription_service. (6) Se contato nao verificado e pede inscricao, entra no fluxo de onboarding step-by-step. (7) Se contato nao verificado em outros casos, envia mensagem pedindo RA ou matricula. (8) Classifica intent via IA (~50 tokens), retornando intent e entities extraidas. (9) Se intent=human_handoff, cria ticket com SLA e transfere para agente humano. (10) Busca dados conforme intent: notas, boletos, holerites, ferias, horarios, etc. (11) Se intent de acao, task_executor executa (gerar boleto, solicitar documento, gerar slides). (12) Busca artigos relevantes na base de conhecimento via ILIKE full-text. (13) Busca resolucoes similares no sistema de aprendizado IA. (14) Gera resposta via ai_service com contexto RAG (dados reais + KB + historico de conversa). (15) Envia resposta via WhatsApp Cloud API. (16) Registra metricas: tokens usados, tempo de resposta, intent, tipo de resolucao. (17) Dispara webhook outbound (message.processed) para endpoints configurados. (18) Publica evento via Redis pub/sub para atualizar painel em tempo real via WebSocket.

## Sistema de Slides via IA

Professores podem gerar apresentacoes de aula completas via IA, tanto pelo painel web quanto pelo WhatsApp. O sistema utiliza templates institucionais que definem cores, fontes, layouts e regras de estrutura. A IA gera o conteudo dos slides em formato JSON estruturado, que pode ser visualizado no painel e exportado como arquivo .pptx (PowerPoint) usando a biblioteca python-pptx. Os templates configurados incluem o "Padrao Anchieta" com cores #1B3A5C/#E8B931 e fontes Montserrat/Open Sans, e o "Minimalista" com cores #2C3E50/#3498DB e fonte Roboto.

Endpoints disponiveis: POST /slides/generate (nova apresentacao), PATCH /slides/presentations/{id} (atualizar com novo prompt), GET /slides/presentations/{id}/download (baixar .pptx), GET /slides/presentations (listar) e GET /slides/templates (listar templates). Via WhatsApp, o professor envia uma mensagem pedindo slides e o intent slide_generate ou slide_update e classificado, gerando a apresentacao automaticamente.

## Servicos do Backend (23 servicos)

O backend possui 23 servicos: ai_client.py (cliente IA unificado que abstrai Groq, Gemini e Anthropic); ai_service.py (gera respostas RAG com dados reais, artigos KB, historico e resolucoes similares); intent_classifier.py (classifica mensagens em 28 intents com extracao de entidades); slide_service.py (gera e atualiza slides via IA seguindo templates institucionais); pptx_service.py (converte JSON de slides para .pptx com cores e fontes do template); boleto_pdf_service.py (gera PDF de boleto com dados do aluno usando ReportLab); task_executor.py (despacha e executa acoes automatizadas); student_service.py (CRUD e queries de alunos); employee_service.py (CRUD e queries de funcionarios); ticket_service.py (CRUD tickets com SLA e webhook outbound); knowledge_service.py (busca artigos KB); whatsapp_service.py (envio de mensagens texto, listas, templates e documentos via Meta API); student_onboarding.py (autocadastro em 6 etapas via WhatsApp); report_service.py (relatorios, dashboard KPIs, export CSV/PDF/Excel); learning_service.py (busca resolucoes similares); webhook_delivery_service.py (despacha eventos com HMAC-SHA256); metrics_service.py (metricas de tempo de resposta); sla_service.py (verificacao periodica de SLA); ws_manager.py (WebSocket via Redis pub/sub); transcription_service.py (transcricao de audio); media_service.py (download de midias WhatsApp); e auth_service.py (geracao e validacao JWT).

## API REST (20 modulos de rotas)

A API possui 20 modulos: auth.py (login, refresh, register, me); students.py (CRUD alunos, notas, frequencia, boletos incluindo PDF, horarios); employees.py (CRUD funcionarios, holerites, ferias, ponto, RH); conversations.py (listar, detalhar, atribuir agente, fechar); tickets.py (CRUD tickets, comentarios, atribuicao); slides.py (templates CRUD, gerar/atualizar/download apresentacoes); knowledge_base.py (categorias e artigos); webhook.py (webhook WhatsApp com verify e incoming); dashboard.py (metricas overview com KPIs expandidos); reports.py (export CSV, PDF e Excel de conversas e tickets); users.py (gestao de usuarios); tenants.py (gestao de tenants e GET/PUT settings); templates.py (templates WhatsApp); webhooks_config.py (CRUD endpoints outbound); metrics.py (metricas da aplicacao); health.py (health check); admin.py (operacoes administrativas); e ws.py (WebSocket real-time).

## Frontend React (16 paginas)

O painel administrativo e construido com React 18, TypeScript, TailwindCSS e Vite. Utiliza axios com interceptors para autenticacao JWT automatica (access + refresh). Possui WebSocket via hook useNotifications para receber atualizacoes em tempo real quando mensagens sao processadas. Layout responsivo com sidebar colapsavel no mobile.

As paginas incluem: Dashboard (KPIs de conversas, taxa de resolucao automatica, tempo medio, satisfacao, economia estimada), Conversas (listagem com filtros e historico em tempo real), Tickets (listagem com status/prioridade e comentarios), Alunos (listagem e detalhe com notas/frequencia/boletos/download PDF), Funcionarios (listagem e detalhe com holerites/ferias/ponto), Slides IA (listagem, geracao via IA, preview e download PPTX), Base de Conhecimento (categorias e artigos CRUD), Relatorios (export CSV/PDF/Excel com filtro de periodo), Metricas IA vs Humano (comparacao de desempenho), Aprendizado IA (insights sobre resolucoes e padroes), Usuarios (gestao com roles), e Configuracoes (bot name, horarios, mensagens, chaves de integracao).

## Tarefas Assincronas (Celery)

O Celery e usado para processamento assincrono de mensagens WhatsApp (que podem levar 2-5 segundos por conta das chamadas de IA), notificacoes agendadas, verificacao de SLA, entrega de webhooks e backups. O Celery Beat agenda tarefas periodicas: process_incoming_message (processamento principal com retry 3x), check_sla_task (verificacao de SLA a cada 5 minutos), send_boleto_reminders_task (lembrete de boletos diario as 9h), send_attendance_alerts_task (alerta de frequencia diario as 10h), send_grade_notifications_task (notificacao de notas a cada 6h), deliver_webhook_task (entrega de webhooks com HMAC), backup_database_task (backup semanal) e save_failed_task_async (Dead Letter Queue).

## Notificacoes Proativas

O sistema envia notificacoes proativas via WhatsApp: (1) Lembretes de boleto, 3 dias antes do vencimento, usando template HSM com nome do aluno, data e valor. (2) Alertas de frequencia, para alunos com mais de 25% de faltas em alguma disciplina. (3) Notificacoes de notas, quando novas notas sao lancadas nas ultimas 24 horas. Todas executam via Celery Beat de forma batch.

## Onboarding de Alunos via WhatsApp

Contatos nao verificados que enviam mensagens com palavras como "inscricao", "cadastro", "novo aluno" ou "quero me matricular" entram em um fluxo de onboarding step-by-step com 6 etapas: boas-vindas e coleta de nome, CPF com validacao e verificacao de duplicata, e-mail, curso desejado, confirmacao dos dados, e criacao do registro de aluno com RA gerado automaticamente. O fluxo e gerenciado pela tabela OnboardingSession que persiste o estado entre mensagens.

## Webhooks Outbound

O sistema dispara eventos webhook para endpoints externos configurados por tenant. Atualmente dois eventos sao emitidos: ticket.created (quando um ticket e aberto) e message.processed (quando uma mensagem e processada). A entrega e assincrona via Celery, com assinatura HMAC-SHA256 no header X-IGS-Signature para validacao pelo receptor. Os endpoints e entregas sao gerenciados via API CRUD completa.

## Monitoramento e Observabilidade

O stack de monitoramento inclui Prometheus (metricas), Grafana (dashboards), Loki (agregacao de logs) e Promtail (coleta de logs dos containers). O FastAPI expoe metricas automaticas via prometheus-fastapi-instrumentator. Metricas customizadas incluem: tokens de IA consumidos por tenant, mensagens processadas por intent, tempo de resposta por tenant, e contadores de resolucao automatica vs humana.

## Dados de Demonstracao

O script seed_demo.py popula o banco com dados realistas para demonstracao e pitch deck: 1 tenant (Faculdade Anchieta), 7 usuarios (admin, agentes, professores), 8 alunos com notas/frequencia/boletos/horarios completos, 5 funcionarios com holerites/ferias/ponto/solicitacoes, 14 contatos WhatsApp, 6 conversas com mensagens realistas, 5 tickets em diferentes status, 3 apresentacoes de slides, 14 artigos na base de conhecimento, pesquisas de satisfacao (media 4.5/5), metricas de resposta e logs de auditoria. Credenciais de demo: admin@igs.com / Admin@123456 (super admin), gestor@anchieta.edu.br / Gestor@2026 (admin tenant).

## CI/CD

O CI roda via GitHub Actions com 3 jobs paralelos em push para master: (1) Backend Lint com ruff check e ruff format --check; (2) Backend Tests com PostgreSQL 16 e Redis 7 executando pytest com asyncio; (3) Frontend Build com npm ci, tsc --noEmit e npm run build. Deploy via tag v* com SSH para servidor, docker compose pull e rolling restart. Lint config: ruff com line-length=100, py312, select E/F/I/N/W, ignore E501/N818.

## Historico de Evolucao

Fase 1 (Estrutura Base): Setup Docker com 12 containers, PostgreSQL, Redis, Celery. Models com multi-tenancy via TenantMixin. Auth JWT com RBAC. API REST completa. Frontend React com 15 paginas. Webhook WhatsApp com HMAC. CI/CD com GitHub Actions.

Fase 2 (IA e Automacao): Cliente IA unificado (Groq/Gemini/Anthropic). Classificador de 26 intents. Servico RAG com dados reais, KB e historico. Processamento assincrono Celery. Task executor para acoes. Transcricao de audio. Sistema de aprendizado IA. Metricas IA vs humano.

Fase 3 (Slides + Demo): Sistema completo de slides via IA com models, routes e service. Intents slide_generate e slide_update. Handlers no task_executor e message_tasks. Seed completo para demo/pitch. CI verde em todos os jobs.

Fase 4 (Completude para Pitch Deck): Export PPTX via python-pptx. Pagina de Slides no frontend com listagem, preview, geracao e download. Dashboard KPIs expandidos com satisfacao, economia e tokens. Boleto PDF via ReportLab com endpoint de download. Envio de documentos via WhatsApp. Notificacoes proativas (frequencia, notas, boleto) via Celery Beat. Onboarding de alunos via WhatsApp integrado ao fluxo de mensagens. Settings funcional com API e frontend conectado. Relatorios PDF e Excel. Webhooks outbound funcionais com HMAC-SHA256.

## Proximos Passos

Os proximos passos incluem: testar envio WhatsApp apos resolucao do bloqueio de spam, configurar servidor de producao e realizar primeiro deploy, preparar demonstracao end-to-end com dados do seed_demo para pitch deck, adicionar preview visual dos slides estilo PowerPoint no frontend, criar templates HSM na Meta para notificacoes proativas, implementar envio automatico de relatorios semanais via Celery Beat, e criptografar tokens do tenant em repouso usando Fernet.

## Comandos Principais

Para subir todos os servicos: make up. Para rodar migracoes: make migrate. Para seed basico: make seed. Para seed completo de demo: make seed-demo. Para rodar testes: make test. Para verificar lint: make lint. Para formatar codigo: make format. Para ver logs: make logs. Para gerar o PDF deste documento: docker compose exec api python scripts/generate_project_pdf.py.
