# MCP-UI Data Flow Architecture

## 🏗️ Component Hierarchy & Data Flow

```mermaid
graph TB
    subgraph "MCP Servers"
        B[BANKING<br/>MCP Server<br/>Port 8001]
        C[CRYPTO<br/>MCP Server<br/>Port 8000]
    end

    subgraph "UI Layer"
        MCP[MCP-UI<br/>Registry]
        STREAM[MCP-UI<br/>Streaming<br/>Client]
    end

    subgraph "Glassmorphism Components"
        subgraph "Banking Components"
            BCARD[BalanceCard]
            BCHART[TransactionChart]
            BACTIONS[QuickActions]
            BCONTACTS[ContactsWidget]
        end

        subgraph "Crypto Components"
            CCARD[PriceWidget]
            CPORT[PortfolioChart]
            CRISK[RiskDashboard]
            CSIGNALS[TradingSignals]
        end
    end

    subgraph "Real-time Streams"
        BSTREAM[Balance<br/>Updates<br/>SSE]
        TSTREAM[Transaction<br/>Notifications<br/>SSE]
        PSTREAM[Portfolio<br/>Updates<br/>SSE]
        SIGSTREAM[Trading<br/>Signals<br/>SSE]
        RISKSTREAM[Risk<br/>Alerts<br/>SSE]
    end

    %% Data Flow
    B --> MCP
    C --> MCP

    MCP --> BCARD
    MCP --> BCHART
    MCP --> BACTIONS
    MCP --> BCONTACTS

    MCP --> CCARD
    MCP --> CPORT
    MCP --> CRISK
    MCP --> CSIGNALS

    %% Streaming Flow
    B --> BSTREAM
    B --> TSTREAM
    C --> PSTREAM
    C --> SIGSTREAM
    C --> RISKSTREAM

    BSTREAM --> STREAM
    TSTREAM --> STREAM
    PSTREAM --> STREAM
    SIGSTREAM --> STREAM
    RISKSTREAM --> STREAM

    STREAM --> BCARD
    STREAM --> BCHART
    STREAM --> CCARD
    STREAM --> CPORT
    STREAM --> CRISK
    STREAM --> CSIGNALS

    %% Styling
    classDef banking fill:#3b82f6,stroke:#1e40af,stroke-width:2px
    classDef crypto fill:#10b981,stroke:#047857,stroke-width:2px
    classDef server fill:#f59e0b,stroke:#d97706,stroke-width:2px
    classDef stream fill:#ef4444,stroke:#dc2626,stroke-width:2px
    classDef ui fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px

    class B,C server
    class MCP,STREAM ui
    class BCARD,BCHART,BACTIONS,BCONTACTS banking
    class CCARD,CPORT,CRISK,CSIGNALS crypto
    class BSTREAM,TSTREAM,PSTREAM,SIGSTREAM,RISKSTREAM stream
```

## 🔄 Detailed Data Flow Patterns

### 1. Component Initialization Flow

```mermaid
sequenceDiagram
    participant UI as MCP-UI Client
    participant REG as Component Registry
    participant API as MCP Server API
    participant COMP as Glassmorphism Component

    UI->>REG: Request component data
    REG->>API: Fetch backend schema
    API-->>REG: Return JSON component definition
    REG-->>UI: Transform to component props
    UI->>COMP: Render with glassmorphism styling
    COMP-->>UI: Interactive component ready
```

### 2. Real-time Update Flow

```mermaid
sequenceDiagram
    participant COMP as Component
    participant STREAM as MCP Streaming Client
    participant SSE as SSE Endpoint
    participant SERVER as MCP Server

    COMP->>STREAM: Subscribe to updates
    STREAM->>SSE: Connect to SSE stream
    SSE->>SERVER: Request real-time data
    SERVER-->>SSE: Stream data events
    SSE-->>STREAM: Forward events
    STREAM-->>COMP: Update component state
    COMP->>COMP: Animate changes with glass effects
```

### 3. Error Handling Flow

