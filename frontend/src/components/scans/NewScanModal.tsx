'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { motion, AnimatePresence } from 'framer-motion'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { scansApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface NewScanModalProps {
  isOpen: boolean
  onClose: () => void
  onScanCreated: () => void
}

interface ScanFormData {
  target_url: string
  scan_types: string[]
  environment_type: string
}

export function NewScanModal({ isOpen, onClose, onScanCreated }: NewScanModalProps) {
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, formState: { errors }, reset } = useForm<ScanFormData>({
    defaultValues: {
      scan_types: ['owasp_zap'],
      environment_type: 'production'
    }
  })

  const scanTypes = [
    { id: 'owasp_zap', name: 'OWASP ZAP', description: 'Análise completa de vulnerabilidades web' },
    { id: 'nmap', name: 'Nmap', description: 'Escaneamento de portas e serviços' },
    { id: 'nikto', name: 'Nikto', description: 'Scanner de vulnerabilidades web' },
    { id: 'sqlmap', name: 'SQLMap', description: 'Detecção de SQL Injection' },
  ]

  const environmentTypes = [
    { id: 'production', name: 'Produção' },
    { id: 'staging', name: 'Homologação' },
    { id: 'development', name: 'Desenvolvimento' },
    { id: 'testing', name: 'Teste' },
  ]

  const onSubmit = async (data: ScanFormData) => {
    setLoading(true)
    try {
      await scansApi.create({
        target_url: data.target_url,
        scan_types: data.scan_types,
        environment_type: data.environment_type,
        options: {}
      })
      
      toast.success('Scan iniciado com sucesso!')
      reset()
      onScanCreated()
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao iniciar scan'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-dark-800 border border-dark-700 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-dark-700">
                <h2 className="text-2xl font-bold text-white">Novo Scan de Segurança</h2>
                <button
                  onClick={handleClose}
                  className="text-dark-400 hover:text-white transition-colors"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
                {/* Target URL */}
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    URL Alvo *
                  </label>
                  <input
                    {...register('target_url', {
                      required: 'URL é obrigatória',
                      pattern: {
                        value: /^https?:\/\/.+/,
                        message: 'URL deve começar com http:// ou https://'
                      }
                    })}
                    type="url"
                    className="form-input w-full"
                    placeholder="https://exemplo.com"
                  />
                  {errors.target_url && (
                    <p className="text-red-400 text-sm mt-1">{errors.target_url.message}</p>
                  )}
                </div>

                {/* Scan Types */}
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-3">
                    Tipos de Scan *
                  </label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {scanTypes.map((type) => (
                      <div key={type.id} className="relative">
                        <input
                          {...register('scan_types', {
                            required: 'Selecione pelo menos um tipo de scan'
                          })}
                          type="checkbox"
                          value={type.id}
                          id={type.id}
                          className="sr-only peer"
                        />
                        <label
                          htmlFor={type.id}
                          className="flex items-start p-4 bg-dark-700 border border-dark-600 rounded-lg cursor-pointer hover:bg-dark-600 peer-checked:bg-brand-600/20 peer-checked:border-brand-500 transition-all"
                        >
                          <div className="flex items-center h-5">
                            <div className="w-4 h-4 border-2 border-dark-400 rounded peer-checked:border-brand-500 peer-checked:bg-brand-500 flex items-center justify-center">
                              <svg className="w-2 h-2 text-white opacity-0 peer-checked:opacity-100" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                          </div>
                          <div className="ml-3 flex-1">
                            <h4 className="text-white font-medium">{type.name}</h4>
                            <p className="text-sm text-dark-400 mt-1">{type.description}</p>
                          </div>
                        </label>
                      </div>
                    ))}
                  </div>
                  {errors.scan_types && (
                    <p className="text-red-400 text-sm mt-1">{errors.scan_types.message}</p>
                  )}
                </div>

                {/* Environment Type */}
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Tipo de Ambiente
                  </label>
                  <select
                    {...register('environment_type')}
                    className="form-select w-full"
                  >
                    {environmentTypes.map((env) => (
                      <option key={env.id} value={env.id}>
                        {env.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Advanced Options */}
                <div className="border border-dark-700 rounded-lg p-4">
                  <h3 className="text-white font-medium mb-3">Configurações Avançadas</h3>
                  <div className="text-sm text-dark-400">
                    <p>• O scan será executado com configurações padrão</p>
                    <p>• Tempo estimado: 5-30 minutos dependendo do tamanho do site</p>
                    <p>• Você receberá notificações sobre o progresso</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-4 pt-4 border-t border-dark-700">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="btn-secondary"
                    disabled={loading}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={loading}
                  >
                    {loading ? (
                      <div className="flex items-center">
                        <div className="loading-spinner w-4 h-4 mr-2" />
                        Iniciando...
                      </div>
                    ) : (
                      'Iniciar Scan'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}