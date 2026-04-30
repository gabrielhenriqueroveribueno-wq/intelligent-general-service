import { useState } from 'react'
import { FileText, Shield, Lock } from 'lucide-react'

type Tab = 'tos' | 'privacy' | 'dpa'

const LAST_UPDATED = '29 de abril de 2026'

function Tos() {
  return (
    <div className="prose prose-sm max-w-none text-gray-700 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Termos de Serviço</h2>
      <p className="text-xs text-gray-400">Última atualização: {LAST_UPDATED}</p>

      <h3 className="font-semibold">1. Aceitação dos Termos</h3>
      <p>
        Ao acessar ou usar o IGS — Intelligent General Service ("Serviço"), você concorda em ficar
        vinculado a estes Termos de Serviço. Se você não concordar com qualquer parte destes termos,
        não poderá usar o Serviço.
      </p>

      <h3 className="font-semibold">2. Descrição do Serviço</h3>
      <p>
        O IGS é uma plataforma SaaS de atendimento automatizado via WhatsApp destinada a
        instituições de ensino. O Serviço permite que instituições ofereçam respostas automáticas a
        alunos e funcionários sobre informações acadêmicas e de RH, utilizando inteligência
        artificial.
      </p>

      <h3 className="font-semibold">3. Cadastro e Conta</h3>
      <p>
        Para usar o Serviço, você deve criar uma conta fornecendo informações verdadeiras e
        completas. Você é responsável por manter a confidencialidade das suas credenciais de acesso
        e por todas as atividades realizadas em sua conta.
      </p>

      <h3 className="font-semibold">4. Uso Aceitável</h3>
      <p>Você concorda em não usar o Serviço para:</p>
      <ul className="list-disc pl-5 space-y-1">
        <li>Enviar mensagens de spam, enganosas ou ilegais</li>
        <li>Violar direitos de privacidade de terceiros</li>
        <li>Transmitir vírus, malware ou código prejudicial</li>
        <li>Tentar acessar sistemas ou dados não autorizados</li>
        <li>Realizar engenharia reversa ou extrair o código-fonte da plataforma</li>
      </ul>

      <h3 className="font-semibold">5. Planos e Pagamento</h3>
      <p>
        O Serviço é oferecido em diferentes planos (Trial, Starter, Pro, Enterprise). Os valores e
        condições de cada plano estão disponíveis na página de preços. O período de trial de 14
        dias não requer cartão de crédito. Após o trial, a contratação de plano pago é necessária
        para continuar usando o Serviço.
      </p>
      <p>
        Os pagamentos são mensais ou anuais, conforme acordado no contrato. O não pagamento dentro
        do prazo pode resultar na suspensão temporária do acesso.
      </p>

      <h3 className="font-semibold">6. Propriedade Intelectual</h3>
      <p>
        O Serviço e seu conteúdo original, funcionalidades e tecnologia são propriedade exclusiva da
        IGS e seus licenciadores. Os dados inseridos pelo cliente (alunos, funcionários,
        conversas) permanecem de propriedade do cliente.
      </p>

      <h3 className="font-semibold">7. Limitação de Responsabilidade</h3>
      <p>
        O IGS não se responsabiliza por danos indiretos, incidentais, especiais ou consequenciais
        decorrentes do uso ou incapacidade de usar o Serviço. Nossa responsabilidade total está
        limitada ao valor pago pelo cliente nos últimos 3 meses.
      </p>

      <h3 className="font-semibold">8. Rescisão</h3>
      <p>
        Qualquer parte pode rescindir o contrato com aviso prévio de 30 dias. Em caso de violação
        material destes termos, o IGS pode rescindir imediatamente sem aviso prévio.
      </p>

      <h3 className="font-semibold">9. Lei Aplicável</h3>
      <p>
        Estes termos são regidos pelas leis da República Federativa do Brasil. Fica eleito o foro
        da comarca de São Paulo/SP para dirimir quaisquer disputas.
      </p>

      <h3 className="font-semibold">10. Contato</h3>
      <p>
        Para dúvidas sobre estes termos, entre em contato: <strong>legal@igs.com.br</strong>
      </p>
    </div>
  )
}

