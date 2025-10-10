import { useCallback, useEffect, useRef, useState } from 'react';

interface MCPUIStreamMessage {
  type: string;
  [key: string]: any;
}

interface UseMCPUIStreamingOptions {
  onMessage: (message: MCPUIStreamMessage) => void;
  refreshInterval?: number;
  errorHandler?: (error: Error) => void;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
}

interface UseMCPUIStreamingReturn {
  isConnected: boolean;
  error: Error | null;
  reconnect: () => void;
  disconnect: () => void;
}

export function useMCPUIStreaming(
  endpoint: string,
  options: UseMCPUIStreamingOptions
): UseMCPUIStreamingReturn {
  const {
    onMessage,
    refreshInterval = 30000,
    errorHandler,
    autoReconnect = true,
    maxReconnectAttempts = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const eventSource = new EventSource(endpoint);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        console.log(`Connected to MCP-UI stream: ${endpoint}`);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (parseError) {
          console.error('Failed to parse MCP-UI stream message:', parseError);
        }
      };

      eventSource.onerror = (event) => {
        const connectionError = new Error(`MCP-UI stream connection failed: ${endpoint}`);
        setError(connectionError);
        setIsConnected(false);

        if (errorHandler) {
          errorHandler(connectionError);
        }

        // Auto-reconnect logic
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(
              `Attempting to reconnect to MCP-UI stream (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
            );
            connect();
          }, delay);
        }
      };
    } catch (connectionError) {
      const error =
        connectionError instanceof Error ? connectionError : new Error('Unknown connection error');
      setError(error);
      setIsConnected(false);

      if (errorHandler) {
        errorHandler(error);
      }
    }
  }, [endpoint, onMessage, errorHandler, autoReconnect, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsConnected(false);
    setError(null);
  }, []);

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    disconnect();
    connect();
  }, [connect, disconnect]);

  // Auto-connect on mount and endpoint change
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    error,
    reconnect,
    disconnect,
  };
}

// Specialized hooks for specific MCP-UI streams

export function useBalanceUpdates(accountId: string, onUpdate: (data: any) => void) {
  return useMCPUIStreaming(`/mcp-ui/stream/balance-updates/${accountId}`, {
    onMessage: (message) => {
      if (message.type === 'balance_update') {
        onUpdate(message);
      }
    },
    refreshInterval: 30000,
  });
}

export function usePriceUpdates(tokenId: string, onUpdate: (data: any) => void) {
  return useMCPUIStreaming(`/mcp-ui/stream/price-updates/${tokenId}`, {
    onMessage: (message) => {
      if (message.type === 'price_update') {
        onUpdate(message);
      }
    },
    refreshInterval: 30000,
  });
}

export function usePortfolioUpdates(onUpdate: (data: any) => void) {
  return useMCPUIStreaming('/mcp-ui/stream/portfolio-updates', {
    onMessage: (message) => {
      if (message.type === 'portfolio_update') {
        onUpdate(message);
      }
    },
    refreshInterval: 45000,
  });
}

export function useTradingSignals(onUpdate: (data: any) => void) {
  return useMCPUIStreaming('/mcp-ui/stream/trading-signals', {
    onMessage: (message) => {
      if (message.type === 'trading_signals_update') {
        onUpdate(message);
      }
    },
    refreshInterval: 120000, // 2 minutes for signals
  });
}

export function useRiskAlerts(onUpdate: (data: any) => void) {
  return useMCPUIStreaming('/mcp-ui/stream/risk-alerts', {
    onMessage: (message) => {
      if (message.type === 'risk_alert') {
        onUpdate(message);
      }
    },
    refreshInterval: 30000,
  });
}

// Dashboard streaming hook for component updates
export function useStreamingDashboardUpdate(
  onComponentUpdate: (componentId: string, updates: any) => void
) {
  const setupBankingStreaming = useCallback((accountId: string, token: string) => {
    // Balance updates
    useBalanceUpdates(accountId, (data) => {
      onComponentUpdate('account_balance', {
        value: `$${data.balance?.toLocaleString() || '0.00'}`,
        lastUpdated: data.timestamp
      });
    });

    // Transaction notifications
    useMCPUIStreaming(`/mcp-ui/stream/transaction-notifications/${accountId}?token=${token}`, {
      onMessage: (message) => {
        if (message.type === 'transaction_notification') {
          // Handle transaction notifications
          console.log('New transaction:', message.transaction);
        }
      }
    });
  }, [onComponentUpdate]);

  const setupCryptoStreaming = useCallback((token: string) => {
    // Portfolio updates
    usePortfolioUpdates((data) => {
      onComponentUpdate('portfolio_overview', {
        content: {
          type: 'metric',
          value: `$${data.total_value?.toLocaleString() || '0.00'}`,
          change: `${data.change_24h?.toFixed(2) || '0.00'}%`,
          changeType: (data.change_24h > 0) ? 'positive' : 'negative'
        }
      });
    });

    // Trading signals
    useTradingSignals((data) => {
      onComponentUpdate('trading_signals', {
        signals: data.signals || [],
        lastUpdated: data.timestamp
      });
    });
  }, [onComponentUpdate]);

  const setupPriceStreaming = useCallback((tokenId: string, componentId: string, token: string) => {
    usePriceUpdates(tokenId, (data) => {
      onComponentUpdate(componentId, {
        price: `$${data.price?.toLocaleString() || '0.00'}`,
        change: `${data.change_24h?.toFixed(2) || '0.00'}%`,
        changeType: data.change_24h > 0 ? 'positive' : 'negative',
        volume: `$${(data.volume_24h / 1000000)?.toFixed(1) || '0.0'}M`,
        lastUpdated: data.timestamp
      });
    });
  }, [onComponentUpdate]);

  const unsubscribeAll = useCallback(() => {
    // For now, no cleanup needed as EventSources handle their own cleanup
    console.log('Streaming cleanup completed');
  }, []);

  return {
    setupBankingStreaming,
    setupCryptoStreaming,
    setupPriceStreaming,
    unsubscribeAll,
    activeConnections: 0 // TODO: track actual connections
  };
}
