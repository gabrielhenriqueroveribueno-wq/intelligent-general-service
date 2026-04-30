# Contribuindo com o IGS

## Pré-requisitos

- Python 3.12+
- Node.js 20+
- Docker e Docker Compose
- Conta Anthropic (para testes com IA)

## Configuração do Ambiente de Desenvolvimento

```bash
# 1. Fork e clone
git clone https://github.com/SEU_USUARIO/intelligent-general-service.git
cd intelligent-general-service

# 2. Crie o .env
cp .env.example .env
# Edite com suas chaves

# 3. Suba a infra (banco, redis, etc.) sem o app
docker compose up -d postgres redis

# 4. Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head

# 5. Frontend
cd ../frontend
npm install
npm run dev
```

## Workflow de Desenvolvimento

Seguimos o padrão **Conventional Commits** e **trunk-based development** (branches curtas, PRs pequenos).

### Fluxo de trabalho

```bash
# 1. Atualize main
git checkout main && git pull

# 2. Crie branch descritiva
git checkout -b feat/nome-da-feature

# 3. Faça as alterações com TDD
# Escreva o teste primeiro → implemente → refatore

# 4. Commit
git add -p   # Revise cada hunk antes de adicionar
git commit -m "feat: descrição concisa do que foi feito"

# 5. Push e abra PR
git push -u origin feat/nome-da-feature
```

### Tipos de Commit

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração sem alterar comportamento |
| `test` | Adição ou correção de testes |
| `docs` | Apenas documentação |
| `chore` | Tarefas de manutenção, deps |
| `perf` | Melhoria de performance |
| `ci` | Mudanças no pipeline CI/CD |

## Testes

Cobertura mínima: **80%**. Sempre escreva testes antes de implementar (TDD).

```bash
# Roda todos os testes
cd backend && pytest -v --cov=app

# Apenas testes unitários
pytest -m unit

# Apenas integração
pytest -m integration

# Frontend
cd frontend && npm test
```

### Estrutura de Testes

```
backend/tests/
├── conftest.py              # Fixtures: db, redis, client
├── unit/
│   ├── services/            # Testa serviços isolados
│   └── utils/               # Testa utilitários
└── integration/
    ├── api/                 # Testa endpoints HTTP
    └── tasks/               # Testa tarefas Celery
```

## Linting e Formatação

```bash
# Backend
cd backend
ruff check app/            # Linting
ruff format app/           # Formatação

# Frontend
cd frontend
npm run lint               # ESLint
npm run type-check         # TypeScript
```

O CI roda essas verificações automaticamente. PRs com erros de lint não serão mergeados.

## Adicionando um Novo Intent (Billie)

Use o comando: `/add-intent nome-do-intent`

O padrão a seguir está em `.claude/commands/add-intent.md`. Resumidamente:

1. Adicione o intent em `app/services/intent_classifier.py`
2. Adicione o handler em `app/services/task_executor.py`
3. Adicione dados de exemplo em `app/services/ai_client.py` (context builder)
4. Escreva testes em `tests/integration/tasks/test_intent_nome.py`
5. Documente na Base de Conhecimento (artigo de exemplo)

## Adicionando Migração de Banco

```bash
# Gera migração automaticamente a partir dos models
cd backend
alembic revision --autogenerate -m "descrição da mudança"

# Revise o arquivo gerado em alembic/versions/
# Então aplique
alembic upgrade head
```

Regras para migrações:

- Toda nova coluna deve ter `nullable=True` ou `default` para não quebrar deploys em produção
- Migrations devem ser reversíveis — implemente sempre o `downgrade()`
- Nunca edite uma migration que já foi aplicada em produção

## Code Review

Antes de abrir PR, verifique:

- [ ] Testes passando (`make test`)
- [ ] Sem erros de lint
- [ ] Sem erros de tipo TypeScript
- [ ] Cobertura ≥ 80% nos arquivos alterados
- [ ] Sem segredos ou credenciais no código
- [ ] Migração de banco incluída se necessário

PRs são revisados em até 2 dias úteis.

## Reportar Bugs

Abra uma issue com:

1. Versão do sistema (veja `/api/v1/health`)
2. Passos para reproduzir
3. Comportamento esperado vs. atual
4. Logs relevantes (sem PII)

## Contato

- Issues: GitHub Issues
- Segurança: security@igs.com.br (não use issues públicas para vulnerabilidades)
- Discussões: Slack interno `#igs-dev`
