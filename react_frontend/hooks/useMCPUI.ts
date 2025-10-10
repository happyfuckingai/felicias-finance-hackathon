import { useCallback, useEffect, useState } from 'react';
import { MCPUIComponent, MCPUIDashboard, mcpUIClient } from '@/lib/mcp-ui-client';
import { useStreamingDashboardUpdate } from './useMCPUIStreaming';

export interface MCPUIState {
  bankingDashboard: MCPUIDashboard | null;
  cryptoDashboard: MCPUIDashboard | null;
  currentView: 'banking' | 'crypto' | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export function useMCPUI() {
  const [state, setState] = useState<MCPUIState>({
    bankingDashboard: null,
    cryptoDashboard: null,
    currentView: null,
    loading: false,
    error: null,
    lastUpdated: null,
  });

  const [authToken, setAuthToken] = useState<string>('');
  const [accountId, setAccountId] = useState<string>('123456789');

  const streaming = useStreamingDashboardUpdate((componentId, updates) => {
    updateComponent(componentId, updates);
  });

  const loadBankingDashboard = useCallback(async () => {
    if (!authToken) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const dashboard = await mcpUIClient.getBankingDashboard(accountId, authToken);
      setState((prev) => ({
        ...prev,
        bankingDashboard: dashboard,
        currentView: 'banking',
        loading: false,
        lastUpdated: new Date(),
      }));

      // Setup streaming for banking
      streaming.setupBankingStreaming(accountId, authToken);
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load banking dashboard',
      }));
    }
  }, [authToken, accountId, streaming]);

  const loadCryptoDashboard = useCallback(async () => {
    if (!authToken) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const dashboard = await mcpUIClient.getCryptoPortfolioDashboard(authToken);
      setState((prev) => ({
        ...prev,
        cryptoDashboard: dashboard,
        currentView: 'crypto',
        loading: false,
        lastUpdated: new Date(),
      }));

      // Setup streaming for crypto
      streaming.setupCryptoStreaming(authToken);
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load crypto dashboard',
      }));
    }
  }, [authToken, streaming]);

  const switchToBanking = useCallback(() => {
    if (state.bankingDashboard) {
      setState((prev) => ({ ...prev, currentView: 'banking' }));
    } else {
      loadBankingDashboard();
    }
  }, [state.bankingDashboard, loadBankingDashboard]);

  const switchToCrypto = useCallback(() => {
    if (state.cryptoDashboard) {
      setState((prev) => ({ ...prev, currentView: 'crypto' }));
    } else {
      loadCryptoDashboard();
    }
  }, [state.cryptoDashboard, loadCryptoDashboard]);

  const updateComponent = useCallback((componentId: string, updates: Partial<MCPUIComponent>) => {
    setState((prev) => {
      const newState = { ...prev };

      if (prev.currentView === 'banking' && prev.bankingDashboard) {
        newState.bankingDashboard = {
          ...prev.bankingDashboard,
          components: prev.bankingDashboard.components.map((comp) =>
            comp.id === componentId ? { ...comp, ...updates } : comp
          ),
        };
      } else if (prev.currentView === 'crypto' && prev.cryptoDashboard) {
        newState.cryptoDashboard = {
          ...prev.cryptoDashboard,
          components: prev.cryptoDashboard.components.map((comp) =>
            comp.id === componentId ? { ...comp, ...updates } : comp
          ),
        };
      }

      newState.lastUpdated = new Date();
      return newState;
    });
  }, []);

  const refreshCurrentDashboard = useCallback(() => {
    if (state.currentView === 'banking') {
      loadBankingDashboard();
    } else if (state.currentView === 'crypto') {
      loadCryptoDashboard();
    }
  }, [state.currentView, loadBankingDashboard, loadCryptoDashboard]);

  const clearDashboards = useCallback(() => {
    setState({
      bankingDashboard: null,
      cryptoDashboard: null,
      currentView: null,
      loading: false,
      error: null,
      lastUpdated: null,
    });
    streaming.unsubscribeAll();
  }, [streaming]);

  // Cleanup streaming on unmount
  useEffect(() => {
    return () => {
      streaming.unsubscribeAll();
    };
  }, [streaming]);

  return {
    ...state,
    authToken,
    setAuthToken,
    accountId,
    setAccountId,
    loadBankingDashboard,
    loadCryptoDashboard,
    switchToBanking,
    switchToCrypto,
    updateComponent,
    refreshCurrentDashboard,
    clearDashboards,
    activeConnections: streaming.activeConnections,
  };
}
