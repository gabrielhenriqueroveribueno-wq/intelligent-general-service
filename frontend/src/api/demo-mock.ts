/**
 * Demo mock data for screenshots.
 * Overrides api.get/post to return realistic data without network calls.
 */
import { api } from './client'
import type { AxiosResponse } from 'axios'

// ── Tipos e dados para o modo demo público /demo ─────────────────────────────

export interface DemoMessage {
  sender: 'user' | 'bot'
  text: string
}

export const DEMO_CONVERSATIONS: Record<'student' | 'employee', DemoMessage[]> = {
  student: [
    { sender: 'bot', text: 'Oi! Sou a Billie, do atendimento da Faculdade Anchieta 😊\nVocê é *aluno*, *funcionário* ou *ainda não faz parte da Anchieta*?' },
    { sender: 'user', text: 'Aluno' },
    { sender: 'bot', text: 'Me passa seu RA que eu puxo seus dados.' },
    { sender: 'user', text: '20241002' },
    { sender: 'bot', text: 'Achei seu cadastro, *Ana Carolina*! Por segurança, me confirma sua senha?' },
    { sender: 'user', text: 'anchieta2026' },
    { sender: 'bot', text: 'Senha confirmada, *Ana*! Como posso te ajudar hoje?' },
    { sender: 'user', text: 'Quero ver minhas notas' },
    { sender: 'bot', text: 'Suas notas do semestre, *Ana*:\n\n- *Cálculo II* — P1: *7.5* | P2: *8.0*\n- *Programação Web* — P1: *9.0* | P2: *9.5*\n- *Banco de Dados II* — P1: *6.5* | P2: *5.0* ⚠️\n- *Eng. Software* — P1: *8.0* | P2: *8.5*\n\nBanco de Dados II ficou apertado na P2. Quer ver frequência ou boletos? 📘' },
    { sender: 'user', text: 'Quero pagar o boleto de abril' },
    { sender: 'bot', text: 'Seu boleto de *abril/2026*:\n- Valor: *R$ 1.890,00*\n- Vencimento: *10/04/2026*\n- Status: *Pendente*\n\nQuer que eu gere o link de pagamento?' },
    { sender: 'user', text: 'Sim!' },
    { sender: 'bot', text: 'Aqui está o link pra pagar:\n\n🔗 [Link de pagamento — simulado]\n\nAceita PIX, cartão e boleto. Precisa de mais alguma coisa?' },
    { sender: 'user', text: 'Não, obrigada!' },
    { sender: 'bot', text: 'Que bom que pude ajudar! Me dá uma nota de *1 a 5* pro atendimento? 1 = ruim, 5 = excelente 🙂' },
    { sender: 'user', text: '5' },
    { sender: 'bot', text: 'Nota *5* registrada! Muito obrigada, *Ana*. Qualquer coisa, é só chamar ✅' },
  ],
  employee: [
    { sender: 'bot', text: 'Oi! Sou a Billie, do atendimento da Faculdade Anchieta 😊\nVocê é *aluno*, *funcionário* ou *ainda não faz parte da Anchieta*?' },
    { sender: 'user', text: 'Funcionário' },
    { sender: 'bot', text: 'Me passa seu código de funcionário (ex: FUNC001).' },
    { sender: 'user', text: 'FUNC001' },
    { sender: 'bot', text: 'Achei seu cadastro, *Carlos Eduardo*! Por segurança, me confirma sua senha?' },
    { sender: 'user', text: 'carlos2026' },
    { sender: 'bot', text: 'Senha confirmada, *Carlos*! Como posso te ajudar?' },
    { sender: 'user', text: 'Quero ver meu holerite de março' },
    { sender: 'bot', text: 'Seu holerite de *março/2026*, *Carlos*:\n\n- Salário bruto: *R$ 4.800,00*\n- INSS: *- R$ 432,00*\n- IRRF: *- R$ 168,00*\n- Vale transporte: *- R$ 288,00*\n- *Salário líquido: R$ 3.912,00*\n\nPrecisa do PDF ou de mais alguma coisa? 📋' },
    { sender: 'user', text: 'Qual meu saldo de férias?' },
    { sender: 'bot', text: 'Seu saldo de férias, *Carlos*:\n\n- Total acumulado: *30 dias*\n- Utilizados: *12 dias*\n- *Disponíveis: 18 dias*\n- Período aquisitivo: 15/03/2025 a 14/03/2026\n- Prazo para gozar: *15/08/2026*\n\nQuer solicitar férias agora? 🌴' },
    { sender: 'user', text: 'Sim, quero tirar 15 dias em julho' },
    { sender: 'bot', text: 'Qual período exato você quer em julho? (ex: 01/07 a 15/07)' },
    { sender: 'user', text: '07/07 a 21/07' },
    { sender: 'bot', text: 'Solicitação registrada!\n\n- Período: *07/07/2026 a 21/07/2026* (15 dias)\n- Protocolo: *FER-2026-0312*\n- Status: *Aguardando aprovação do gestor*\n\nVocê receberá uma notificação quando for aprovada. Mais alguma coisa? ✅' },
    { sender: 'user', text: 'Não, valeu!' },
    { sender: 'bot', text: 'Que bom que pude ajudar! Me dá uma nota de *1 a 5* pro atendimento? 1 = ruim, 5 = excelente 😊' },
    { sender: 'user', text: '5' },
    { sender: 'bot', text: 'Nota *5* registrada! Obrigada, *Carlos*. Qualquer coisa, é só chamar ✅' },
  ],
}

