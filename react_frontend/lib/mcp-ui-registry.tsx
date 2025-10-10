// MCP-UI Component Registry
// Registers all MCP-UI component renderers
// Banking Components
import { BalanceCard } from '@/components/mcp-ui/banking/balance-card';
import { ContactsWidget } from '@/components/mcp-ui/banking/contacts-widget';
import { TransactionChart } from '@/components/mcp-ui/banking/transaction-chart';
import { PortfolioChart } from '@/components/mcp-ui/crypto/portfolio-chart';
// Crypto Components
import { PriceWidget } from '@/components/mcp-ui/crypto/price-widget';
import { RiskDashboard } from '@/components/mcp-ui/crypto/risk-dashboard';
import { TradingSignals } from '@/components/mcp-ui/crypto/trading-signals';
import { registerComponentRenderer } from './mcp-ui-client';

// Register all component renderers
export function initializeMCPUIComponents() {
  // Banking components
  registerComponentRenderer('card', (component) => <BalanceCard component={component} />);
  registerComponentRenderer('chart', (component) => <TransactionChart component={component} />);
  registerComponentRenderer('contacts', (component) => <ContactsWidget component={component} />);

  // Crypto components
  registerComponentRenderer('price-card', (component) => <PriceWidget component={component} />);
  registerComponentRenderer('risk-dashboard', (component) => (
    <RiskDashboard component={component} />
  ));
  registerComponentRenderer('signals-list', (component) => (
    <TradingSignals component={component} />
  ));

  // Generic components that work for both
  registerComponentRenderer('metric', (component) => <BalanceCard component={component} />);
  registerComponentRenderer('list', (component) => <ContactsWidget component={component} />);
  registerComponentRenderer('actions', (component) => {
    // Simple actions renderer - can be expanded
    return (
      <div className="flex gap-2 p-4">
        {component.actions?.map((action: any, index: number) => (
          <button
            key={index}
            className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-md px-4 py-2"
          >
            {action.label}
          </button>
        ))}
      </div>
    );
  });
}

// Call this once at app initialization
initializeMCPUIComponents();
