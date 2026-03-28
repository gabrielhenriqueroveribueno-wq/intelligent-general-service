# Instruções para Claude Code - Evolução Completa do IGS

## REGRAS IMPORTANTES
- NÃO exclua nenhum arquivo existente do projeto
- Mantenha a mesma formatação e padrões de código já usados (ruff, TypeScript strict)
- Mantenha compatibilidade com PostgreSQL (JSONB, UUID, ARRAY)
- Após cada alteração rode `ruff check --fix app/` e `ruff format app/` no diretório backend
- Faça commit e push para `master` ao final
- Mantenha todos os ForeignKeys existentes nos models
- Siga a arquitetura existente: FastAPI + Celery + Claude API + React + PostgreSQL

## CONTEXTO DO PROJETO
O IGS (Intelligent General Service) é um SaaS de atendimento inteligente via WhatsApp para a Faculdade Anchieta.
O projeto está em `D:\Projetos\intelligent-general-service`.
Leia o arquivo `CLAUDE.md` na raiz para entender a arquitetura completa.

---

## FUNCIONALIDADES A IMPLEMENTAR

### 1. SISTEMA DE APRENDIZADO DA IA COM TICKETS RESOLVIDOS

A IA precisa aprender com os tickets anteriores para sugerir soluções melhores.

**Backend - Novo model `backend/app/models/ticket_learning.py`:**
- Criar tabela `ticket_resolutions` com campos:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK tenants.id)
  - `ticket_id` (UUID, FK tickets.id)
  - `conversation_id` (UUID, FK conversations.id, nullable)
  - `problem_category` (String) — categoria do problema (matrícula, boleto, nota, etc.)
  - `problem_description` (Text) — descrição resumida do problema
  - `resolution_description` (Text) — como foi resolvido
  - `resolution_steps` (JSONB) — passos da resolução em JSON
  - `resolution_type` (String) — auto, human, escalated
  - `satisfaction_score` (Integer, 1-5) — avaliação do atendimento
  - `resolution_time_seconds` (Integer) — tempo até resolução
  - `tags` (ARRAY Text) — tags para busca
  - `ai_embedding_summary` (Text) — resumo gerado pela IA para matching
  - `times_used_as_reference` (Integer, default 0) — quantas vezes essa resolução foi usada como referência
  - `created_at`, `updated_at` (timestamps)

**Backend - Novo service `backend/app/services/learning_service.py`:**
- Função `index_resolved_ticket(db, ticket_id)`:
  - Quando um ticket é fechado com resolução, extrair a conversa completa
  - Usar Claude para gerar um resumo estruturado do problema e da solução
  - Salvar em `ticket_resolutions`
- Função `find_similar_resolutions(db, tenant_id, problem_description, limit=5)`:
  - Buscar resoluções similares usando ILIKE no problem_description, tags e ai_embedding_summary
  - Ordenar por satisfaction_score DESC e times_used_as_reference DESC
  - Retornar as melhores resoluções como contexto para a IA
- Função `get_resolution_stats(db, tenant_id)`:
  - Estatísticas: total resoluções, média de satisfação, tempo médio de resolução, categorias mais comuns

**Backend - Modificar `backend/app/services/ai_service.py`:**
- No `BOT_SYSTEM_PROMPT`, adicionar seção `RESOLUÇÕES ANTERIORES SIMILARES:`
- Antes de gerar resposta, chamar `find_similar_resolutions()` com a mensagem do usuário
- Incluir as resoluções encontradas no contexto do Claude
- A IA deve sugerir soluções baseadas nos tickets resolvidos anteriormente com melhor avaliação
- Quando não houver solução no sistema, a IA deve sugerir as melhores opções de correção baseadas nos padrões observados

**Backend - Modificar `backend/app/tasks/message_tasks.py`:**
- Após resolver um ticket automaticamente, chamar `index_resolved_ticket()`
- Ao classificar intent, buscar resoluções similares e passar como contexto

### 2. TRANSCRIÇÃO DE ÁUDIO DO WHATSAPP

**Backend - Novo service `backend/app/services/transcription_service.py`:**
- Quando receber mensagem de áudio (type="audio"):
  - Baixar o áudio via Media Service existente
  - Usar Claude API para transcrever (enviar como base64)
  - Salvar a transcrição no campo `content` da Message
  - Marcar `message_type` como "audio_transcribed"
- Criar função `transcribe_audio(audio_bytes, mime_type) -> str`

**Backend - Modificar `backend/app/tasks/message_tasks.py`:**
- No processamento de mensagens de áudio, chamar `transcribe_audio()` antes de classificar intent
- O texto transcrito deve ser usado como input para classificação e resposta
- Salvar a transcrição no banco para histórico e aprendizado

### 3. MÉTRICAS DE TEMPO DE ATENDIMENTO (HUMANO vs IA)