const DEMO_DATA: Record<string, unknown> = {
  '/api/v1/auth/me': {
    id: 'demo-001',
    email: 'gestor@anchieta.edu.br',
    full_name: 'Gabriel Bueno',
    role: 'admin',
    tenant_id: 'tenant-001',
  },

  '/api/v1/dashboard/overview': {
    total_conversations_today: 47,
    total_conversations_week: 312,
    total_conversations_month: 1248,
    auto_resolution_rate: 87.3,
    avg_response_time_seconds: 145,
    open_tickets: 8,
    sla_breached_tickets: 1,
    active_agents: 3,
    avg_satisfaction: 4.6,
    total_students: 847,
    total_employees: 62,
    total_messages_month: 3842,
    ai_tokens_month: 284500,
    estimated_savings: 18400,
  },

  '/api/v1/conversations': {
    items: [
      { id: 'c1', contact_name: 'Ana Carolina Silva', contact_phone: '5511999881234', status: 'active', started_at: '2026-04-14T14:20:00Z', last_message_at: '2026-04-14T14:32:00Z', message_count: 8, channel: 'whatsapp', context_type: 'Aluno', last_sentiment: 'positive' },
      { id: 'c2', contact_name: 'Pedro Henrique Santos', contact_phone: '5511998774321', status: 'active', started_at: '2026-04-14T14:10:00Z', last_message_at: '2026-04-14T14:28:00Z', message_count: 5, channel: 'whatsapp', context_type: 'Aluno', last_sentiment: 'negative' },
      { id: 'c3', contact_name: 'Maria Eduarda Oliveira', contact_phone: '5511997665432', status: 'waiting_agent', started_at: '2026-04-14T13:50:00Z', last_message_at: '2026-04-14T14:15:00Z', message_count: 12, channel: 'whatsapp', context_type: 'Aluno', last_sentiment: 'negative' },
      { id: 'c4', contact_name: 'Lucas Oliveira Silva', contact_phone: '5511997791909', status: 'active', started_at: '2026-04-14T13:30:00Z', last_message_at: '2026-04-14T13:55:00Z', message_count: 6, channel: 'whatsapp', context_type: 'Aluno', last_sentiment: 'neutral' },
      { id: 'c5', contact_name: 'Juliana Costa Ferreira', contact_phone: '5511996554321', status: 'closed', started_at: '2026-04-14T13:10:00Z', last_message_at: '2026-04-14T13:40:00Z', message_count: 4, channel: 'whatsapp', context_type: 'Aluno', last_sentiment: 'positive' },
      { id: 'c6', contact_name: 'Rafael Almeida Souza', contact_phone: '5511995443210', status: 'closed', started_at: '2026-04-14T11:50:00Z', last_message_at: '2026-04-14T12:20:00Z', message_count: 7, channel: 'whatsapp', context_type: 'Funcionario', last_sentiment: 'positive' },
      { id: 'c7', contact_name: 'Camila Rodrigues Lima', contact_phone: '5511994332109', status: 'active', started_at: '2026-04-14T11:20:00Z', last_message_at: '2026-04-14T11:45:00Z', message_count: 3, channel: 'whatsapp', context_type: 'Aluno', last_sentiment: null },
      { id: 'c8', contact_name: 'Thiago Nascimento', contact_phone: '5511993221098', status: 'closed', started_at: '2026-04-14T10:00:00Z', last_message_at: '2026-04-14T10:30:00Z', message_count: 9, channel: 'whatsapp', context_type: 'Funcionario', last_sentiment: 'positive' },
    ],
    total: 312,
    page: 1,
    limit: 20,
  },

  '/api/v1/evasion/at-risk': {
    critical: 1,
    high: 1,
    medium: 1,
    low: 5,
    total_at_risk: 3,
    students: [
      { id: 's4', full_name: 'Maria Eduarda Oliveira', registration_number: '20241004', course: 'Direito', enrollment_status: 'active', evasion_risk_score: 82, evasion_risk_level: 'critical', evasion_factors: ['Média de notas crítica (3.8)', 'Frequência crítica (falta 35%)', '2 boleto(s) em atraso', 'Sentimento negativo recente'] },
      { id: 's3', full_name: 'Pedro Henrique Santos', registration_number: '20241003', course: 'Engenharia Civil', enrollment_status: 'active', evasion_risk_score: 65, evasion_risk_level: 'high', evasion_factors: ['Média de notas crítica (4.2)', 'Frequência crítica (falta 28%)', '1 boleto em atraso'] },
      { id: 's5', full_name: 'Rafael Almeida Souza', registration_number: '20241005', course: 'Ciencia da Computacao', enrollment_status: 'active', evasion_risk_score: 40, evasion_risk_level: 'medium', evasion_factors: ['Média de notas abaixo do ideal (5.8)', '1 boleto em atraso'] },
    ],
  },

  '/api/v1/push-subscriptions/vapid-public-key': {
    public_key: '',
    enabled: false,
  },

  '/api/v1/conversations/c1': {
    id: 'c1', contact_name: 'Ana Carolina Silva', contact_phone: '5511999881234', contact_type: 'student',
    status: 'active', started_at: '2026-04-14T14:20:00Z', last_message_at: '2026-04-14T14:32:00Z', created_at: '2026-04-14T14:20:00Z', message_count: 8, channel: 'whatsapp', context_type: 'Aluno',
    messages: [
      { id: 'm1', sender_type: 'user', content: 'Oi, preciso ver minhas notas do semestre', created_at: '2026-04-14T14:20:00Z', intent: 'grade_query' },
      { id: 'm2', sender_type: 'bot', content: 'Oi, Ana! Vou puxar suas notas aqui.\n\n- Calculo I - P1: 7.5 | P2: 8.0\n- Programacao Web - P1: 9.0 | P2: 8.5\n- Banco de Dados - P1: 6.5 | P2: 7.0\n- Eng. Software - P1: 8.0 | P2: 9.0\n\nVoce ta indo super bem! Quer ver frequencia ou boletos?', created_at: '2026-04-14T14:20:05Z', intent: 'grade_query' },
      { id: 'm3', sender_type: 'user', content: 'Quero ver os boletos', created_at: '2026-04-14T14:22:00Z', intent: 'boleto_query' },
      { id: 'm4', sender_type: 'bot', content: 'Seus boletos, Ana:\n\n- Marco/2026: R$ 1.450,00 - Pago\n- Abril/2026: R$ 1.450,00 - Vencimento 15/04/2026 - Pendente\n\nQuer que eu gere o link de pagamento pro de abril?', created_at: '2026-04-14T14:22:04Z', intent: 'boleto_query' },
      { id: 'm5', sender_type: 'user', content: 'Sim, gera por favor', created_at: '2026-04-14T14:25:00Z', intent: 'generate_pix' },
      { id: 'm6', sender_type: 'bot', content: 'Aqui esta o link pra pagar:\n\nhttps://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=123456\n\nValor: R$ 1.450,00\nAceita PIX, cartao de credito/debito e boleto.\n\nPrecisa de mais alguma coisa?', created_at: '2026-04-14T14:25:06Z', intent: 'generate_pix' },
      { id: 'm7', sender_type: 'user', content: 'So isso, obrigada!', created_at: '2026-04-14T14:30:00Z', intent: 'farewell' },
      { id: 'm8', sender_type: 'bot', content: 'Que bom que pude ajudar! Me da uma nota de 1 a 5 pro atendimento? 1 = ruim, 5 = excelente', created_at: '2026-04-14T14:30:03Z', intent: 'farewell' },
    ],
  },
  '/api/v1/conversations/c2': {
    id: 'c2', contact_name: 'Pedro Henrique Santos', contact_phone: '5511998774321', contact_type: 'student',
    status: 'active', started_at: '2026-04-14T14:10:00Z', last_message_at: '2026-04-14T14:28:00Z', created_at: '2026-04-14T14:10:00Z', message_count: 5, channel: 'whatsapp', context_type: 'Aluno',
    messages: [
      { id: 'm10', sender_type: 'user', content: 'Ola, quero ver minha frequencia', created_at: '2026-04-14T14:10:00Z', intent: 'attendance_query' },
      { id: 'm11', sender_type: 'bot', content: 'Oi, Pedro! Sua frequencia do semestre:\n\n- Resistencia dos Materiais: 90% (4 faltas)\n- Calculo III: 85% (6 faltas)\n- Topografia: 95% (2 faltas)\n- Mecanica dos Solos: 70% (12 faltas) ⚠️\n\nAtencao em Mecanica dos Solos — ta perto do limite de 25%!', created_at: '2026-04-14T14:10:04Z', intent: 'attendance_query' },
      { id: 'm12', sender_type: 'user', content: 'Quantas faltas posso ter ainda em mecanica?', created_at: '2026-04-14T14:15:00Z', intent: 'attendance_query' },
      { id: 'm13', sender_type: 'bot', content: 'Em Mecanica dos Solos voce tem 12 faltas de 40 aulas. O limite e 25% (10 faltas). Voce ja ultrapassou o limite! Recomendo conversar com o professor ou ir na secretaria pra verificar se tem algum abono pendente.', created_at: '2026-04-14T14:15:04Z', intent: 'attendance_query' },
      { id: 'm14', sender_type: 'user', content: 'Obrigado, vou resolver isso', created_at: '2026-04-14T14:28:00Z', intent: 'farewell' },
    ],
  },
  '/api/v1/conversations/c3': {
    id: 'c3', contact_name: 'Maria Eduarda Oliveira', contact_phone: '5511997665432', contact_type: 'student',
    status: 'active', assigned_agent_id: 'agent-carlos-001', started_at: '2026-04-14T13:50:00Z', last_message_at: '2026-04-14T14:15:00Z', created_at: '2026-04-14T13:50:00Z', message_count: 6, channel: 'whatsapp', context_type: 'Aluno',
    messages: [
      { id: 'm20', sender_type: 'user', content: 'Preciso falar com alguem da secretaria', created_at: '2026-04-14T13:50:00Z', intent: 'handoff' },
      { id: 'm21', sender_type: 'bot', content: 'Entendi, Maria! Vou transferir voce para um atendente humano. Um momento, por favor.', created_at: '2026-04-14T13:50:03Z', intent: 'handoff' },
      { id: 'm22', sender_type: 'bot', content: 'Ticket criado! Protocolo: TKT-2026-0847\nUm agente vai te responder em breve.', created_at: '2026-04-14T13:50:05Z', intent: 'handoff' },
      { id: 'm23', sender_type: 'user', content: 'E sobre minha matricula que ta bloqueada', created_at: '2026-04-14T14:00:00Z', intent: 'general_query' },
      { id: 'm24', sender_type: 'user', content: 'Tem alguem ai?', created_at: '2026-04-14T14:10:00Z', intent: 'general_query' },
      { id: 'm25', sender_type: 'agent', content: 'Oi Maria! Sou o Carlos da secretaria. Vou verificar sua matricula agora. Pode me passar seu RA?', created_at: '2026-04-14T14:15:00Z', intent: 'agent_response' },
    ],
  },
  '/api/v1/conversations/c4': {
    id: 'c4', contact_name: 'Lucas Oliveira Silva', contact_phone: '5511997791909', contact_type: 'student',
    status: 'active', started_at: '2026-04-14T13:30:00Z', last_message_at: '2026-04-14T13:55:00Z', created_at: '2026-04-14T13:30:00Z', message_count: 4, channel: 'whatsapp', context_type: 'Aluno',
    messages: [
      { id: 'm30', sender_type: 'user', content: 'Quero agendar atendimento presencial', created_at: '2026-04-14T13:30:00Z', intent: 'schedule_appointment' },
      { id: 'm31', sender_type: 'bot', content: 'Claro, Lucas! Horarios disponiveis para esta semana:\n\n- Terca 15/04: 09:00, 10:30, 14:00\n- Quarta 16/04: 08:00, 11:00, 15:30\n- Quinta 17/04: 09:00, 14:00, 16:30\n\nQual horario voce prefere?', created_at: '2026-04-14T13:30:05Z', intent: 'schedule_appointment' },
      { id: 'm32', sender_type: 'user', content: 'Quarta as 11h', created_at: '2026-04-14T13:45:00Z', intent: 'schedule_appointment' },
      { id: 'm33', sender_type: 'bot', content: 'Agendado! Seu atendimento presencial:\n\nData: Quarta, 16/04/2026 as 11:00\nLocal: Secretaria Academica\nProtocolo: AGD-2026-0312\n\nChegue 5 minutos antes. Precisa de mais alguma coisa?', created_at: '2026-04-14T13:45:04Z', intent: 'schedule_appointment' },
    ],
  },
  '/api/v1/conversations/c5': {
    id: 'c5', contact_name: 'Juliana Costa Ferreira', contact_phone: '5511996554321', contact_type: 'student',
    status: 'closed', started_at: '2026-04-14T13:10:00Z', last_message_at: '2026-04-14T13:40:00Z', created_at: '2026-04-14T13:10:00Z', message_count: 4, channel: 'whatsapp', context_type: 'Aluno',
    messages: [
      { id: 'm40', sender_type: 'user', content: 'Quais os horarios da biblioteca?', created_at: '2026-04-14T13:10:00Z', intent: 'schedule_query' },
      { id: 'm41', sender_type: 'bot', content: 'Oi, Juliana! A biblioteca funciona:\n\n- Segunda a Sexta: 07:30 as 21:30\n- Sabado: 08:00 as 12:00\n- Domingo e feriados: Fechada\n\nPrecisa de mais alguma coisa?', created_at: '2026-04-14T13:10:04Z', intent: 'schedule_query' },
      { id: 'm42', sender_type: 'user', content: 'Nao, obrigada!', created_at: '2026-04-14T13:35:00Z', intent: 'farewell' },
      { id: 'm43', sender_type: 'bot', content: 'Que bom que pude ajudar! Me da uma nota de 1 a 5 pro atendimento? 1 = ruim, 5 = excelente', created_at: '2026-04-14T13:35:03Z', intent: 'farewell' },
    ],
  },
  '/api/v1/conversations/c6': {
    id: 'c6', contact_name: 'Rafael Almeida Souza', contact_phone: '5511995443210', contact_type: 'employee',
    status: 'closed', started_at: '2026-04-14T11:50:00Z', last_message_at: '2026-04-14T12:20:00Z', created_at: '2026-04-14T11:50:00Z', message_count: 4, channel: 'whatsapp', context_type: 'Funcionario',
    messages: [
      { id: 'm50', sender_type: 'user', content: 'Preciso do meu holerite de marco', created_at: '2026-04-14T11:50:00Z', intent: 'payslip_query' },
      { id: 'm51', sender_type: 'bot', content: 'Oi, Rafael! Seu holerite de Marco/2026:\n\nSalario Bruto: R$ 4.200,00\nINSS: -R$ 378,00\nIRRF: -R$ 142,80\nVale Transporte: -R$ 252,00\nSalario Liquido: R$ 3.427,20\n\nQuer que eu envie o PDF?', created_at: '2026-04-14T11:50:05Z', intent: 'payslip_query' },
      { id: 'm52', sender_type: 'user', content: 'Nao precisa, era so conferir. Valeu!', created_at: '2026-04-14T12:15:00Z', intent: 'farewell' },
      { id: 'm53', sender_type: 'bot', content: 'Tranquilo! Me da uma nota de 1 a 5 pro atendimento? 1 = ruim, 5 = excelente', created_at: '2026-04-14T12:15:03Z', intent: 'farewell' },
    ],
  },
  '/api/v1/conversations/c7': {
    id: 'c7', contact_name: 'Camila Rodrigues Lima', contact_phone: '5511994332109', contact_type: 'student',
    status: 'active', started_at: '2026-04-14T11:20:00Z', last_message_at: '2026-04-14T11:45:00Z', created_at: '2026-04-14T11:20:00Z', message_count: 3, channel: 'whatsapp', context_type: 'Aluno',
    messages: [
      { id: 'm60', sender_type: 'user', content: 'Oi, como faco pra pedir meu historico escolar?', created_at: '2026-04-14T11:20:00Z', intent: 'document_query' },
      { id: 'm61', sender_type: 'bot', content: 'Oi, Camila! Para solicitar o historico escolar:\n\n1. Acesse o portal do aluno\n2. Va em Documentos > Historico Escolar\n3. Clique em "Solicitar"\n\nO prazo e de 5 dias uteis. Taxa: R$ 15,00\n\nOu se preferir, posso abrir a solicitacao aqui mesmo!', created_at: '2026-04-14T11:20:04Z', intent: 'document_query' },
      { id: 'm62', sender_type: 'user', content: 'Abre pra mim aqui mesmo', created_at: '2026-04-14T11:45:00Z', intent: 'document_query' },
    ],
  },
  '/api/v1/conversations/c8': {
    id: 'c8', contact_name: 'Thiago Nascimento', contact_phone: '5511993221098', contact_type: 'employee',
    status: 'closed', started_at: '2026-04-14T10:00:00Z', last_message_at: '2026-04-14T10:30:00Z', created_at: '2026-04-14T10:00:00Z', message_count: 6, channel: 'whatsapp', context_type: 'Funcionario',
    messages: [
      { id: 'm70', sender_type: 'user', content: 'Bom dia, quero solicitar ferias', created_at: '2026-04-14T10:00:00Z', intent: 'vacation_request' },
      { id: 'm71', sender_type: 'bot', content: 'Bom dia, Thiago! Vou verificar seu saldo de ferias.\n\nVoce tem 20 dias disponiveis.\nPeriodo aquisitivo: 15/03/2025 a 14/03/2026\n\nQual periodo voce gostaria de tirar ferias?', created_at: '2026-04-14T10:00:05Z', intent: 'vacation_request' },
      { id: 'm72', sender_type: 'user', content: '01/06 a 20/06', created_at: '2026-04-14T10:05:00Z', intent: 'vacation_request' },
      { id: 'm73', sender_type: 'bot', content: 'Solicitacao registrada!\n\nPeriodo: 01/06/2026 a 20/06/2026 (20 dias)\nProtocolo: FER-2026-0089\nStatus: Aguardando aprovacao do gestor\n\nVoce recebera uma notificacao quando for aprovada. Mais alguma coisa?', created_at: '2026-04-14T10:05:04Z', intent: 'vacation_request' },
      { id: 'm74', sender_type: 'user', content: 'Nao, era so isso. Obrigado!', created_at: '2026-04-14T10:25:00Z', intent: 'farewell' },
      { id: 'm75', sender_type: 'bot', content: 'De nada, Thiago! Me da uma nota de 1 a 5 pro atendimento? 1 = ruim, 5 = excelente', created_at: '2026-04-14T10:25:03Z', intent: 'farewell' },
    ],
  },

  '/api/v1/tickets': {
    items: [
      { id: 't1', protocol_number: 'TKT-2026-0847', subject: 'Solicitacao de atendimento humano', status: 'open', priority: 'medium', created_at: '2026-04-14T14:15:00Z', sla_deadline: '2026-04-14T18:15:00Z', assigned_to_name: null, contact_name: 'Maria Eduarda Oliveira' },
      { id: 't2', protocol_number: 'TKT-2026-0846', subject: 'Chamado de Infraestrutura', status: 'in_progress', priority: 'high', created_at: '2026-04-14T10:30:00Z', sla_deadline: '2026-04-14T14:30:00Z', assigned_to_name: 'Suporte 1', contact_name: 'Prof. Andre Silva' },
      { id: 't3', protocol_number: 'TKT-2026-0845', subject: 'Problema com matricula', status: 'open', priority: 'critical', created_at: '2026-04-14T09:00:00Z', sla_deadline: '2026-04-14T11:00:00Z', assigned_to_name: null, contact_name: 'Rafael Almeida Souza' },
      { id: 't4', protocol_number: 'TKT-2026-0844', subject: 'Duvida sobre boleto', status: 'resolved', priority: 'low', created_at: '2026-04-13T16:00:00Z', sla_deadline: '2026-04-14T16:00:00Z', assigned_to_name: 'Suporte 2', contact_name: 'Juliana Costa' },
      { id: 't5', protocol_number: 'TKT-2026-0843', subject: 'Erro no sistema de notas', status: 'resolved', priority: 'high', created_at: '2026-04-13T11:00:00Z', sla_deadline: '2026-04-13T15:00:00Z', assigned_to_name: 'Suporte 1', contact_name: 'Pedro Santos' },
      { id: 't6', protocol_number: 'TKT-2026-0842', subject: 'Solicitacao de historico escolar', status: 'closed', priority: 'low', created_at: '2026-04-12T14:00:00Z', sla_deadline: '2026-04-13T14:00:00Z', assigned_to_name: 'Suporte 2', contact_name: 'Ana Carolina Silva' },
    ],
    total: 847,
    page: 1,
    limit: 20,
  },

  '/api/v1/students': {
    items: [
      { id: 's1', registration_number: '20241001', full_name: 'Lucas Oliveira Silva', course: 'Ciencia da Computacao', semester: 4, enrollment_status: 'active', email: 'lucas.silva@aluno.anchieta.edu.br', evasion_risk_score: 0, evasion_risk_level: 'low' },
      { id: 's2', registration_number: '20241002', full_name: 'Ana Carolina Silva', course: 'Administracao', semester: 6, enrollment_status: 'active', email: 'ana.silva@aluno.anchieta.edu.br', evasion_risk_score: 0, evasion_risk_level: 'low' },
      { id: 's3', registration_number: '20241003', full_name: 'Pedro Henrique Santos', course: 'Engenharia Civil', semester: 3, enrollment_status: 'active', email: 'pedro.santos@aluno.anchieta.edu.br', evasion_risk_score: 65, evasion_risk_level: 'high', evasion_factors: '["Média de notas crítica (4.2)","Frequência crítica (falta 28%)","1 boleto em atraso"]' },
      { id: 's4', registration_number: '20241004', full_name: 'Maria Eduarda Oliveira', course: 'Direito', semester: 8, enrollment_status: 'active', email: 'maria.oliveira@aluno.anchieta.edu.br', evasion_risk_score: 82, evasion_risk_level: 'critical', evasion_factors: '["Média de notas crítica (3.8)","Frequência crítica (falta 35%)","2 boleto(s) em atraso","Sentimento negativo recente"]' },
      { id: 's5', registration_number: '20241005', full_name: 'Rafael Almeida Souza', course: 'Ciencia da Computacao', semester: 2, enrollment_status: 'active', email: 'rafael.souza@aluno.anchieta.edu.br', evasion_risk_score: 40, evasion_risk_level: 'medium', evasion_factors: '["Média de notas abaixo do ideal (5.8)","1 boleto em atraso"]' },
      { id: 's6', registration_number: '20231015', full_name: 'Juliana Costa Ferreira', course: 'Psicologia', semester: 5, enrollment_status: 'active', email: 'juliana.ferreira@aluno.anchieta.edu.br', evasion_risk_score: 0, evasion_risk_level: 'low' },
      { id: 's7', registration_number: '20231020', full_name: 'Thiago Nascimento Lima', course: 'Administracao', semester: 7, enrollment_status: 'active', email: 'thiago.lima@aluno.anchieta.edu.br', evasion_risk_score: 0, evasion_risk_level: 'low' },
      { id: 's8', registration_number: '20221008', full_name: 'Camila Rodrigues Santos', course: 'Engenharia Civil', semester: 10, enrollment_status: 'graduated', email: 'camila.santos@aluno.anchieta.edu.br', evasion_risk_score: 0, evasion_risk_level: 'low' },
    ],
    total: 847,
    page: 1,
    limit: 20,
  },

  '/api/v1/students/s1': {
    id: 's1',
    registration_number: '20241001',
    full_name: 'Lucas Oliveira Silva',
    course: 'Ciencia da Computacao',
    semester: 4,
    enrollment_status: 'active',
    email: 'lucas.silva@aluno.anchieta.edu.br',
    phone: '5511997791909',
    cpf: '***.***.***-01',
  },

  '/api/v1/employees': {
    items: [
      { id: 'e1', employee_number: 'FUNC001', full_name: 'Carlos Eduardo Martins', department: 'Secretaria Academica', position: 'Coordenador', status: 'active' },
      { id: 'e2', employee_number: 'FUNC002', full_name: 'Patricia Souza Lima', department: 'Financeiro', position: 'Analista Financeiro', status: 'active' },
      { id: 'e3', employee_number: 'FUNC003', full_name: 'Roberto Alves Costa', department: 'TI', position: 'Suporte Tecnico', status: 'active' },
      { id: 'e4', employee_number: 'FUNC004', full_name: 'Fernanda Oliveira Santos', department: 'RH', position: 'Analista de RH', status: 'active' },
      { id: 'e5', employee_number: 'FUNC005', full_name: 'Marcos Pereira Silva', department: 'Biblioteca', position: 'Bibliotecario', status: 'active' },
    ],
    total: 62,
    page: 1,
    limit: 20,
  },

  '/api/v1/employees/e1': {
    id: 'e1',
    employee_number: 'FUNC001',
    full_name: 'Carlos Eduardo Martins',
    department: 'Secretaria Academica',
    position: 'Coordenador',
    status: 'active',
    email: 'carlos.martins@anchieta.edu.br',
    phone: '5511998001234',
    hire_date: '2019-03-15',
    cpf: '***.***.***-45',
  },

  '/api/v1/kb/articles': [
    { id: 'kb1', title: 'Como solicitar 2a via de boleto', category: 'Financeiro', content: 'Para solicitar a 2a via do boleto, envie "boleto" pelo WhatsApp para a Billie. Ela vai gerar automaticamente o link de pagamento via Mercado Pago.', applies_to: 'student', usage_count: 342 },
    { id: 'kb2', title: 'Horarios de atendimento da secretaria', category: 'Geral', content: 'A secretaria funciona de segunda a sexta, das 8h as 18h. Sabados das 8h ao meio-dia.', applies_to: 'all', usage_count: 289 },
    { id: 'kb3', title: 'Como consultar notas pelo sistema', category: 'Academico', content: 'Acesse o portal do aluno ou envie "notas" pelo WhatsApp para a Billie.', applies_to: 'student', usage_count: 256 },
    { id: 'kb4', title: 'Processo de rematricula', category: 'Academico', content: 'A rematricula acontece nos meses de janeiro e julho. Verifique o calendario academico.', applies_to: 'student', usage_count: 198 },
    { id: 'kb5', title: 'Como solicitar ferias', category: 'RH', content: 'O funcionario deve solicitar ferias com 30 dias de antecedencia pelo WhatsApp ou diretamente ao RH.', applies_to: 'employee', usage_count: 87 },
    { id: 'kb6', title: 'Canais de pagamento aceitos', category: 'Financeiro', content: 'Aceitamos PIX, cartao de credito, cartao de debito e boleto bancario via Mercado Pago.', applies_to: 'student', usage_count: 156 },
    { id: 'kb7', title: 'Agendamento presencial', category: 'Geral', content: 'Para agendar atendimento presencial, envie "agendar" pelo WhatsApp. Horarios disponiveis de segunda a sexta.', applies_to: 'all', usage_count: 73 },
  ],

  '/api/v1/metrics/dashboard': {
    total_interactions: 3842,
    comparison: {
      by_responder_type: {
        bot: { avg_response_time_seconds: 2.8, total_interactions: 3456, resolution_rate: 87.3, avg_satisfaction: 4.6 },
        human: { avg_response_time_seconds: 480, total_interactions: 386, resolution_rate: 94.1, avg_satisfaction: 4.3 },
      },
    },
    roi: {
      bot_interactions: 3456,
      human_interactions: 386,
      ai_monthly_cost: 420,
      human_monthly_cost: 8200,
      hypothetical_full_human_cost: 26800,
      monthly_savings: 18400,
      savings_percentage: 68.7,
      avg_time_saved_per_interaction_seconds: 252,
    },
    learning_stats: {
      total_resolutions: 1847,
      avg_satisfaction: 4.6,
      avg_resolution_time_seconds: 145,
      top_categories: [
        { category: 'Consulta de Notas', count: 523 },
        { category: 'Boletos e Pagamentos', count: 412 },
        { category: 'Horarios e Grade', count: 298 },
        { category: 'Documentos', count: 234 },
        { category: 'Matricula', count: 189 },
        { category: 'Ferias e RH', count: 112 },
        { category: 'Outros', count: 79 },
      ],
    },
  },

  '/api/v1/metrics/monitored-accounts': [],

  '/api/v1/learning/insights': {
    total_resolutions: 1847,
    avg_satisfaction: 4.6,
    avg_resolution_time: 145,
    categories: [
      { name: 'Consulta de Notas', count: 523, percentage: 28.3 },
      { name: 'Boletos e Pagamentos', count: 412, percentage: 22.3 },
      { name: 'Horarios e Grade', count: 298, percentage: 16.1 },
      { name: 'Documentos', count: 234, percentage: 12.7 },
      { name: 'Matricula', count: 189, percentage: 10.2 },
      { name: 'Outros', count: 191, percentage: 10.3 },
    ],
  },

  '/api/v1/tenants/settings/current': {
    bot_name: 'Billie',
    welcome_message: 'Oi! Sou a Billie, do atendimento da Faculdade Anchieta.',
    business_hours_start: '08:00',
    business_hours_end: '18:00',
    out_of_hours_message: 'Nosso horario de atendimento e de 8h as 18h.',
    has_whatsapp_config: true,
    has_ai_key: true,
  },

  '/api/v1/tenants': [
    {
      id: 'tenant-001',
      name: 'Faculdade Anchieta',
      slug: 'anchieta',
      plan: 'pro',
      is_active: true,
      whatsapp_phone: '+55 11 99888-1234',
    },
    {
      id: 'tenant-002',
      name: 'Colegio Novo Tempo',
      slug: 'novo-tempo',
      plan: 'basic',
      is_active: true,
      whatsapp_phone: '+55 11 97777-5555',
    },
    {
      id: 'tenant-003',
      name: 'Instituto Aurora',
      slug: 'aurora',
      plan: 'enterprise',
      is_active: false,
      whatsapp_phone: null,
    },
  ],

  '/api/v1/report-subscriptions': [
    {
      id: 'sub-1',
      name: 'Relatório Diretor',
      period: 'weekly',
      recipients: ['diretor@anchieta.edu.br', 'secretaria@anchieta.edu.br'],
      is_active: true,
      send_hour_utc: 11,
      last_sent_at: '2026-04-22T11:00:00Z',
      created_at: '2026-02-15T10:00:00Z',
    },
    {
      id: 'sub-2',
      name: 'KPIs Diarios Coordenacao',
      period: 'daily',
      recipients: ['coordenacao@anchieta.edu.br'],
      is_active: true,
      send_hour_utc: 11,
      last_sent_at: '2026-04-23T11:00:00Z',
      created_at: '2026-03-01T09:00:00Z',
    },
    {
      id: 'sub-3',
      name: 'Resumo Mensal Financeiro',
      period: 'monthly',
      recipients: ['financeiro@anchieta.edu.br'],
      is_active: false,
      send_hour_utc: 13,
      last_sent_at: '2026-04-01T13:00:00Z',
      created_at: '2026-01-10T14:00:00Z',
    },
  ],

  '/api/v1/integrations/providers': [
    {
      type: 'sophia',
      label: 'Sophia (Prima)',
      description: 'ERP educacional usado em faculdades de medio/grande porte',
      config_fields: [
        { name: 'base_url', label: 'URL base', type: 'url', required: true, placeholder: 'https://escola.sophia.com.br' },
        { name: 'tenant_code', label: 'Codigo da instituicao', type: 'text' },
      ],
      credential_fields: [
        { name: 'auth.token', label: 'API Token', type: 'password', required: true },
      ],
    },
    {
      type: 'totvs',
      label: 'TOTVS RM Educacional',
      description: 'Modulo educacional do TOTVS RM',
      config_fields: [
        { name: 'base_url', label: 'URL base', type: 'url', required: true, placeholder: 'https://escola.totvs.com.br/api/framework/v1' },
        { name: 'coligada', label: 'Codigo da Coligada (CODCOLIGADA)', type: 'text', required: true, placeholder: '1' },
      ],
      credential_fields: [
        { name: 'username', label: 'Usuario RM', type: 'text', required: true },
        { name: 'password', label: 'Senha RM', type: 'password', required: true },
      ],
    },
    {
      type: 'generic_rest',
      label: 'REST Generico',
      description: 'Configure URL e credenciais para qualquer sistema com API JSON',
      config_fields: [
        { name: 'base_url', label: 'URL base', type: 'url', required: true },
        { name: 'students_endpoint', label: 'Endpoint de alunos', type: 'text', placeholder: '/api/students' },
        { name: 'employees_endpoint', label: 'Endpoint de funcionarios', type: 'text', placeholder: '/api/employees' },
      ],
      credential_fields: [
        { name: 'auth.type', label: 'Tipo de autenticacao', type: 'select', options: ['bearer', 'basic', 'header'], default: 'bearer' },
        { name: 'auth.token', label: 'Token (bearer)', type: 'password' },
      ],
    },
  ],

  '/api/v1/integrations': [
    {
      id: 'int-1',
      name: 'Sophia Producao',
      provider_type: 'sophia',
      config: { base_url: 'https://anchieta.sophia.com.br', tenant_code: 'ANCHIETA' },
      has_credentials: true,
      status: 'active',
      sync_cron: '0 */6 * * *',
      last_sync_at: '2026-04-27T06:15:00Z',
      last_sync_duration_ms: 12340,
      last_sync_records_synced: 847,
      last_sync_error: null,
      created_at: '2026-04-15T10:00:00Z',
    },
    {
      id: 'int-2',
      name: 'TOTVS RH Funcionarios',
      provider_type: 'totvs',
      config: { base_url: 'https://anchieta.totvs.com.br/api/framework/v1', coligada: '1' },
      has_credentials: true,
      status: 'paused',
      sync_cron: '0 6 * * *',
      last_sync_at: '2026-04-26T06:00:00Z',
      last_sync_duration_ms: 5210,
      last_sync_records_synced: 62,
      last_sync_error: null,
      created_at: '2026-04-20T15:00:00Z',
    },
  ],

  '/api/v1/admin/ai-health': {
    overall: 'healthy',
    healthy_count: 3,
    total_providers: 3,
    has_critical: false,
    has_degraded: false,
    checked_at: Date.now() / 1000,
    cached: false,
    providers: [
      { name: 'anthropic', state: 'healthy', detail: '', latency_ms: 412, circuit_open: false, circuit_failures: 0, checked_at: Date.now() / 1000 },
      { name: 'groq', state: 'healthy', detail: '', latency_ms: 187, circuit_open: false, circuit_failures: 0, checked_at: Date.now() / 1000 },
      { name: 'gemini', state: 'healthy', detail: '', latency_ms: 521, circuit_open: false, circuit_failures: 0, checked_at: Date.now() / 1000 },
    ],
  },

  '/api/v1/slides/presentations': {
    items: [
      {
        id: 'sl1', title: 'Introducao a Algoritmos', subject: 'Programacao I', total_slides: 4, version: 1, status: 'ready', created_at: '2026-04-10T10:00:00Z', updated_at: '2026-04-10T10:00:00Z', prompt_used: 'Crie uma aula introdutoria sobre algoritmos',
        slides_content: [
          { slide_number: 1, title: 'O que e um Algoritmo?', content: ['Sequencia finita de instrucoes', 'Resolve um problema especifico', 'Exemplo: receita de bolo'], layout: 'title_content', notes: 'Usar exemplos do dia a dia' },
          { slide_number: 2, title: 'Caracteristicas', content: ['Finitude — sempre termina', 'Entrada e saida definidas', 'Efetividade — passos executaveis', 'Generalidade — funciona para varias entradas'], layout: 'bullet_list' },
          { slide_number: 3, title: 'Pseudocodigo', content: ['INICIO', '  LEIA numero', '  SE numero > 0 ENTAO', '    ESCREVA "Positivo"', '  SENAO', '    ESCREVA "Negativo"', '  FIM SE', 'FIM'], layout: 'code' },
          { slide_number: 4, title: 'Exercicios', content: ['Escreva um algoritmo para calcular a media de 3 notas', 'Escreva um algoritmo para verificar se um numero e par', 'Desafio: algoritmo de ordenacao por selecao'], layout: 'bullet_list', notes: 'Tempo estimado: 20 min' },
        ],
      },
      {
        id: 'sl2', title: 'Estruturas de Dados: Listas e Filas', subject: 'Estrutura de Dados', total_slides: 3, version: 2, status: 'ready', created_at: '2026-04-08T14:00:00Z', updated_at: '2026-04-09T09:00:00Z', prompt_used: 'Aula sobre listas e filas',
        slides_content: [
          { slide_number: 1, title: 'Listas Encadeadas', content: ['Cada no aponta para o proximo', 'Insercao e remocao em O(1)', 'Busca em O(n)'], layout: 'title_content' },
          { slide_number: 2, title: 'Filas (Queue)', content: ['FIFO — First In, First Out', 'Operacoes: enqueue, dequeue, peek', 'Exemplo: fila de impressao'], layout: 'bullet_list' },
          { slide_number: 3, title: 'Comparativo', content: ['Array vs Lista: acesso vs insercao', 'Fila vs Pilha: FIFO vs LIFO', 'Quando usar cada estrutura'], layout: 'comparison' },
        ],
      },
      {
        id: 'sl3', title: 'Normalizacao de Bancos de Dados', subject: 'Banco de Dados II', total_slides: 3, version: 1, status: 'ready', created_at: '2026-04-05T09:00:00Z', updated_at: '2026-04-05T09:00:00Z', prompt_used: 'Aula sobre normalizacao ate 3FN',
        slides_content: [
          { slide_number: 1, title: 'Por que Normalizar?', content: ['Eliminar redundancia de dados', 'Evitar anomalias de insercao/atualizacao/remocao', 'Garantir integridade referencial'], layout: 'title_content' },
          { slide_number: 2, title: '1FN, 2FN e 3FN', content: ['1FN: atributos atomicos, sem grupos repetidos', '2FN: 1FN + sem dependencias parciais', '3FN: 2FN + sem dependencias transitivas'], layout: 'bullet_list' },
          { slide_number: 3, title: 'Exemplo Pratico', content: ['Tabela desnormalizada: Pedido(id, cliente, cidade, produto, qtd)', 'Apos 1FN: separar produtos repetidos', 'Apos 3FN: tabela Cliente, Pedido, ItemPedido'], layout: 'code' },
        ],
      },
    ],
    total: 3,
  },

  '/api/v1/users': [
    { id: 'u1', full_name: 'Gabriel Bueno', email: 'admin@igs.com', role: 'super_admin' },
    { id: 'u2', full_name: 'Marcos Diretor', email: 'gestor@anchieta.edu.br', role: 'admin' },
    { id: 'u3', full_name: 'Suporte 1', email: 'suporte1@anchieta.edu.br', role: 'agent' },
    { id: 'u4', full_name: 'Suporte 2', email: 'suporte2@anchieta.edu.br', role: 'agent' },
    { id: 'u5', full_name: 'Prof. Andre Silva', email: 'prof.andre@anchieta.edu.br', role: 'teacher' },
  ],
}