function Privacy() {
  return (
    <div className="prose prose-sm max-w-none text-gray-700 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Política de Privacidade</h2>
      <p className="text-xs text-gray-400">Última atualização: {LAST_UPDATED}</p>

      <p>
        Esta Política de Privacidade descreve como o IGS coleta, usa, armazena e protege as
        informações pessoais em conformidade com a Lei Geral de Proteção de Dados (LGPD — Lei
        13.709/2018).
      </p>

      <h3 className="font-semibold">1. Dados Coletados</h3>
      <p>Coletamos os seguintes tipos de dados:</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Dados de conta</strong>: nome, e-mail, cargo dos usuários do painel</li>
        <li><strong>Dados de contato (WhatsApp)</strong>: número de telefone, nome, mensagens trocadas</li>
        <li><strong>Dados acadêmicos/RH</strong>: importados pelo cliente (notas, frequência, holerite etc.)</li>
        <li><strong>Dados de uso</strong>: logs de acesso, métricas de desempenho (sem PII)</li>
      </ul>

      <h3 className="font-semibold">2. Finalidade do Tratamento</h3>
      <p>Os dados são tratados para:</p>
      <ul className="list-disc pl-5 space-y-1">
        <li>Prestar o serviço de atendimento automatizado contratado</li>
        <li>Identificar e autenticar usuários do painel</li>
        <li>Gerar relatórios e métricas para o cliente</li>
        <li>Cumprir obrigações legais e regulatórias</li>
      </ul>

      <h3 className="font-semibold">3. Base Legal</h3>
      <p>
        O tratamento é baseado na execução de contrato (Art. 7°, V, LGPD) e no legítimo interesse
        do operador para fins de suporte técnico e segurança (Art. 7°, IX, LGPD).
      </p>

      <h3 className="font-semibold">4. Armazenamento e Segurança</h3>
      <p>
        Os dados são armazenados em servidores localizados no Brasil (região de São Paulo). Adotamos
        criptografia AES-256 em repouso e TLS 1.3 em trânsito. Dados sensíveis como CPF são
        armazenados com criptografia adicional (Fernet).
      </p>

      <h3 className="font-semibold">5. Compartilhamento de Dados</h3>
      <p>
        Não vendemos dados pessoais. Podemos compartilhar com subprocessadores (provedores de
        infraestrutura, API de IA) exclusivamente para prestação do serviço, sob cláusulas
        contratuais que garantem proteção equivalente.
      </p>

      <h3 className="font-semibold">6. Retenção de Dados</h3>
      <p>
        Dados de usuários ativos são mantidos enquanto o contrato estiver vigente. Após rescisão,
        os dados são mantidos por 90 dias para possibilitar exportação, após o que são excluídos.
        Dados de alunos/funcionários inativos há mais de 5 anos são anonimizados automaticamente.
      </p>

      <h3 className="font-semibold">7. Direitos dos Titulares</h3>
      <p>Nos termos do Art. 18 da LGPD, os titulares têm direito a:</p>
      <ul className="list-disc pl-5 space-y-1">
        <li>Confirmação da existência de tratamento</li>
        <li>Acesso aos dados</li>
        <li>Correção de dados incompletos ou desatualizados</li>
        <li>Anonimização, bloqueio ou eliminação</li>
        <li>Portabilidade dos dados</li>
        <li>Revogação do consentimento</li>
      </ul>
      <p>
        Solicitações devem ser enviadas para: <strong>privacidade@igs.com.br</strong>. Respondemos
        em até 15 dias úteis.
      </p>

      <h3 className="font-semibold">8. Cookies</h3>
      <p>
        O painel utiliza cookies de sessão (autenticação JWT) e cookies de preferência (tema,
        idioma). Não utilizamos cookies de rastreamento de terceiros.
      </p>

      <h3 className="font-semibold">9. Encarregado (DPO)</h3>
      <p>
        Nosso Encarregado de Proteção de Dados pode ser contatado em:{' '}
        <strong>dpo@igs.com.br</strong>
      </p>
    </div>
  )
}

