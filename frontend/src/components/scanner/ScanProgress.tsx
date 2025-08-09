'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/Progress';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { 
  Play, 
  Pause, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Shield, 
  Search, 
  Globe,
  AlertTriangle,
  Zap
} from 'lucide-react';
import { useRouter } from 'next/navigation';

interface ScanProgressData {
  type: string;
  scan_id: string;
  overall_progress: number;
  message: string;
  status: string;
  timestamp: number;
  scanner_type?: string;
  scanner_progress?: Record<string, number>;
  vulnerability_summary?: Record<string, number>;
  duration_seconds?: number;
}

interface ScanProgressProps {
  scanId: string;
  onComplete?: () => void;
  onCancel?: () => void;
}

const ScanProgress: React.FC<ScanProgressProps> = ({ 
  scanId, 
  onComplete,
  onCancel 
}) => {
  const router = useRouter();
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('pending');
  const [message, setMessage] = useState('Preparando scan...');
  const [scannerProgress, setScannerProgress] = useState<Record<string, number>>({});
  const [currentScanner, setCurrentScanner] = useState<string>('');
  const [vulnerabilitySummary, setVulnerabilitySummary] = useState<Record<string, number>>({});
  const [duration, setDuration] = useState<number>(0);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [error, setError] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Scanner icons mapping
  const scannerIcons: Record<string, React.ReactNode> = {
    'owasp_zap': <Shield className="w-4 h-4" />,
    'nmap_port': <Search className="w-4 h-4" />,
    'ssl_tls': <Globe className="w-4 h-4" />
  };

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (!scanId) return null;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = localStorage.getItem('access_token') || '';
    
    const ws = new WebSocket(`${protocol}//${host}/api/v1/ws/scan/${scanId}/progress?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected to scan:', scanId);
      setIsConnected(true);
      setReconnectAttempts(0);
      setError('');
    };

    ws.onmessage = (event) => {
      try {
        const data: ScanProgressData = JSON.parse(event.data);
        
        if (data.type === 'progress_update') {
          setProgress(data.overall_progress);
          setStatus(data.status);
          setMessage(data.message);
          
          if (data.scanner_type) {
            setCurrentScanner(data.scanner_type);
          }
          
          if (data.scanner_progress) {
            setScannerProgress(data.scanner_progress);
          }
          
          // Set start time on first progress update
          if (data.status === 'running' && !startTime) {
            setStartTime(new Date());
          }
          
        } else if (data.type === 'scan_completion') {
          setProgress(data.overall_progress);
          setStatus(data.status);
          setMessage(data.message);
          
          if (data.vulnerability_summary) {
            setVulnerabilitySummary(data.vulnerability_summary);
          }
          
          if (data.duration_seconds) {
            setDuration(data.duration_seconds);
          }
          
          // Call completion callback after a short delay
          setTimeout(() => {
            if (onComplete) {
              onComplete();
            }
          }, 2000);
          
        } else if (data.type === 'heartbeat') {
          // Handle heartbeat (keep connection alive)
          console.log('Heartbeat received for scan:', data.scan_id);
        }
        
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      setIsConnected(false);
      
      // Attempt to reconnect if not a normal closure
      if (event.code !== 1000 && reconnectAttempts < 5) {
        const timeout = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
        setTimeout(() => {
          setReconnectAttempts(prev => prev + 1);
          connectWebSocket();
        }, timeout);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Erro de conexão. Tentando reconectar...');
    };

    return ws;
  }, [scanId, startTime, onComplete, reconnectAttempts]);

  useEffect(() => {
    const ws = connectWebSocket();
    
    return () => {
      if (ws) {
        ws.close(1000, 'Component unmounted');
      }
    };
  }, [connectWebSocket]);

  // Timer for elapsed time
  useEffect(() => {
    if (startTime && status === 'running') {
      const interval = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now.getTime() - startTime.getTime()) / 1000);
        setDuration(elapsed);
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [startTime, status]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-600';
      case 'running': return 'text-blue-600';
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'cancelled': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-5 h-5" />;
      case 'running': return <Play className="w-5 h-5" />;
      case 'completed': return <CheckCircle className="w-5 h-5" />;
      case 'failed': return <XCircle className="w-5 h-5" />;
      case 'cancelled': return <Pause className="w-5 h-5" />;
      default: return <Clock className="w-5 h-5" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return 'Aguardando';
      case 'running': return 'Executando';
      case 'completed': return 'Concluído';
      case 'failed': return 'Falhou';
      case 'cancelled': return 'Cancelado';
      default: return 'Status desconhecido';
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const handleCancel = async () => {
    try {
      const response = await fetch(`/api/v1/scans/${scanId}/cancel`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Erro ao cancelar scan');
      }

      if (onCancel) {
        onCancel();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao cancelar scan');
    }
  };

  const handleViewResults = () => {
    router.push(`/dashboard/scans/${scanId}`);
  };

  const getTotalVulnerabilities = () => {
    return Object.values(vulnerabilitySummary).reduce((sum, count) => sum + count, 0);
  };

  return (
    <Card className="max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`text-2xl ${getStatusColor(status)}`}>
              {getStatusIcon(status)}
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">
                Progresso do Scan
              </h3>
              <p className={`text-sm font-medium ${getStatusColor(status)}`}>
                {getStatusText(status)}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            {duration > 0 && (
              <>
                <Clock className="w-4 h-4" />
                <span>{formatDuration(duration)}</span>
              </>
            )}
            {!isConnected && (
              <div className="flex items-center space-x-1 text-orange-600">
                <AlertTriangle className="w-4 h-4" />
                <span>Reconectando...</span>
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Progresso Geral</span>
            <span className="text-sm text-gray-600">{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-3" />
          <p className="text-sm text-gray-600 mt-2">{message}</p>
        </div>

        {/* Current Scanner */}
        {currentScanner && status === 'running' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 text-blue-800">
              {scannerIcons[currentScanner]}
              <span className="font-medium">
                Executando: {currentScanner.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          </div>
        )}

        {/* Scanner Progress Details */}
        {Object.keys(scannerProgress).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              Detalhes por Scanner
            </h4>
            <div className="space-y-3">
              {Object.entries(scannerProgress).map(([scanner, scannerProg]) => (
                <div key={scanner}>
                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <div className="flex items-center space-x-2">
                      {scannerIcons[scanner]}
                      <span className="capitalize">
                        {scanner.replace('_', ' ')}
                      </span>
                    </div>
                    <span>{Math.round(scannerProg)}%</span>
                  </div>
                  <Progress value={scannerProg} className="h-2" />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Vulnerability Summary */}
        {status === 'completed' && Object.keys(vulnerabilitySummary).length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 text-green-800 mb-3">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Scan Concluído!</span>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
              {Object.entries(vulnerabilitySummary).map(([severity, count]) => (
                <div key={severity} className="text-center">
                  <div className="text-lg font-bold text-gray-900">{count}</div>
                  <div className="text-xs text-gray-600 capitalize">{severity}</div>
                </div>
              ))}
              <div className="text-center border-l border-gray-300 pl-2">
                <div className="text-lg font-bold text-blue-600">{getTotalVulnerabilities()}</div>
                <div className="text-xs text-gray-600">Total</div>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Actions */}
        <div className="flex space-x-3">
          {status === 'running' && (
            <Button onClick={handleCancel} variant="outline" size="sm">
              Cancelar Scan
            </Button>
          )}
          
          {status === 'completed' && (
            <Button onClick={handleViewResults} className="flex items-center space-x-2">
              <Zap className="w-4 h-4" />
              <span>Ver Resultados</span>
            </Button>
          )}
          
          {(status === 'failed' || status === 'cancelled') && (
            <Button onClick={() => router.push('/dashboard/scans')} variant="outline">
              Voltar aos Scans
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ScanProgress;