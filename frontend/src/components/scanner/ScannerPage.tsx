'use client';

import React, { useState } from 'react';
import ScannerForm from './ScannerForm';
import ScanProgress from './ScanProgress';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ArrowLeft } from 'lucide-react';

interface ScannerPageProps {
  initialScanId?: string;
  showBackButton?: boolean;
  onBack?: () => void;
}

const ScannerPage: React.FC<ScannerPageProps> = ({ 
  initialScanId, 
  showBackButton = false, 
  onBack 
}) => {
  const [currentScanId, setCurrentScanId] = useState<string | null>(initialScanId || null);
  const [showResults, setShowResults] = useState(false);

  const handleScanStarted = (scanId: string) => {
    setCurrentScanId(scanId);
    setShowResults(false);
  };

  const handleScanComplete = () => {
    setShowResults(true);
  };

  const handleNewScan = () => {
    setCurrentScanId(null);
    setShowResults(false);
  };

  const handleScanCancel = () => {
    // Reset to form view after cancellation
    setTimeout(() => {
      setCurrentScanId(null);
      setShowResults(false);
    }, 2000);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header with back button */}
      {showBackButton && (
        <div className="mb-6">
          <Button 
            variant="outline" 
            onClick={onBack}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Voltar</span>
          </Button>
        </div>
      )}

      {/* Main Content */}
      {!currentScanId ? (
        <>
          {/* Scanner Form */}
          <ScannerForm onScanStarted={handleScanStarted} />
          
          {/* Info Cards */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <div className="w-6 h-6 bg-blue-600 rounded"></div>
                  </div>
                  <h3 className="font-semibold text-gray-900">Análise Completa</h3>
                </div>
                <p className="text-gray-600 text-sm">
                  Identifica vulnerabilidades de segurança, portas abertas e configurações incorretas
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <div className="w-6 h-6 bg-green-600 rounded"></div>
                  </div>
                  <h3 className="font-semibold text-gray-900">Tempo Real</h3>
                </div>
                <p className="text-gray-600 text-sm">
                  Acompanhe o progresso do scan em tempo real com atualizações automáticas
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <div className="w-6 h-6 bg-purple-600 rounded"></div>
                  </div>
                  <h3 className="font-semibold text-gray-900">Relatórios</h3>
                </div>
                <p className="text-gray-600 text-sm">
                  Gere relatórios detalhados em PDF com recomendações de correção
                </p>
              </CardContent>
            </Card>
          </div>
        </>
      ) : (
        <>
          {/* Progress Tracking */}
          <ScanProgress 
            scanId={currentScanId}
            onComplete={handleScanComplete}
            onCancel={handleScanCancel}
          />

          {/* Action to start new scan */}
          <div className="mt-6 text-center">
            <Button 
              variant="outline" 
              onClick={handleNewScan}
              className="flex items-center space-x-2 mx-auto"
            >
              <span>Iniciar Novo Scan</span>
            </Button>
          </div>
        </>
      )}
    </div>
  );
};

export default ScannerPage;