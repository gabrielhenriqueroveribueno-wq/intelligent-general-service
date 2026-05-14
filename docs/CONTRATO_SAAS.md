# CONTRATO DE LICENÇA DE USO DE SOFTWARE COMO SERVIÇO (SaaS) E PRESTAÇÃO DE SERVIÇOS

**Versão 1.0 — 2026**

Por este instrumento particular, de um lado:

**CONTRATADA**

**[RAZÃO SOCIAL DA CONTRATADA] LTDA.**, pessoa jurídica de direito privado, inscrita no CNPJ sob nº **[CNPJ]**, com sede em **[ENDEREÇO COMPLETO]**, neste ato representada na forma de seus atos constitutivos, doravante denominada simplesmente **"CONTRATADA"** ou **"IGS"**;

**CONTRATANTE**

**[RAZÃO SOCIAL DA CONTRATANTE]**, pessoa jurídica de direito privado/mantenedora de instituição de ensino, inscrita no CNPJ sob nº **[CNPJ]**, com sede em **[ENDEREÇO COMPLETO]**, neste ato representada na forma de seus atos constitutivos, doravante denominada simplesmente **"CONTRATANTE"** ou **"INSTITUIÇÃO"**;

Quando em conjunto referidas como **"Partes"** e isoladamente como **"Parte"**, têm entre si justo e contratado o presente **Contrato de Licença de Uso de Software como Serviço (SaaS) e Prestação de Serviços** (**"Contrato"**), que se regerá pelas seguintes cláusulas e condições:

---

## 1. DEFINIÇÕES

1.1. Para os fins deste Contrato, os termos abaixo terão os seguintes significados:

| Termo | Definição |
|-------|-----------|
| **Plataforma** ou **IGS** | Software de atendimento inteligente via WhatsApp para instituições de ensino, denominado *Intelligent General Service*, de titularidade da CONTRATADA, acessível por meio de navegador web e/ou API. |
| **Usuário Final** | Aluno, responsável financeiro, candidato ou colaborador da CONTRATANTE que interage com a Plataforma via WhatsApp ou portal. |
| **Usuário Administrativo** | Colaborador autorizado da CONTRATANTE com acesso ao painel administrativo da Plataforma. |
| **Dados Pessoais** | Conforme definição da Lei nº 13.709/2018 (LGPD). |
| **Tenant** | Instância lógica isolada da Plataforma associada exclusivamente à CONTRATANTE. |
| **Tokens de IA** | Unidade de consumo dos modelos de linguagem utilizados pela Plataforma para classificar intenções e gerar respostas. |
| **Mensagem WhatsApp** | Cada mensagem enviada ou recebida via WhatsApp Business API (Meta), incluindo custos repassáveis cobrados pela Meta. |
| **Janela de 24 horas** | Período de 24 horas após a última mensagem do Usuário Final, durante o qual a CONTRATANTE pode enviar mensagens gratuitas conforme política Meta. |

---

## 2. OBJETO

2.1. A CONTRATADA, mediante o pagamento da remuneração prevista neste Contrato, concede à CONTRATANTE **licença de uso não-exclusiva, intransferível e revogável** da Plataforma IGS, na modalidade **Software como Serviço (SaaS)**, juntamente com os serviços acessórios descritos no Anexo I.

2.2. A licença autoriza a CONTRATANTE a:

a) acessar o painel administrativo da Plataforma por meio dos Usuários Administrativos autorizados;
b) integrar a Plataforma ao número de WhatsApp Business da INSTITUIÇÃO;
c) utilizar a Plataforma para atender Usuários Finais nos termos deste Contrato.

2.3. **Funcionalidades incluídas** (referência ao plano contratado — Cláusula 4):

**2.3.1. Atendimento automatizado via WhatsApp:**

