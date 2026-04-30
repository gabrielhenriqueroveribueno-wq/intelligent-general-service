# IGS — Atendimento inteligente via WhatsApp para escolas

> Sua escola atende alunos no WhatsApp com IA, 24 horas por dia.
> Notas, boletos, frequência, holerite, agendamentos — respondidos em 3 segundos
> com dados reais do seu sistema.

---

## O problema

A maioria das escolas atende alunos manualmente:

- Equipe de 3-4 atendentes em horário comercial — **R$ 26.800/mês**
- Atendimento só de segunda a sexta, 8h às 18h
- Aluno espera 8 minutos em média por uma resposta simples
- Em pico (provas, matrícula) o tempo triplica
- Respostas inconsistentes entre atendentes
- Equipe esgotada respondendo perguntas repetitivas

## A solução

O **IGS** é uma plataforma SaaS que conecta WhatsApp Business + IA da Anthropic
+ seu sistema acadêmico. A "Billie" — IA personalizada da escola — atende
automaticamente as perguntas frequentes e transfere pra um humano quando
necessário.

### O que a Billie faz hoje

**Para alunos:**
- ✅ Consulta de notas e frequência
- ✅ Boletos com pagamento via PIX/cartão
- ✅ Horários de aula e biblioteca
- ✅ Agendamento de atendimento presencial
- ✅ Solicitação de documentos (histórico, declarações)

**Para funcionários:**
- ✅ Holerite e contracheque
- ✅ Solicitação e saldo de férias
- ✅ Solicitações de RH

**Para gestores:**
- ✅ Dashboard em tempo real
- ✅ Métricas IA vs humano e ROI
- ✅ Tickets com SLA
- ✅ Relatórios semanais por email

---

## Resultados em 90 dias (caso de uso real)

| Métrica | Antes | Depois |
|---|---|---|
| Custo mensal de atendimento | R$ 26.800 | **R$ 8.620** (-68%) |
| Tempo médio de resposta | 8 min | **2,4 min** |
| Conversas atendidas/mês | 1.250 | **3.842** (3.1x) |
| Resolução automática | 0% | **87,3%** |
| Satisfação dos alunos | 3,2/5 | **4,6/5** |
| Disponibilidade | 8h/dia | **24h/dia** |

**Economia anual projetada: R$ 218.000**

---

## Por que escolher o IGS?

### 🛡️ Segurança em primeiro lugar
- Dados isolados por escola (multi-tenancy)
- CPFs e tokens criptografados (Fernet)
- Verificação obrigatória (RA + senha)
- HMAC validado em todo webhook
- JWT com refresh tokens
- Compliance LGPD
- Suite de testes automatizados rodando em CI/CD

### 🧠 IA que não inventa
A Billie usa o padrão **RAG** (Retrieval-Augmented Generation): só responde
com dados que estão no seu banco. Quando não tem informação, ela diz
claramente e oferece transferir pra humano.

### ⚡ Resiliente
Se um provider de IA falha (Anthropic, Groq, Gemini), o sistema tenta o
próximo automaticamente. Se todos caem, a Billie ainda responde com
templates baseados em palavras-chave.

### 🔌 Integração simples
- Importação CSV mensal de alunos/funcionários
- Conecta no seu WhatsApp Business existente
- Integração via API com sistemas acadêmicos (plano Enterprise)
- Setup em 1 hora

---

## Planos

| | **Basic** | **Pro** | **Enterprise** |
|---|---|---|---|
| Mensalidade | R$ 497 | R$ 997 | Sob consulta |
| Alunos | até 500 | até 2.000 | acima |
| Atendimento WhatsApp 24/7 | ✅ | ✅ | ✅ |
| Painel admin | ✅ | ✅ | ✅ |
| Pagamento PIX/cartão | — | ✅ | ✅ |
| Slides IA + Relatórios PDF | — | ✅ | ✅ |
| Métricas IA vs Humano | — | ✅ | ✅ |
| Integração sistema acadêmico | — | — | ✅ |
| SLA garantido | — | — | ✅ |
| Suporte | Email | Prioritário | Dedicado |

**Sem taxa de setup. Sem fidelidade. Cancele quando quiser.**

---

## Próximos passos

1. **Demonstração ao vivo de 30 minutos** — agendamento gratuito
2. Te mostramos a Billie atendendo no seu próprio WhatsApp
3. Setup em até 5 dias úteis
4. Primeiros 30 dias com suporte premium incluso

📧 contato@igs.com.br
📱 (11) 99999-9999
🌐 https://igs.com.br
