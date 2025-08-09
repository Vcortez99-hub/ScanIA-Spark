import './globals.css'
import { Inter } from 'next/font/google'
import { ClientProviders } from '@/components/providers/ClientProviders'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'ScanIA - Sistema Inteligente de Análise de Cybersegurança',
  description: 'Sistema completo de análise de vulnerabilidades e cybersegurança',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className="dark">
      <body className={`${inter.className} bg-gray-900 text-gray-100 min-h-screen`}>
        <ClientProviders>
          {children}
        </ClientProviders>
      </body>
    </html>
  )
}