// Student detail sub-data (served via dynamic routes)
const STUDENT_GRADES = [
  { subject_name: 'Calculo II', academic_period: '2026.1', grade_type: 'P1', grade_value: 7.5, status: 'in_progress' },
  { subject_name: 'Calculo II', academic_period: '2026.1', grade_type: 'P2', grade_value: 8.0, status: 'approved' },
  { subject_name: 'Programacao Web', academic_period: '2026.1', grade_type: 'P1', grade_value: 9.0, status: 'in_progress' },
  { subject_name: 'Programacao Web', academic_period: '2026.1', grade_type: 'P2', grade_value: 9.5, status: 'approved' },
  { subject_name: 'Banco de Dados II', academic_period: '2026.1', grade_type: 'P1', grade_value: 6.5, status: 'in_progress' },
  { subject_name: 'Banco de Dados II', academic_period: '2026.1', grade_type: 'P2', grade_value: 5.0, status: 'failed' },
  { subject_name: 'Engenharia de Software', academic_period: '2026.1', grade_type: 'P1', grade_value: 8.0, status: 'in_progress' },
  { subject_name: 'Engenharia de Software', academic_period: '2026.1', grade_type: 'P2', grade_value: 8.5, status: 'approved' },
  { subject_name: 'Redes de Computadores', academic_period: '2026.1', grade_type: 'P1', grade_value: 7.0, status: 'in_progress' },
]

