'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Checkbox } from '@/components/ui/Checkbox';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Loader2, Play, Settings, Globe, Shield, Search } from 'lucide-react';

interface ScanType {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  estimatedTime: string;
  enabled: boolean;
}

interface ScannerFormProps {
  onScanStarted?: (scanId: string) => void;
}

const ScannerForm: React.FC<ScannerFormProps> = ({ onScanStarted }) => {
  const router = useRouter();
  const [targetUrl, setTargetUrl] = useState('');
  const [selectedScanTypes, setSelectedScanTypes] = useState<string[]>(['owasp_zap']);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const scanTypes: ScanType[] = [
    {
      id: 'owasp_zap',
      name: 'Vulnerabilidades Web',
      description: 'Detecta XSS, SQLi, CSRF e outras vulnerabilidades web',
      icon: <Shield className="w-5 h-5" />,
      estimatedTime: '5-15 min',
      enabled: true
    },
    {
      id: 'nmap_port',
      name: 'Scan de Portas',
      description: 'Identifica portas abertas e serviços expostos',
      icon: <Search className="w-5 h-5" />,
      estimatedTime: '2-5 min',
      enabled: true
    },
    {
      id: 'ssl_tls',
      name: 'Análise SSL/TLS',
      description: 'Verifica configuração de certificados e criptografia',
      icon: <Globe className="w-5 h-5" />,
      estimatedTime: '1-3 min',
      enabled: false
    }
  ];

  const validateUrl = (url: string): boolean => {
    try {
      new URL(url);
      return url.startsWith('http://') || url.startsWith('https://');
    } catch {
      return false;
    }
  };

  const handleScanTypeToggle = (scanTypeId: string) => {
    setSelectedScanTypes(prev => {
      if (prev.includes(scanTypeId)) {
        return prev.filter(id => id !== scanTypeId);
      } else {
        return [...prev, scanTypeId];
      }
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!targetUrl) {
      setError('Por favor, insira uma URL válida');
      return;
    }

    if (!validateUrl(targetUrl)) {
      setError('URL deve começar com http:// ou https://');
      return;
    }

    if (selectedScanTypes.length === 0) {
      setError('Selecione pelo menos um tipo de scan');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/scans', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          target_url: targetUrl,
          scan_types: selectedScanTypes,
          options: {
            // Advanced options can be added here
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao iniciar scan');
      }

      const data = await response.json();
      const scanId = data.id;

      // Call callback if provided
      if (onScanStarted) {
        onScanStarted(scanId);
      } else {
        // Navigate to scan progress page
        router.push(`/dashboard/scans/${scanId}`);
      }

    } catch (err) {
      console.error('Error starting scan:', err);
      setError(err instanceof Error ? err.message : 'Erro ao iniciar scan');
    } finally {
      setIsLoading(false);
    }
  };

  const estimatedTotalTime = () => {
    const selectedTypes = scanTypes.filter(type => selectedScanTypes.includes(type.id));
    if (selectedTypes.length === 0) return '0 min';
    
    const totalMinutes = selectedTypes.reduce((sum, type) => {
      const maxTime = parseInt(type.estimatedTime.split('-')[1]);
      return sum + maxTime;
    }, 0);
    
    return `~${Math.ceil(totalMinutes * 0.8)} min`; // 80% of sequential time (parallel execution)
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Play className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Novo Scan de Segurança</h2>
            <p className="text-gray-600">Analise vulnerabilidades em aplicações web</p>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* URL Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              URL do Target
            </label>
            <Input
              type="url"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="https://exemplo.com"
              className="w-full"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              A URL deve começar com http:// ou https://
            </p>
          </div>

          {/* Scan Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Tipos de Scan
            </label>
            <div className="space-y-3">
              {scanTypes.map((scanType) => (
                <label
                  key={scanType.id}
                  className={`flex items-start space-x-3 p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedScanTypes.includes(scanType.id)
                      ? 'bg-blue-50 border-blue-200'
                      : scanType.enabled
                      ? 'bg-white border-gray-200 hover:bg-gray-50'
                      : 'bg-gray-50 border-gray-200 cursor-not-allowed opacity-60'
                  }`}
                >
                  <Checkbox
                    checked={selectedScanTypes.includes(scanType.id)}
                    onChange={() => scanType.enabled && handleScanTypeToggle(scanType.id)}
                    disabled={!scanType.enabled}
                    className="mt-0.5"
                  />
                  <div className="flex items-start space-x-3 flex-1">
                    <div className="text-blue-600 mt-0.5">
                      {scanType.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <div className="text-sm font-medium text-gray-900">
                          {scanType.name}
                        </div>
                        <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          {scanType.estimatedTime}
                        </div>
                        {!scanType.enabled && (
                          <div className="text-xs text-orange-600 bg-orange-100 px-2 py-1 rounded">
                            Em breve
                          </div>
                        )}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {scanType.description}
                      </div>
                    </div>
                  </div>
                </label>
              ))}
            </div>
            
            {selectedScanTypes.length > 0 && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-sm text-blue-800">
                  <strong>Tempo estimado:</strong> {estimatedTotalTime()}
                </div>
              </div>
            )}
          </div>

          {/* Advanced Options */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              <Settings className="w-4 h-4" />
              <span>{showAdvanced ? 'Ocultar' : 'Mostrar'} opções avançadas</span>
            </button>
            
            {showAdvanced && (
              <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg space-y-4">
                <h4 className="text-sm font-medium text-gray-900">Opções Avançadas</h4>
                <div className="text-sm text-gray-600">
                  Configurações avançadas estarão disponíveis em breve.
                </div>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isLoading || selectedScanTypes.length === 0}
            className="w-full"
            size="lg"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Iniciando Scan...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Play className="w-4 h-4" />
                <span>Iniciar Scan</span>
              </div>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default ScannerForm;