**Backend - Novo model `backend/app/models/metrics.py`:**
- Tabela `response_time_metrics`:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK)
  - `conversation_id` (UUID, FK)
  - `message_id` (UUID, FK)
  - `responder_type` (String) — "bot", "human", "agent"
  - `response_time_seconds` (Float) — tempo entre mensagem do usuário e resposta
  - `message_count_in_conversation` (Integer) — quantas mensagens até resolver
  - `was_resolved` (Boolean) — se o problema foi resolvido
  - `resolution_time_total_seconds` (Float) — tempo total até resolução
  - `created_at` (timestamp)

- Tabela `whatsapp_monitored_accounts`:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK)
  - `account_name` (String) — nome da conta WhatsApp monitorada
  - `phone_number` (String) — número da conta
  - `account_type` (String) — "human_agent", "ai_bot", "mixed"
  - `is_active` (Boolean)
  - `monitoring_start_date` (DateTime)
  - `notes` (Text)
  - `created_at`, `updated_at`

**Backend - Novo service `backend/app/services/metrics_service.py`:**
- `record_response_time(db, conversation_id, message_id, responder_type, response_time)` — registra métrica
- `get_comparison_report(db, tenant_id, start_date, end_date)` — retorna:
  - Tempo médio de resposta: IA vs Humano
  - Taxa de resolução: IA vs Humano
  - Satisfação média: IA vs Humano
  - Quantidade de atendimentos simultâneos
  - Custo estimado por atendimento (humano: salário/atendimentos, IA: tokens*preço)
  - Gráfico de evolução temporal
- `calculate_roi(db, tenant_id)` — calcula ROI:
  - Custo mensal estimado com atendentes humanos
  - Custo mensal estimado com IA (tokens Claude)
  - Economia mensal e percentual
  - Tempo médio economizado por atendimento

**Backend - Novo endpoint `backend/app/api/v1/metrics.py`:**
- `GET /api/v1/metrics/comparison` — relatório comparativo IA vs Humano
- `GET /api/v1/metrics/roi` — cálculo de ROI
- `GET /api/v1/metrics/monitored-accounts` — lista contas monitoradas
- `POST /api/v1/metrics/monitored-accounts` — adiciona conta para monitorar
- `GET /api/v1/metrics/dashboard` — dados para dashboard de métricas

**Registrar no router:** Adicionar o novo router de metrics em `backend/app/api/v1/router.py`

### 4. AUTOMAÇÃO COMPLETA DE TAREFAS PELO WHATSAPP (Não é robô comum)

O sistema NÃO é um robô de respostas prontas. É uma IA que executa tarefas reais.

**Backend - Modificar `backend/app/services/intent_classifier.py`:**
Adicionar novos intents ao classificador:
- `generate_boleto` — gerar boleto de pagamento
- `enrollment_request` — pedido de matrícula/rematrícula
- `document_request` — solicitar documentos (declaração, histórico, diploma)
- `class_enrollment` — inscrição em disciplinas
- `grade_appeal` — recurso de nota
- `transfer_request` — pedido de transferência
- `scholarship_query` — consulta sobre bolsas
- `internship_query` — estágio/TCC
- `event_registration` — inscrição em eventos
- `library_query` — consulta biblioteca (empréstimo, renovação, multa)
- `financial_negotiation` — negociação de débitos
- `certificate_request` — solicitar certificados

**Backend - Novo service `backend/app/services/task_executor.py`:**
- Serviço que executa ações reais no sistema baseado no intent:
  - `execute_generate_boleto(db, tenant_id, student_id, data)` — gera um boleto real
  - `execute_enrollment_request(db, tenant_id, student_id, data)` — registra pedido de matrícula
  - `execute_document_request(db, tenant_id, contact_id, document_type)` — registra solicitação de documento
  - `execute_class_enrollment(db, tenant_id, student_id, subject_data)` — inscreve em disciplina
  - Cada função retorna um dict com o resultado para a IA formatar a resposta

**Backend - Novo model `backend/app/models/service_request.py`:**
- Tabela `service_requests`:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK)
  - `contact_id` (UUID, FK)
  - `request_type` (String) — tipo da solicitação
  - `status` (String) — pending, processing, completed, rejected
  - `request_data` (JSONB) — dados do pedido
  - `result_data` (JSONB) — resultado/resposta
  - `conversation_id` (UUID, FK, nullable)
  - `processed_by` (String) — "ai" ou "human"
  - `processing_time_seconds` (Float)
  - `created_at`, `updated_at`

**Backend - Modificar `backend/app/tasks/message_tasks.py`:**
- Após classificar o intent, se for um intent de ação (generate_boleto, enrollment_request, etc.):
  - Chamar o `task_executor` para executar a ação
  - Passar o resultado para a IA formatar a resposta ao usuário
  - Registrar em `service_requests`

