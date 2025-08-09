import { useEffect, useRef, useCallback, useState } from 'react';

export interface WebSocketMessage {
  data: string;
  timestamp: Date;
}

export interface WebSocketOptions {
  reconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export interface WebSocketHook {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: string) => void;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error';
}

export const useWebSocket = (
  url: string | null,
  options: WebSocketOptions = {}
): WebSocketHook => {
  const {
    reconnect = true,
    maxReconnectAttempts = 5,
    reconnectInterval = 1000,
    onOpen,
    onClose,
    onError,
    onMessage
  } = options;

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutId = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef<number>(0);
  const shouldReconnect = useRef<boolean>(true);

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');

  const connect = useCallback(() => {
    if (!url || ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    if (ws.current) {
      ws.current.close();
    }

    setConnectionState('connecting');
    
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = (event) => {
        console.log('WebSocket connected:', url);
        setIsConnected(true);
        setConnectionState('connected');
        reconnectAttempts.current = 0;
        
        if (reconnectTimeoutId.current) {
          clearTimeout(reconnectTimeoutId.current);
          reconnectTimeoutId.current = null;
        }
        
        onOpen?.(event);
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        setConnectionState('disconnected');
        
        onClose?.(event);

        // Attempt reconnection if enabled and not manually closed
        if (
          reconnect &&
          shouldReconnect.current &&
          event.code !== 1000 &&
          reconnectAttempts.current < maxReconnectAttempts
        ) {
          const timeout = reconnectInterval * Math.pow(2, reconnectAttempts.current);
          console.log(`Attempting to reconnect in ${timeout}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeoutId.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, timeout);
        }
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setConnectionState('error');
        onError?.(event);
      };

      ws.current.onmessage = (event) => {
        const message: WebSocketMessage = {
          data: event.data,
          timestamp: new Date()
        };
        
        setLastMessage(message);
        onMessage?.(message);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionState('error');
    }
  }, [url, reconnect, maxReconnectAttempts, reconnectInterval, onOpen, onClose, onError, onMessage]);

  const disconnect = useCallback(() => {
    shouldReconnect.current = false;
    
    if (reconnectTimeoutId.current) {
      clearTimeout(reconnectTimeoutId.current);
      reconnectTimeoutId.current = null;
    }
    
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.close(1000, 'Manual disconnect');
    }
    
    ws.current = null;
    setIsConnected(false);
    setConnectionState('disconnected');
  }, []);

  const reconnectManually = useCallback(() => {
    shouldReconnect.current = true;
    reconnectAttempts.current = 0;
    disconnect();
    setTimeout(() => connect(), 100);
  }, [connect, disconnect]);

  const sendMessage = useCallback((message: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(message);
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, []);

  // Auto-connect when URL changes
  useEffect(() => {
    if (url) {
      shouldReconnect.current = true;
      connect();
    }

    return () => {
      shouldReconnect.current = false;
      if (reconnectTimeoutId.current) {
        clearTimeout(reconnectTimeoutId.current);
      }
      if (ws.current) {
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [url, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    reconnect: reconnectManually,
    connectionState
  };
};