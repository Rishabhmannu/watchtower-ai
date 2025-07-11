import { useEffect, useRef, useState } from 'react';

interface SystemStatus {
  banking_services: {
    healthy: number;
    total: number;
    percentage: number;
    services: Array<{
      name: string;
      healthy: boolean;
      port: string | null;
    }>;
  };
  cache: {
    connected_clients: number;
    hit_ratio: number;
  };
  overall_health: boolean;
}

interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: SystemStatus;
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = () => {
    try {
      // Close existing connection if any
      if (websocketRef.current) {
        websocketRef.current.close();
      }

      const ws = new WebSocket('ws://localhost:5050/ws');
      websocketRef.current = ws;

      // Add connection timeout
      const timeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.close();
          console.log('WebSocket connection timeout');
        }
      }, 5000);

      ws.onopen = () => {
        console.log('WebSocket connected');
        clearTimeout(timeout);  // ← Add this
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          if (message.type === 'system_status') {
            setSystemStatus(message.data);
            setLastUpdate(message.timestamp);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            console.log(`Reconnecting... attempt ${reconnectAttempts.current}`);
            connect();
          }, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket connection error - likely backend connection issue');
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setIsConnected(false);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    setIsConnected(false);
  };

  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, []);

  return {
    isConnected,
    systemStatus,
    lastUpdate,
    connect,
    disconnect,
    reconnectAttempts: reconnectAttempts.current
  };
}