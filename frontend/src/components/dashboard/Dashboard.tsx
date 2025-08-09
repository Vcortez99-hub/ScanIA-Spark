'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { motion } from 'framer-motion'

export function Dashboard() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">
              Bem-vindo, {user?.full_name}! 👋
            </h1>
            <p className="text-gray-400">
              Sistema Inteligente de Análise de Cybersegurança
            </p>
          </div>
          <button
            onClick={logout}
            className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
          >
            Sair
          </button>
        </div>
      </div>

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-gray-800 p-6 rounded-lg"
        >
          <h3 className="text-lg font-semibold text-white mb-4">📊 Estatísticas</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Scans Total:</span>
              <span className="text-blue-400 font-bold">-</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Vulnerabilidades:</span>
              <span className="text-red-400 font-bold">-</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Status:</span>
              <span className="text-green-400 font-bold">Ativo</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="bg-gray-800 p-6 rounded-lg"
        >
          <h3 className="text-lg font-semibold text-white mb-4">🚀 Novo Scan</h3>
          <p className="text-gray-400 mb-4">
            Inicie uma nova análise de segurança
          </p>
          <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
            Iniciar Scan
          </button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-gray-800 p-6 rounded-lg"
        >
          <h3 className="text-lg font-semibold text-white mb-4">⚠️ Alertas</h3>
          <p className="text-gray-400 mb-4">
            Nenhum alerta crítico no momento
          </p>
          <div className="bg-green-900 text-green-300 px-3 py-1 rounded text-sm">
            Sistema funcionando normalmente
          </div>
        </motion.div>
      </div>

      {/* Backend Connection Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="bg-gray-800 rounded-lg p-6 mt-8"
      >
        <h3 className="text-lg font-semibold text-white mb-4">🔗 Status da Conexão</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-300">Frontend: Conectado</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-300">Backend API: Conectado</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-300">Banco de Dados: Conectado</span>
          </div>
        </div>
      </motion.div>
    </div>
  )
}