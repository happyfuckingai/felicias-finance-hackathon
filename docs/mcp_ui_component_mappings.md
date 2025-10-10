# MCP-UI Component Mappings - Glassmorphism Implementation

## 🏦 Banking Component Specifications

### 1. Balance Card Component
**Backend Schema:** `{"type": "card", "title": "Account Balance", "value": "$12,543.67", "change": "+2.1%", "changeType": "positive"}`

**Glassmorphism Implementation:**
```tsx
<GlassBalanceCard
  balance={value}
  change={change}
  changeType={changeType}
  title={title}
  accountId={account_id}
/>
```

**Styling Specifications:**
- **Container:** `glass-card` with `depth="surface"`
- **Background:** `var(--glass-bg-primary)`
- **Border:** `var(--glass-border-primary)`
- **Shadow:** `0 8px 32px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.15)`
- **Balance Text:** `var(--text-primary)`, `font-size: 2rem`, `font-weight: 700`
- **Change Indicator:** Conditional color based on `changeType`
  - `positive`: `var(--text-success)`
  - `negative`: `var(--text-error)`
  - `neutral`: `var(--text-secondary)`

### 2. Transaction Chart Component
**Backend Schema:** `{"type": "chart", "chartType": "bar", "data": [...], "title": "Recent Transactions"}`

**Glassmorphism Implementation:**
```tsx
<GlassTransactionChart
  data={data}
  chartType={chartType}
  title={title}
  height="300px"
/>
```

**Styling Specifications:**
- **Container:** `glass-surface` with `depth="elevated"`
- **Chart Background:** `var(--glass-bg-secondary)`
- **Grid Lines:** `rgba(255, 255, 255, 0.1)`
- **Bar Colors:**
  - Debit: `var(--text-error)` with 0.7 opacity
  - Credit: `var(--text-success)` with 0.7 opacity
- **Hover Effects:** `glass-hover` class for interactive elements

### 3. Quick Actions Panel
**Backend Schema:** `{"type": "actions", "actions": [{"id": "transfer", "label": "Make Transfer", "icon": "arrow-right"}]}`

**Glassmorphism Implementation:**
```tsx
<GlassQuickActions
  actions={actions}
  layout="horizontal"
/>
```

**Styling Specifications:**
- **Container:** `glass-overlay` with `depth="surface"`
- **Button Style:** `glass-card` with `variant="interactive"`
- **Icon Color:** `var(--glass-accent-primary)`
- **Hover State:** `glass-active` with enhanced glow

### 4. Contacts Widget
**Backend Schema:** `{"type": "list", "items": [{"name": "John Doe", "account": "1234567890", "type": "external"}]}`

**Glassmorphism Implementation:**
```tsx
<GlassContactsWidget
  contacts={items}
  showActions={true}
/>
```

**Styling Specifications:**
- **Container:** `glass-surface`
- **Contact Item:** `glass-card` with `size="compact"`
- **Type Indicator:**
  - External: `var(--glass-accent-secondary)`
  - Internal: `var(--glass-accent-primary)`
- **Action Buttons:** `glass-hover` with `size="small"`

---

## ₿ Crypto Component Specifications

### 1. Price Widget Component
**Backend Schema:** `{"type": "price-card", "price": "$45,230.50", "change": "+2.34%", "changeType": "positive"}`

**Glassmorphism Implementation:**
```tsx
<GlassPriceWidget
  tokenId={token_id}
  price={price}
  change={change}
  changeType={changeType}
  volume={volume}
/>
```

**Styling Specifications:**
- **Container:** `glass-card` with `variant="price"`
- **Price Display:** Large monospace font, `var(--text-primary)`
- **Change Animation:** Smooth transition with `glass-hover` effects
- **Volume Indicator:** Subtle `var(--text-tertiary)` text

### 2. Portfolio Chart Component
**Backend Schema:** `{"type": "chart", "chartType": "area", "data": [...], "color": "#10b981"}`

**Glassmorphism Implementation:**
```tsx
<GlassPortfolioChart
  data={data}
  chartType={chartType}
  color={color}
  showChange={true}
/>
```