- Classificação automática de intenções por IA em mais de 40 categorias (consulta de notas, frequência, horários, boletos, holerites, férias, ponto, solicitações de RH, biblioteca, agendamentos, OCR de documentos, geração de PIX, negociação financeira, entre outras);
- Geração de respostas com base em dados reais da INSTITUIÇÃO (modelo RAG — *Retrieval-Augmented Generation*), sem invenção de informações;
- Verificação de identidade do Usuário Final por número de matrícula (RA) ou número de funcionário;
- Encaminhamento para atendimento humano (handoff) quando solicitado ou quando a IA detecta complexidade;
- Detecção de sentimento e priorização de atendimento.

**2.3.2. Painel administrativo:**

- Visualização de conversas em tempo real (WebSocket);
- Gestão de tickets com SLA;
- Cadastros de alunos, funcionários, base de conhecimento (FAQ);
- Importação em massa via CSV;
- Dashboard de métricas e relatórios automáticos;
- Análise de risco de evasão de alunos via IA;
- Aprendizado contínuo a partir de resoluções de tickets fechados;
- Multi-tenancy com isolamento lógico via PostgreSQL Row-Level Security (RLS).

**2.3.3. Integrações:**

- API REST documentada (OpenAPI/Swagger);
- Webhooks de saída para sistemas externos;
- Conector SQL genérico para sincronização com sistemas acadêmicos legados (SQL Server, MySQL, PostgreSQL e Oracle), conforme disponibilidade técnica;
- Integração com gateway Mercado Pago para emissão de boletos e PIX.

**2.3.4. Conformidade e segurança:**

- Criptografia em trânsito (TLS 1.3 via Let's Encrypt) e em repouso (Fernet AES-128 para campos sensíveis);
- Autenticação JWT com refresh tokens;
- Anonimização automática de dados pessoais conforme política de retenção;
- Exportação e exclusão de dados pessoais sob demanda (LGPD Art. 18);
- Verificação HMAC das requisições do webhook Meta.

2.4. A relação detalhada de funcionalidades por plano consta do **Anexo I**.

---

## 3. VIGÊNCIA E RENOVAÇÃO

3.1. O presente Contrato vigorará pelo prazo de **12 (doze) meses**, contados da data de sua assinatura, **renovando-se automaticamente** por períodos iguais e sucessivos, salvo manifestação contrária por escrito de qualquer das Partes com antecedência mínima de **30 (trinta) dias** do término do período em curso.

3.2. **Período de Teste Gratuito:** A CONTRATADA poderá conceder, a seu critério, período de teste gratuito de até 14 (quatorze) dias antes do início da cobrança, durante o qual qualquer Parte poderá rescindir o Contrato sem ônus mediante notificação por escrito.

3.3. **Setup e Onboarding:** A CONTRATADA realizará a configuração inicial em até **5 (cinco) dias úteis** após a assinatura, incluindo:

a) provisionamento do tenant na infraestrutura;
b) configuração do número WhatsApp Business e webhook Meta;
c) importação inicial dos cadastros via CSV ou integração SQL;
d) treinamento remoto de até **2 (duas) horas** para os Usuários Administrativos;
e) revisão da base de conhecimento inicial.

---

## 4. REMUNERAÇÃO E FORMA DE PAGAMENTO

4.1. Pela licença de uso e pelos serviços ora contratados, a CONTRATANTE pagará à CONTRATADA o valor mensal correspondente ao **plano contratado**:

| Plano | Valor Mensal | Limite de Alunos Ativos | Recursos Extras |
|-------|--------------|-------------------------|-----------------|
| **Starter** | R$ 297,00 | até 500 | atendimento básico, 1 número WhatsApp |
| **Pro** | R$ 497,00 | ilimitado | RH/holerite, evasão IA, 3 números WhatsApp |
| **Enterprise** | sob consulta | ilimitado | multi-unidade, SLA dedicado, integrações customizadas |

**Plano contratado:** **[ ] Starter / [ ] Pro / [ ] Enterprise — valor: R$ [VALOR],00**

4.2. **Custos repassáveis (Anexo II):** Adicionalmente ao valor da licença, a CONTRATANTE arcará com os custos cobrados por terceiros, quando aplicável:

