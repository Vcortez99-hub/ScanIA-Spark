'use client'

import { useState } from 'react'
import { useQuery } from 'react-query'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { motion } from 'framer-motion'
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  XMarkIcon,
  CheckIcon,
  EyeIcon,
  LinkIcon
} from '@heroicons/react/24/outline'
import { vulnerabilitiesApi } from '@/lib/api'
import toast from 'react-hot-toast'

export function VulnerabilitiesList() {
  const [page, setPage] = useState(1)
  const [severityFilter, setSeverityFilter] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [searchFilter, setSearchFilter] = useState('')
  
  const { data, isLoading, refetch } = useQuery(
    ['vulnerabilities', page, severityFilter, statusFilter, searchFilter],
    () => vulnerabilitiesApi.list({ 
      page, 
      per_page: 10, 
      severity: severityFilter.length > 0 ? severityFilter : undefined,
      status: statusFilter.length > 0 ? statusFilter : undefined,
      search: searchFilter || undefined
    }),
    { refetchInterval: 30000 }
  )

  const handleMarkFalsePositive = async (vulnId: string) => {
    const reason = prompt('Motivo para marcar como falso positivo:')
    if (!reason) return
    
    try {
      await vulnerabilitiesApi.markFalsePositive(vulnId, reason)
      toast.success('Vulnerabilidade marcada como falso positivo')
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao marcar como falso positivo')
    }
  }

  const handleMarkRemediated = async (vulnId: string) => {
    const notes = prompt('Notas sobre a correção:')
    if (!notes) return
    
    try {
      await vulnerabilitiesApi.markRemediated(vulnId, notes)
      toast.success('Vulnerabilidade marcada como corrigida')
      refetch()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao marcar como corrigida')
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-400 bg-red-500/20 border-red-500/30'
      case 'high':
        return 'text-orange-400 bg-orange-500/20 border-orange-500/30'
      case 'medium':
        return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30'
      case 'low':
        return 'text-green-400 bg-green-500/20 border-green-500/30'
      case 'info':
        return 'text-blue-400 bg-blue-500/20 border-blue-500/30'
      default:
        return 'text-dark-400 bg-dark-500/20 border-dark-500/30'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'text-red-400'
      case 'in_progress':
        return 'text-yellow-400'
      case 'fixed':
        return 'text-green-400'
      case 'false_positive':
        return 'text-blue-400'
      case 'accepted_risk':
        return 'text-purple-400'
      default:
        return 'text-dark-400'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'open':
        return 'Aberta'
      case 'in_progress':
        return 'Em Progresso'
      case 'fixed':
        return 'Corrigida'
      case 'false_positive':
        return 'Falso Positivo'
      case 'accepted_risk':
        return 'Risco Aceito'
      default:
        return status
    }
  }

  const vulnerabilities = data?.data?.vulnerabilities || []

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Vulnerabilidades</h1>
          <p className="text-dark-400">Gerencie e monitore vulnerabilidades encontradas</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-dark-800 border border-dark-700 rounded-lg p-4 mb-6">
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-400" />
            <input
              type="text"
              placeholder="Buscar vulnerabilidades..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="form-input w-full pl-10"
            />
          </div>

          {/* Severity Filters */}
          <div>
            <p className="text-sm font-medium text-dark-300 mb-2">Severidade</p>
            <div className="flex flex-wrap gap-2">
              {['critical', 'high', 'medium', 'low', 'info'].map((severity) => (
                <button
                  key={severity}
                  onClick={() => {
                    if (severityFilter.includes(severity)) {
                      setSeverityFilter(severityFilter.filter(s => s !== severity))
                    } else {
                      setSeverityFilter([...severityFilter, severity])
                    }
                  }}
                  className={`px-3 py-1 rounded border text-sm transition-colors ${
                    severityFilter.includes(severity)
                      ? getSeverityColor(severity)
                      : 'text-dark-400 bg-dark-700 border-dark-600 hover:border-dark-500'
                  }`}
                >
                  {severity.charAt(0).toUpperCase() + severity.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Status Filters */}
          <div>
            <p className="text-sm font-medium text-dark-300 mb-2">Status</p>
            <div className="flex flex-wrap gap-2">
              {['open', 'in_progress', 'fixed', 'false_positive'].map((status) => (
                <button
                  key={status}
                  onClick={() => {
                    if (statusFilter.includes(status)) {
                      setStatusFilter(statusFilter.filter(s => s !== status))
                    } else {
                      setStatusFilter([...statusFilter, status])
                    }
                  }}
                  className={`px-3 py-1 rounded border text-sm transition-colors ${
                    statusFilter.includes(status)
                      ? 'bg-brand-600 text-white border-brand-500'
                      : 'text-dark-400 bg-dark-700 border-dark-600 hover:border-dark-500'
                  }`}
                >
                  {getStatusText(status)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {data?.data && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
            <p className="text-sm text-dark-400">Total</p>
            <p className="text-2xl font-bold text-white">{data.data.total}</p>
          </div>
          {Object.entries(data.data.severity_counts || {}).map(([severity, count]: [string, any]) => (
            <div key={severity} className="bg-dark-800 border border-dark-700 rounded-lg p-4">
              <p className={`text-sm ${getSeverityColor(severity).split(' ')[0]}`}>
                {severity.charAt(0).toUpperCase() + severity.slice(1)}
              </p>
              <p className="text-2xl font-bold text-white">{count}</p>
            </div>
          ))}
        </div>
      )}

      {/* Vulnerabilities List */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="vulnerability-card animate-pulse">
              <div className="h-6 bg-dark-700 rounded w-2/3 mb-2" />
              <div className="h-4 bg-dark-700 rounded w-1/2 mb-4" />
              <div className="flex justify-between">
                <div className="h-4 bg-dark-700 rounded w-1/4" />
                <div className="h-4 bg-dark-700 rounded w-1/6" />
              </div>
            </div>
          ))}
        </div>
      ) : vulnerabilities.length === 0 ? (
        <div className="text-center py-12">
          <ShieldCheckIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Nenhuma vulnerabilidade encontrada</h3>
          <p className="text-dark-400">Isso é uma boa notícia! Seus sistemas estão seguros.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {vulnerabilities.map((vuln: any, index: number) => (
            <motion.div
              key={vuln.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="vulnerability-card"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className={`px-2 py-1 rounded border text-xs font-medium ${getSeverityColor(vuln.severity)}`}>
                      {vuln.severity.toUpperCase()}
                    </span>
                    {vuln.cvss_score && (
                      <span className="ml-2 text-sm text-dark-400">
                        CVSS: {vuln.cvss_score}
                      </span>
                    )}
                    {vuln.cve_id && (
                      <span className="ml-2 text-sm text-blue-400">
                        {vuln.cve_id}
                      </span>
                    )}
                  </div>
                  
                  <h3 className="text-lg font-semibold text-white mb-1">{vuln.title}</h3>
                  <p className="text-dark-300 text-sm line-clamp-2">{vuln.description}</p>
                </div>
                
                <div className="ml-4 flex items-center">
                  <span className={`text-sm font-medium ${getStatusColor(vuln.status)}`}>
                    {getStatusText(vuln.status)}
                  </span>
                </div>
              </div>

              {/* Affected URL */}
              <div className="mb-3">
                <div className="flex items-center text-sm text-dark-400">
                  <LinkIcon className="w-4 h-4 mr-1" />
                  <span className="truncate">{vuln.affected_url}</span>
                </div>
                {vuln.affected_component && (
                  <div className="text-xs text-dark-500 mt-1">
                    Componente: {vuln.affected_component}
                  </div>
                )}
              </div>

              {/* Risk Indicators */}
              <div className="flex flex-wrap gap-2 mb-3">
                <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(vuln.risk_level.toLowerCase())}`}>
                  Risco: {vuln.risk_level}
                </span>
                <span className="px-2 py-1 rounded text-xs bg-dark-700 text-dark-300">
                  Urgência: {vuln.remediation_urgency}/5
                </span>
                {vuln.vulnerability_type && (
                  <span className="px-2 py-1 rounded text-xs bg-dark-700 text-dark-300">
                    {vuln.vulnerability_type}
                  </span>
                )}
              </div>

              {/* Actions */}
              <div className="flex justify-between items-center pt-3 border-t border-dark-700">
                <div className="text-sm text-dark-400">
                  {format(new Date(vuln.created_at), 'dd/MM/yyyy HH:mm', { locale: ptBR })}
                </div>
                
                <div className="flex gap-2">
                  <button
                    className="p-2 text-dark-400 hover:text-white transition-colors"
                    title="Ver detalhes"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                  
                  {vuln.status === 'open' && (
                    <>
                      <button
                        onClick={() => handleMarkRemediated(vuln.id)}
                        className="p-2 text-green-400 hover:text-green-300 transition-colors"
                        title="Marcar como corrigida"
                      >
                        <CheckIcon className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => handleMarkFalsePositive(vuln.id)}
                        className="p-2 text-blue-400 hover:text-blue-300 transition-colors"
                        title="Marcar como falso positivo"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </>
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