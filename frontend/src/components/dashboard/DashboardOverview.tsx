'use client'

import { useQuery } from 'react-query'
import { motion } from 'framer-motion'
import { 
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { scansApi, vulnerabilitiesApi } from '@/lib/api'
import { RecentScans } from './RecentScans'
import { VulnerabilityChart } from './VulnerabilityChart'

export function DashboardOverview() {
  const { data: scanStats, isLoading: loadingScans } = useQuery(
    'scan-stats',
    () => scansApi.getStats(),
    { refetchInterval: 30000 }
  )

  const { data: vulnStats, isLoading: loadingVulns } = useQuery(
    'vulnerability-stats',
    () => vulnerabilitiesApi.getStats(),
    { refetchInterval: 30000 }
  )

  const stats = [
    {
      name: 'Total de Scans',
      value: scanStats?.data?.total_scans || 0,
      icon: MagnifyingGlassIcon,
      color: 'bg-blue-500',
      loading: loadingScans
    },
    {
      name: 'Scans Executando',
      value: scanStats?.data?.running_scans || 0,
      icon: ClockIcon,
      color: 'bg-yellow-500',
      loading: loadingScans
    },
    {
      name: 'Scans Concluídos',
      value: scanStats?.data?.completed_scans || 0,
      icon: CheckCircleIcon,
      color: 'bg-green-500',
      loading: loadingScans
    },
    {
      name: 'Scans Falharam',
      value: scanStats?.data?.failed_scans || 0,
      icon: XCircleIcon,
      color: 'bg-red-500',
      loading: loadingScans
    },
  ]

  const vulnerabilityStats = [
    {
      name: 'Total de Vulnerabilidades',
      value: vulnStats?.data?.total_vulnerabilities || 0,
      icon: ExclamationTriangleIcon,
      color: 'bg-purple-500',
      loading: loadingVulns
    },
    {
      name: 'Críticas Abertas',
      value: vulnStats?.data?.critical_open || 0,
      icon: ExclamationTriangleIcon,
      color: 'bg-red-600',
      loading: loadingVulns
    },
    {
      name: 'Altas Abertas',
      value: vulnStats?.data?.high_open || 0,
      icon: ExclamationTriangleIcon,
      color: 'bg-orange-500',
      loading: loadingVulns
    },
    {
      name: 'CVSS Médio',
      value: vulnStats?.data?.avg_cvss_score?.toFixed(1) || '0.0',
      icon: ChartBarIcon,
      color: 'bg-indigo-500',
      loading: loadingVulns
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Visão Geral</h1>
        <p className="text-dark-400">Dashboard principal do sistema de cybersegurança</p>
      </div>

      {/* Scan Statistics */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Estatísticas de Scans</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="dashboard-widget"
            >
              <div className="flex items-center">
                <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-bold text-white">
                    {stat.loading ? (
                      <div className="w-8 h-6 bg-dark-700 rounded animate-pulse" />
                    ) : (
                      stat.value
                    )}
                  </p>
                  <p className="text-sm text-dark-400">{stat.name}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Vulnerability Statistics */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Estatísticas de Vulnerabilidades</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {vulnerabilityStats.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: (index + 4) * 0.1 }}
              className="dashboard-widget"
            >
              <div className="flex items-center">
                <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-2xl font-bold text-white">
                    {stat.loading ? (
                      <div className="w-8 h-6 bg-dark-700 rounded animate-pulse" />
                    ) : (
                      stat.value
                    )}
                  </p>
                  <p className="text-sm text-dark-400">{stat.name}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vulnerability Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.8 }}
          className="dashboard-widget"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Distribuição de Vulnerabilidades</h3>
          <VulnerabilityChart data={vulnStats?.data} loading={loadingVulns} />
        </motion.div>

        {/* Recent Scans */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.9 }}
          className="dashboard-widget"
        >
          <h3 className="text-lg font-semibold text-white mb-4">Scans Recentes</h3>
          <RecentScans />
        </motion.div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.0 }}
        className="dashboard-widget"
      >
        <h3 className="text-lg font-semibold text-white mb-4">Ações Rápidas</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 bg-dark-700 hover:bg-dark-600 rounded-lg transition-colors text-left">
            <MagnifyingGlassIcon className="w-8 h-8 text-brand-500 mb-2" />
            <h4 className="font-medium text-white mb-1">Novo Scan</h4>
            <p className="text-sm text-dark-400">Iniciar uma nova análise de segurança</p>
          </button>
          
          <button className="p-4 bg-dark-700 hover:bg-dark-600 rounded-lg transition-colors text-left">
            <ExclamationTriangleIcon className="w-8 h-8 text-orange-500 mb-2" />
            <h4 className="font-medium text-white mb-1">Ver Vulnerabilidades</h4>
            <p className="text-sm text-dark-400">Revisar vulnerabilidades encontradas</p>
          </button>
          
          <button className="p-4 bg-dark-700 hover:bg-dark-600 rounded-lg transition-colors text-left">
            <DocumentTextIcon className="w-8 h-8 text-green-500 mb-2" />
            <h4 className="font-medium text-white mb-1">Gerar Relatório</h4>
            <p className="text-sm text-dark-400">Criar relatório detalhado</p>
          </button>
        </div>
      </motion.div>
    </div>
  )
}