a) **Mensagens WhatsApp fora da janela de 24 horas** (mensagens-modelo da Meta): repassadas pelo valor de custo conforme tabela Meta vigente. As mensagens dentro da janela de 24 horas e mensagens recebidas dos Usuários Finais **não geram custo adicional**;
b) **Taxas do gateway de pagamento Mercado Pago**, conforme política Mercado Pago vigente, retidas diretamente nas cobranças geradas;
c) **Excedente de tokens de IA**, caso o consumo mensal exceda em mais de 100% a média histórica do plano (cláusula 4.6).

4.3. **Forma de pagamento:** O valor mensal será cobrado em ciclos de 30 (trinta) dias, com vencimento no mesmo dia do mês da assinatura, mediante:

- [ ] **PIX** com QR Code;
- [ ] **Cartão de crédito** recorrente via Mercado Pago;
- [ ] **Boleto bancário**.

4.4. **Reajuste:** Os valores serão reajustados anualmente pelo **IPCA** (Índice Nacional de Preços ao Consumidor Amplo) acumulado no período, ou outro índice oficial que venha a substituí-lo.

4.5. **Inadimplência:** O não pagamento na data de vencimento ensejará:

a) acréscimo de **multa de 2%** (dois por cento) sobre o valor em atraso;
b) **juros moratórios de 1%** (um por cento) ao mês, pro rata die;
c) **correção monetária** pelo IPCA;
d) **suspensão do acesso à Plataforma** após 10 (dez) dias de atraso, mediante notificação;
e) **rescisão automática** após 30 (trinta) dias de atraso, sem prejuízo da cobrança dos valores devidos.

4.6. **Política de uso justo (Fair Use) de IA:** O consumo de tokens de IA está sujeito a limites de uso justo. Caso o consumo mensal exceda em mais de 100% (cem por cento) a média histórica do plano (apurada pelo painel da Plataforma), a CONTRATADA notificará a CONTRATANTE com 7 (sete) dias de antecedência antes de aplicar qualquer cobrança adicional.

---

## 5. OBRIGAÇÕES DA CONTRATADA

5.1. Compete à CONTRATADA:

a) Disponibilizar a Plataforma com disponibilidade mensal mínima de **99,5% (noventa e nove vírgula cinco por cento)**, conforme SLA detalhado na Cláusula 9;
b) Realizar backup diário dos dados da CONTRATANTE, com retenção mínima de **30 (trinta) dias**;
c) Manter a Plataforma atualizada, aplicando correções de segurança em tempo hábil;
d) Prestar suporte técnico nos termos do plano contratado;
e) Tratar os Dados Pessoais conforme a LGPD e a Cláusula 8 deste Contrato;
f) Notificar a CONTRATANTE sobre **incidentes de segurança** em até **48 (quarenta e oito) horas** após sua identificação;
g) Garantir o isolamento lógico dos dados da CONTRATANTE em relação a outros clientes (multi-tenancy);
h) Fornecer canais de exportação de dados em formato legível por máquina (JSON, CSV).

---

## 6. OBRIGAÇÕES DA CONTRATANTE

6.1. Compete à CONTRATANTE:

a) **Pagar pontualmente** os valores devidos;
b) Designar **Usuários Administrativos** e gerenciar suas credenciais com segurança;
c) Manter atualizada a base de cadastros (alunos, funcionários, FAQ);
d) **Não utilizar a Plataforma** para finalidades ilegais, ofensivas, discriminatórias ou que violem direitos de terceiros;
e) Garantir que a Conta WhatsApp Business utilizada está em conformidade com as **políticas da Meta**;
f) **Obter consentimento dos Usuários Finais** para o tratamento de dados pessoais, quando exigido pela LGPD, e divulgar adequadamente sua Política de Privacidade;
g) Cumprir a Política de Uso Aceitável (Anexo III);
h) Notificar a CONTRATADA sobre eventuais incidentes de segurança que envolvam credenciais ou dados da Plataforma;
i) **Não realizar engenharia reversa**, descompilação ou tentativa de acesso não autorizado ao código-fonte ou infraestrutura da Plataforma;
j) Validar previamente a precisão das respostas automáticas para consultas críticas (financeiras, acadêmicas, médicas).

