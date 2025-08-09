'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface ThemeContextType {
  isDark: boolean
  toggleTheme: () => void
  setTheme: (theme: 'light' | 'dark') => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(true) // Default to dark mode

  useEffect(() => {
    // Check for saved theme preference or default to dark
    if (typeof window === 'undefined') return
    
    const savedTheme = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    const shouldBeDark = savedTheme ? savedTheme === 'dark' : prefersDark !== false
    
    setIsDark(shouldBeDark)
    updateTheme(shouldBeDark)
  }, [])

  const updateTheme = (dark: boolean) => {
    if (typeof window === 'undefined') return
    
    const root = document.documentElement
    if (dark) {
      root.classList.add('dark')
      root.style.colorScheme = 'dark'
    } else {
      root.classList.remove('dark')
      root.style.colorScheme = 'light'
    }
  }

  const toggleTheme = () => {
    const newTheme = !isDark
    setIsDark(newTheme)
    updateTheme(newTheme)
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', newTheme ? 'dark' : 'light')
    }
  }

  const setTheme = (theme: 'light' | 'dark') => {
    const dark = theme === 'dark'
    setIsDark(dark)
    updateTheme(dark)
    if (typeof window !== 'undefined') {
      localStorage.setItem('theme', theme)
    }
  }

  const value = {
    isDark,
    toggleTheme,
    setTheme
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}