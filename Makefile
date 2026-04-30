.PHONY: help up down build restart logs shell migrate seed seed-demo test lint format backup ssl deploy validate-restore

DEPLOY_HOST ?=
DEPLOY_PATH ?= /opt/igs

# Exibe ajuda
help:
	@echo "IGS - Intelligent General Service"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make up         - Sobe todos os serviços"
	@echo "  make down       - Para todos os serviços"
	@echo "  make build      - Reconstrói as imagens Docker"
	@echo "  make restart    - Reinicia todos os serviços"
	@echo "  make logs       - Exibe logs de todos os serviços"
	@echo "  make shell      - Abre shell no container da API"
	@echo "  make migrate    - Executa migrações do banco de dados"
	@echo "  make seed       - Popula o banco com dados iniciais"
	@echo "  make seed-demo  - Popula com dados completos para demo/pitch"
	@echo "  make test       - Executa os testes"
	@echo "  make lint       - Executa linting (ruff)"
	@echo "  make format     - Formata o código (ruff format)"
	@echo "  make backup     - Executa backup manual do banco"
	@echo "  make ssl        - Obtém certificado SSL Let's Encrypt (DOMAIN= EMAIL=)"
	@echo "  make deploy     - Deploy remoto via SSH (DEPLOY_HOST=ubuntu@ip)"
	@echo "  make validate-restore - Valida restauração do último backup"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

shell:
	docker compose exec api bash

migrate:
	docker compose exec api alembic upgrade head

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(name)"

seed:
	docker compose exec api python scripts/seed_db.py

seed-demo:
	docker compose exec api python scripts/seed_demo.py

test:
	docker compose exec api pytest app/tests/ -v

test-cov:
	docker compose exec api pytest app/tests/ -v --cov=app --cov-report=html

lint:
	docker compose exec api ruff check app/

format:
	docker compose exec api ruff format app/

create-tenant:
	docker compose exec api python scripts/create_tenant.py

import-students:
	docker compose exec api python scripts/import_students.py $(file)

import-employees:
	docker compose exec api python scripts/import_employees.py $(file)

backup:
	bash scripts/backup_db.sh

ssl:
	bash scripts/init-letsencrypt.sh $(DOMAIN) $(EMAIL)

# Produção
up-prod:
	docker compose -f docker-compose.prod.yml up -d

down-prod:
	docker compose -f docker-compose.prod.yml down

# Deploy remoto via SSH (requer DEPLOY_HOST=usuario@ip)
deploy:
	@if [ -z "$(DEPLOY_HOST)" ]; then echo "Uso: make deploy DEPLOY_HOST=ubuntu@IP"; exit 1; fi
	DEPLOY_HOST=$(DEPLOY_HOST) DEPLOY_PATH=$(DEPLOY_PATH) bash scripts/deploy.sh

# Valida restauração do último backup
validate-restore:
	bash scripts/validate_restore.sh $(file)