const STUDENT_ATTENDANCE = [
  { subject_name: 'Calculo II', academic_period: '2026.1', total_classes: 40, attended: 36, absence_pct: 10.0 },
  { subject_name: 'Programacao Web', academic_period: '2026.1', total_classes: 40, attended: 38, absence_pct: 5.0 },
  { subject_name: 'Banco de Dados II', academic_period: '2026.1', total_classes: 40, attended: 28, absence_pct: 30.0 },
  { subject_name: 'Engenharia de Software', academic_period: '2026.1', total_classes: 40, attended: 34, absence_pct: 15.0 },
  { subject_name: 'Redes de Computadores', academic_period: '2026.1', total_classes: 40, attended: 37, absence_pct: 7.5 },
]

const STUDENT_BOLETOS = [
  { reference_month: '2026-01', amount: 1890.00, due_date: '2026-01-10', status: 'paid' },
  { reference_month: '2026-02', amount: 1890.00, due_date: '2026-02-10', status: 'paid' },
  { reference_month: '2026-03', amount: 1890.00, due_date: '2026-03-10', status: 'paid' },
  { reference_month: '2026-04', amount: 1890.00, due_date: '2026-04-10', status: 'pending' },
]

const EMPLOYEE_PAYSLIPS = [
  { reference_month: '2026-03', gross_salary: 4800.00, net_salary: 3890.00, deductions: 910.00, status: 'paid' },
  { reference_month: '2026-02', gross_salary: 4800.00, net_salary: 3890.00, deductions: 910.00, status: 'paid' },
  { reference_month: '2026-01', gross_salary: 4800.00, net_salary: 3890.00, deductions: 910.00, status: 'paid' },
]