---

## 7. PROPRIEDADE INTELECTUAL

7.1. A Plataforma IGS, incluindo seu código-fonte, modelos de IA, banco de dados estrutural, interfaces gráficas, marca e demais elementos, é de **propriedade exclusiva da CONTRATADA**, sendo este Contrato uma mera licença de uso, nos termos da Lei nº 9.609/1998.

7.2. **Dados da CONTRATANTE:** Os dados cadastrados, importados ou gerados pela CONTRATANTE durante o uso da Plataforma (incluindo mensagens dos Usuários Finais, resoluções de tickets, base de conhecimento) **permanecem de propriedade da CONTRATANTE**, que poderá exportá-los a qualquer momento.

7.3. **Uso de dados agregados e anonimizados:** A CONTRATADA poderá utilizar dados estatísticos agregados e completamente anonimizados (sem possibilidade de identificação direta ou indireta da CONTRATANTE ou dos Usuários Finais) para fins de:

a) melhoria contínua dos modelos de classificação de intenções;
b) benchmarks de mercado;
c) materiais de marketing.

7.4. **Vedações:** É vedada a utilização da Plataforma por terceiros não autorizados, bem como o sublicenciamento, locação ou cessão da licença sem prévia e expressa autorização da CONTRATADA.

---

## 8. PROTEÇÃO DE DADOS PESSOAIS (LGPD)

8.1. As Partes obrigam-se a observar a **Lei nº 13.709/2018 (LGPD)** e demais normas aplicáveis.

8.2. **Papéis das Partes:** Para os fins da LGPD:

a) a **CONTRATANTE** atua como **Controladora** dos dados dos Usuários Finais;
b) a **CONTRATADA** atua como **Operadora**, processando dados em nome da CONTRATANTE, conforme instruções deste Contrato.

8.3. **Hipóteses de tratamento:** O tratamento de dados pessoais pela Plataforma se dá com base em:

a) **execução de contrato** com o Usuário Final (Art. 7º, V, LGPD);
b) **legítimo interesse** para prevenção de fraudes e segurança (Art. 7º, IX);
c) **consentimento** quando aplicável (Art. 7º, I);
d) **cumprimento de obrigação legal/regulatória** (Art. 7º, II).

8.4. **Medidas técnicas e administrativas implementadas pela CONTRATADA:**

a) criptografia em trânsito (TLS 1.3) e em repouso (Fernet AES-128 para CPF, telefone, tokens);
b) autenticação JWT com expiração de **15 minutos** para tokens de acesso;
c) **Row-Level Security** no PostgreSQL para isolamento entre tenants;
d) **rate limiting** e proteção contra ataques de força bruta;
e) verificação **HMAC** de origem nos webhooks;
f) **logs de auditoria** com retenção mínima de 90 dias;
g) backup diário criptografado;
h) **anonimização automática** programada de dados conforme política interna.

8.5. **Direitos dos titulares (Art. 18, LGPD):** A Plataforma fornece, nativamente:

a) endpoint de **exportação de dados pessoais** (`GET /api/v1/auth/me/export`);
b) endpoint de **exclusão/anonimização** (`DELETE /api/v1/auth/me`);
c) endpoint de **portabilidade** em formato JSON.

8.6. **Subprocessadores autorizados:** A CONTRATANTE autoriza expressamente o uso dos seguintes subprocessadores pela CONTRATADA:

| Subprocessador | Finalidade | Localização |
|----------------|-----------|-------------|
| Meta Platforms | API WhatsApp Business | EUA / Irlanda |
| Groq Inc. (ou equivalente) | Provedor de modelo de linguagem | EUA |
| Anthropic PBC | Provedor de modelo Claude (fallback) | EUA |
| Mercado Pago | Gateway de pagamento | Brasil |
| Oracle Cloud / AWS / Azure | Infraestrutura de hospedagem | Brasil ou país com adequado nível de proteção |
| Resend | Envio de emails transacionais | EUA |