### 5. CADASTRO E AUTOATENDIMENTO DO ALUNO PELO WHATSAPP

**Backend - Novo service `backend/app/services/student_onboarding.py`:**
- Fluxo de autocadastro pelo WhatsApp:
  1. Aluno envia mensagem pela primeira vez
  2. Bot pergunta: "Você é aluno, funcionário ou deseja se inscrever?"
  3. Se "inscrever" → iniciar fluxo de inscrição
  4. Bot coleta dados step-by-step: nome completo, CPF, email, telefone, curso desejado
  5. Valida CPF, verifica duplicatas
  6. Cria registro preliminar em `students` com status "pending_enrollment"
  7. Gera boleto de matrícula
  8. Envia confirmação com número de protocolo

- Tabela `onboarding_sessions` para rastrear o fluxo:
  - `id`, `tenant_id`, `contact_id`, `current_step`, `collected_data` (JSONB), `status`, `created_at`

### 6. SISTEMA DE AVALIAÇÃO E SATISFAÇÃO

**Backend - Novo model: adicionar em `backend/app/models/conversation.py` ou novo arquivo:**
- Tabela `satisfaction_surveys`:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK)
  - `conversation_id` (UUID, FK)
  - `contact_id` (UUID, FK)
  - `score` (Integer, 1-5) — nota do atendimento
  - `feedback_text` (Text, nullable) — comentário opcional
  - `responder_type` (String) — quem atendeu: "bot", "human"
  - `survey_sent_at` (DateTime)
  - `responded_at` (DateTime, nullable)
  - `created_at`

**Backend - Modificar fluxo de fechamento de conversa:**
- Quando uma conversa é fechada, enviar pesquisa de satisfação via WhatsApp template
- Coletar a resposta e salvar em `satisfaction_surveys`
- Usar a nota para ranquear as resoluções no sistema de aprendizado

### 7. FRONTEND - DASHBOARD DE MÉTRICAS E ROI

**Frontend - Nova página `frontend/src/pages/MetricsDashboard.tsx`:**
- Gráfico comparativo: Tempo médio de resposta IA vs Humano (barra)
- Gráfico: Volume de atendimentos por dia (linha)
- Cards: Economia mensal, ROI, satisfação média
- Tabela: Contas WhatsApp monitoradas com tempos médios
- Gráfico pizza: Distribuição de intents/categorias de problemas
- Gráfico: Evolução da satisfação ao longo do tempo

**Frontend - Nova página `frontend/src/pages/LearningInsights.tsx`:**
- Lista de resoluções mais utilizadas como referência
- Categorias de problemas mais comuns
- Taxa de sucesso por categoria
- Resoluções com melhor avaliação

**Frontend - Atualizar Sidebar `frontend/src/components/layout/Sidebar.tsx`:**
- Adicionar link "Métricas IA vs Humano" com ícone adequado
- Adicionar link "Aprendizado IA" com ícone adequado

**Frontend - Atualizar `frontend/src/App.tsx`:**
- Adicionar rotas para as novas páginas

### 8. REGISTRAR TUDO NO SISTEMA

**Backend - Atualizar `backend/app/models/__init__.py`:**
- Importar todos os novos models

**Backend - Atualizar `backend/app/api/v1/router.py`:**
- Registrar todos os novos routers

**Backend - Atualizar `backend/alembic/env.py`:**
- Importar todos os novos models para o Alembic detectar

---

## FLUXO COMPLETO DO ATENDIMENTO INTELIGENTE (resumo)

```
1. Aluno/Funcionário envia mensagem no WhatsApp (texto ou áudio)
2. Se áudio → transcrever para texto
3. Se primeiro contato → fluxo de cadastro/verificação
4. Classificar intent da mensagem
5. Buscar resoluções similares de tickets anteriores (aprendizado)
6. Buscar dados do aluno/funcionário no banco
7. Buscar artigos da KB relevantes
8. Se intent é uma AÇÃO (gerar boleto, matrícula, etc.) → executar a ação
9. Gerar resposta com Claude usando todo o contexto (dados + KB + resoluções anteriores)
10. Enviar resposta via WhatsApp
11. Registrar métricas de tempo de resposta
12. Se conversa fechada → enviar pesquisa de satisfação
13. Se ticket resolvido → indexar resolução para aprendizado futuro
```

---

## APÓS IMPLEMENTAR

1. Rode `ruff check --fix app/` e `ruff format app/` no diretório backend
2. Verifique se os testes existentes ainda passam: `cd backend && python -m pytest app/tests/ -v`
3. Se algum teste quebrar, corrija mantendo a lógica original
4. Faça commit e push:
```bash
git add .
git commit -m "feat: sistema de aprendizado IA, transcrição de áudio, métricas IA vs Humano, automação de tarefas pelo WhatsApp"
git push origin master
```
5. Verifique o CI no GitHub Actions e corrija se necessário até passar
