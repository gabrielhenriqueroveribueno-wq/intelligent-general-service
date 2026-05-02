#!/usr/bin/env bash
# setup-vm.sh — Provisionamento inicial da VM Oracle Cloud (Ubuntu 22.04)
# Execute como root ou com sudo logo após criar a VM:
#
#   ssh ubuntu@137.131.151.205
#   curl -fsSL https://raw.githubusercontent.com/SEU_USUARIO/intelligent-general-service/master/scripts/setup-vm.sh | bash
#
# Ou copie e execute diretamente:
#   bash setup-vm.sh

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/SEU_USUARIO/intelligent-general-service.git}"
APP_DIR="/opt/igs"
SWAP_SIZE="2G"

echo "════════════════════════════════════════"
echo "  IGS — Setup inicial da VM"
echo "  $(date)"
echo "════════════════════════════════════════"

# ── 1. Sistema base ───────────────────────────────────────────────────────────
echo ""
echo "▶ Atualizando sistema..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq git curl wget unzip htop

# ── 2. Swap (crítico para 1GB RAM) ───────────────────────────────────────────
echo ""
echo "▶ Configurando swap de $SWAP_SIZE..."
if ! swapon --show | grep -q '/swapfile'; then
  fallocate -l "$SWAP_SIZE" /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo 'vm.swappiness=10' >> /etc/sysctl.conf
  sysctl -p -q
  echo "  Swap criado: $(swapon --show)"
else
  echo "  Swap já existe, pulando."
fi

# ── 3. Docker ─────────────────────────────────────────────────────────────────
echo ""
echo "▶ Instalando Docker..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker ubuntu 2>/dev/null || true
  systemctl enable docker
  systemctl start docker
  echo "  Docker $(docker --version) instalado."
else
  echo "  Docker já instalado: $(docker --version)"
fi

# ── 4. Firewall (Oracle Linux requer iptables além do Security Group) ─────────
echo ""
echo "▶ Configurando firewall..."
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 22 -j ACCEPT 2>/dev/null || true
# Persiste as regras
if command -v netfilter-persistent &> /dev/null; then
  netfilter-persistent save 2>/dev/null || true
elif command -v iptables-save &> /dev/null; then
  iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
fi
echo "  Portas 80, 443, 22 abertas."

# ── 5. Clonar repositório ─────────────────────────────────────────────────────
echo ""
echo "▶ Clonando repositório em $APP_DIR..."
if [ -d "$APP_DIR" ]; then
  echo "  Diretório já existe, atualizando..."
  cd "$APP_DIR"
  git fetch origin master
  git reset --hard origin/master
else
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi
echo "  Código em: $APP_DIR ($(git rev-parse --short HEAD))"

# ── 6. Configurar .env ────────────────────────────────────────────────────────
echo ""
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.prod.example" "$APP_DIR/.env"
  echo "▶ Arquivo .env criado a partir de .env.prod.example"
  echo ""
  echo "  ┌─────────────────────────────────────────────────────────────┐"
  echo "  │  ATENÇÃO: Edite $APP_DIR/.env antes de continuar!           │"
  echo "  │  Variáveis obrigatórias:                                     │"
  echo "  │    DOMAIN=          (seu domínio, ex: api.seusite.com.br)   │"
  echo "  │    ANTHROPIC_API_KEY=                                        │"
  echo "  │    WHATSAPP_APP_SECRET=                                      │"
  echo "  │    WHATSAPP_VERIFY_TOKEN=                                    │"
  echo "  │    JWT_SECRET_KEY=  (gere: openssl rand -hex 32)            │"
  echo "  │    ENCRYPTION_KEY=  (gere: python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())') │"
  echo "  │    POSTGRES_PASSWORD=                                        │"
  echo "  └─────────────────────────────────────────────────────────────┘"
  echo ""
  echo "  Após editar, execute:"
  echo "    cd $APP_DIR && bash scripts/first-start.sh"
else
  echo "▶ .env já existe, pulando."
fi

echo ""
echo "════════════════════════════════════════"
echo "  Setup concluído!"
echo "  Próximo passo: edite /opt/igs/.env e"
echo "  execute: cd /opt/igs && bash scripts/first-start.sh"
echo "════════════════════════════════════════"
