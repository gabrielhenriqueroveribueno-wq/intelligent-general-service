import { useState } from 'react'
import { Download, BarChart2 } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

export default function Reports() {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [isExporting, setIsExporting] = useState<string | null>(null)

  const exportReport = async (type: 'conversations' | 'tickets') => {
    if (!startDate || !endDate) {
      toast.error('Selecione o período')
      return
    }
    setIsExporting(type)
    try {
      const res = await api.get(`/api/v1/reports/${type}`, {
        params: { start_date: startDate, end_date: endDate },
        responseType: 'blob',
      })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `${type}_${startDate}_${endDate}.csv`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Relatório exportado!')
    } catch {
      toast.error('Erro ao exportar relatório')
    } finally {
      setIsExporting(null)
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Relatórios</h1>
        <p className="text-sm text-gray-500">Exporte dados para análise</p>
      </div>

      <div className="card max-w-lg">
        <h3 className="font-medium mb-4">Período</h3>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Data inicial</label>
            <input type="datetime-local" className="input" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Data final</label>
            <input type="datetime-local" className="input" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
        </div>

        <div className="space-y-2">
          <button
            onClick={() => exportReport('conversations')}
            disabled={!!isExporting}
            className="btn-primary w-full gap-2"
          >
            <Download size={16} />
            {isExporting === 'conversations' ? 'Exportando...' : 'Exportar Conversas (CSV)'}
          </button>
          <button
            onClick={() => exportReport('tickets')}
            disabled={!!isExporting}
            className="btn-secondary w-full gap-2"
          >
            <Download size={16} />
            {isExporting === 'tickets' ? 'Exportando...' : 'Exportar Tickets (CSV)'}
          </button>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-2 text-gray-500">
          <BarChart2 size={18} />
          <p className="text-sm">Para dashboards avançados com gráficos históricos, acesse o <strong>Grafana</strong> em <code className="bg-gray-100 px-1 rounded">localhost:3001</code></p>
        </div>
      </div>
    </div>
  )
}
