# IGS — Guia de Instalação para Administrador

> Versão: 2026-05  
> Este guia cobre a instalação manual em Oracle Cloud Free Tier (Ubuntu 22.04) com Caddy + Docker Compose.

---

## Pré-requisitos

| Item | Requisito |
|------|-----------|
| Servidor | Ubuntu 22.04 LTS, mínimo 1 GB RAM, 50 GB disco |
| Domínio | Subdomínio apontando para o IP (ex.: `igs-cliente.duckdns.org`) |
| WhatsApp | Conta Meta Business + App com Cloud API habilitada |
| IA | Chave Groq API (gratuita em console.groq.com) **ou** Anthropic |
| Email (opcional) | Conta Resend (resend.com) para envio de emails transacionais |

---

## Instalação rápida (script automático)

```bash
curl -fsSL https://raw.githubusercontent.com/seu-repo/igs/main/scripts/install.sh | bash
```

O script irá:
1. Instalar Docker e Docker Compose
2. Clonar o repositório
3. Fazer perguntas interativas (domínio, email, chaves)
4. Gerar `.env` com segredos aleatórios
5. Subir os containers
6. Rodar as migrações
7. Criar o tenant inicial
8. Configurar backup diário

---

## Instalação manual passo a passo

### 1. Instalar Docker

```bash
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER
# Reconecte a sessão SSH
```

### 2. Clonar o repositório

```bash
sudo git clone https://github.com/seu-repo/igs.git /opt/igs
sudo chown -R $USER:$USER /opt/igs
cd /opt/igs
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
nano .env
```

Campos obrigatórios no `.env`:

```env
# Domínio (usado pelo Caddy para SSL automático)
DOMAIN=igs-cliente.duckdns.org

# Banco de dados (altere as senhas)
POSTGRES_DB=igs_db
POSTGRES_USER=igs_user
POSTGRES_PASSWORD=SuaSenhaSegura123!

# JWT (gere com: openssl rand -hex 32)
JWT_SECRET_KEY=<gere-uma-chave-aleatoria>

# Encryption key (gere com: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=<chave-fernet-base64>

# IA (use groq por padrão — gratuito)
AI_PROVIDER=groq
GROQ_API_KEY=gsk_...

# WhatsApp (obtenha no Meta for Developers)
WHATSAPP_APP_SECRET=...
WHATSAPP_VERIFY_TOKEN=meu-token-verificacao

# Email (opcional — para reset de senha e relatórios)
RESEND_API_KEY=re_...
SMTP_FROM_EMAIL=noreply@suainstituicao.edu.br

# Frontend URL (usado nos links de email)
FRONTEND_URL=https://igs-cliente.duckdns.org
```

### 4. Configurar o Caddyfile

O arquivo `Caddyfile` na raiz já está pré-configurado. Apenas confirme que `DOMAIN` está correto no `.env`.

### 5. Subir os serviços

```bash
docker compose -f docker-compose.prod-light.yml up -d
```

Aguarde ~2 minutos para o PostgreSQL e Redis inicializarem.

### 6. Rodar as migrações

```bash
docker compose -f docker-compose.prod-light.yml exec api alembic upgrade head
```

### 7. Popular o banco com dados iniciais

```bash
docker compose -f docker-compose.prod-light.yml exec api python scripts/seed_db.py
```

Isso cria:
- Super admin: `admin@igs.com` / `Admin@123456` (troque a senha imediatamente!)
- Configurações padrão de planos e features

### 8. Criar o tenant da instituição

```bash
docker compose -f docker-compose.prod-light.yml exec api python scripts/create_tenant.py \
  --name "Faculdade Exemplo" \
  --slug "faculdade-exemplo" \
  --email "gestor@faculdade.edu.br" \
  --password "Gestor@2026"
```

### 9. Verificar que tudo está funcionando

```bash
# Checar status dos containers
docker compose -f docker-compose.prod-light.yml ps

# Checar logs da API
docker compose -f docker-compose.prod-light.yml logs api --tail=50

# Teste de health check
curl https://igs-cliente.duckdns.org/api/v1/health
```

Resposta esperada: `{"status":"healthy","version":"1.0.0"}`

---

## Configurar WhatsApp

1. Acesse o [Meta for Developers](https://developers.facebook.com)
2. Crie um App → WhatsApp → configurar webhook:
   - URL: `https://igs-cliente.duckdns.org/api/v1/webhook/whatsapp`
   - Token: o valor de `WHATSAPP_VERIFY_TOKEN` no `.env`
   - Eventos: `messages`
3. No painel IGS → Configurações → WhatsApp, insira:
   - Phone Number ID
   - Access Token permanente

---

## Importar alunos e funcionários

### Via CSV

```bash
# Alunos (colunas: ra,nome,email,curso,turma,status)
docker compose -f docker-compose.prod-light.yml exec api \
  python scripts/import_students.py --tenant-slug faculdade-exemplo --file /tmp/alunos.csv

# Funcionários (colunas: matricula,nome,email,departamento,cargo,status)
docker compose -f docker-compose.prod-light.yml exec api \
  python scripts/import_employees.py --tenant-slug faculdade-exemplo --file /tmp/funcionarios.csv
```

### Via integração SQL (sistemas acadêmicos)

Configure no painel: **Configurações → Integrações → Novo → Sistema Acadêmico SQL**

Preencha host, porta, usuário, senha e banco. O IGS sincroniza automaticamente a cada hora.

---

## Atualizar o sistema

```bash
cd /opt/igs
git pull
docker compose -f docker-compose.prod-light.yml build api celery-worker
docker compose -f docker-compose.prod-light.yml up -d
docker compose -f docker-compose.prod-light.yml exec api alembic upgrade head
```

---

## Backup manual

```bash
docker compose -f docker-compose.prod-light.yml exec postgres \
  pg_dump -U igs_user igs_db | gzip > backup-$(date +%Y%m%d).sql.gz
```

---

## Suporte

Dúvidas ou problemas: gabriel.henrique.roveri.bueno@gmail.com
