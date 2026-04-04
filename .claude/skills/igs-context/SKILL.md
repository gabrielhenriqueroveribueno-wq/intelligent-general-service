# IGS — Contexto do Projeto

## Quando usar esta skill
Sempre que for trabalhar em qualquer parte do projeto IGS. Esta skill carrega o contexto arquitetural completo.

## Arquitetura Core
- Fluxo: Meta WhatsApp API → FastAPI webhook → Celery Worker → IA (RAG) → WhatsApp reply
- Multi-tenancy: shared database + `tenant_id` em todas as tabelas escopadas
- IA: Groq (llama-3.3-70b-versatile) como provider ativo via `ai_client.py` unificado
- Auth: JWT access 15min + refresh 7d, RBAC com 5 roles

## Padrão RAG (IMUTÁVEL)
A IA NUNCA inventa dados. O fluxo é SEMPRE:
1. Classificar intent (~50 tokens, chamada barata)
2. Buscar dados reais no banco baseado no intent
3. Gerar resposta formatada com os dados reais

## 28 Intents do Sistema
Alunos (17): grade_query, attendance_query, schedule_query, boleto_query, enrollment_query,
generate_boleto, enrollment_request, document_request, class_enrollment, grade_appeal,
transfer_request, scholarship_query, internship_query, event_registration, library_query,
financial_negotiation, certificate_request

Funcionários (4): payslip_query, vacation_query, time_record_query, hr_request
Professores (2): slide_generate, slide_update
Gerais (5): faq, greeting, verification, human_handoff, unknown

## 23 Serviços Backend
ai_client.py | ai_service.py | intent_classifier.py | slide_service.py | pptx_service.py |
boleto_pdf_service.py | task_executor.py | student_service.py | employee_service.py |
ticket_service.py | knowledge_service.py | whatsapp_service.py | student_onboarding.py |
report_service.py | learning_service.py | webhook_delivery_service.py | metrics_service.py |
sla_service.py | ws_manager.py | transcription_service.py | media_service.py | auth_service.py

## Regras Invioláveis
- SEMPRE usar SQLAlchemy 2.0 async (nunca sync em contexto async)
- SEMPRE validar assinatura HMAC-SHA256 antes de processar webhook
- SEMPRE escopar queries por tenant_id
- NUNCA fazer chamada síncrona à IA no handler do webhook (usar Celery)
- NUNCA modificar migrations já aplicadas (sempre criar nova migration)
- SEMPRE rodar `make lint` (ruff) antes de commitar

## Comandos Essenciais
make up | make migrate | make seed | make seed-demo | make test | make lint | make format | make logs
