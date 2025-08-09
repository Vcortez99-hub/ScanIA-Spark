'use client'

import { motion } from 'framer-motion'
import { 
  HomeIcon, 
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  PlusIcon,
  ArrowRightOnRectangleIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/AuthContext'

interface SidebarProps {
  currentView: string
  onViewChange: (view: string) => void
  onNewScan: () => void
}

export function Sidebar({ currentView, onViewChange, onNewScan }: SidebarProps) {
  const { user, logout } = useAuth()

  const navigation = [
    { id: 'overview', name: 'Visão Geral', icon: HomeIcon },
    { id: 'scans', name: 'Scans', icon: MagnifyingGlassIcon },
    { id: 'vulnerabilities', name: 'Vulnerabilidades', icon: ExclamationTriangleIcon },
    { id: 'chat', name: 'Chat IA', icon: ChatBubbleLeftRightIcon },
    { id: 'reports', name: 'Relatórios', icon: DocumentTextIcon },
    { id: 'settings', name: 'Configurações', icon: Cog6ToothIcon },
  ]

  return (
    <div className="w-64 bg-dark-900 border-r border-dark-700 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-dark-700">
        <div className="flex items-center">
          <div className="w-10 h-10 bg-gradient-to-br from-brand-500 to-brand-600 rounded-lg flex items-center justify-center">
            <ShieldCheckIcon className="w-6 h-6 text-white" />
          </div>
          <div className="ml-3">
            <h1 className="text-xl font-bold text-white">ScanIA</h1>
            <p className="text-xs text-dark-400">v1.0.0</p>
          </div>
        </div>
      </div>

      {/* New Scan Button */}
      <div className="p-4">
        <button
          onClick={onNewScan}
          className="w-full bg-brand-600 hover:bg-brand-700 text-white px-4 py-3 rounded-lg font-medium transition-colors flex items-center justify-center"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Novo Scan
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 pb-4">
        <ul className="space-y-2">
          {navigation.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onViewChange(item.id)}
                className={`w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors ${
                  currentView === item.id
                    ? 'bg-brand-600 text-white'
                    : 'text-dark-300 hover:bg-dark-800 hover:text-white'
                }`}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* User Info */}
      <div className="p-4 border-t border-dark-700">
        <div className="flex items-center mb-3">
          <div className="w-8 h-8 bg-brand-600 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-medium">
              {user?.full_name?.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="ml-3 flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {user?.full_name}
            </p>
            <p className="text-xs text-dark-400 truncate">
              {user?.email}
            </p>
          </div>
        </div>
        
        <button
          onClick={logout}
          className="w-full flex items-center px-3 py-2 text-dark-300 hover:bg-dark-800 hover:text-white rounded-lg transition-colors"
        >
          <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
          Sair
        </button>
      </div>
    </div>
  )
}