```mermaid
flowchart TD
    A[Component Request] --> B{Data Available?}
    B -->|Yes| C[Render Component]
    B -->|No| D[Show Loading State]
    D --> E{Timeout?}
    E -->|No| F[Retry Request]
    E -->|Yes| G[Show Error State]
    G --> H[Display Glass Error Card]
    H --> I[Offer Retry Action]

    C --> J[Subscribe to Updates]
    J --> K[Real-time Updates Active]

    classDef success fill:#10b981,color:#fff
    classDef error fill:#ef4444,color:#fff
    classDef warning fill:#f59e0b,color:#000

    class C,K success
    class G,H,I error
    class D,F warning
```

## 📊 Component State Management

### Banking Component States

```typescript
interface BankingComponentState {
  balance: {
    value: number;
    change: number;
    changeType: 'positive' | 'negative' | 'neutral';
    lastUpdated: Date;
    isLoading: boolean;
    error?: string;
  };
  transactions: {
    data: Transaction[];
    isLoading: boolean;
    lastUpdated: Date;
    error?: string;
  };
  contacts: {
    data: Contact[];
    isLoading: boolean;
    error?: string;
  };
}
```

### Crypto Component States

```typescript
interface CryptoComponentState {
  portfolio: {
    totalValue: number;
    change24h: number;
    changeType: 'positive' | 'negative' | 'neutral';
    holdings: Holding[];
    lastUpdated: Date;
    isLoading: boolean;
    error?: string;
  };
  signals: {
    data: TradingSignal[];
    lastUpdated: Date;
    isLoading: boolean;
    error?: string;
  };
  risk: {
    metrics: RiskMetrics;
    level: 'low' | 'moderate' | 'high';
    recommendations: string[];
    lastUpdated: Date;
    isLoading: boolean;
    error?: string;
  };
}
```

## 🔄 Update Patterns

### 1. Balance Updates (30-second intervals)
```typescript
const handleBalanceUpdate = (event: BalanceUpdateEvent) => {
  setBalance(prev => ({
    ...prev,
    value: event.balance,
    change: event.change,
    changeType: event.change > 0 ? 'positive' : 'negative',
    lastUpdated: new Date(event.timestamp)
  }));

  // Trigger glassmorphism animation
  triggerBalanceAnimation();
};
```

### 2. Chart Data Updates (60-second intervals)
```typescript
const handleChartUpdate = (event: ChartUpdateEvent) => {
  setChartData(prev => {
    const newData = [...prev, ...event.newPoints];
    return newData.slice(-50); // Keep last 50 points
  });

  // Smooth transition animation
  animateChartTransition();
};
```

### 3. Signal Updates (2-minute intervals)
```typescript
const handleSignalUpdate = (event: SignalUpdateEvent) => {
  setSignals(prev => {
    const updated = prev.map(signal =>
      event.signals.find(s => s.token_id === signal.token_id) || signal
    );

    // Add new signals with animation
    const newSignals = event.signals.filter(signal =>
      !prev.some(s => s.token_id === signal.token_id)
    );

    return [...updated, ...newSignals];
  });

  // Animate new signals in
  animateSignalEntrance(newSignals);
};
```

## 🚨 Error Recovery Patterns

### Network Error Handling
```typescript
const handleNetworkError = (error: NetworkError) => {
  setErrorState({
    type: 'network',
    message: 'Connection lost. Retrying...',
    retryCount: error.retryCount
  });

  // Show glass error overlay
  showErrorOverlay();

  // Auto-retry with exponential backoff
  retryWithBackoff();
};
```

### Data Validation Error
```typescript
const handleDataError = (error: DataError) => {
  setErrorState({
    type: 'data',
    message: 'Invalid data received. Using cached data.',
    fallbackData: getCachedData()
  });

  // Maintain UI stability
  showFallbackData();
};
```

This architecture ensures seamless integration between MCP server responses and glassmorphism UI components, with robust error handling and smooth real-time updates.