const EMPLOYEE_VACATION = {
  total_days: 30,
  used_days: 12,
  remaining_days: 18,
  deadline_date: '2026-08-15',
}

const EMPLOYEE_REQUESTS = [
  { id: 'r1', request_type: 'ferias', status: 'approved', created_at: '2026-03-01T10:00:00Z', response_text: 'Aprovado para julho/2026' },
  { id: 'r2', request_type: 'declaracao', status: 'approved', created_at: '2026-02-15T14:00:00Z', response_text: 'Documento emitido e enviado por e-mail' },
  { id: 'r3', request_type: 'holerite', status: 'pending', created_at: '2026-04-10T09:00:00Z', response_text: null },
]

const SLIDES_TEMPLATES = [
  { id: 'tpl1', name: 'Aula Expositiva', description: 'Template para aulas teóricas com slides de conteúdo' },
  { id: 'tpl2', name: 'Exercicios Praticos', description: 'Template com enunciados e espaco para resolucao' },
  { id: 'tpl3', name: 'Revisao de Prova', description: 'Template para revisao com questoes modelo' },
]

// Map dynamic URLs to their mock data keys or inline data
const DYNAMIC_ROUTES: [RegExp, string | unknown][] = [
  [/^\/api\/v1\/conversations\/[^/]+$/, '__conversation_dynamic__'],
  [/^\/api\/v1\/students\/[^/]+\/grades$/, STUDENT_GRADES],
  [/^\/api\/v1\/students\/[^/]+\/attendance$/, STUDENT_ATTENDANCE],
  [/^\/api\/v1\/students\/[^/]+\/boletos$/, STUDENT_BOLETOS],
  [/^\/api\/v1\/students\/[^/]+$/, '/api/v1/students/s1'],
  [/^\/api\/v1\/employees\/[^/]+\/payslips$/, EMPLOYEE_PAYSLIPS],
  [/^\/api\/v1\/employees\/[^/]+\/vacation$/, EMPLOYEE_VACATION],
  [/^\/api\/v1\/employees\/[^/]+\/requests$/, EMPLOYEE_REQUESTS],
  [/^\/api\/v1\/employees\/[^/]+$/, '/api/v1/employees/e1'],
  [/^\/api\/v1\/slides\/templates$/, SLIDES_TEMPLATES],
  [/^\/api\/v1\/reports\/conversations/, new Blob(['id,contato,status,inicio,fim\nc1,Ana Carolina Silva,active,2026-04-14 14:20,2026-04-14 14:32\nc2,Pedro Henrique Santos,active,2026-04-14 14:10,2026-04-14 14:28\nc3,Maria Eduarda Oliveira,waiting_agent,2026-04-14 13:50,2026-04-14 14:15'], { type: 'text/csv' })],
  [/^\/api\/v1\/reports\/tickets/, new Blob(['protocolo,assunto,prioridade,status,criado\nTKT-2026-0847,Solicitacao de atendimento humano,medium,open,2026-04-14\nTKT-2026-0846,Chamado de Infraestrutura,high,in_progress,2026-04-14\nTKT-2026-0845,Problema com matricula,critical,open,2026-04-14'], { type: 'text/csv' })],
  [/^\/api\/v1\/onboarding\/templates\/students\.csv$/, new Blob(['registration_number,full_name,course,semester,enrollment_status,email,phone\n20241001,Ana Carolina Silva,Ciencia da Computacao,4,active,ana.silva@aluno.anchieta.edu.br,5511999881234\n20241002,Pedro Henrique Santos,Engenharia Civil,3,active,pedro.santos@aluno.anchieta.edu.br,5511998774321'], { type: 'text/csv' })],
  [/^\/api\/v1\/onboarding\/templates\/employees\.csv$/, new Blob(['employee_number,full_name,department,position,status,email,phone,hire_date\nFUNC001,Carlos Eduardo Martins,Secretaria Academica,Coordenador,active,carlos.martins@anchieta.edu.br,5511998001234,2019-03-15\nFUNC002,Patricia Souza Lima,Financeiro,Analista,active,patricia.lima@anchieta.edu.br,5511997442118,2021-08-01'], { type: 'text/csv' })],
]

