// MCP-UI Client Library
// Consumes MCP-UI schemas from MCP servers and provides dynamic component rendering

export interface MCPUIComponent {
  type: string;
  id: string;
  title?: string;
  content?: any;
  layout?: {
    width?: string;
    height?: string;
  };
  [key: string]: any;
}

export interface MCPUIDashboard {
  title: string;
  components: MCPUIComponent[];
  layout: string;
  refreshInterval?: number;
}

export interface MCPUIStreamEvent {
  event: string;
  data: string;
}

export class MCPUIClient {
  private bankingServerUrl: string;
  private cryptoServerUrl: string;
  private apiKey: string;

  constructor(
    bankingServerUrl = 'http://localhost:8001',
    cryptoServerUrl = 'http://localhost:8000',
    apiKey = ''
  ) {
    this.bankingServerUrl = bankingServerUrl;
    this.cryptoServerUrl = cryptoServerUrl;
    this.apiKey = apiKey;
  }

  // Banking Dashboard Methods
  async getBankingDashboard(accountId: string, token: string): Promise<MCPUIDashboard> {
    const response = await fetch(`${this.bankingServerUrl}/mcp-ui/dashboard/${accountId}`, {
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'X-Auth-Token': token,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch banking dashboard: ${response.statusText}`);
    }

    return response.json();
  }

  async getBalanceCard(accountId: string, token: string): Promise<{ component: MCPUIComponent }> {
    const response = await fetch(
      `${this.bankingServerUrl}/mcp-ui/components/balance-card/${accountId}`,
      {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'X-Auth-Token': token,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch balance card: ${response.statusText}`);
    }

    return response.json();
  }

  async getTransactionChart(
    accountId: string,
    days = 30,
    token: string
  ): Promise<{ component: MCPUIComponent }> {
    const response = await fetch(
      `${this.bankingServerUrl}/mcp-ui/components/transaction-chart/${accountId}?days=${days}`,
      {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'X-Auth-Token': token,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch transaction chart: ${response.statusText}`);
    }

    return response.json();
  }

  async getContactsWidget(token: string): Promise<{ component: MCPUIComponent }> {
    const response = await fetch(`${this.bankingServerUrl}/mcp-ui/components/contacts-widget`, {
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'X-Auth-Token': token,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch contacts widget: ${response.statusText}`);
    }

    return response.json();
  }

  // Crypto Dashboard Methods
  async getCryptoPortfolioDashboard(token: string): Promise<MCPUIDashboard> {
    const response = await fetch(`${this.cryptoServerUrl}/mcp-ui/portfolio-dashboard`, {
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'X-Auth-Token': token,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch crypto portfolio dashboard: ${response.statusText}`);
    }

    return response.json();
  }

  async getPriceWidget(tokenId: string, token: string): Promise<{ component: MCPUIComponent }> {
    const response = await fetch(
      `${this.cryptoServerUrl}/mcp-ui/components/price-widget/${tokenId}`,
      {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          'X-Auth-Token': token,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch price widget: ${response.statusText}`);
    }

    return response.json();
  }

  async getPortfolioChart(token: string): Promise<{ component: MCPUIComponent }> {
    const response = await fetch(`${this.cryptoServerUrl}/mcp-ui/components/portfolio-chart`, {
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'X-Auth-Token': token,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch portfolio chart: ${response.statusText}`);
    }

    return response.json();
  }

  async getRiskDashboard(token: string): Promise<{ component: MCPUIComponent }> {
    const response = await fetch(`${this.cryptoServerUrl}/mcp-ui/components/risk-dashboard`, {
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'X-Auth-Token': token,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch risk dashboard: ${response.statusText}`);
    }

    return response.json();
  }

  async getTradingSignals(token: string): Promise<{ component: MCPUIComponent }> {
    const response = await fetch(`${this.cryptoServerUrl}/mcp-ui/components/trading-signals`, {
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'X-Auth-Token': token,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch trading signals: ${response.statusText}`);
    }

    return response.json();
  }

  // Real-time Streaming Methods
  subscribeToBalanceUpdates(
    accountId: string,
    token: string,
    onUpdate: (data: any) => void
  ): EventSource {
    const eventSource = new EventSource(
      `${this.bankingServerUrl}/mcp-ui/stream/balance-updates/${accountId}?token=${token}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (error) {
        console.error('Failed to parse balance update:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('Balance updates stream error:', error);
    };

    return eventSource;
  }

  subscribeToTransactionNotifications(
    accountId: string,
    token: string,
    onUpdate: (data: any) => void
  ): EventSource {
    const eventSource = new EventSource(
      `${this.bankingServerUrl}/mcp-ui/stream/transaction-notifications/${accountId}?token=${token}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (error) {
        console.error('Failed to parse transaction notification:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('Transaction notifications stream error:', error);
    };

    return eventSource;
  }

  subscribeToPriceUpdates(
    tokenId: string,
    token: string,
    onUpdate: (data: any) => void
  ): EventSource {
    const eventSource = new EventSource(
      `${this.cryptoServerUrl}/mcp-ui/stream/price-updates/${tokenId}?token=${token}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (error) {
        console.error('Failed to parse price update:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('Price updates stream error:', error);
    };

    return eventSource;
  }

  subscribeToPortfolioUpdates(token: string, onUpdate: (data: any) => void): EventSource {
    const eventSource = new EventSource(
      `${this.cryptoServerUrl}/mcp-ui/stream/portfolio-updates?token=${token}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (error) {
        console.error('Failed to parse portfolio update:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('Portfolio updates stream error:', error);
    };

    return eventSource;
  }

  subscribeToTradingSignals(token: string, onUpdate: (data: any) => void): EventSource {
    const eventSource = new EventSource(
      `${this.cryptoServerUrl}/mcp-ui/stream/trading-signals?token=${token}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onUpdate(data);
      } catch (error) {
        console.error('Failed to parse trading signals:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('Trading signals stream error:', error);
    };

    return eventSource;
  }
}

// Default client instance
export const mcpUIClient = new MCPUIClient();

// Component Type Registry
export interface ComponentRenderer {
  (component: MCPUIComponent): React.ReactElement | null;
}

const componentRenderers: Record<string, ComponentRenderer> = {};

export function registerComponentRenderer(type: string, renderer: ComponentRenderer): void {
  componentRenderers[type] = renderer;
}

export function renderMCPUIComponent(component: MCPUIComponent): React.ReactElement | null {
  const renderer = componentRenderers[component.type];
  if (!renderer) {
    console.warn(`No renderer registered for component type: ${component.type}`);
    return null;
  }
  return renderer(component);
}
