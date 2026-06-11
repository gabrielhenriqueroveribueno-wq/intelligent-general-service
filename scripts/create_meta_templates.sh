#!/usr/bin/env bash
# Cria os templates HSM (boleto_lembrete, frequencia_alerta, rematricula) na WABA.
# Uso (no servidor, em /opt/igs):  bash scripts/create_meta_templates.sh
# Idempotente: a Meta retorna erro de nome duplicado se já existir — seguro re-rodar.
set -euo pipefail

ENV_FILE="${ENV_FILE:-.env}"
TOKEN=$(grep '^WHATSAPP_ACCESS_TOKEN' "$ENV_FILE" | cut -d= -f2)
WABA=$(grep '^WHATSAPP_BUSINESS_ACCOUNT_ID' "$ENV_FILE" | cut -d= -f2)
API="https://graph.facebook.com/v18.0/${WABA}/message_templates"

create() {
  local payload="$1"
  curl -sS --max-time 30 -X POST "$API" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$payload"
  echo
}

# 1) boleto_lembrete — UTILITY — params: nome, vencimento, valor
create '{
  "name": "boleto_lembrete",
  "language": "pt_BR",
  "category": "UTILITY",
  "components": [
    {
      "type": "BODY",
      "text": "Olá, {{1}}! 👋 Lembrete da secretaria: seu boleto vence em {{2}}, no valor de {{3}}. Se você já realizou o pagamento, desconsidere esta mensagem. Qualquer dúvida, é só responder por aqui.",
      "example": {"body_text": [["João", "15/06/2026", "R$ 350,00"]]}
    }
  ]
}'

# 2) frequencia_alerta — UTILITY — params: nome, disciplina, percentual
create '{
  "name": "frequencia_alerta",
  "language": "pt_BR",
  "category": "UTILITY",
  "components": [
    {
      "type": "BODY",
      "text": "Olá, {{1}}! Notamos que sua frequência em {{2}} está em {{3}}. Lembre-se: o mínimo para aprovação é 75%. Se precisar de ajuda ou quiser ver o detalhamento, é só responder aqui.",
      "example": {"body_text": [["Maria", "Cálculo I", "68%"]]}
    }
  ]
}'

# 3) rematricula — MARKETING — params: nome, periodo
create '{
  "name": "rematricula",
  "language": "pt_BR",
  "category": "MARKETING",
  "components": [
    {
      "type": "BODY",
      "text": "Oi, {{1}}! O período de rematrícula para {{2}} já está aberto. 🎓 Quer que eu te ajude com o processo? É só me chamar por aqui.",
      "example": {"body_text": [["Lucas", "2026.2"]]}
    },
    {"type": "FOOTER", "text": "Para não receber campanhas, responda SAIR."}
  ]
}'
