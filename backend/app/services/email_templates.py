"""
Templates HTML de email — usados pelo email_service para enviar mensagens formatadas.
"""


def _base(title: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f4f7fa; margin: 0; padding: 0; }}
  .wrapper {{ max-width: 600px; margin: 32px auto; background: #fff;
              border-radius: 12px; overflow: hidden;
              box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  .header {{ background: linear-gradient(135deg, #2563eb, #4f46e5);
             padding: 28px 32px; color: #fff; }}
  .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
  .header p  {{ margin: 4px 0 0; font-size: 13px; opacity: .8; }}
  .body {{ padding: 28px 32px; color: #374151; line-height: 1.6; }}
  .body h2 {{ font-size: 17px; margin-top: 0; color: #1f2937; }}
  .btn {{ display: inline-block; background: #2563eb; color: #fff !important;
          text-decoration: none; padding: 12px 28px; border-radius: 8px;
          font-weight: 600; font-size: 14px; margin-top: 16px; }}
  .footer {{ padding: 16px 32px; background: #f9fafb; border-top: 1px solid #e5e7eb;
             font-size: 11px; color: #9ca3af; text-align: center; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
  th {{ text-align: left; font-size: 11px; font-weight: 600; color: #6b7280;
        padding: 6px 8px; background: #f3f4f6; }}
  td {{ padding: 8px; font-size: 13px; border-bottom: 1px solid #e5e7eb; }}
  .pill {{ display: inline-block; padding: 2px 10px; border-radius: 99px;
           font-size: 11px; font-weight: 600; }}
  .green {{ background: #d1fae5; color: #065f46; }}
  .red   {{ background: #fee2e2; color: #991b1b; }}
  .blue  {{ background: #dbeafe; color: #1e40af; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🤖 IGS — Intelligent General Service</h1>
    <p>{title}</p>
  </div>
  <div class="body">{content}</div>
  <div class="footer">
    Você recebe este email porque é administrador do IGS. <br>
    © 2026 IGS — Intelligent General Service
  </div>
</div>
</body>
</html>"""


def welcome(institution_name: str, admin_name: str, login_url: str = "https://igs.com.br/login") -> str:
    content = f"""
<h2>Bem-vindo(a) ao IGS, {admin_name}!</h2>
<p>Sua conta da <strong>{institution_name}</strong> foi criada com sucesso.
Você tem <strong>14 dias de trial gratuito</strong> para testar todas as funcionalidades.</p>

<h3 style="font-size:15px; margin-top:24px;">Próximos passos:</h3>
<ol style="padding-left:20px; font-size:14px;">
  <li style="margin-bottom:8px;">Acesse o painel e explore o dashboard</li>
  <li style="margin-bottom:8px;">Importe seus alunos e funcionários via CSV</li>
  <li style="margin-bottom:8px;">Configure o WhatsApp Business API (temos tutorial)</li>
  <li style="margin-bottom:8px;">Converse com a Billie pelo WhatsApp!</li>
</ol>

<a href="{login_url}" class="btn">Acessar o painel →</a>

<p style="margin-top:24px; font-size:13px; color:#6b7280;">
  Dúvidas? Responda este email ou acesse nossa documentação.
  Nossa equipe responde em até 4h em dias úteis.
</p>
"""
    return _base(f"Bem-vindo(a), {admin_name}!", content)


def trial_expiring(institution_name: str, days_left: int, upgrade_url: str = "https://igs.com.br/upgrade") -> str:
    content = f"""
<h2>Seu trial expira em {days_left} {'dia' if days_left == 1 else 'dias'}</h2>
<p>Sua conta da <strong>{institution_name}</strong> está no trial.
Faltam <strong>{days_left} {'dia' if days_left == 1 else 'dias'}</strong> para o encerramento.</p>

<p>Faça upgrade agora para continuar atendendo alunos sem interrupção:</p>
<a href="{upgrade_url}" class="btn">Fazer upgrade →</a>

<p style="margin-top:24px; font-size:13px; color:#6b7280;">
  Se você precisar de mais tempo ou tiver dúvidas sobre planos,
  basta responder este email.
</p>
"""
    return _base(f"Trial expirando — {institution_name}", content)


def password_reset(admin_name: str, reset_url: str, expires_minutes: int = 30) -> str:
    content = f"""
<h2>Redefinição de senha</h2>
<p>Olá, <strong>{admin_name}</strong>. Recebemos uma solicitação de redefinição
de senha para sua conta no IGS.</p>

<p>Clique no botão abaixo para criar uma nova senha.
O link é válido por <strong>{expires_minutes} minutos</strong>.</p>

<a href="{reset_url}" class="btn">Redefinir senha →</a>

<p style="margin-top:24px; font-size:13px; color:#6b7280;">
  Se você não solicitou a redefinição, ignore este email.
  Sua senha não será alterada.
</p>
"""
    return _base("Redefinição de senha", content)


def weekly_report(
    institution_name: str,
    week_label: str,
    stats: dict,
) -> str:
    resolved = stats.get("resolved", 0)
    total = stats.get("total_conversations", 0)
    ai_pct = round(resolved / total * 100) if total else 0
    satisfaction = stats.get("avg_satisfaction", 0)
    top_intents = stats.get("top_intents", [])

    intents_rows = "".join(
        f"<tr><td>{i['intent']}</td><td>{i['count']}</td></tr>"
        for i in top_intents[:5]
    )

    content = f"""
<h2>Relatório semanal — {week_label}</h2>
<p>Resumo de atendimentos da <strong>{institution_name}</strong>:</p>

<table>
  <tr><th>Métrica</th><th>Valor</th></tr>
  <tr><td>Total de conversas</td><td><strong>{total}</strong></td></tr>
  <tr><td>Resolvidos pela IA</td>
      <td><span class="pill {'green' if ai_pct >= 70 else 'blue'}">{ai_pct}%</span></td></tr>
  <tr><td>Satisfação média</td>
      <td><strong>{satisfaction:.1f} / 5.0</strong></td></tr>
  <tr><td>Tickets abertos</td><td>{stats.get('open_tickets', 0)}</td></tr>
</table>

<h3 style="font-size:14px; margin-top:20px;">Top assuntos da semana:</h3>
<table>
  <tr><th>Assunto</th><th>Quantidade</th></tr>
  {intents_rows if intents_rows else '<tr><td colspan="2">Sem dados</td></tr>'}
</table>
"""
    return _base(f"Relatório semanal — {institution_name}", content)


def handoff_alert(
    institution_name: str,
    contact_name: str,
    conversation_url: str,
) -> str:
    content = f"""
<h2>Nova conversa aguardando atendimento humano</h2>
<p>O contato <strong>{contact_name}</strong> da <strong>{institution_name}</strong>
solicitou atendimento humano via WhatsApp.</p>

<a href="{conversation_url}" class="btn">Ver conversa →</a>

<p style="margin-top:16px; font-size:13px; color:#6b7280;">
  Se você já assumiu este atendimento, pode ignorar este email.
</p>
"""
    return _base(f"Handoff: {contact_name} aguarda atendimento", content)
