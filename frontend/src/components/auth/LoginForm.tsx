'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { EyeIcon, EyeSlashIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/AuthContext'

interface LoginFormData {
  email: string
  password: string
}

interface RegisterFormData {
  email: string
  password: string
  full_name: string
  confirmPassword: string
}

export function LoginForm() {
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()

  const loginForm = useForm<LoginFormData>()
  const registerForm = useForm<RegisterFormData>()

  const onLoginSubmit = async (data: LoginFormData) => {
    setLoading(true)
    try {
      await login(data.email, data.password)
    } finally {
      setLoading(false)
    }
  }

  const onRegisterSubmit = async (data: RegisterFormData) => {
    if (data.password !== data.confirmPassword) {
      registerForm.setError('confirmPassword', { message: 'Senhas não coincidem' })
      return
    }

    setLoading(true)
    try {
      const success = await register(data.email, data.password, data.full_name)
      if (success) {
        setIsLogin(true)
        registerForm.reset()
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-2xl p-8 shadow-2xl">
      {/* Header */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5, type: 'spring' }}
          className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4"
        >
          <ShieldCheckIcon className="w-8 h-8 text-white" />
        </motion.div>
        <h1 className="text-3xl font-bold text-white mb-2">ScanIA</h1>
        <p className="text-gray-400">Sistema Inteligente de Análise de Cybersegurança</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex rounded-lg bg-gray-900 p-1 mb-6">
        <button
          onClick={() => setIsLogin(true)}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            isLogin
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Entrar
        </button>
        <button
          onClick={() => setIsLogin(false)}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            !isLogin
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Registrar
        </button>
      </div>

      {/* Login Form */}
      {isLogin && (
        <motion.form
          key="login"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          onSubmit={loginForm.handleSubmit(onLoginSubmit)}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <input
              {...loginForm.register('email', {
                required: 'Email é obrigatório',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Email inválido'
                }
              })}
              type="email"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="seu@email.com"
            />
            {loginForm.formState.errors.email && (
              <p className="text-red-400 text-sm mt-1">
                {loginForm.formState.errors.email.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Senha
            </label>
            <div className="relative">
              <input
                {...loginForm.register('password', {
                  required: 'Senha é obrigatória'
                })}
                type={showPassword ? 'text' : 'password'}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-300"
              >
                {showPassword ? (
                  <EyeSlashIcon className="w-5 h-5" />
                ) : (
                  <EyeIcon className="w-5 h-5" />
                )}
              </button>
            </div>
            {loginForm.formState.errors.password && (
              <p className="text-red-400 text-sm mt-1">
                {loginForm.formState.errors.password.message}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Entrando...
              </div>
            ) : (
              'Entrar'
            )}
          </button>
        </motion.form>
      )}

      {/* Register Form */}
      {!isLogin && (
        <motion.form
          key="register"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          onSubmit={registerForm.handleSubmit(onRegisterSubmit)}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Nome Completo
            </label>
            <input
              {...registerForm.register('full_name', {
                required: 'Nome é obrigatório',
                minLength: { value: 2, message: 'Nome deve ter pelo menos 2 caracteres' }
              })}
              type="text"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Seu Nome Completo"
            />
            {registerForm.formState.errors.full_name && (
              <p className="text-red-400 text-sm mt-1">
                {registerForm.formState.errors.full_name.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <input
              {...registerForm.register('email', {
                required: 'Email é obrigatório',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Email inválido'
                }
              })}
              type="email"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="seu@email.com"
            />
            {registerForm.formState.errors.email && (
              <p className="text-red-400 text-sm mt-1">
                {registerForm.formState.errors.email.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Senha
            </label>
            <input
              {...registerForm.register('password', {
                required: 'Senha é obrigatória',
                minLength: { value: 8, message: 'Senha deve ter pelo menos 8 caracteres' }
              })}
              type="password"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="••••••••"
            />
            {registerForm.formState.errors.password && (
              <p className="text-red-400 text-sm mt-1">
                {registerForm.formState.errors.password.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Confirmar Senha
            </label>
            <input
              {...registerForm.register('confirmPassword', {
                required: 'Confirmação de senha é obrigatória'
              })}
              type="password"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="••••••••"
            />
            {registerForm.formState.errors.confirmPassword && (
              <p className="text-red-400 text-sm mt-1">
                {registerForm.formState.errors.confirmPassword.message}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Registrando...
              </div>
            ) : (
              'Criar Conta'
            )}
          </button>
        </motion.form>
      )}
    </div>
  )
}