'use client'

import { useState } from 'react'
import { useQuery } from 'react-query'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { motion } from 'framer-motion'
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationCircleIcon,
  PlayIcon,
  StopIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline'
import { scansApi } from '@/lib/api'
import toast from 'react-hot-toast'

export function ScansList() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchFilter, setSearchFilter] = useState('')
  
  const { data, isLoading, refetch } = useQuery(
    ['scans', page, statusFilter, searchFilter],
    () => scansApi.list({ 
      page, 
      per_page: 10, 
      status: statusFilter || undefined,
      target: searchFilter || undefined
    }),
    { refetchInterval: 5000 }
  )

  const handleCancelScan = async (scanId: string) => {
    try {
      await scansApi.cancel(scanId)
      toast.success('Scan cancelado com sucesso')
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao cancelar scan')
    }
  }

  const handleDeleteScan = async (scanId: string) => {
    if (!confirm('Tem certeza que deseja excluir este scan?')) return
    
    try {
      await scansApi.delete(scanId)
      toast.success('Scan excluído com sucesso')
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir scan')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <ClockIcon className="w-5 h-5 text-blue-500" />
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />
      default:
        return <ExclamationCircleIcon className="w-5 h-5 text-yellow-500" />
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

  const formatDuration = (seconds: number) => {
    if (!seconds) return '-'
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
  }

  const scans = data?.data?.scans || []

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Scans de Segurança</h1>
          <p className="text-dark-400">Gerencie e monitore suas análises de segurança</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-dark-800 border border-dark-700 rounded-lg p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400" />
              <input
                type="text"
                placeholder="Buscar por URL..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="form-input w-full pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="md:w-48">
            <div className="relative">
              <FunnelIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="form-select w-full pl-10"
              >
                <option value="">Todos os status</option>
                <option value="pending">Pendente</option>
                <option value="running">Executando</option>
                <option value="completed">Concluído</option>
                <option value="failed">Falhou</option>
                <option value="cancelled">Cancelado</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Scans List */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="scan-card animate-pulse">
              <div className="h-6 bg-dark-700 rounded w-1/3 mb-2" />
              <div className="h-4 bg-dark-700 rounded w-1/2 mb-4" />
              <div className="flex justify-between">
                <div className="h-4 bg-dark-700 rounded w-1/4" />
                <div className="h-4 bg-dark-700 rounded w-1/6" />
              </div>
            </div>
          ))}
        </div>
      ) : scans.length === 0 ? (
        <div className="text-center py-12">
          <MagnifyingGlassIcon className="w-16 h-16 text-dark-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Nenhum scan encontrado</h3>
          <p className="text-dark-400 mb-6">Inicie seu primeiro scan de segurança</p>
        </div>
      ) : (
        <div className="space-y-4">
          {scans.map((scan: any, index: number) => (
            <motion.div
              key={scan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="scan-card"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    {getStatusIcon(scan.status)}
                    <h3 className="text-lg font-semibold text-white ml-2">
                      {new URL(scan.target_url).hostname}
                    </h3>
                    <span className="ml-auto text-sm text-dark-400">
                      #{scan.scan_number}
                    </span>
                  </div>
                  
                  <p className="text-dark-300 text-sm mb-2">{scan.target_url}</p>
                  
                  <div className="flex flex-wrap gap-2 mb-3">
                    {scan.scan_types.map((type: string) => (
                      <span 
                        key={type}
                        className="px-2 py-1 bg-dark-700 text-dark-300 rounded text-xs"
                      >
                        {type.toUpperCase()}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Progress Bar for Running Scans */}
              {scan.status === 'running' && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-dark-400 mb-1">
                    <span>Executando...</span>
                    <span>~60% concluído</span>
                  </div>
                  <div className="w-full bg-dark-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
                  </div>
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-xs text-dark-400">Status</p>
                  <p className="text-sm font-medium text-white">{getStatusText(scan.status)}</p>
                </div>
                <div>
                  <p className="text-xs text-dark-400">Vulnerabilidades</p>
                  <p className="text-sm font-medium text-white">{scan.total_vulnerabilities}</p>
                </div>
                <div>
                  <p className="text-xs text-dark-400">Risco</p>
                  <p className={`text-sm font-medium ${getRiskColor(scan.risk_score)}`}>
                    {scan.risk_score.toFixed(0)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-dark-400">Duração</p>
                  <p className="text-sm font-medium text-white">
                    {formatDuration(scan.duration_seconds)}
                  </p>
                </div>
              </div>

              {/* Vulnerability Summary */}
              {scan.vulnerability_summary && Object.values(scan.vulnerability_summary).some((v: any) => v > 0) && (
                <div className="mb-4">
                  <p className="text-xs text-dark-400 mb-2">Distribuição de Vulnerabilidades</p>
                  <div className="flex gap-2">
                    {Object.entries(scan.vulnerability_summary).map(([severity, count]: [string, any]) => 
                      count > 0 && (
                        <span 
                          key={severity}
                          className={`px-2 py-1 rounded text-xs risk-${severity}`}
                        >
                          {count} {severity}
                        </span>
                      )
                    )}
                  </div>
                </div>
              )}

              {/* Footer */}
              <div className="flex justify-between items-center pt-4 border-t border-dark-700">
                <div className="text-sm text-dark-400">
                  Criado em {format(new Date(scan.created_at), 'dd/MM/yyyy HH:mm', { locale: ptBR })}
                </div>
                
                <div className="flex gap-2">
                  <button
                    className="p-2 text-dark-400 hover:text-white transition-colors"
                    title="Ver detalhes"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                  
                  {scan.status === 'running' && (
                    <button
                      onClick={() => handleCancelScan(scan.id)}
                      className="p-2 text-yellow-400 hover:text-yellow-300 transition-colors"
                      title="Cancelar scan"
                    >
                      <StopIcon className="w-4 h-4" />
                    </button>
                  )}
                  
                  {scan.status !== 'running' && (
                    <button
                      onClick={() => handleDeleteScan(scan.id)}
                      className="p-2 text-red-400 hover:text-red-300 transition-colors"
                      title="Excluir scan"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {data?.data && data.data.total > data.data.per_page && (
        <div className="flex justify-center mt-8">
          <div className="flex gap-2">
            <button
              onClick={() => setPage(page - 1)}
              disabled={!data.data.has_prev}
              className="px-3 py-2 bg-dark-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-600 transition-colors"
            >
              Anterior
            </button>
            
            <span className="px-3 py-2 text-dark-300">
              Página {page} de {Math.ceil(data.data.total / data.data.per_page)}
            </span>
            
            <button
              onClick={() => setPage(page + 1)}
              disabled={!data.data.has_next}
              className="px-3 py-2 bg-dark-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-dark-600 transition-colors"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  )
}