function findMockData(url: string): unknown {
  const path = url.split('?')[0]

  // Exact match
  if (DEMO_DATA[path]) return DEMO_DATA[path]

  // Dynamic route matching
  for (const [pattern, target] of DYNAMIC_ROUTES) {
    if (pattern.test(path)) {
      if (target === '__conversation_dynamic__') {
        // Extract conversation ID from URL and look up its data
        const convId = path.split('/').pop()
        return DEMO_DATA[`/api/v1/conversations/${convId}`] || DEMO_DATA['/api/v1/conversations/c1']
      }
      return typeof target === 'string' ? DEMO_DATA[target] : target
    }
  }

  console.warn('[demo-mock] No mock for:', path)
  return { items: [], total: 0 }
}

function mockResponse(data: unknown): Promise<AxiosResponse> {
  return Promise.resolve({
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {} as any,
  })
}

export function enableDemoMock() {
  // Override api methods directly — most reliable approach
  const originalGet = api.get.bind(api)
  const originalPost = api.post.bind(api)

  api.get = ((url: string, config?: any) => {
    let data = findMockData(url)

    // Apply filters for list endpoints
    const params = config?.params
    if (params && data && typeof data === 'object' && 'items' in (data as any)) {
      const list = data as { items: any[]; total: number; page: number; limit: number }
      let filtered = [...list.items]

      if (params.status) {
        filtered = filtered.filter((item: any) => item.status === params.status)
      }
      if (params.search) {
        const q = params.search.toLowerCase()
        filtered = filtered.filter((item: any) =>
          Object.values(item).some((v) => typeof v === 'string' && v.toLowerCase().includes(q))
        )
      }

      data = { ...list, items: filtered, total: filtered.length }
    }

    return mockResponse(data)
  }) as typeof api.get

  api.post = ((url: string, body?: any, ..._args: any[]) => {
    // Handle KB article creation — persist to in-memory mock
    if (url === '/api/v1/kb/articles' && body) {
      const articles = DEMO_DATA['/api/v1/kb/articles'] as any[]
      const newArticle = {
        id: `kb${articles.length + 1}`,
        title: body.title || 'Sem titulo',
        category: body.category || 'Geral',
        content: body.content || '',
        applies_to: body.applies_to || 'all',
        usage_count: 0,
      }
      articles.push(newArticle)
      return mockResponse(newArticle)
    }

    // Onboarding: create new tenant + admin
    if (url === '/api/v1/onboarding/tenants' && body) {
      const tenants = DEMO_DATA['/api/v1/tenants'] as any[]
      const newTenant = {
        id: `tenant-${tenants.length + 1}`.padEnd(11, '0'),
        name: body.tenant_name,
        slug: body.tenant_slug,
        plan: body.plan || 'basic',
        is_active: true,
        whatsapp_phone: null,
      }
      tenants.push(newTenant)
      return mockResponse({
        tenant_id: newTenant.id,
        slug: newTenant.slug,
        admin_email: body.admin_email,
        admin_user_id: `user-${Date.now()}`,
        login_url: '/login',
      })
    }

    // Onboarding: import CSV (students/employees) — fake counts
    if (url.match(/\/api\/v1\/onboarding\/tenants\/[^/]+\/import-(students|employees)/)) {
      return mockResponse({
        created: 42,
        skipped: 3,
        errors: [],
      })
    }

    // WhatsApp test send
    if (url === '/api/v1/tenants/whatsapp/test') {
      return mockResponse({
        status: 'success',
        message: 'Mensagem de teste enviada (DEMO MODE — nenhuma mensagem real foi enviada)',
        whatsapp_msg_id: `demo-${Date.now()}`,
      })
    }

    // Force AI health re-check
    if (url === '/api/v1/admin/ai-health/check') {
      return mockResponse(findMockData('/api/v1/admin/ai-health'))
    }

    // Integrations: create
    if (url === '/api/v1/integrations' && body) {
      const list = DEMO_DATA['/api/v1/integrations'] as any[]
      const newInt = {
        id: `int-${list.length + 1}`,
        name: body.name,
        provider_type: body.provider_type,
        config: body.config || {},
        has_credentials: !!body.credentials && Object.keys(body.credentials).length > 0,
        status: 'pending',
        sync_cron: body.sync_cron || '0 */6 * * *',
        last_sync_at: null,
        last_sync_duration_ms: null,
        last_sync_records_synced: null,
        last_sync_error: null,
        created_at: new Date().toISOString(),
      }
      list.unshift(newInt)
      return mockResponse(newInt)
    }

    // Integrations: test connection
    if (url.match(/\/api\/v1\/integrations\/[^/]+\/test/)) {
      return mockResponse({
        success: true,
        message: 'OK (DEMO MODE — sem chamada real)',
      })
    }

    // Integrations: sync now
    if (url.match(/\/api\/v1\/integrations\/[^/]+\/sync-now/)) {
      return mockResponse({
        success: true,
        message: 'Sincronização agendada (DEMO MODE)',
      })
    }

    // Report subscriptions: create
    if (url === '/api/v1/report-subscriptions' && body) {
      const subs = DEMO_DATA['/api/v1/report-subscriptions'] as any[]
      const newSub = {
        id: `sub-${subs.length + 1}`,
        name: body.name,
        period: body.period,
        recipients: body.recipients,
        is_active: body.is_active ?? true,
        send_hour_utc: body.send_hour_utc ?? 11,
        last_sent_at: null,
        created_at: new Date().toISOString(),
      }
      subs.unshift(newSub)
      return mockResponse(newSub)
    }

    // Send now
    if (url.match(/\/api\/v1\/report-subscriptions\/[^/]+\/send-now/)) {
      return mockResponse({
        sent: 2,
        failed: [],
        subject: '[IGS] Relatorio Semanal - Faculdade Anchieta (3.842 conversas)',
        period: 'weekly',
      })
    }

    // Preview
    if (url === '/api/v1/report-subscriptions/preview') {
      return mockResponse({
        subject: '[IGS] Relatorio Semanal - Faculdade Anchieta (3.842 conversas)',
        kpis: {
          total_conversations: 3842,
          bot_resolutions: 3355,
          auto_resolution_rate: 87.3,
          avg_satisfaction: 4.6,
          open_tickets: 8,
          sla_breached: 1,
        },
        html: `
          <div style="font-family:sans-serif;max-width:640px;margin:0 auto">
            <div style="background:linear-gradient(135deg,#1d4ed8,#312e81);padding:32px;color:white;border-radius:12px 12px 0 0">
              <p style="margin:0;font-size:12px;letter-spacing:1px">IGS — Relatorio Semanal</p>
              <h1 style="margin:8px 0">Faculdade Anchieta</h1>
              <p style="margin:0;opacity:0.9">14/04/2026 a 21/04/2026 (DEMO)</p>
            </div>
            <div style="background:white;padding:24px;border:1px solid #e5e7eb">
              <h2>📊 KPIs do periodo</h2>
              <p>Conversas: <b>3.842</b> — <span style="color:#16a34a">▲ +22%</span></p>
              <p>Resolucao automatica: <b style="color:#16a34a">87,3%</b></p>
              <p>Satisfacao: <b>4,6/5</b></p>
              <p>Tickets abertos: <b>8</b> (1 com SLA violado)</p>
              <h3>🎯 Top assuntos</h3>
              <ul>
                <li>Consulta de notas — 523</li>
                <li>Boletos / pagamento — 412</li>
                <li>Horarios / grade — 298</li>
              </ul>
            </div>
          </div>
        `,
      })
    }

    // Conversations: take-over
    if (url.match(/\/api\/v1\/conversations\/[^/]+\/take-over/)) {
      const convId = url.split('/')[5]
      const conv = DEMO_DATA[`/api/v1/conversations/${convId}`] as any
      if (conv) {
        conv.assigned_agent_id = 'demo-001'
        conv.status = 'active'
      }
      return mockResponse({ ...conv })
    }

    // Conversations: release
    if (url.match(/\/api\/v1\/conversations\/[^/]+\/release/)) {
      const convId = url.split('/')[5]
      const conv = DEMO_DATA[`/api/v1/conversations/${convId}`] as any
      if (conv) {
        conv.assigned_agent_id = null
        conv.status = 'active'
      }
      return mockResponse({ ...conv })
    }

    // Conversations: agent message
    if (url.match(/\/api\/v1\/conversations\/[^/]+\/messages/) && body) {
      const msg = {
        id: `msg-${Date.now()}`,
        sender_type: 'agent',
        content: body.content,
        intent: null,
        created_at: new Date().toISOString(),
      }
      const convId = url.split('/')[5]
      const conv = DEMO_DATA[`/api/v1/conversations/${convId}`] as any
      if (conv?.messages) conv.messages.push(msg)
      return mockResponse(msg)
    }

    // Evasion: recalculate
    if (url === '/api/v1/evasion/recalculate') {
      return mockResponse({ status: 'queued' })
    }

    return mockResponse(findMockData(url))
  }) as typeof api.post

  api.put = ((url: string, ..._args: any[]) => {
    return mockResponse(findMockData(url))
  }) as typeof api.put

  api.patch = ((url: string, body?: any, ..._args: any[]) => {
    // Update report subscription
    const subMatch = url.match(/\/api\/v1\/report-subscriptions\/([^/]+)$/)
    if (subMatch && body) {
      const subs = DEMO_DATA['/api/v1/report-subscriptions'] as any[]
      const idx = subs.findIndex((s: any) => s.id === subMatch[1])
      if (idx !== -1) {
        subs[idx] = { ...subs[idx], ...body }
        return mockResponse(subs[idx])
      }
    }
    // Update integration
    const intMatch = url.match(/\/api\/v1\/integrations\/([^/]+)$/)
    if (intMatch && body) {
      const list = DEMO_DATA['/api/v1/integrations'] as any[]
      const idx = list.findIndex((i: any) => i.id === intMatch[1])
      if (idx !== -1) {
        list[idx] = { ...list[idx], ...body }
        return mockResponse(list[idx])
      }
    }
    return mockResponse(findMockData(url))
  }) as typeof api.patch

  api.delete = ((url: string, ..._args: any[]) => {
    // Handle KB article deletion
    const kbMatch = url.match(/\/api\/v1\/kb\/articles\/(.+)/)
    if (kbMatch) {
      const articles = DEMO_DATA['/api/v1/kb/articles'] as any[]
      const idx = articles.findIndex((a: any) => a.id === kbMatch[1])
      if (idx !== -1) articles.splice(idx, 1)
      return mockResponse({ success: true })
    }
    // Handle report subscription deletion
    const subMatch = url.match(/\/api\/v1\/report-subscriptions\/([^/]+)$/)
    if (subMatch) {
      const subs = DEMO_DATA['/api/v1/report-subscriptions'] as any[]
      const idx = subs.findIndex((s: any) => s.id === subMatch[1])
      if (idx !== -1) subs.splice(idx, 1)
      return mockResponse({ success: true })
    }
    // Handle integration deletion
    const intMatch = url.match(/\/api\/v1\/integrations\/([^/]+)$/)
    if (intMatch) {
      const list = DEMO_DATA['/api/v1/integrations'] as any[]
      const idx = list.findIndex((i: any) => i.id === intMatch[1])
      if (idx !== -1) list.splice(idx, 1)
      return mockResponse({ success: true })
    }
    return mockResponse(findMockData(url))
  }) as typeof api.delete

  // Suppress the original references to avoid linter warnings
  void originalGet
  void originalPost

  console.log('[demo-mock] Mock mode enabled — all API calls return demo data')
}
