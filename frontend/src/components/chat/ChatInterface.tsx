'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  PaperAirplaneIcon,
  ChatBubbleLeftRightIcon,
  UserIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Olá! Eu sou o assistente de IA do ScanIA. Como posso ajudá-lo com suas análises de cybersegurança hoje?',
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Esta funcionalidade está em desenvolvimento. Em breve você poderá conversar comigo sobre vulnerabilidades, análises de segurança e obter recomendações personalizadas para melhorar a segurança de seus sistemas.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiMessage])
      setIsTyping(false)
    }, 2000)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-brand-500 to-brand-600 rounded-xl flex items-center justify-center">
          <ChatBubbleLeftRightIcon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4">
          <h1 className="text-3xl font-bold text-white">Chat com IA</h1>
          <p className="text-dark-400">Converse sobre cybersegurança com nosso assistente inteligente</p>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 bg-dark-800 border border-dark-700 rounded-2xl flex flex-col overflow-hidden">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start max-w-3xl ${
                message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}>
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user' 
                    ? 'bg-brand-600 ml-3' 
                    : 'bg-dark-700 mr-3'
                }`}>
                  {message.role === 'user' ? (
                    <UserIcon className="w-4 h-4 text-white" />
                  ) : (
                    <CpuChipIcon className="w-4 h-4 text-dark-300" />
                  )}
                </div>

                {/* Message Bubble */}
                <div className={`px-4 py-3 rounded-2xl ${
                  message.role === 'user'
                    ? 'bg-brand-600 text-white'
                    : 'bg-dark-700 text-dark-100'
                }`}>
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  <p className={`text-xs mt-2 ${
                    message.role === 'user' 
                      ? 'text-brand-200' 
                      : 'text-dark-400'
                  }`}>
                    {message.timestamp.toLocaleTimeString('pt-BR', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="flex items-start max-w-3xl">
                <div className="w-8 h-8 bg-dark-700 rounded-full flex items-center justify-center mr-3">
                  <CpuChipIcon className="w-4 h-4 text-dark-300" />
                </div>
                <div className="bg-dark-700 px-4 py-3 rounded-2xl">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-dark-400 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-dark-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-dark-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-dark-700 p-4">
          <div className="flex items-end gap-3">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua pergunta sobre cybersegurança..."
              className="form-textarea flex-1 resize-none max-h-32"
              rows={1}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isTyping}
              className="btn-primary p-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </div>
          
          <div className="flex flex-wrap gap-2 mt-3">
            <button 
              onClick={() => setInputValue('Quais são as principais vulnerabilidades encontradas nos meus scans?')}
              className="px-3 py-1 bg-dark-700 hover:bg-dark-600 text-dark-300 hover:text-white rounded-lg text-sm transition-colors"
            >
              Principais vulnerabilidades
            </button>
            <button 
              onClick={() => setInputValue('Como posso melhorar a segurança do meu website?')}
              className="px-3 py-1 bg-dark-700 hover:bg-dark-600 text-dark-300 hover:text-white rounded-lg text-sm transition-colors"
            >
              Melhorar segurança
            </button>
            <button 
              onClick={() => setInputValue('Explique o que é uma vulnerabilidade crítica')}
              className="px-3 py-1 bg-dark-700 hover:bg-dark-600 text-dark-300 hover:text-white rounded-lg text-sm transition-colors"
            >
              O que é vulnerabilidade crítica?
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}