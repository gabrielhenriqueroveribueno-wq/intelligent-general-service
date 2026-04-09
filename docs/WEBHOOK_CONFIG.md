# Configuração do Webhook WhatsApp (Meta)

## URL atual (ngrok - temporária)

```
https://nondeafeningly-waugh-dayle.ngrok-free.dev/api/v1/webhook/whatsapp
```

> **Atenção:** Essa URL muda toda vez que o ngrok é reiniciado.

## Como reconfigurar o webhook na Meta

1. Acesse: https://developers.facebook.com/apps/
2. Selecione seu app
3. No menu lateral: **WhatsApp** → **Configuração** (ou **Configuration**)
4. Na seção **Webhook**, clique em **Editar**
5. Cole a nova URL do ngrok + `/api/v1/webhook/whatsapp`
6. **Verify Token:** `igs-verify-token-2026`
7. Clique em **Verificar e salvar**
8. Certifique-se que a subscription **messages** está ativa

## Como iniciar o ngrok

```bash
ngrok http 8000
```

Copie a URL `https://xxxx.ngrok-free.dev` gerada e substitua no webhook da Meta.

## Dados da conta Meta

| Campo | Valor |
|-------|-------|
| Phone Number ID | `1142668418921479` |
| Business Account ID | `2126788561496352` |
| Verify Token | `igs-verify-token-2026` |
| Número do bot | 92679-8094 |

## Token de acesso

O token temporário da Meta expira a cada ~1-2 horas.

Para gerar um **token permanente** (System User Token):
1. Acesse: https://business.facebook.com/settings/system-users
2. Crie um System User com role **Admin**
3. Gere um token com permissões: `whatsapp_business_messaging`, `whatsapp_business_management`
4. Esse token não expira

## Deploy futuro (Oracle Cloud / VPS)

Quando tiver um servidor com IP fixo:
1. Apontar domínio (ex: `api.igs.com.br`) pro IP do servidor
2. Configurar HTTPS com Let's Encrypt (Certbot)
3. Webhook final: `https://api.igs.com.br/api/v1/webhook/whatsapp`
4. Configurar uma vez na Meta e nunca mais muda
