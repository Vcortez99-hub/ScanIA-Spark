'use client'

import { useAuth } from '@/contexts/AuthContext'
import { LoginForm } from '@/components/auth/LoginForm'
import { Dashboard } from '@/components/dashboard/Dashboard'
import { LoadingScreen } from '@/components/ui/LoadingScreen'
import { motion } from 'framer-motion'

export default function HomePage() {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingScreen />
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <LoginForm />
        </motion.div>
      </div>
    )
  }

  return <Dashboard />
}