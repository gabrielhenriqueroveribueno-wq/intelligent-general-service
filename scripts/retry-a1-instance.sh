#!/bin/bash
# Cria instância VM.Standard.A1.Flex no Oracle Cloud Free Tier via OCI CLI.
# Execute no OCI Cloud Shell — já vem autenticado, sem configuração extra.
#
# Uso:
#   1. Abra o Cloud Shell no console OCI (ícone >_ no canto superior direito)
#   2. Cole este script ou execute: bash <(curl -s <url-raw-deste-arquivo>)
#   3. Preencha as variáveis abaixo com seus OCIDs (consulte: Identity > Compartments)
#
# Problema: VM.Standard.A1.Flex (ARM, 2 OCPU / 12 GB) tem alta demanda no
# Free Tier e frequentemente retorna "Out of capacity". Este script tenta
# automaticamente a cada 5 minutos até conseguir.

set -euo pipefail

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
COMPARTMENT_ID="ocid1.compartment.oc1..SUBSTITUA"
SUBNET_ID="ocid1.subnet.oc1.sa-saopaulo-1.SUBSTITUA"
IMAGE_ID="ocid1.image.oc1.sa-saopaulo-1.SUBSTITUA"   # Ubuntu 22.04 Minimal aarch64
DISPLAY_NAME="igs-a1"
AVAILABILITY_DOMAIN="MyIQ:SA-SAOPAULO-1-AD-1"
OCPUS=2
MEMORY_GB=12
RETRY_INTERVAL=300   # segundos entre tentativas
# ─────────────────────────────────────────────────────────────────────────────

# Usa a chave SSH já presente no Cloud Shell (~/.ssh/id_rsa.pub gerada pelo OCI)
SSH_KEY_FILE="$HOME/.ssh/id_rsa.pub"
if [ ! -f "$SSH_KEY_FILE" ]; then
  echo "Gerando par de chaves SSH..."
  ssh-keygen -t rsa -b 4096 -f "$HOME/.ssh/id_rsa" -N ""
fi

echo "=============================================="
echo "  IGS — Retry A1.Flex Oracle Cloud Free Tier"
echo "  Shape : VM.Standard.A1.Flex"
echo "  Config: ${OCPUS} OCPU / ${MEMORY_GB} GB RAM"
echo "  Região: $AVAILABILITY_DOMAIN"
echo "  Retry : a cada ${RETRY_INTERVAL}s"
echo "=============================================="

ATTEMPT=0
while true; do
  ATTEMPT=$((ATTEMPT + 1))
  echo ""
  echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Tentativa #${ATTEMPT}..."

  RESULT=$(oci compute instance launch \
    --availability-domain "$AVAILABILITY_DOMAIN" \
    --compartment-id "$COMPARTMENT_ID" \
    --shape "VM.Standard.A1.Flex" \
    --shape-config "{\"ocpus\":${OCPUS},\"memoryInGBs\":${MEMORY_GB}}" \
    --image-id "$IMAGE_ID" \
    --subnet-id "$SUBNET_ID" \
    --display-name "$DISPLAY_NAME" \
    --assign-public-ip true \
    --ssh-authorized-keys-file "$SSH_KEY_FILE" \
    --wait-for-state RUNNING \
    --max-wait-seconds 300 \
    2>&1 || true)

  if echo "$RESULT" | grep -q '"lifecycle-state": "RUNNING"'; then
    echo ""
    echo "✅ Instância criada e RUNNING!"
    PUBLIC_IP=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data'].get('public-ip','N/A'))" 2>/dev/null || echo "verifique no console OCI")
    echo "   IP público: $PUBLIC_IP"
    echo "   Nome      : $DISPLAY_NAME"
    echo ""
    echo "Próximo passo: ssh ubuntu@$PUBLIC_IP"
    break
  fi

  if echo "$RESULT" | grep -qi "out of capacity\|InternalError\|LimitExceeded"; then
    echo "❌ Sem capacidade. Próxima tentativa em ${RETRY_INTERVAL}s..."
  else
    echo "⚠️  Resposta inesperada:"
    echo "$RESULT" | head -5
    echo "   Aguardando ${RETRY_INTERVAL}s antes de tentar novamente..."
  fi

  sleep "$RETRY_INTERVAL"
done