8.7. **Alteração de subprocessadores:** A CONTRATADA notificará a CONTRATANTE com **30 (trinta) dias** de antecedência sobre qualquer alteração na lista de subprocessadores, podendo a CONTRATANTE opor-se justificadamente.

8.8. **Transferência internacional:** Eventuais transferências internacionais de dados serão realizadas em conformidade com o Art. 33 da LGPD e cláusulas contratuais padrão, quando aplicáveis.

8.9. **Encarregado de Dados (DPO):** As Partes designam seus respectivos Encarregados:

- **DPO da CONTRATADA:** [NOME] — [EMAIL]
- **DPO da CONTRATANTE:** [NOME] — [EMAIL]

8.10. **Incidente de segurança:** Em caso de incidente envolvendo dados pessoais, a CONTRATADA notificará a CONTRATANTE em até **48 horas**, com informações suficientes para que a CONTRATANTE cumpra suas obrigações perante a ANPD.

8.11. **Devolução/exclusão pós-rescisão:** Encerrado o Contrato, a CONTRATADA disponibilizará os dados da CONTRATANTE em formato exportável por **30 (trinta) dias**, após o que procederá à exclusão definitiva, salvo retenção exigida por lei.

---

## 9. NÍVEL DE SERVIÇO (SLA)

9.1. **Disponibilidade:** A CONTRATADA compromete-se com disponibilidade mensal mínima de **99,5%**, medida em janela mensal corrida, **excluindo-se**:

a) manutenções programadas, comunicadas com antecedência mínima de 48 horas, em janelas fora do horário comercial;
b) indisponibilidade decorrente de subprocessadores (Meta, Groq, gateway de pagamento), provedores de internet ou casos fortuitos/força maior;
c) interrupções causadas por uso indevido da CONTRATANTE.

9.2. **Métrica de disponibilidade:** Apurada mensalmente pelo painel `/status` da própria Plataforma e pelo sistema de monitoramento (Prometheus + alertas).

9.3. **Crédito por descumprimento de SLA:**

| Disponibilidade Mensal | Crédito (na fatura seguinte) |
|------------------------|------------------------------|
| < 99,5% e ≥ 99,0% | 5% do valor mensal |
| < 99,0% e ≥ 98,0% | 10% do valor mensal |
| < 98,0% | 20% do valor mensal |

9.4. **Suporte técnico:**

| Plano | Canal | Horário | Tempo de Resposta |
|-------|-------|---------|-------------------|
| Starter | Email | Dias úteis 9h–18h | até 24 horas úteis |
| Pro | Email + WhatsApp | Dias úteis 9h–20h | até 8 horas úteis |
| Enterprise | Email + WhatsApp + Telefone | 24/7 para incidentes críticos | até 1 hora para incidentes críticos |

---

## 10. CONFIDENCIALIDADE

10.1. As Partes obrigam-se a manter sigilo sobre todas as **Informações Confidenciais** trocadas durante a vigência deste Contrato e por **5 (cinco) anos** após seu encerramento.

10.2. **Informações Confidenciais** abrangem, sem se limitar a: dados de Usuários Finais, configurações da Plataforma, valores comerciais, métricas operacionais, dados financeiros e estratégicos.

10.3. **Exceções:** Não constituem informação confidencial as informações que (i) sejam de domínio público sem culpa da Parte receptora; (ii) sejam conhecidas pela Parte antes da divulgação; (iii) sejam divulgadas por ordem judicial ou autoridade competente.

---

## 11. LIMITAÇÃO DE RESPONSABILIDADE

11.1. **A responsabilidade total da CONTRATADA**, por qualquer causa relacionada a este Contrato, está limitada ao **valor efetivamente pago pela CONTRATANTE nos 12 (doze) meses anteriores** ao evento que originou a responsabilidade.

11.2. **A CONTRATADA não responde por:**

