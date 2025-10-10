# BigQuery Google Cloud Web3 Integration

## Översikt

Denna integration kombinerar Google Cloud Web3 Gateway med BigQuery för att leverera real-tids blockchain analytics, portfolio performance tracking, och risk management för crypto-portfoljer.

## Arkitektur

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Google Cloud    │    │  BigQuery        │    │  Analytics      │
│ Web3 Gateway    │───▶│  Materialized    │───▶│  Services       │
│                 │    │  Views           │    │                 │
│ - Multi-chain   │    │                  │    │ - Portfolio     │
│ - Real-tids     │    │ - Cross-chain    │    │ - Risk Metrics  │
│ - Balances      │    │ - Performance    │    │ - Rebalancing   │
│ - Transactions  │    │ - Risk Metrics   │    │ - Benchmarking  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Komponenter

### 1. BigQuery Configuration (`crypto/config/bigquery_config.py`)
- Dataset schemas för blockchain analytics
- Table definitions med partitionering och clustering
- SQL templates för vanliga queries
- Setup instructions för BigQuery

### 2. BigQuery Views (`crypto/config/bigquery_views.sql`)
- Optimerade materialized views för performance
- Cross-chain balance aggregation
- Daily portfolio value tracking
- Transaction pattern analysis
- Risk metrics aggregation

### 3. BigQuery Queries (`crypto/config/bigquery_queries.py`)
- Portfolio performance queries
- Risk analysis queries
- Cross-chain balance queries
- Transaction analytics queries
- Real-tids monitoring queries

### 4. BigQuery Service (`crypto/services/bigquery_service.py`)
- BigQuery client wrapper
- Query caching och optimization
- Integration med Google Cloud Web3
- Portfolio analytics från BigQuery data

### 5. Portfolio Analytics (`crypto/services/portfolio_analytics.py`)
- Advanced portfolio performance tracking
- Risk-adjusted returns calculation
- Multi-chain portfolio analysis
- Rebalancing recommendations
- Integration med BigQuery materialized views

### 6. Web3 BigQuery Integration (`crypto/services/web3_bigquery_integration.py`)
- Unified interface för alla services
- Comprehensive wallet analysis
- Real-tids monitoring
- Portfolio optimization
- Risk management dashboard

## Installation och Setup

### 1. Google Cloud Setup

```bash
# 1. Skapa Google Cloud project
gcloud projects create felicia-finance-blockchain

# 2. Aktivera nödvändiga APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable web3gateway.googleapis.com

# 3. Skapa service account
gcloud iam service-accounts create bigquery-web3-service
gcloud projects add-iam-policy-binding felicia-finance-blockchain \
  --member="serviceAccount:bigquery-web3-service@felicia-finance-blockchain.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"

# 4. Generera service account key
gcloud iam service-accounts keys create credentials.json \
  --iam-account=bigquery-web3-service@felicia-finance-blockchain.iam.gserviceaccount.com
```

### 2. BigQuery Dataset Setup

```sql
-- Kör följande SQL i BigQuery för att skapa datasets och tables
-- Se crypto/config/bigquery_config.py för kompletta DDL statements

-- Skapa blockchain_analytics dataset
CREATE SCHEMA `felicia-finance-blockchain.blockchain_analytics`
OPTIONS(
  description = "Blockchain analytics och Google Cloud Web3 data",
  location = "EU"
);

-- Skapa tables enligt schema i bigquery_config.py
-- Skapa materialized views enligt bigquery_views.sql
```

### 3. Python Dependencies

```bash
pip install google-cloud-bigquery
pip install google-cloud-web3-gateway
pip install pandas numpy scipy
pip install aiohttp asyncio
```

## Användning

### Basic Usage

```python
from crypto.services.web3_bigquery_integration import get_web3_bigquery_integration

# Initiera integration
integration = get_web3_bigquery_integration(
    project_id="felicia-finance-blockchain",
    credentials_path="credentials.json"
)

async with integration:
    # Hämta comprehensive wallet analysis
    analysis = await integration.get_comprehensive_wallet_analysis(
        wallet_address="0x1234...",
        include_live_data=True,
        include_risk_analysis=True
    )

    print(f"Portfolio Value: ${analysis['portfolio_data']['total_value_usd']}")
    print(f"Risk Score: {analysis['risk_analysis']['overall_risk_score']}")
```

### Portfolio Analytics

```python
from crypto.services.portfolio_analytics import PortfolioAnalyticsService

# Hämta portfolio performance
portfolio_service = PortfolioAnalyticsService(project_id="felicia-finance-blockchain")

async with portfolio_service:
    performance = await portfolio_service.get_performance_analytics(
        wallet_address="0x1234...",
        days=30
    )

    print(f"Total Return: {performance['performance_data']['total_return_percent']}%")
    print(f"Sharpe Ratio: {performance['advanced_metrics']['risk_metrics']['sharpe_ratio']}")
```

### Risk Dashboard

```python
# Hämta risk dashboard
risk_dashboard = await portfolio_service.get_risk_dashboard(wallet_address="0x1234...")

print(f"Risk Level: {risk_dashboard['overall_risk_score']}")
print(f"Active Alerts: {len(risk_dashboard['risk_alerts'])}")

for alert in risk_dashboard['risk_alerts']:
    print(f"- {alert['severity']}: {alert['message']}")
```

### Real-tids Monitoring