function Dpa() {
  return (
    <div className="prose prose-sm max-w-none text-gray-700 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">
        Acordo de Processamento de Dados (DPA — LGPD)
      </h2>
      <p className="text-xs text-gray-400">Última atualização: {LAST_UPDATED}</p>

      <p>
        Este Acordo de Processamento de Dados ("DPA") complementa o Contrato de Prestação de
        Serviços entre a IGS ("Operador") e o Cliente ("Controlador"), nos termos da Lei Geral de
        Proteção de Dados (Lei 13.709/2018).
      </p>

      <h3 className="font-semibold">1. Definições</h3>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Controlador</strong>: a instituição de ensino contratante do IGS</li>
        <li><strong>Operador</strong>: IGS Tecnologia, que processa dados em nome do Controlador</li>
        <li><strong>Titulares</strong>: alunos e funcionários da instituição</li>
        <li><strong>Dados Pessoais</strong>: qualquer informação relacionada a pessoa natural identificada</li>
      </ul>

      <h3 className="font-semibold">2. Responsabilidades do Operador</h3>
      <p>O Operador se compromete a:</p>
      <ul className="list-disc pl-5 space-y-1">
        <li>Tratar dados apenas conforme instruções documentadas do Controlador</li>
        <li>Garantir confidencialidade por todos os colaboradores com acesso aos dados</li>
        <li>Notificar o Controlador em até 72h sobre incidentes de segurança</li>
        <li>Auxiliar o Controlador no atendimento de requisições de titulares</li>
        <li>Excluir ou devolver todos os dados ao término do contrato</li>
        <li>Manter registros de atividades de tratamento (Art. 37, LGPD)</li>
      </ul>

      <h3 className="font-semibold">3. Suboperadores</h3>
      <p>O Operador utiliza os seguintes suboperadores aprovados:</p>
      <ul className="list-disc pl-5 space-y-1">
        <li><strong>Anthropic</strong> (EUA): processamento de linguagem natural via API Claude</li>
        <li><strong>Meta Platforms</strong> (EUA): transmissão de mensagens WhatsApp</li>
        <li><strong>Oracle Cloud</strong> (Brasil): infraestrutura de servidores e banco de dados</li>
      </ul>
      <p>
        Todos os suboperadores estão sujeitos a obrigações contratuais equivalentes às deste DPA e a
        mecanismos de transferência internacional reconhecidos (cláusulas contratuais padrão).
      </p>

      <h3 className="font-semibold">4. Transferência Internacional de Dados</h3>
      <p>
        O uso das APIs da Anthropic e Meta implica transferência de dados para os Estados Unidos.
        Essa transferência é amparada por cláusulas contratuais padrão e pelo legítimo interesse na
        execução do contrato de serviço (Art. 33, II e VI, LGPD).
      </p>

      <h3 className="font-semibold">5. Medidas de Segurança</h3>
      <p>O Operador implementa as seguintes medidas técnicas e organizacionais:</p>
      <ul className="list-disc pl-5 space-y-1">
        <li>Criptografia AES-256 em repouso, TLS 1.3 em trânsito</li>
        <li>Autenticação multifator para acessos administrativos</li>
        <li>Logs de auditoria de todos os acessos a dados sensíveis</li>
        <li>Controle de acesso baseado em papéis (RBAC)</li>
        <li>Backups diários com retenção de 30 dias</li>
        <li>Testes de penetração semestrais</li>
      </ul>

      <h3 className="font-semibold">6. Gestão de Incidentes</h3>
      <p>
        Em caso de incidente envolvendo dados pessoais, o Operador notificará o Controlador em até
        72 horas com: descrição do incidente, categorias e volume aproximado de dados afetados,
        medidas tomadas e recomendadas. O Controlador é responsável por notificar a ANPD conforme
        Art. 48 da LGPD.
      </p>

      <h3 className="font-semibold">7. Auditoria</h3>
      <p>
        O Controlador pode solicitar, com antecedência mínima de 30 dias, evidências de
        conformidade (relatórios de auditoria, certificações). Auditorias in loco estão disponíveis
        para clientes Enterprise.
      </p>

      <h3 className="font-semibold">8. Vigência</h3>
      <p>
        Este DPA vigora enquanto o Contrato de Prestação de Serviços estiver ativo. As obrigações
        de confidencialidade e segurança sobrevivem à rescisão por 5 anos.
      </p>

      <h3 className="font-semibold">9. Contato DPO</h3>
      <p>
        Para questões relacionadas a este DPA:{' '}
        <strong>dpo@igs.com.br</strong> | +55 11 99999-0001
      </p>
    </div>
  )
}

export default function Legal() {
  const [tab, setTab] = useState<Tab>('tos')

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'tos', label: 'Termos de Serviço', icon: <FileText size={16} /> },
    { id: 'privacy', label: 'Privacidade', icon: <Shield size={16} /> },
    { id: 'dpa', label: 'DPA / LGPD', icon: <Lock size={16} /> },
  ]

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Documentos Legais</h1>
          <p className="text-gray-500 mt-2">Termos, privacidade e conformidade LGPD</p>
        </div>

        <div className="card overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors flex-1 justify-center ${
                  tab === t.id
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {t.icon}
                <span className="hidden sm:inline">{t.label}</span>
              </button>
            ))}
          </div>

          <div className="p-6">
            {tab === 'tos' && <Tos />}
            {tab === 'privacy' && <Privacy />}
            {tab === 'dpa' && <Dpa />}
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Dúvidas? Entre em contato: legal@igs.com.br
        </p>
      </div>
    </div>
  )
}
