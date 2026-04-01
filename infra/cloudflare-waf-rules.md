# Cloudflare WAF Rules — IGS Production

Plano: **Free** (3 WAF Custom Rules + 5 Page Rules disponíveis)

---

## Regra 1: Block SQL Injection + XSS on API (exceto webhook)

**Name:** `Block SQLi/XSS on API`
**When:** `(http.request.uri.path contains "/api/" and not http.request.uri.path contains "/api/v1/webhook/")`
**Expression (editavel):**

```
(http.request.uri.path contains "/api/" and not http.request.uri.path contains "/api/v1/webhook/")
and (
  http.request.uri.query contains "UNION" or
  http.request.uri.query contains "SELECT" or
  http.request.uri.query contains "<script" or
  http.request.uri.query contains "DROP " or
  http.request.uri.query contains "--" or
  http.request.uri.query contains "'" or
  http.request.body.raw contains "UNION SELECT" or
  http.request.body.raw contains "<script>"
)
```

**Action:** `Block`

**Motivo:** Bloqueia tentativas de SQL Injection e XSS em todos os endpoints da API,
EXCETO o webhook do WhatsApp (que recebe JSON da Meta com conteúdo variável de usuários
e poderia gerar falso-positivos com aspas simples em nomes).

---

## Regra 2: Rate Limit + Challenge suspeito no login

**Name:** `Rate limit login + challenge bots`
**When:**

```
(http.request.uri.path eq "/api/v1/auth/login" and http.request.method eq "POST")
```

**Action:** `Managed Challenge` (CAPTCHA interativo para bots)

**Adicionalmente, configurar Rate Limiting Rule (Security > WAF > Rate limiting):**
- Path: `/api/v1/auth/login`
- Method: POST
- Threshold: 10 requests per 1 minute per IP
- Action: Block for 10 minutes

**Motivo:** Protege contra brute-force de credenciais. O Managed Challenge
filtra bots automatizados antes mesmo do rate limit. IPs legítimos passam normalmente.

---

## Regra 3: Allow Meta webhook IPs + challenge todo o resto no webhook

**Name:** `Protect webhook — allow Meta only`
**When:**

```
(http.request.uri.path contains "/api/v1/webhook/whatsapp")
and not (
  ip.src in {185.60.216.0/22 157.240.0.0/16 31.13.24.0/21 31.13.64.0/18 66.220.144.0/20 69.63.176.0/20 69.171.224.0/19 74.119.76.0/22 102.132.96.0/20 129.134.0.0/16 147.75.208.0/20 157.240.0.0/17 163.70.128.0/17 173.252.64.0/18 179.60.192.0/22 185.89.218.0/23 204.15.20.0/22}
)
```

**Action:** `Block`

**Motivo:** O webhook da Meta DEVE aceitar POSTs apenas dos IPs oficiais do Facebook/Meta.
Esta regra bloqueia qualquer IP que não esteja na lista oficial de ranges da Meta,
impedindo spoofing de webhooks. Os IPs listados são os ASNs oficiais da Meta (AS32934).
A verificação HMAC no FastAPI é a segunda camada de defesa.

**Nota:** Atualize os IPs periodicamente consultando:
`whois -h whois.radb.net -- '-i origin AS32934' | grep ^route`

---

## Page Rules (complementares)

### Page Rule 1: Cache agressivo no frontend
- URL: `igs.yourdomain.com/assets/*`
- Settings: Cache Level = Cache Everything, Edge Cache TTL = 1 month, Browser Cache TTL = 1 year

### Page Rule 2: Sem cache na API
- URL: `igs.yourdomain.com/api/*`
- Settings: Cache Level = Bypass, SSL = Full (Strict)

### Page Rule 3: Force HTTPS
- URL: `http://igs.yourdomain.com/*`
- Settings: Always Use HTTPS

---

## Configuracoes adicionais (Security > Settings)

1. **SSL/TLS:** Full (Strict) — requer certificado valido no origin
2. **Minimum TLS:** 1.2
3. **Security Level:** Medium
4. **Bot Fight Mode:** ON
5. **Browser Integrity Check:** ON
6. **Hotlink Protection:** ON
7. **Under Attack Mode:** OFF (ativar manualmente durante DDoS)

## Headers de Seguranca (Transform Rules)

Adicionar via Rules > Transform Rules > Modify Response Header:

| Header | Value |
|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