a) decisões tomadas pela CONTRATANTE com base em respostas geradas pela IA, sendo obrigação da CONTRATANTE validar conteúdo de natureza financeira, acadêmica ou crítica antes de aplicar suas consequências;
b) indisponibilidade de subprocessadores (Meta, Groq, gateway de pagamento);
c) suspensão da conta WhatsApp Business pela Meta em razão de descumprimento de suas políticas pela CONTRATANTE;
d) lucros cessantes, danos indiretos, perda de oportunidade ou dano moral institucional;
e) uso indevido da Plataforma por Usuários Administrativos da CONTRATANTE.

11.3. **Limitação não aplicável:** A limitação prevista na cláusula 11.1 não se aplica em casos de:

a) violação dolosa de propriedade intelectual;
b) descumprimento doloso da LGPD pela CONTRATADA;
c) divulgação dolosa de Informações Confidenciais.

---

## 12. RESCISÃO

12.1. **Rescisão sem justa causa:** Qualquer Parte poderá rescindir o presente Contrato mediante notificação por escrito com **30 (trinta) dias** de antecedência, sem ônus, ressalvado o pagamento dos valores referentes ao período de uso.

12.2. **Rescisão por justa causa:** O Contrato poderá ser rescindido imediatamente, sem multa, pela Parte inocente, em caso de:

a) **inadimplência** superior a 30 (trinta) dias (em favor da CONTRATADA);
b) **descumprimento de obrigação contratual relevante**, não sanado em 15 (quinze) dias após notificação;
c) **falência, recuperação judicial** ou insolvência declarada;
d) **violação à LGPD** com risco grave aos titulares.

12.3. **Multa rescisória:** Caso a CONTRATANTE rescinda sem justa causa antes do término do período em curso, será devida multa equivalente a **3 (três) mensalidades** vigentes, salvo se houver descumprimento de SLA reincidente pela CONTRATADA.

12.4. **Efeitos da rescisão:** Após a rescisão:

a) o acesso à Plataforma será bloqueado em até 7 (sete) dias;
b) os dados serão disponibilizados para exportação por 30 (trinta) dias;
c) após 60 (sessenta) dias, todos os dados serão excluídos definitivamente, ressalvada retenção exigida por lei.

---

## 13. DISPOSIÇÕES GERAIS

13.1. **Independência das cláusulas:** A eventual invalidade de qualquer cláusula não afetará as demais.

13.2. **Cessão:** Nenhuma das Partes poderá ceder este Contrato sem prévio consentimento por escrito da outra, salvo em caso de reorganização societária ou alienação de unidade produtiva, mediante simples notificação.

13.3. **Tolerância:** A eventual tolerância no descumprimento de qualquer cláusula não constituirá novação nem renúncia.

13.4. **Notificações:** Toda comunicação formal entre as Partes será feita por email aos endereços indicados pelos representantes, considerando-se entregue na data do envio comprovado.

13.5. **Força maior:** Nenhuma das Partes será responsável por descumprimento decorrente de evento de força maior ou caso fortuito, conforme Art. 393 do Código Civil.

13.6. **Integralidade:** Este Contrato e seus Anexos representam a integralidade do acordo entre as Partes, substituindo entendimentos anteriores.

---

## 14. FORO

14.1. Fica eleito o **Foro da Comarca de [CIDADE]/[UF]**, com renúncia expressa a qualquer outro, por mais privilegiado que seja, para dirimir quaisquer dúvidas ou litígios oriundos deste Contrato.

---

E, por estarem assim justas e contratadas, assinam as Partes este Contrato em via eletrônica, com mesma validade jurídica, conforme MP 2.200-2/2001 e Lei nº 14.063/2020.

**[CIDADE]**, **[DATA]**.

<br>

| **CONTRATADA** | **CONTRATANTE** |
|---|---|
| _______________________________ | _______________________________ |
| **[RAZÃO SOCIAL DA CONTRATADA]** | **[RAZÃO SOCIAL DA CONTRATANTE]** |
| CNPJ: [CNPJ] | CNPJ: [CNPJ] |
| Representante: [NOME] | Representante: [NOME] |
| CPF: [CPF] | CPF: [CPF] |

**Testemunhas:**

1. _____________________________________ — Nome: [NOME] — CPF: [CPF]
2. _____________________________________ — Nome: [NOME] — CPF: [CPF]

