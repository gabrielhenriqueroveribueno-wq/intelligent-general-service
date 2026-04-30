import { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Upload,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2,
  GraduationCap,
  Users,
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

type ImportKind = 'students' | 'employees'

interface ImportResult {
  created: number
  skipped: number
  errors: string[]
}

export default function ImportData() {
  const { user } = useAuth()
  const [kind, setKind] = useState<ImportKind>('students')
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const tenantId = user?.tenant_id
  if (!tenantId) {
    return (
      <div className="card">
        <p className="text-sm text-gray-600">
          Voce precisa estar logado em uma instituicao para importar dados.
        </p>
      </div>
    )
  }

  const uploadMutation = useMutation({
    mutationFn: async (payload: { file: File; kind: ImportKind }) => {
      const form = new FormData()
      form.append('file', payload.file)
      const endpoint =
        payload.kind === 'students'
          ? `/api/v1/onboarding/tenants/${tenantId}/import-students`
          : `/api/v1/onboarding/tenants/${tenantId}/import-employees`
      const res = await api.post(endpoint, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return res.data as ImportResult
    },
    onSuccess: (data) => {
      setResult(data)
      toast.success(
        `Importacao concluida: ${data.created} criados, ${data.skipped} ignorados`,
      )
      setFile(null)
      if (inputRef.current) inputRef.current.value = ''
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || 'Erro na importacao'
      toast.error(typeof detail === 'string' ? detail : 'Falha ao enviar arquivo')
    },
  })

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) validateAndSetFile(dropped)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0]
    if (picked) validateAndSetFile(picked)
  }

  const validateAndSetFile = (picked: File) => {
    if (!picked.name.toLowerCase().endsWith('.csv')) {
      toast.error('O arquivo deve ser .csv')
      return
    }
    if (picked.size > 5 * 1024 * 1024) {
      toast.error('Arquivo excede o limite de 5 MB')
      return
    }
    setFile(picked)
    setResult(null)
  }

  const downloadTemplate = () => {
    const endpoint =
      kind === 'students'
        ? '/api/v1/onboarding/templates/students.csv'
        : '/api/v1/onboarding/templates/employees.csv'
    api
      .get(endpoint, { responseType: 'blob' })
      .then((res) => {
        const blob = new Blob([res.data], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download =
          kind === 'students' ? 'template_alunos.csv' : 'template_funcionarios.csv'
        a.click()
        URL.revokeObjectURL(url)
      })
      .catch(() => toast.error('Erro ao baixar template'))
  }

  const kindConfig = {
    students: {
      icon: GraduationCap,
      label: 'Alunos',
      cols: [
        'registration_number',
        'full_name',
        'course',
        'semester',
        'enrollment_status',
        'email',
        'phone',
      ],
    },
    employees: {
      icon: Users,
      label: 'Funcionarios',
      cols: [
        'employee_number',
        'full_name',
        'department',
        'position',
        'status',
        'email',
        'phone',
        'hire_date',
      ],
    },
  } as const

  const config = kindConfig[kind]
  const Icon = config.icon

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Importar Dados</h1>
        <p className="text-sm text-gray-500">
          Faca upload de uma planilha CSV com a base de alunos ou funcionarios
        </p>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => {
            setKind('students')
            setResult(null)
          }}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium',
            kind === 'students'
              ? 'bg-blue-600 text-white'
              : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50',
          )}
        >
          <GraduationCap size={16} /> Alunos
        </button>
        <button
          onClick={() => {
            setKind('employees')
            setResult(null)
          }}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium',
            kind === 'employees'
              ? 'bg-blue-600 text-white'
              : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50',
          )}
        >
          <Users size={16} /> Funcionarios
        </button>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Icon className="text-blue-600" size={20} />
            </div>
            <div>
              <h3 className="font-semibold">{config.label}</h3>
              <p className="text-xs text-gray-500">
                Colunas esperadas: <span className="font-mono">{config.cols.join(', ')}</span>
              </p>
            </div>
          </div>
          <button
            onClick={downloadTemplate}
            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            <Download size={14} /> Baixar template
          </button>
        </div>

        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragActive(true)
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={clsx(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400',
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileInput}
          />
          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileSpreadsheet className="text-green-600" size={24} />
              <div className="text-left">
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-gray-500">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
          ) : (
            <>
              <Upload className="mx-auto text-gray-400 mb-2" size={32} />
              <p className="text-sm font-medium">
                Arraste o arquivo CSV aqui ou clique para selecionar
              </p>
              <p className="text-xs text-gray-500 mt-1">Maximo 5 MB</p>
            </>
          )}
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={() => file && uploadMutation.mutate({ file, kind })}
            disabled={!file || uploadMutation.isPending}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploadMutation.isPending && (
              <Loader2 className="animate-spin" size={16} />
            )}
            Importar
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle2 className="text-green-600" size={20} />
            <h3 className="font-semibold">Resultado da importacao</h3>
          </div>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-green-50 rounded-lg p-3">
              <p className="text-xs text-green-700">Criados</p>
              <p className="text-2xl font-bold text-green-700">{result.created}</p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3">
              <p className="text-xs text-yellow-700">Ja existiam</p>
              <p className="text-2xl font-bold text-yellow-700">{result.skipped}</p>
            </div>
            <div className="bg-red-50 rounded-lg p-3">
              <p className="text-xs text-red-700">Erros</p>
              <p className="text-2xl font-bold text-red-700">{result.errors.length}</p>
            </div>
          </div>
          {result.errors.length > 0 && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="text-red-600" size={16} />
                <p className="text-sm font-medium text-red-900">
                  Linhas com erro (primeiras 50)
                </p>
              </div>
              <ul className="text-xs text-red-800 space-y-1 max-h-40 overflow-y-auto">
                {result.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
