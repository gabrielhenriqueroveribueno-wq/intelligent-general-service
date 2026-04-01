"""
Gera um PDF com a descricao completa do projeto IGS
para compartilhar contexto com outras IAs ou stakeholders.

Uso: python scripts/generate_project_pdf.py
Ou via Docker: docker compose exec api python scripts/generate_project_pdf.py
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

OUTPUT_PATH = "docs/IGS_Project_Overview.pdf"


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1B3A5C"),
        spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1B3A5C"),
        spaceBefore=16,
        spaceAfter=6,
    )
    h3 = ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        fontSize=12,
        textColor=colors.HexColor("#2C3E50"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "BulletCustom",
        parent=body,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=3,
    )
    code_style = ParagraphStyle(
        "Code",
        parent=styles["Code"],
        fontSize=8,
        leading=10,
        backColor=colors.HexColor("#F5F5F5"),
        leftIndent=10,
        spaceAfter=2,
    )
    small = ParagraphStyle("Small", parent=body, fontSize=8, textColor=colors.grey)

    elements = []

    # ── CAPA ──────────────────────────────────────────────────────────────
    elements.append(Spacer(1, 4 * cm))
    elements.append(Paragraph("IGS — Intelligent General Service", title_style))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(
        Paragraph(
            "Documento de Contexto Completo do Projeto",
            ParagraphStyle("Subtitle", parent=body, fontSize=14, textColor=colors.grey),
        )
    )
    elements.append(Spacer(1, 1 * cm))
    elements.append(
        Paragraph(
            "SaaS de atendimento inteligente via WhatsApp para instituicoes de ensino. "
            "Atende alunos (notas, frequencia, boletos, horarios) e funcionarios "
            "(holerite, ferias, ponto, solicitacoes RH) com respostas automaticas via IA.",
            body,
        )
    )
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(
        Paragraph(
            "Repositorio: github.com/gabrielhenriqueroveribueno-wq/intelligent-general-service",
            small,
        )
    )
    elements.append(Paragraph("Branch principal: master | Linguagem: Python 3.12 + React 18", small))
    elements.append(Paragraph("Data do documento: Abril 2026", small))
    elements.append(PageBreak())

    # ── 1. VISAO GERAL ───────────────────────────────────────────────────
    elements.append(Paragraph("1. Visao Geral", h2))
    elements.append(
        Paragraph(
            "O IGS (Intelligent General Service) e um SaaS multi-tenant de atendimento "
            "inteligente via WhatsApp, projetado para instituicoes de ensino. O sistema "
            "recebe mensagens de alunos e funcionarios pelo WhatsApp, classifica a intencao "
            "da mensagem usando IA, busca dados reais no banco de dados e gera respostas "
            "contextualizadas automaticamente. O projeto utiliza um padrao RAG (Retrieval-Augmented "
            "Generation) onde a IA nunca inventa dados — ela apenas formata informacoes reais "
            "consultadas no banco.",
            body,
        )
    )
    elements.append(
        Paragraph(
            "Alem do atendimento automatico, o sistema oferece: painel administrativo completo "
            "em React, sistema de tickets com SLA, base de conhecimento, geracao de slides via IA "
            "para professores, exportacao de relatorios em CSV/PDF/Excel, notificacoes proativas "
            "(lembretes de boleto, alertas de frequencia, notas), onboarding de alunos via WhatsApp, "
            "metricas de desempenho IA vs humano, webhooks outbound, e monitoramento completo "
            "via Prometheus + Grafana + Loki.",
            body,
        )
    )

    # ── 2. ARQUITETURA ───────────────────────────────────────────────────
    elements.append(Paragraph("2. Arquitetura", h2))
    elements.append(
        Paragraph(
            "O fluxo principal e: Usuario WhatsApp envia mensagem para a Meta Cloud API, "
            "que faz POST no webhook do FastAPI. O FastAPI valida a assinatura HMAC, persiste "
            "a mensagem no PostgreSQL e enfileira uma tarefa no Celery via Redis. O worker Celery "
            "processa a mensagem: identifica o contato, classifica a intencao via IA (~50 tokens), "
            "busca dados relevantes no banco, gera a resposta via IA com contexto real, e envia "
            "a resposta de volta pelo WhatsApp Cloud API. Todo o processamento e assincrono para "
            "que o webhook retorne 200 rapidamente (requisito da Meta).",
            body,
        )
    )

    stack_data = [
        ["Camada", "Tecnologia"],
        ["Backend", "FastAPI (Python 3.12), SQLAlchemy 2.0 async, Alembic"],
        ["Database", "PostgreSQL 16 (asyncpg)"],
        ["Cache/Queue", "Redis 7 + Celery"],
        ["Frontend", "React 18 + TypeScript + TailwindCSS + Vite"],
        ["WhatsApp", "Meta Business Cloud API"],
        ["IA", "Multi-provider: Groq (ativo), Gemini, Anthropic"],
        ["Monitoring", "Prometheus + Grafana + Loki + Promtail"],
        ["Infra", "Docker + Docker Compose (12 containers)"],
        ["Auth", "JWT (access 15min + refresh 7d)"],
        ["Proxy", "Nginx"],
    ]
    t = Table(stack_data, colWidths=[3.5 * cm, 13 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B3A5C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(
        Paragraph(
            "O provider de IA ativo e o Groq (llama-3.3-70b-versatile), configuravel via "
            "variavel de ambiente AI_PROVIDER. O sistema suporta troca transparente entre "
            "Groq, Google Gemini e Anthropic Claude atraves do ai_client.py unificado.",
            body,
        )
    )

    # ── 3. MULTI-TENANCY ─────────────────────────────────────────────────
    elements.append(Paragraph("3. Multi-tenancy", h2))
    elements.append(
        Paragraph(
            "O sistema usa estrategia de banco compartilhado com coluna tenant_id em todas as "
            "tabelas escopadas. O isolamento e garantido a nivel ORM pelo TenantMixin e pelo "
            "JWT que carrega o tenant_id do usuario autenticado. Cada tenant pode ter suas "
            "proprias chaves de API (WhatsApp, Claude), configuracoes de bot, horarios de "
            "funcionamento e SLA customizados. Os roles disponiveis sao: super_admin, admin, "
            "manager, agent e teacher.",
            body,
        )
    )

    # ── 4. MODELOS DE DADOS ──────────────────────────────────────────────
    elements.append(Paragraph("4. Modelos de Dados (19 tabelas)", h2))
    models_text = [
        ("Tenant/Auth", "Tenant, TenantSettings, User (5 roles)"),
        ("Academico", "Student, Grade, AttendanceRecord, ClassSchedule"),
        ("RH", "Employee, Payslip, VacationBalance, TimeRecord, HRRequest"),
        ("Financeiro", "Boleto"),
        ("Atendimento", "Contact, Conversation, Message, Ticket, TicketComment"),
        ("Conhecimento", "KBCategory, KBArticle"),
        ("Slides IA", "SlideTemplate, SlidePresentation, SlideGenerationLog"),
        ("Notificacoes", "MessageTemplate, ScheduledNotification"),
        ("Satisfacao", "SatisfactionSurvey, OnboardingSession"),
        ("Operacional", "ServiceRequest, ResponseTimeMetric, AuditLog, FailedTask, SLAConfig"),
        ("Aprendizado", "TicketResolution"),
        ("Webhooks", "WebhookEndpoint, WebhookDelivery"),
    ]
    for group, tables in models_text:
        elements.append(Paragraph(f"<b>{group}:</b> {tables}", bullet))

    # ── 5. CLASSIFICACAO DE INTENTS ──────────────────────────────────────
    elements.append(Paragraph("5. Sistema de Classificacao de Intents (28 intents)", h2))
    elements.append(
        Paragraph(
            "O sistema usa um classificador de intents em duas etapas. Primeiro, uma chamada "
            "barata a IA (~50 tokens) classifica a mensagem do usuario em um dos 28 intents. "
            "Depois, com base no intent, o sistema busca os dados relevantes no banco e faz uma "
            "segunda chamada a IA para gerar a resposta formatada com os dados reais.",
            body,
        )
    )
    elements.append(
        Paragraph(
            "<b>Alunos (17):</b> grade_query, attendance_query, schedule_query, boleto_query, "
            "enrollment_query, generate_boleto, enrollment_request, document_request, "
            "class_enrollment, grade_appeal, transfer_request, scholarship_query, "
            "internship_query, event_registration, library_query, financial_negotiation, "
            "certificate_request",
            bullet,
        )
    )
    elements.append(
        Paragraph(
            "<b>Funcionarios (4):</b> payslip_query, vacation_query, time_record_query, hr_request",
            bullet,
        )
    )
    elements.append(
        Paragraph("<b>Professores (2):</b> slide_generate, slide_update", bullet)
    )
    elements.append(
        Paragraph(
            "<b>Geral (5):</b> faq, greeting, verification, human_handoff, unknown",
            bullet,
        )
    )

    # ── 6. FLUXO COMPLETO DE MENSAGEM ────────────────────────────────────
    elements.append(Paragraph("6. Fluxo Completo de Processamento de Mensagem", h2))
    flow_steps = [
        "1. Meta Cloud API recebe mensagem do usuario e envia POST para /api/v1/webhook/whatsapp",
        "2. FastAPI valida assinatura HMAC-SHA256, identifica tenant, persiste mensagem no banco",
        "3. Tarefa Celery 'process_incoming_message' e enfileirada no Redis",
        "4. Worker carrega mensagem, conversa, contato e configuracoes do tenant",
        "5. Se mensagem de audio: transcreve via transcription_service",
        "6. Se contato nao verificado e pede inscricao: entra no fluxo de onboarding step-by-step",
        "7. Se contato nao verificado (outros casos): envia mensagem pedindo RA ou matricula",
        "8. Classifica intent via IA (~50 tokens) — retorna intent + entities extraidas",
        "9. Se intent=human_handoff: cria ticket com SLA e transfere para agente humano",
        "10. Busca dados conforme intent: notas, boletos, holerites, ferias, horarios, etc.",
        "11. Se intent de acao: task_executor executa (gerar boleto, solicitar documento, gerar slides)",
        "12. Busca artigos relevantes na base de conhecimento (KB) via ILIKE full-text",
        "13. Busca resolucoes similares no sistema de aprendizado IA",
        "14. Gera resposta via ai_service com contexto RAG (dados reais + KB + historico de conversa)",
        "15. Envia resposta via WhatsApp Cloud API",
        "16. Registra metricas: tokens usados, tempo de resposta, intent, tipo de resolucao",
        "17. Dispara webhook outbound (message.processed) para endpoints configurados",
        "18. Publica evento via Redis pub/sub para atualizar painel em tempo real via WebSocket",
    ]
    for step in flow_steps:
        elements.append(Paragraph(step, bullet))

    elements.append(PageBreak())

    # ── 7. SISTEMA DE SLIDES ─────────────────────────────────────────────
    elements.append(Paragraph("7. Sistema de Slides via IA", h2))
    elements.append(
        Paragraph(
            "Professores podem gerar apresentacoes de aula completas via IA, tanto pelo painel "
            "web quanto pelo WhatsApp. O sistema utiliza templates institucionais que definem "
            "cores, fontes, layouts e regras de estrutura. A IA gera o conteudo dos slides "
            "em formato JSON estruturado, que pode ser visualizado no painel e exportado "
            "como arquivo .pptx (PowerPoint) usando a biblioteca python-pptx.",
            body,
        )
    )
    elements.append(
        Paragraph(
            "Endpoints: POST /slides/generate (nova apresentacao), PATCH /slides/presentations/{id} "
            "(atualizar com novo prompt), GET /slides/presentations/{id}/download (baixar .pptx), "
            "GET /slides/presentations (listar), GET /slides/templates (listar templates). "
            "Via WhatsApp: o professor envia uma mensagem pedindo slides e o intent slide_generate "
            "ou slide_update e classificado, gerando a apresentacao automaticamente.",
            body,
        )
    )

    # ── 8. SERVICOS BACKEND ──────────────────────────────────────────────
    elements.append(Paragraph("8. Servicos do Backend (23 servicos)", h2))
    services = [
        ("ai_client.py", "Cliente IA unificado — abstrai Groq, Gemini e Anthropic em uma interface unica"),
        ("ai_service.py", "Gera respostas RAG com dados reais, artigos KB, historico de conversa e resolucoes similares"),
        ("intent_classifier.py", "Classifica mensagens em 28 intents com extracao de entidades"),
        ("slide_service.py", "Gera e atualiza apresentacoes de slides via IA seguindo templates institucionais"),
        ("pptx_service.py", "Converte JSON de slides para arquivo .pptx com cores, fontes e layouts do template"),
        ("boleto_pdf_service.py", "Gera PDF de boleto com dados do aluno usando ReportLab"),
        ("task_executor.py", "Despacha e executa acoes automatizadas (boleto, matricula, documentos, slides)"),
        ("student_service.py", "CRUD e consultas de alunos, notas, frequencia, boletos, horarios"),
        ("employee_service.py", "CRUD e consultas de funcionarios, holerites, ferias, ponto, RH"),
        ("ticket_service.py", "CRUD de tickets com protocolos, SLA automatico e webhook outbound"),
        ("knowledge_service.py", "Busca de artigos na base de conhecimento via ILIKE"),
        ("whatsapp_service.py", "Envio de mensagens texto, listas interativas, templates e documentos via Meta API"),
        ("student_onboarding.py", "Autocadastro de alunos via WhatsApp em 6 etapas (nome, CPF, email, curso, confirmacao)"),
        ("report_service.py", "Relatorios de conversas/tickets, dashboard KPIs, export CSV/PDF/Excel"),
        ("learning_service.py", "Sistema de aprendizado — busca resolucoes similares para melhorar respostas futuras"),
        ("webhook_delivery_service.py", "Despacha eventos para endpoints externos com assinatura HMAC-SHA256"),
        ("metrics_service.py", "Registra metricas de tempo de resposta por conversa/mensagem"),
        ("sla_service.py", "Verificacao periodica de violacoes de SLA em tickets abertos"),
        ("ws_manager.py", "Gerenciamento de WebSocket via Redis pub/sub para atualizacoes em tempo real"),
        ("transcription_service.py", "Transcricao de mensagens de audio recebidas via WhatsApp"),
        ("media_service.py", "Download de midias (audio, imagens) do WhatsApp para processamento"),
        ("auth_service.py", "Geracao e validacao de tokens JWT (access + refresh)"),
    ]
    for name, desc in services:
        elements.append(Paragraph(f"<b>{name}</b> — {desc}", bullet))

    # ── 9. API ROUTES ────────────────────────────────────────────────────
    elements.append(Paragraph("9. API REST (20 modulos de rotas)", h2))
    routes = [
        "auth.py — POST /login, /refresh, /register; GET /me",
        "students.py — CRUD alunos, notas, frequencia, boletos (inc. PDF), horarios",
        "employees.py — CRUD funcionarios, holerites, ferias, ponto, solicitacoes RH",
        "conversations.py — Listar, detalhar, atribuir agente, fechar conversas",
        "tickets.py — CRUD tickets, comentarios, atribuicao, resolucao",
        "slides.py — Templates CRUD, gerar/atualizar/download apresentacoes",
        "knowledge_base.py — Categorias e artigos CRUD",
        "webhook.py — Webhook WhatsApp (verify challenge + incoming messages)",
        "dashboard.py — Metricas overview com KPIs expandidos",
        "reports.py — Export CSV, PDF e Excel de conversas e tickets",
        "users.py — Gestao de usuarios do painel",
        "tenants.py — Gestao de tenants + GET/PUT settings",
        "templates.py — Templates de mensagem WhatsApp",
        "webhooks_config.py — CRUD de endpoints webhook outbound",
        "metrics.py — Metricas da aplicacao",
        "health.py — Health check",
        "admin.py — Operacoes administrativas",
        "ws.py — WebSocket real-time para painel",
    ]
    for r in routes:
        elements.append(Paragraph(r, bullet))

    elements.append(PageBreak())

    # ── 10. FRONTEND ─────────────────────────────────────────────────────
    elements.append(Paragraph("10. Frontend React (16 paginas)", h2))
    elements.append(
        Paragraph(
            "O painel administrativo e construido com React 18, TypeScript, TailwindCSS e Vite. "
            "Utiliza axios com interceptors para autenticacao JWT automatica (access + refresh). "
            "Possui WebSocket via hook useNotifications para receber atualizacoes em tempo real "
            "quando mensagens sao processadas. Layout responsivo com sidebar colapsavel no mobile.",
            body,
        )
    )
    pages = [
        "Dashboard — KPIs: conversas hoje/semana/mes, taxa de resolucao automatica, tempo medio, satisfacao, economia",
        "Conversas — Listagem com filtros, detalhamento com historico de mensagens em tempo real",
        "Tickets — Listagem com filtros de status/prioridade, comentarios, atribuicao",
        "Alunos — Listagem, detalhe com notas/frequencia/boletos, download PDF de boleto",
        "Funcionarios — Listagem, detalhe com holerites/ferias/ponto",
        "Slides IA — Listagem de apresentacoes, geracao via IA, preview de slides, download PPTX",
        "Base de Conhecimento — Categorias e artigos CRUD",
        "Relatorios — Export CSV/PDF/Excel de conversas e tickets com filtro de periodo",
        "Metricas IA vs Humano — Comparacao de desempenho entre atendimento automatico e humano",
        "Aprendizado IA — Insights sobre resolucoes e padroes aprendidos pelo sistema",
        "Usuarios — Gestao de usuarios do painel com roles",
        "Configuracoes — Bot name, horarios, mensagens, chaves de integracao (WhatsApp, Claude)",
    ]
    for p in pages:
        elements.append(Paragraph(p, bullet))

    # ── 11. CELERY TASKS ─────────────────────────────────────────────────
    elements.append(Paragraph("11. Tarefas Assincronas (Celery)", h2))
    elements.append(
        Paragraph(
            "O Celery e usado para processamento assincrono de mensagens WhatsApp (que podem "
            "levar 2-5 segundos por conta das chamadas de IA), notificacoes agendadas, "
            "verificacao de SLA, entrega de webhooks e backups. O Celery Beat agenda tarefas "
            "periodicas:",
            body,
        )
    )
    tasks = [
        "process_incoming_message — Processamento principal de mensagens (com retry 3x)",
        "check_sla_task — Verifica violacoes de SLA a cada 5 minutos",
        "send_boleto_reminders_task — Lembrete de boletos vencendo em 3 dias (diario, 9h)",
        "send_attendance_alerts_task — Alerta de frequencia baixa (diario, 10h)",
        "send_grade_notifications_task — Notificacao de novas notas (a cada 6h)",
        "deliver_webhook_task — Entrega de eventos webhook com HMAC-SHA256",
        "backup_database_task — Backup semanal do banco (segunda, 3h)",
        "save_failed_task_async — Dead Letter Queue para tarefas falhas",
    ]
    for t in tasks:
        elements.append(Paragraph(t, bullet))

    # ── 12. NOTIFICACOES PROATIVAS ───────────────────────────────────────
    elements.append(Paragraph("12. Notificacoes Proativas", h2))
    elements.append(
        Paragraph(
            "O sistema envia notificacoes proativas via WhatsApp para alunos e funcionarios: "
            "(1) Lembretes de boleto — 3 dias antes do vencimento, usando template HSM aprovado "
            "na Meta, com nome do aluno, data e valor. "
            "(2) Alertas de frequencia — para alunos com mais de 25% de faltas em alguma disciplina. "
            "(3) Notificacoes de notas — quando novas notas sao lancadas nas ultimas 24 horas. "
            "Todas as notificacoes sao agendadas via Celery Beat e executam de forma batch "
            "consultando o banco de dados.",
            body,
        )
    )

    # ── 13. ONBOARDING ───────────────────────────────────────────────────
    elements.append(Paragraph("13. Onboarding de Alunos via WhatsApp", h2))
    elements.append(
        Paragraph(
            "Contatos nao verificados que enviam mensagens contendo palavras como 'inscricao', "
            "'cadastro', 'novo aluno' ou 'quero me matricular' entram em um fluxo de onboarding "
            "step-by-step: (1) Boas-vindas e coleta de nome, (2) CPF com validacao, "
            "(3) E-mail, (4) Curso desejado, (5) Confirmacao dos dados, (6) Criacao do "
            "registro de aluno com RA gerado automaticamente. O fluxo e gerenciado pela "
            "tabela OnboardingSession que persiste o estado entre mensagens.",
            body,
        )
    )

    # ── 14. WEBHOOKS OUTBOUND ────────────────────────────────────────────
    elements.append(Paragraph("14. Webhooks Outbound", h2))
    elements.append(
        Paragraph(
            "O sistema dispara eventos webhook para endpoints externos configurados por tenant. "
            "Atualmente dois eventos sao emitidos: 'ticket.created' (quando um ticket e aberto) "
            "e 'message.processed' (quando uma mensagem e processada). A entrega e assincrona "
            "via Celery, com assinatura HMAC-SHA256 no header X-IGS-Signature para validacao "
            "pelo receptor. Os endpoints e entregas sao gerenciados via API CRUD completa.",
            body,
        )
    )

    elements.append(PageBreak())

    # ── 15. MONITORAMENTO ────────────────────────────────────────────────
    elements.append(Paragraph("15. Monitoramento e Observabilidade", h2))
    elements.append(
        Paragraph(
            "O stack de monitoramento inclui Prometheus (metricas), Grafana (dashboards), "
            "Loki (agregacao de logs) e Promtail (coleta de logs dos containers). O FastAPI "
            "expoe metricas automaticas via prometheus-fastapi-instrumentator. Metricas "
            "customizadas incluem: tokens de IA consumidos por tenant, mensagens processadas "
            "por intent, tempo de resposta por tenant, e contadores de resolucao automatica "
            "vs humana.",
            body,
        )
    )

    # ── 16. DADOS DE DEMO ────────────────────────────────────────────────
    elements.append(Paragraph("16. Dados de Demonstracao (seed_demo.py)", h2))
    elements.append(
        Paragraph(
            "O script seed_demo.py popula o banco com dados realistas para demonstracao e pitch deck: "
            "1 tenant (Faculdade Anchieta), 7 usuarios (admin, agentes, professores), "
            "8 alunos com notas/frequencia/boletos/horarios completos, 5 funcionarios com "
            "holerites/ferias/ponto/solicitacoes, 14 contatos WhatsApp, 6 conversas com "
            "mensagens realistas, 5 tickets em diferentes status, 3 apresentacoes de slides, "
            "14 artigos na base de conhecimento, pesquisas de satisfacao (media 4.5/5), "
            "metricas de resposta e logs de auditoria. Executar: make seed-demo",
            body,
        )
    )

    # ── 17. CI/CD ────────────────────────────────────────────────────────
    elements.append(Paragraph("17. CI/CD", h2))
    elements.append(
        Paragraph(
            "O CI roda via GitHub Actions com 3 jobs paralelos em push para master: "
            "(1) Backend Lint — ruff check + ruff format --check. "
            "(2) Backend Tests — PostgreSQL 16 + Redis 7, pytest com asyncio. "
            "(3) Frontend Build — npm ci, tsc --noEmit, npm run build. "
            "Deploy via tag v* com SSH para servidor, docker compose pull e rolling restart. "
            "Lint config: ruff com line-length=100, py312, select E/F/I/N/W.",
            body,
        )
    )

    # ── 18. HISTORICO ────────────────────────────────────────────────────
    elements.append(Paragraph("18. Historico de Evolucao", h2))
    phases = [
        (
            "Fase 1 — Estrutura Base",
            "Docker (12 containers), PostgreSQL, Redis, Celery. Models com multi-tenancy. "
            "Auth JWT com RBAC. API REST completa. Frontend React com 15 paginas. "
            "Webhook WhatsApp com HMAC. CI/CD com GitHub Actions.",
        ),
        (
            "Fase 2 — IA e Automacao",
            "Cliente IA unificado (Groq/Gemini/Anthropic). Classificador de 26 intents. "
            "Servico RAG com dados reais + KB. Processamento assincrono Celery. "
            "Task executor para acoes. Transcricao de audio. Sistema de aprendizado IA. "
            "Metricas IA vs humano.",
        ),
        (
            "Fase 3 — Slides + Demo",
            "Sistema completo de slides via IA (models, routes, service). "
            "Intents slide_generate e slide_update. Handlers no task_executor e message_tasks. "
            "Seed completo para demo/pitch. CI verde.",
        ),
        (
            "Fase 4 — Completude para Pitch Deck",
            "Export PPTX (python-pptx). Pagina de Slides no frontend. Dashboard KPIs expandidos "
            "(satisfacao, economia, tokens). Boleto PDF (ReportLab). Envio de documentos WhatsApp. "
            "Notificacoes proativas (frequencia, notas, boleto). Onboarding via WhatsApp. "
            "Settings funcional com API. Relatorios PDF/Excel. Webhooks outbound funcionais.",
        ),
    ]
    for phase_title, phase_desc in phases:
        elements.append(Paragraph(f"<b>{phase_title}:</b> {phase_desc}", bullet))

    # ── 19. PROXIMOS PASSOS ──────────────────────────────────────────────
    elements.append(Paragraph("19. Proximos Passos", h2))
    next_steps = [
        "Testar envio WhatsApp apos resolucao do bloqueio de spam",
        "Configurar servidor de producao e realizar primeiro deploy",
        "Preparar demonstracao end-to-end com dados do seed_demo para pitch deck",
        "Adicionar preview visual dos slides estilo PowerPoint no frontend",
        "Criar templates HSM na Meta para notificacoes proativas",
        "Implementar envio automatico de relatorios semanais via Celery Beat",
        "Criptografar tokens do tenant em repouso usando Fernet",
    ]
    for s in next_steps:
        elements.append(Paragraph(s, bullet))

    # ── FOOTER ───────────────────────────────────────────────────────────
    elements.append(Spacer(1, 2 * cm))
    elements.append(
        Paragraph(
            "Documento gerado automaticamente pelo sistema IGS. "
            "Para informacoes detalhadas, consulte docs/CONTEXT.md e CLAUDE.md no repositorio.",
            small,
        )
    )

    doc.build(elements)
    print(f"PDF gerado com sucesso: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