**Styling Specifications:**
- **Container:** `glass-surface` with `depth="elevated"`
- **Chart Area:** Gradient fill from `color` to transparent
- **Grid:** `rgba(255, 255, 255, 0.08)` lines
- **Tooltip:** `glass-card` with `depth="overlay"`

### 3. Risk Dashboard Component
**Backend Schema:** `{"type": "risk-dashboard", "metrics": {...}, "riskLevel": "moderate", "recommendations": [...]}`

**Glassmorphism Implementation:**
```tsx
<GlassRiskDashboard
  metrics={metrics}
  riskLevel={riskLevel}
  recommendations={recommendations}
/>
```

**Styling Specifications:**
- **Container:** `glass-card` with `variant="warning"` for risk levels
- **Metric Cards:** `glass-surface` grid layout
- **Risk Level Colors:**
  - `low`: `var(--text-success)`
  - `moderate`: `var(--text-warning)`
  - `high`: `var(--text-error)`
- **Recommendation List:** Bulleted with `var(--text-secondary)`

### 4. Trading Signals Component
**Backend Schema:** `{"type": "signals-list", "signals": [{"token": "BTC", "signal": "BUY", "confidence": 0.85}]}`

**Glassmorphism Implementation:**
```tsx
<GlassTradingSignals
  signals={signals}
  showConfidence={true}
/>
```

**Styling Specifications:**
- **Container:** `glass-surface`
- **Signal Item:** `glass-card` with signal-based colors
- **Signal Colors:**
  - `BUY`: `var(--text-success)`
  - `SELL`: `var(--text-error)`
  - `HOLD`: `var(--text-warning)`
- **Confidence Bar:** Gradient from `var(--glass-accent-primary)` to `var(--glass-accent-secondary)`

---

## 🎨 Shared Component Properties

### Layout Grid System
```css
.glass-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.glass-grid-responsive {
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}
```

### Animation & Transitions
```css
.glass-transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-pulse {
  animation: glass-pulse 2s infinite;
}

@keyframes glass-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

### Interactive States
```css
.glass-interactive {
  cursor: pointer;
  user-select: none;
}

.glass-interactive:hover {
  background: var(--glass-bg-primary);
  transform: translateY(-2px);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.glass-interactive:active {
  transform: translateY(0);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
```

---

## 🔄 Real-time Data Flow

### SSE Stream Integration
```tsx
// Example implementation for balance updates
useMCPUIStreaming('/mcp-ui/stream/balance-updates/{account_id}', {
  onMessage: (data) => {
    if (data.type === 'balance_update') {
      updateBalanceCard(data);
    }
  },
  refreshInterval: 30000
});
```

### Component Update Patterns
- **Balance Updates:** Real-time number animation with `glass-pulse`
- **Chart Updates:** Smooth data transitions, new points slide in
- **Signal Updates:** Fade in new signals with `glass-transition`
- **Error States:** Subtle red tint with `glass-card` error variant

---

## 📱 Responsive Breakpoints

### Banking Layout
```css
/* Desktop */
.banking-dashboard {
  grid-template-columns: 2fr 1fr;
}

/* Tablet */
@media (max-width: 1024px) {
  .banking-dashboard {
    grid-template-columns: 1fr;
  }
}

/* Mobile */
@media (max-width: 768px) {
  .banking-dashboard {
    gap: 0.5rem;
  }

  .glass-card {
    padding: 1rem;
    border-radius: 12px;
  }
}
```

### Crypto Layout
```css
/* Desktop */
.crypto-dashboard {
  grid-template-columns: repeat(3, 1fr);
}

/* Tablet */
@media (max-width: 1024px) {
  .crypto-dashboard {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Mobile */
@media (max-width: 768px) {
  .crypto-dashboard {
    grid-template-columns: 1fr;
  }
}
```

This specification provides complete mapping from MCP server responses to glassmorphism UI components, ensuring consistent styling and optimal user experience across banking and crypto interfaces.