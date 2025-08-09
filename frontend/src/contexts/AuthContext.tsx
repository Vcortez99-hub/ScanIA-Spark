'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
  last_login?: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string, full_name: string) => Promise<boolean>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      if (typeof window === 'undefined') {
        setLoading(false)
        return
      }
      
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setLoading(false)
        return
      }

      const response = await authApi.getCurrentUser()
      setUser(response.data)
    } catch (error) {
      console.error('Auth check failed:', error)
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await authApi.login(email, password)
      const { access_token, user: userData } = response.data

      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', access_token)
      }
      setUser(userData)
      
      toast.success(`Bem-vindo, ${userData.full_name}!`)
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao fazer login'
      toast.error(message)
      return false
    }
  }

  const register = async (email: string, password: string, full_name: string): Promise<boolean> => {
    try {
      const response = await authApi.register(email, password, full_name)
      toast.success('Conta criada com sucesso! Faça login para continuar.')
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao criar conta'
      toast.error(message)
      return false
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
      }
      setUser(null)
      toast.success('Logout realizado com sucesso')
    }
  }

  const refreshUser = async () => {
    try {
      const response = await authApi.getCurrentUser()
      setUser(response.data)
    } catch (error) {
      console.error('Failed to refresh user:', error)
      logout()
    }
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    refreshUser
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}