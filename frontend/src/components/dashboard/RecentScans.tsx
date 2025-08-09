'use client'

import { useQuery } from 'react-query'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { scansApi } from '@/lib/api'
import { ClockIcon, CheckCircleIcon, XCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'

export function RecentScans() {
  const { data: scansData, isLoading } = useQuery(
    'recent-scans',
    () => scansApi.list({ page: 1, per_page: 5 }),
    { refetchInterval: 10000 }
  )

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <ClockIcon className="w-4 h-4 text-blue-500" />
      case 'completed':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />
      case 'failed':
        return <XCircleIcon className="w-4 h-4 text-red-500" />
      default:
        return <ExclamationCircleIcon className="w-4 h-4 text-yellow-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Pendente'
      case 'running':
        return 'Executando'
      case 'completed':
        return 'Concluído'
      case 'failed':
        return 'Falhou'
      case 'cancelled':
        return 'Cancelado'
      default:
        return status
    }
  }

  const getRiskColor = (riskScore: number) => {
    if (riskScore >= 80) return 'text-red-400'
    if (riskScore >= 60) return 'text-orange-400'
    if (riskScore >= 40) return 'text-yellow-400'
    return 'text-green-400'
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-dark-700 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="w-32 h-4 bg-dark-600 rounded" />
                <div className="w-16 h-4 bg-dark-600 rounded" />
              </div>
              <div className="w-24 h-3 bg-dark-600 rounded" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  const scans = scansData?.data?.scans || []

  if (scans.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-dark-400">Nenhum scan encontrado</p>
        <p className="text-sm text-dark-500 mt-1">Inicie seu primeiro scan para ver os resultados aqui</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {scans.map((scan: any) => (
        <div
          key={scan.id}
          className="bg-dark-700 hover:bg-dark-600 rounded-lg p-3 transition-colors cursor-pointer"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              {getStatusIcon(scan.status)}
              <span className="ml-2 text-sm font-medium text-white truncate max-w-48">
                {new URL(scan.target_url).hostname}
              </span>
            </div>
            <span className="text-xs text-dark-400">
              {getStatusText(scan.status)}
            </span>
          </div>
          
          <div className="flex items-center justify-between text-xs">
            <span className="text-dark-400">
              {format(new Date(scan.created_at), 'dd/MM/yyyy HH:mm', { locale: ptBR })}
            </span>
            {scan.total_vulnerabilities > 0 && (
              <div className="flex items-center">
                <span className="text-dark-400 mr-2">{scan.total_vulnerabilities} vulns</span>
                <span className={`font-medium ${getRiskColor(scan.risk_score)}`}>
                  {scan.risk_score.toFixed(0)}%
                </span>
              </div>
            )}
          </div>
          
          {scan.status === 'running' && (
            <div className="mt-2">
              <div className="w-full bg-dark-600 rounded-full h-1">
                <div className="bg-blue-500 h-1 rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}