---

# ANEXO I — DESCRIÇÃO TÉCNICA DOS PLANOS

## Plano Starter — R$ 297,00/mês

- Até **500 alunos ativos**
- Bot WhatsApp 24/7 (classificação de intenções + RAG)
- **Domínios cobertos:** notas, boletos, frequência, horários, FAQ, encaminhamento humano
- Painel administrativo completo
- Tickets com SLA básico
- Relatórios semanais por email
- Base de conhecimento (FAQ)
- **1 número WhatsApp**
- Suporte por email (24h úteis)
- Backup diário
- LGPD compliance

## Plano Pro — R$ 497,00/mês

Tudo do Starter, mais:

- **Alunos ilimitados**
- Módulo **RH e funcionários** (holerite, férias, ponto, solicitações)
- **Análise de risco de evasão** por IA (score 0-100, fatores explicáveis)
- Dashboard de métricas avançado
- Aprendizado contínuo a partir de tickets fechados
- **Até 3 números** WhatsApp
- Relatórios semanais e mensais (email + PDF)
- Negociação financeira automática (parcelamento, PIX, geração de boleto)
- OCR de documentos
- Agendamento de atendimentos
- Web Push notifications
- Suporte prioritário (8h úteis)

## Plano Enterprise — sob consulta

Tudo do Pro, mais:

- **Múltiplas unidades / CNPJs** em um único contrato
- Integração customizada com sistemas legados (TOTVS RM, SAP, sistemas próprios)
- Conector SQL direto para sistemas acadêmicos (MSSQL, MySQL, PostgreSQL, Oracle)
- SLA customizado com suporte 24/7
- Treinamento presencial e onboarding dedicado
- Deploy on-premise disponível
- Relatórios customizados
- Gerente de conta dedicado
- Auditorias técnicas anuais

---

# ANEXO II — CUSTOS REPASSÁVEIS

## Mensagens WhatsApp (Meta Cloud API)

A Meta cobra **mensagens-modelo** enviadas fora da janela de 24 horas (lembretes proativos, notificações). O custo é repassado pelo valor de tabela Meta vigente. Mensagens recebidas e mensagens enviadas dentro da janela de 24 horas **são gratuitas**.

**Categorias e preços de referência (sujeito a alteração pela Meta):**

| Categoria | Preço por Mensagem (BRL) |
|-----------|--------------------------|
| Utilitárias (lembretes, atualizações) | ~R$ 0,05 |
| Autenticação (códigos, OTP) | ~R$ 0,03 |
| Marketing | ~R$ 0,15 |
| Serviço (dentro da janela 24h) | **gratuita** |

## Mercado Pago

Taxas conforme política Mercado Pago vigente, retidas diretamente nas transações:

- **PIX:** 0,99% por transação
- **Boleto:** R$ 3,49 fixo por boleto pago
- **Cartão de crédito (à vista):** ~3,79%
- **Cartão de crédito (parcelado):** taxa variável

---

# ANEXO III — POLÍTICA DE USO ACEITÁVEL

A CONTRATANTE compromete-se a **NÃO**:

1. Utilizar a Plataforma para envio de **SPAM** ou comunicações não solicitadas em massa em violação às políticas Meta;
2. Coletar ou processar dados pessoais **sensíveis** (origem racial, religiosa, dados de saúde, biométricos) sem base legal adequada;
3. Permitir acesso a Usuários Administrativos **menores de 18 anos** ou sem autorização institucional;
4. Tentar **acessar dados de outros tenants** ou da infraestrutura;
5. Realizar **engenharia reversa**, scraping não autorizado ou cópia da Plataforma;
6. Utilizar a Plataforma para finalidades **ilegais, discriminatórias ou abusivas**;
7. Compartilhar credenciais de acesso ao painel administrativo;
8. Enviar conteúdo **enganoso** aos Usuários Finais.

O descumprimento poderá ensejar **suspensão imediata** do acesso, sem prejuízo das demais penalidades contratuais e legais.