```python
# Hämta real-tids monitoring data
monitoring = await integration.get_real_time_portfolio_monitoring(
    wallet_address="0x1234...",
    monitoring_interval=60  # 60 sekunder
)

print(f"Current Value: ${monitoring['real_time_metrics']['portfolio_value']}")
print(f"Active Alerts: {monitoring['real_time_metrics']['active_alerts_count']}")
```

### Portfolio Optimization

```python
# Hämta optimization recommendations
optimization = await integration.get_portfolio_optimization_recommendations(
    wallet_address="0x1234..."
)

print("Optimization Actions:")
for action in optimization['optimization_actions']:
    print(f"- {action['action'].upper()} {action['amount_usd']:.2f} USD of {action['token_symbol']}")
    print(f"  Reason: {action['reason']}")
```

## Features

### ✅ Real-tids Portfolio Performance
- Live data från Google Cloud Web3 Gateway
- Historical data från BigQuery materialized views
- Advanced performance metrics (Sharpe, Sortino, Calmar ratios)
- Benchmarking mot BTC, ETH och market indices

### ✅ Risk Management
- Value at Risk (VaR) calculations
- Portfolio volatility analysis
- Maximum drawdown tracking
- Risk-adjusted performance metrics
- Automated risk alerts och notifications

### ✅ Cross-Chain Analytics
- Multi-chain balance aggregation
- Cross-chain transaction analysis
- Chain-specific risk metrics
- Diversification analysis across chains

### ✅ Portfolio Optimization
- Automated rebalancing recommendations
- Risk-optimized allocation targets
- Position sizing optimization
- Performance impact analysis

### ✅ Transaction Analytics
- Transaction pattern recognition
- Gas optimization analysis
- Counterparty analysis
- Time-based trading pattern analysis

### ✅ BigQuery Integration
- Optimerade materialized views för performance
- Partitionering och clustering för kostnadseffektivitet
- Real-tids data refresh med automatisk cache
- Advanced SQL queries för complex analytics

## Performance Optimization

### BigQuery Optimizations
- **Partitionering**: Time-based partitioning för alla time-series data
- **Clustering**: Optimized clustering keys för snabba queries
- **Materialized Views**: Pre-computed aggregations för vanliga queries
- **Query Caching**: Intelligent caching för repeated queries

### Real-tids Features
- **Live Data Integration**: Direct integration med Google Cloud Web3 Gateway
- **Incremental Updates**: Delta processing för real-tids data
- **Streaming Analytics**: Real-tids processing av nya transactions
- **Alerting System**: Automated alerts för risk thresholds

## Monitoring och Alerts

### Risk Alerts
- Portfolio VaR exceeds threshold
- Unusual volatility spikes
- Large position concentrations
- Failed transactions
- Performance deviations

### Performance Alerts
- Significant portfolio losses
- Underperformance vs benchmarks
- Sharpe ratio degradation
- Maximum drawdown breaches

### System Alerts
- BigQuery query failures
- Web3 provider issues
- Cache performance degradation
- Service health monitoring

## Security

### Google Cloud Security
- Service account authentication
- IAM roles och permissions
- VPC Service Controls
- Data encryption at rest och in transit

### Data Privacy
- Wallet addresses anonymized i logs
- Secure credential management
- Access control för sensitive data
- Audit logging för alla operations

## Cost Optimization

### BigQuery Cost Management
- Efficient partitioning för kostnadskontroll
- Query result caching
- Materialized views för repeated queries
- Slot utilization optimization

### Google Cloud Web3 Costs
- Efficient API usage
- Request batching
- Response caching
- Rate limiting compliance

## Troubleshooting

### Common Issues

1. **BigQuery Permission Errors**
   ```bash
   # Kontrollera IAM permissions
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:SERVICE_ACCOUNT" \
     --role="roles/bigquery.dataViewer"
   ```

2. **Web3 Provider Connection Issues**
   ```python
   # Kontrollera provider health
   health = await web3_provider.health_check()
   print(f"Provider Status: {health['status']}")
   ```

3. **Cache Issues**
   ```python
   # Rensa cache om det behövs
   await integration.clear_cache()
   ```

### Debugging

```python
# Aktivera debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Kontrollera service health
health_check = await integration.health_check()
print(json.dumps(health_check, indent=2))
```

## API Reference

### Web3BigQueryIntegration

#### Methods
- `get_comprehensive_wallet_analysis()` - Comprehensive wallet analysis
- `get_real_time_portfolio_monitoring()` - Real-tids monitoring
- `get_portfolio_optimization_recommendations()` - Optimization recommendations

#### Parameters
- `wallet_address`: Ethereum wallet address
- `include_live_data`: Include live Web3 data
- `include_risk_analysis`: Include risk analysis

### PortfolioAnalyticsService

#### Methods
- `get_portfolio_snapshot()` - Portfolio snapshot
- `get_performance_analytics()` - Performance analytics
- `get_risk_dashboard()` - Risk dashboard
- `get_rebalancing_analysis()` - Rebalancing analysis

### BigQueryService

#### Methods
- `execute_query()` - Execute BigQuery query
- `get_portfolio_performance()` - Portfolio performance
- `get_cross_chain_balances()` - Cross-chain balances
- `get_risk_metrics()` - Risk metrics

## Support

För support och frågor:
- Kontrollera logs för detaljerad error information
- Använd health check endpoints för service status
- Konsultera Google Cloud documentation för BigQuery och Web3 Gateway
- Review integration code för troubleshooting

## License

Denna integration är del av HappyOS Crypto system och följer samma licensvillkor.