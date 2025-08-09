'use client'

import { motion } from 'framer-motion'

export function LoadingScreen() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="w-16 h-16 border-4 border-blue-500/20 border-t-blue-500 rounded-full mx-auto mb-4"
        />
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h1 className="text-2xl font-bold text-blue-400 mb-2">ScanIA</h1>
          <p className="text-gray-400">Carregando sistema...</p>
        </motion.div>
      </motion.div>
    </div>
  )
}