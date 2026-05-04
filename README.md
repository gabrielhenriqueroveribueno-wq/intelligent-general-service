# IGS — Intelligent General Service

**[🌐 Site de apresentação](https://site-wine-nine-59.vercel.app)**

SaaS de atendimento inteligente via WhatsApp para instituições de ensino. A Billie (agente de IA) responde automaticamente sobre notas, boletos, frequência, holerite, férias e muito mais — usando dados reais da instituição, 24h por dia.

## Funcionalidades

- **Atendimento 24/7** via WhatsApp com IA (Claude API)
- **Multi-tenant** — cada instituição tem seus dados isolados
- **Billie** — agente com 35+ intenções cobertas
- **Handoff humano** — transferência para atendente quando necessário
- **Painel admin** — conversas, tickets, KB, relatórios, métricas
- **LGPD compliant** — anonimização automática, direito ao esquecimento
- **Rate limiting** e planos com limites configuráveis

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic |
| Banco | PostgreSQL 16 |
| Cache/Fila | Redis 7 + Celery |
| Frontend | React 18 + TypeScript + TailwindCSS + Vite |
| WhatsApp | Meta Business Cloud API |
| IA | Claude API (claude-opus-4-6) |
| Monitoramento | Prometheus + Grafana + Loki |
| Infra | Docker Compose |
| Auth | JWT (access 15min + refresh 7d) |

## Início Rápido

### Pré-requisitos

- Docker e Docker Compose
- Chave da API Anthropic (`ANTHROPIC_API_KEY`)
- App Meta Business para WhatsApp (opcional para dev)

### Setup

```bash
# Clone o repositório
git clone https://github.com/seu-org/intelligent-general-service.git
cd intelligent-general-service

# Configure o ambiente
cp .env.example .env
# Edite .env com suas chaves

# Suba todos os serviços
make up

# Rode as migrações
make migrate

# Popule o banco com dados iniciais
make seed
```

### Acessos (desenvolvimento)

| Serviço | URL | Credencial |
|---------|-----|-----------|
| API (Swagger) | http://localhost:8000/docs | — |
| Frontend | http://localhost:3000 | — |
| Grafana | http://localhost:3001 | admin / admin123 |
| Prometheus | http://localhost:9090 | — |
| Super Admin | http://localhost:3000/login | admin@igs.com / Admin@123456 |
| Admin Tenant | http://localhost:3000/login | gestor@anchieta.edu.br / Gestor@2026 |

## Comandos Úteis

```bash
make up              # Sobe todos os containers
make down            # Para todos os containers
make migrate         # Roda migrações Alembic
make seed            # Popula banco de dados
make test            # Roda suite de testes
make logs            # Ver logs de todos os serviços
make shell           # Shell no container da API
make create-tenant   # Cria novo tenant interativo
make import-students file=alunos.csv   # Importa alunos CSV
make import-employees file=funcs.csv   # Importa funcionários CSV
```

## Arquitetura

```
WhatsApp User
    │
    ▼
Meta Cloud API
    │ POST webhook
    ▼
FastAPI (webhook)  ──►  Redis (fila)  ──►  Celery Worker
    │                                           │
    ▼                                           ▼
PostgreSQL                               Claude API (IA)
    │                                           │
    └──────────────────────────────────────────►
                                        WhatsApp reply
```

### Fluxo de Mensagem

1. Usuário envia mensagem no WhatsApp
2. Meta faz POST no webhook com HMAC assinado
3. FastAPI valida assinatura e persiste a mensagem
4. Tarefa Celery é enfileirada
5. Worker identifica contato (via RA/matrícula)
6. Claude classifica intenção (~50 tokens)
7. Sistema busca dados reais no PostgreSQL
8. Claude gera resposta contextualizada
9. Resposta enviada via WhatsApp Cloud API

## Estrutura do Projeto

```
intelligent-general-service/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints REST
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── schemas/         # Schemas Pydantic
│   │   ├── services/        # Lógica de negócio
│   │   ├── tasks/           # Tarefas Celery
│   │   └── middleware/      # Rate limit, logging, métricas
│   ├── alembic/             # Migrações de banco
│   └── tests/               # Suite de testes
├── frontend/
│   └── src/
│       ├── pages/           # Páginas React
│       ├── components/      # Componentes reutilizáveis
│       ├── context/         # Auth context
│       └── api/             # Cliente axios
├── monitoring/              # Prometheus, Grafana, Loki
├── nginx/                   # Reverse proxy
├── scripts/                 # Seed, importações
├── docs/                    # Documentação
└── docker-compose.yml
```

## Variáveis de Ambiente

Veja `.env.example` para a lista completa. Variáveis críticas:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/igs
ANTHROPIC_API_KEY=sk-ant-...
WHATSAPP_APP_SECRET=...
JWT_SECRET_KEY=...          # Troque em produção!
ENCRYPTION_KEY=...          # Chave Fernet para CPF/tokens
```

## Testes

```bash
make test
# ou diretamente:
docker compose exec api pytest -v --cov=app
```

## Deploy em Produção

```bash
# Build e sobe em modo produção
docker compose -f docker-compose.prod.yml up -d

# Roda migrações
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

Veja `docs/CONTEXT.md` para decisões de arquitetura e estado atual do projeto.

## Documentação

- [Site de Apresentação](https://site-wine-nine-59.vercel.app)
- [Resumo do Projeto](docs/RESUMO_APRESENTACAO.md)
- [Manual do Administrador](docs/ADMIN_MANUAL.md)
- [Contexto do Projeto](docs/CONTEXT.md)
- [Configuração do Webhook](docs/WEBHOOK_CONFIG.md)

## Licença

Proprietário — todos os direitos reservados. Veja `LICENSE` para detalhes.
