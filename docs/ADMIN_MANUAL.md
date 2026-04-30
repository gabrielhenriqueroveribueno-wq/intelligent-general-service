# Manual do Administrador — IGS

## Índice

1. [Acesso ao Painel](#1-acesso-ao-painel)
2. [Visão Geral do Dashboard](#2-visão-geral-do-dashboard)
3. [Conversas e Atendimento](#3-conversas-e-atendimento)
4. [Tickets de Suporte](#4-tickets-de-suporte)
5. [Alunos](#5-alunos)
6. [Funcionários](#6-funcionários)
7. [Base de Conhecimento](#7-base-de-conhecimento)
8. [Relatórios e Métricas](#8-relatórios-e-métricas)
9. [Usuários e Permissões](#9-usuários-e-permissões)
10. [Configurações do Sistema](#10-configurações-do-sistema)
11. [Integração WhatsApp](#11-integração-whatsapp)
12. [LGPD e Privacidade](#12-lgpd-e-privacidade)
13. [Auditoria](#13-auditoria)
14. [Solução de Problemas](#14-solução-de-problemas)

---

## 1. Acesso ao Painel

### Login

Acesse o painel em `https://app.igs.com.br` com seu e-mail e senha cadastrados.

- **Super Admin**: acesso completo a todos os tenants
- **Admin**: acesso completo ao tenant da sua instituição
- **Manager**: acesso a conversas, tickets, relatórios
- **Agent**: acesso a conversas e tickets atribuídos

### Redefinir Senha

Na tela de login, clique em **"Esqueci minha senha"** e informe o e-mail cadastrado. Você receberá um link válido por 1 hora.

---

## 2. Visão Geral do Dashboard

O Dashboard exibe em tempo real:

| Card | Descrição |
|------|-----------|
| Conversas Hoje | Total de atendimentos iniciados no dia |
| Tickets Abertos | Tickets aguardando resolução |
| Taxa de Resolução | % resolvidos pela IA sem intervenção humana |
| Tempo Médio | Tempo médio de resposta da Billie |

### Gráficos

- **Conversas por hora**: volume ao longo do dia
- **Intenções mais frequentes**: quais perguntas chegam mais
- **Satisfação**: pontuação média dos feedbacks

---

## 3. Conversas e Atendimento

### Visualizar Conversas

Em **Conversas**, você vê todas as sessões ativas e históricas. Use os filtros:

- **Status**: ativa, encerrada, aguardando humano
- **Período**: hoje, última semana, mês
- **Busca**: por número de telefone ou nome do contato

### Assumir Atendimento (Handoff)

Quando a Billie não consegue resolver, o status muda para **"aguardando humano"**. Para assumir:

1. Abra a conversa
2. Clique em **"Assumir atendimento"**
3. Responda diretamente pelo painel (mensagem enviada via WhatsApp)

### Encerrar Conversa

Clique em **"Encerrar"** ao finalizar. Isso libera a conversa para nova interação do contato.

---

## 4. Tickets de Suporte

Tickets são criados automaticamente quando a Billie detecta uma solicitação que exige ação humana (ex: revisão de nota, 2ª via de documento).

### Triagem

| Campo | Descrição |
|-------|-----------|
| Prioridade | low / medium / high / urgent |
| Categoria | academic, financial, hr, general |
| Responsável | Usuário do painel atribuído |

### Fluxo

```
Aberto → Em andamento → Resolvido → Fechado
```

Use **"Adicionar comentário"** para registrar ações internas (não visíveis ao aluno/funcionário).

---

## 5. Alunos

### Buscar Aluno

Em **Alunos**, busque por nome ou RA (Registro Acadêmico). Clique no aluno para ver:

- Dados cadastrais
- Status de matrícula
- Histórico de conversas com a Billie

### Importar Alunos

Em **Importar Dados → Alunos**, faça upload de arquivo CSV. Formato esperado:

```csv
ra,full_name,email,phone,course,enrollment_status
20240001,João Silva,joao@email.com,11999990001,Engenharia,active
```

Campos obrigatórios: `ra`, `full_name`, `enrollment_status`

---

## 6. Funcionários

Mesma lógica dos alunos, identificados por `employee_number`. Status possíveis: `active`, `inactive`.

### Holerite e Ponto

A Billie responde consultas sobre holerite e ponto a partir dos dados importados. Para atualizar:

1. Exporte o relatório do seu sistema de RH em CSV
2. Importe em **Importar Dados → Funcionários**

---

## 7. Base de Conhecimento

Artigos da KB são usados pela Billie para responder perguntas abertas.

### Criar Artigo

1. Vá em **Base de Conhecimento → Novo Artigo**
2. Preencha título e conteúdo (suporta Markdown)
3. Adicione tags relevantes (ex: "matrícula", "boleto")
4. Clique em **Publicar**

### Boas Práticas

- Escreva em linguagem clara e direta
- Use listas para passos numerados
- Inclua sinônimos nas tags (ex: "mensalidade, boleto, financeiro")
- Atualize artigos desatualizados marcando como rascunho primeiro

---

## 8. Relatórios e Métricas

### Relatório Semanal

Gerado automaticamente toda segunda-feira e enviado por e-mail aos admins. Contém:

- Volume de mensagens
- Taxa de resolução por intenção
- Top 10 dúvidas mais frequentes
- Alertas de evasão detectados

### Métricas em Tempo Real

Em **Métricas**, acompanhe:

- Latência da Billie (P50/P95/P99)
- Tokens consumidos (custo estimado)
- Erros de IA (circuit breaker status)
- Uso por tenant (apenas Super Admin)

### Exportar Dados

Em **Relatórios**, selecione o período e clique em **"Exportar CSV"** ou **"Exportar PDF"**.

---

## 9. Usuários e Permissões

### Papéis

| Papel | Permissões |
|-------|------------|
| `super_admin` | Tudo + gerenciar tenants |
| `admin` | Tudo no tenant |
| `manager` | Conversas, tickets, relatórios, KB |
| `agent` | Conversas e tickets atribuídos |

### Convidar Usuário

Em **Usuários → Convidar**, informe e-mail e papel. O usuário receberá link de ativação por e-mail válido por 48 horas.

### Limites por Plano

| Plano | Usuários Máx. |
|-------|--------------|
| Trial | 3 |
| Starter | 10 |
| Pro | 50 |
| Enterprise | Ilimitado |

---

## 10. Configurações do Sistema

### Perfil do Tenant

Em **Configurações → Geral**, configure:

- Nome da instituição
- Horário de atendimento (fora do horário, Billie informa o usuário)
- Mensagem de boas-vindas personalizada
- Idioma padrão das respostas

### Chaves de API

Em **Configurações → Integrações**, você pode usar sua própria chave Anthropic (Claude API) para faturamento direto. Se não configurada, usa a chave global do IGS.

### Notificações

Configure quais eventos disparam e-mail para admins:

- Novo ticket de alta prioridade
- Alerta de evasão detectado
- Falha no envio de mensagem
- Limite de mensagens mensais atingindo 80%

---

## 11. Integração WhatsApp

### Configuração Inicial

Siga o guia em **WhatsApp Setup** no painel. Você precisará de:

1. Conta Meta Business Manager
2. Número de telefone dedicado (não pode estar no WhatsApp pessoal)
3. App Meta aprovado para WhatsApp Business API

### Verificar Webhook

Após configurar, clique em **"Testar conexão"**. O sistema enviará uma mensagem de teste ao número configurado.

### Múltiplos Números

No plano Enterprise, é possível configurar mais de um número (ex: um para alunos, outro para funcionários). Contate o suporte para ativar.

---

## 12. LGPD e Privacidade

### Direito ao Esquecimento (Art. 18, LGPD)

Quando um titular solicitar exclusão dos seus dados:

1. Vá em **Admin → LGPD → Anonimizar**
2. Informe o ID do aluno ou funcionário
3. Confirme a ação com a justificativa

Os dados PII (nome, CPF, telefone, e-mail) são substituídos por valores anonimizados. O histórico de mensagens é mantido sem vínculo ao titular.

### Retenção Automática

O sistema executa anonimização automática mensal para registros inativos há mais de **5 anos** (Art. 6°, III — minimização de dados).

### Exportar Dados do Titular

Para atender solicitações de portabilidade, contate `privacidade@igs.com.br` com o CPF/RA do titular.

---

## 13. Auditoria

Em **Auditoria**, todos os eventos críticos ficam registrados:

- Login/logout de usuários
- Criação/edição/exclusão de registros
- Anonimizações LGPD
- Alterações de configuração

Use os filtros por ação e período para investigar incidentes.

---

## 14. Solução de Problemas

### Billie não responde mensagens

1. Verifique **Status do Sistema** — todos os serviços devem estar verdes
2. Confira o token do WhatsApp em **Configurações → Integrações** (tokens Meta expiram)
3. Verifique se o limite mensal de mensagens não foi atingido (**Configurações → Plano**)

### Aluno não consegue se identificar

A Billie pede o RA na primeira mensagem. Verifique se o RA existe no sistema em **Alunos → Buscar**.

### Mensagens duplicadas

Pode ocorrer se o webhook do Meta receber o mesmo evento mais de uma vez. O sistema tem deduplicação por `wamid`, mas em casos raros pode ocorrer. Reporte em `suporte@igs.com.br`.

### Contato com Suporte

- **E-mail**: suporte@igs.com.br
- **WhatsApp**: +55 11 99999-0000
- **Horário**: Segunda a Sexta, 9h–18h (BRT)
- **SLA**: Respostas em até 4 horas úteis (plano Pro/Enterprise)
