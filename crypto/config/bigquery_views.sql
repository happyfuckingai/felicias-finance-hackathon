-- =============================================================================
-- BigQuery Materialized Views för Google Cloud Web3 Blockchain Analytics
-- T018: Materialized Views för Blockchain-data
-- =============================================================================

-- =============================================================================
-- 1. CROSS-CHAIN BALANCE VIEWS
-- =============================================================================

-- Materialized view för cross-chain wallet balances aggregation
CREATE OR REPLACE MATERIALIZED VIEW `blockchain_analytics.cross_chain_balances_mv`
PARTITION BY DATE(timestamp)
CLUSTER BY wallet_address, chain, token_symbol
OPTIONS(
  enable_refresh = true,
  refresh_interval_minutes = 60,
  max_staleness = INTERVAL 2 HOUR
) AS
SELECT
  wallet_address,
  chain,
  token_symbol,
  token_address,
  -- Senaste balance per wallet/chain/token
  ARRAY_AGG(
    STRUCT(
      balance,
      balance_formatted,
      decimals,
      timestamp
    )
    ORDER BY timestamp DESC
    LIMIT 1
  )[OFFSET(0)].*,

  -- Aggregerade värden
  COUNT(*) as total_snapshots,
  MIN(timestamp) as first_snapshot,
  MAX(timestamp) as latest_snapshot,

  -- Beräkna total value per wallet/chain
  SUM(
    CASE
      WHEN total_value_usd IS NOT NULL THEN total_value_usd
      ELSE balance_formatted * 1.0  -- Placeholder för native tokens
    END
  ) as total_chain_value_usd

FROM `blockchain_analytics.cross_chain_balances`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY wallet_address, chain, token_symbol, token_address;

-- Materialized view för total wallet portfolio values
CREATE OR REPLACE MATERIALIZED VIEW `blockchain_analytics.wallet_portfolio_summary_mv`
PARTITION BY DATE(timestamp)
CLUSTER BY wallet_address
OPTIONS(
  enable_refresh = true,
  refresh_interval_minutes = 30,
  max_staleness = INTERVAL 1 HOUR
) AS
WITH latest_balances AS (
  SELECT
    wallet_address,
    chain,
    token_symbol,
    balance_formatted,
    decimals,
    total_value_usd,
    timestamp,
    ROW_NUMBER() OVER (
      PARTITION BY wallet_address, chain, token_symbol
      ORDER BY timestamp DESC
    ) as rn
  FROM `blockchain_analytics.cross_chain_balances`
  WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
)

SELECT
  wallet_address,
  timestamp,

  -- Total portfolio value
  SUM(
    CASE
      WHEN total_value_usd IS NOT NULL THEN total_value_usd
      ELSE balance_formatted * 1.0  -- Placeholder
    END
  ) as total_portfolio_value_usd,

  -- Chain distribution
  ARRAY_AGG(
    STRUCT(
      chain,
      SUM(
        CASE
          WHEN total_value_usd IS NOT NULL THEN total_value_usd
          ELSE balance_formatted * 1.0
        END
      ) as chain_value
    )
    ORDER BY chain
  ) as chain_distribution,

  -- Token allocation
  ARRAY_AGG(
    STRUCT(
      token_symbol,
      SUM(
        CASE
          WHEN total_value_usd IS NOT NULL THEN total_value_usd
          ELSE balance_formatted * 1.0
        END
      ) as token_value
    )
    ORDER BY token_value DESC
    LIMIT 20
  ) as top_tokens,

  -- Portfolio diversity metrics
  COUNT(DISTINCT chain) as num_chains,
  COUNT(DISTINCT token_symbol) as num_tokens,
  COUNT(*) as total_positions

FROM latest_balances
WHERE rn = 1
GROUP BY wallet_address, timestamp;

-- =============================================================================
-- 2. TRANSACTION ANALYTICS VIEWS
-- =============================================================================

-- Materialized view för transaction analytics
CREATE OR REPLACE MATERIALIZED VIEW `blockchain_analytics.transaction_analytics_mv`
PARTITION BY DATE(timestamp)
CLUSTER BY wallet_address, chain, status
OPTIONS(
  enable_refresh = true,
  refresh_interval_minutes = 120,
  max_staleness = INTERVAL 4 HOUR
) AS
SELECT
  wallet_address,
  chain,
  DATE(timestamp) as date,

  -- Transaction counts
  COUNT(*) as total_transactions,
  COUNTIF(status = 'success') as successful_transactions,
  COUNTIF(status = 'failed') as failed_transactions,
  COUNTIF(status = 'pending') as pending_transactions,

  -- Value analytics
  SUM(CAST(value AS FLOAT64)) as total_value_transferred,
  AVG(CAST(value AS FLOAT64)) as avg_transaction_value,
  MIN(CAST(value AS FLOAT64)) as min_transaction_value,
  MAX(CAST(value AS FLOAT64)) as max_transaction_value,

  -- Gas analytics
  SUM(CAST(gas_used AS INT64)) as total_gas_used,
  AVG(CAST(gas_used AS INT64)) as avg_gas_used,
  SUM(CAST(gas_price AS FLOAT64) * CAST(gas_used AS INT64)) as total_gas_cost,

  -- Time analytics
  MIN(timestamp) as first_transaction,
  MAX(timestamp) as latest_transaction,
  TIMESTAMP_DIFF(MAX(timestamp), MIN(timestamp), HOUR) as active_hours,

  -- Address interactions
  COUNT(DISTINCT from_address) as unique_from_addresses,
  COUNT(DISTINCT to_address) as unique_to_addresses,
  COUNT(DISTINCT tx_hash) as unique_transactions

FROM `blockchain_analytics.blockchain_transactions`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY wallet_address, chain, DATE(timestamp);

-- Materialized view för transaction patterns
CREATE OR REPLACE MATERIALIZED VIEW `blockchain_analytics.transaction_patterns_mv`
PARTITION BY DATE(timestamp)
CLUSTER BY wallet_address, chain
OPTIONS(
  enable_refresh = true,
  refresh_interval_minutes = 180,
  max_staleness = INTERVAL 6 HOUR
) AS
WITH transaction_sequences AS (
  SELECT
    wallet_address,
    chain,
    timestamp,
    tx_hash,
    value,
    status,
    from_address,
    to_address,

    -- Calculate time differences
    LAG(timestamp) OVER (
      PARTITION BY wallet_address, chain
      ORDER BY timestamp
    ) as prev_timestamp,

    LEAD(timestamp) OVER (
      PARTITION BY wallet_address, chain
      ORDER BY timestamp
    ) as next_timestamp

  FROM `blockchain_analytics.blockchain_transactions`
  WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND status = 'success'
)

SELECT
  wallet_address,
  chain,

  -- Transaction frequency patterns
  COUNT(*) as total_transactions,
  AVG(
    CASE
      WHEN prev_timestamp IS NOT NULL
      THEN TIMESTAMP_DIFF(timestamp, prev_timestamp, MINUTE)
      ELSE NULL
    END
  ) as avg_time_between_transactions,

  -- Transaction size patterns
  STDDEV(CAST(value AS FLOAT64)) as transaction_size_stddev,
  COUNTIF(
    CAST(value AS FLOAT64) > 1000
  ) as large_transactions,  -- > $1000

  -- Address patterns
  COUNT(DISTINCT from_address) as unique_senders,
  COUNT(DISTINCT to_address) as unique_recipients,

  -- Time patterns
  EXTRACT(HOUR FROM timestamp) as transaction_hour,
  EXTRACT(DAYOFWEEK FROM timestamp) as transaction_day_of_week,

  -- Success patterns
  COUNTIF(status = 'success') / COUNT(*) as success_rate

FROM transaction_sequences
GROUP BY wallet_address, chain, EXTRACT(HOUR FROM timestamp), EXTRACT(DAYOFWEEK FROM timestamp);

-- =============================================================================
-- 3. DAILY PORTFOLIO VALUE VIEWS
-- =============================================================================

-- Materialized view för daily portfolio snapshots
CREATE OR REPLACE MATERIALIZED VIEW `blockchain_analytics.daily_portfolio_values_mv`
PARTITION BY DATE(snapshot_date)
CLUSTER BY wallet_address
OPTIONS(
  enable_refresh = true,
  refresh_interval_minutes = 60,
  max_staleness = INTERVAL 2 HOUR
) AS
WITH daily_snapshots AS (
  SELECT
    wallet_address,
    DATE(timestamp) as snapshot_date,

    -- Portfolio value at end of day
    ARRAY_AGG(
      STRUCT(
        total_value_usd,
        timestamp
      )
      ORDER BY timestamp DESC
      LIMIT 1
    )[OFFSET(0)].total_value_usd as end_of_day_value,

    -- Daily change
    ARRAY_AGG(
      total_value_usd
      ORDER BY timestamp
    ) as daily_values

  FROM `blockchain_analytics.portfolio_snapshots`
  WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
  GROUP BY wallet_address, DATE(timestamp)
)

SELECT
  wallet_address,
  snapshot_date,
  end_of_day_value,

  -- Daily return calculation
  LAG(end_of_day_value) OVER (
    PARTITION BY wallet_address
    ORDER BY snapshot_date
  ) as previous_day_value,

  CASE
    WHEN LAG(end_of_day_value) OVER (
      PARTITION BY wallet_address
      ORDER BY snapshot_date
    ) IS NOT NULL
    THEN (end_of_day_value - LAG(end_of_day_value) OVER (
      PARTITION BY wallet_address
      ORDER BY snapshot_date
    )) / LAG(end_of_day_value) OVER (
      PARTITION BY wallet_address
      ORDER BY snapshot_date
    )
    ELSE 0
  END as daily_return,

  -- Rolling averages
  AVG(end_of_day_value) OVER (
    PARTITION BY wallet_address
    ORDER BY snapshot_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as weekly_avg_value,

  AVG(end_of_day_value) OVER (
    PARTITION BY wallet_address
    ORDER BY snapshot_date
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as monthly_avg_value

FROM daily_snapshots
WHERE end_of_day_value IS NOT NULL;

-- =============================================================================
-- 4. RISK METRICS AGGREGATED VIEWS
-- =============================================================================

-- Materialized view för aggregated risk metrics
CREATE OR REPLACE MATERIALIZED VIEW `blockchain_analytics.risk_metrics_aggregated_mv`
PARTITION BY DATE(timestamp)
CLUSTER BY wallet_address
OPTIONS(
  enable_refresh = true,
  refresh_interval_minutes = 120,
  max_staleness = INTERVAL 4 HOUR
) AS
SELECT
  wallet_address,
  DATE(timestamp) as date,

  -- Latest risk metrics per day
  ARRAY_AGG(
    STRUCT(
      var_95,
      var_99,
      volatility,
      sharpe_ratio,
      max_drawdown,
      beta,
      alpha,
      chain_diversification,
      portfolio_value,
      timestamp
    )
    ORDER BY timestamp DESC
    LIMIT 1
  )[OFFSET(0)].*,

  -- Risk trend analysis
  AVG(
    ARRAY_AGG(var_95 ORDER BY timestamp DESC LIMIT 7)[OFFSET(0)]
  ) as weekly_avg_var_95,

  AVG(
    ARRAY_AGG(volatility ORDER BY timestamp DESC LIMIT 7)[OFFSET(0)]
  ) as weekly_avg_volatility,

  -- Risk level categorization
  CASE
    WHEN ARRAY_AGG(var_95 ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] > 0.15
    THEN 'HIGH_RISK'
    WHEN ARRAY_AGG(var_95 ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] > 0.08
    THEN 'MEDIUM_RISK'
    ELSE 'LOW_RISK'
  END as risk_category,

  -- Diversification score
  CASE
    WHEN ARRAY_AGG(chain_diversification ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] IS NULL
    THEN 0.0
    ELSE ARRAY_AGG(chain_diversification ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)]
  END as diversification_score

FROM `blockchain_analytics.risk_metrics`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY wallet_address, DATE(timestamp);

-- =============================================================================
-- 5. PERFORMANCE BENCHMARKING VIEWS
-- =============================================================================

-- Materialized view för performance vs market benchmarks
CREATE OR REPLACE MATERIALIZED VIEW `blockchain_analytics.performance_benchmarking_mv`
PARTITION BY DATE(timestamp)
CLUSTER BY wallet_address
OPTIONS(
  enable_refresh = true,
  refresh_interval_minutes = 240,
  max_staleness = INTERVAL 8 HOUR
) AS
WITH portfolio_returns AS (
  SELECT
    wallet_address,
    DATE(timestamp) as date,
    portfolio_return_1d as portfolio_1d,
    portfolio_return_7d as portfolio_7d,
    portfolio_return_30d as portfolio_30d
  FROM `blockchain_analytics.performance_benchmarks`
  WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
),

market_returns AS (
  SELECT
    'MARKET' as wallet_address,
    DATE(timestamp) as date,
    AVG(btc_return_1d) as btc_1d,
    AVG(btc_return_7d) as btc_7d,
    AVG(btc_return_30d) as btc_30d,
    AVG(eth_return_1d) as eth_1d,
    AVG(eth_return_7d) as eth_7d,
    AVG(eth_return_30d) as eth_30d
  FROM `blockchain_analytics.performance_benchmarks`
  WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
  GROUP BY DATE(timestamp)
)

SELECT
  p.wallet_address,
  p.date,

  -- Portfolio returns
  p.portfolio_1d,
  p.portfolio_7d,
  p.portfolio_30d,

  -- Market benchmarks
  m.btc_1d,
  m.btc_7d,
  m.btc_30d,
  m.eth_1d,
  m.eth_7d,
  m.eth_30d,

  -- Relative performance
  CASE
    WHEN p.portfolio_1d IS NOT NULL AND m.btc_1d IS NOT NULL
    THEN p.portfolio_1d - m.btc_1d
    ELSE NULL
  END as relative_vs_btc_1d,

  CASE
    WHEN p.portfolio_7d IS NOT NULL AND m.btc_7d IS NOT NULL
    THEN p.portfolio_7d - m.btc_7d
    ELSE NULL
  END as relative_vs_btc_7d,

  CASE
    WHEN p.portfolio_30d IS NOT NULL AND m.btc_30d IS NOT NULL
    THEN p.portfolio_30d - m.btc_30d
    ELSE NULL
  END as relative_vs_btc_30d,

  -- Performance ranking
  CASE
    WHEN p.portfolio_30d > m.btc_30d THEN 'OUTPERFORMING_BTC'
    WHEN p.portfolio_30d < m.btc_30d THEN 'UNDERPERFORMING_BTC'
    ELSE 'MARKET_PERFORMING'
  END as btc_performance_category,

  CASE
    WHEN p.portfolio_30d > m.eth_30d THEN 'OUTPERFORMING_ETH'
    WHEN p.portfolio_30d < m.eth_30d THEN 'UNDERPERFORMING_ETH'
    ELSE 'MARKET_PERFORMING'
  END as eth_performance_category

FROM portfolio_returns p
CROSS JOIN market_returns m
WHERE p.date = m.date;

-- =============================================================================
-- 6. REAL-TIME ANALYTICS VIEWS
-- =============================================================================

-- Materialized view för real-time wallet health
CREATE OR REPLACE MATERIALIZED VIEW `blockchain_analytics.realtime_wallet_health_mv`
PARTITION BY DATE(timestamp)
CLUSTER BY wallet_address
OPTIONS(
  enable_refresh = true,
  refresh_interval_minutes = 15,
  max_staleness = INTERVAL 30 MINUTE
) AS
WITH latest_data AS (
  SELECT
    wallet_address,
    timestamp,

    -- Balance health
    ARRAY_AGG(
      STRUCT(
        chain,
        balance_formatted,
        total_value_usd
      )
      ORDER BY timestamp DESC
      LIMIT 1
    )[OFFSET(0)] as latest_balance,

    -- Transaction health
    ARRAY_AGG(
      STRUCT(
        status,
        gas_used,
        timestamp
      )
      ORDER BY timestamp DESC
      LIMIT 5
    ) as recent_transactions,

    -- Risk health
    ARRAY_AGG(
      STRUCT(
        var_95,
        volatility,
        max_drawdown
      )
      ORDER BY timestamp DESC
      LIMIT 1
    )[OFFSET(0)] as latest_risk

  FROM `blockchain_analytics.*`
  WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  GROUP BY wallet_address, timestamp
)

SELECT
  wallet_address,
  timestamp,

  -- Overall health score (0-100)
  CASE
    WHEN latest_balance.total_value_usd IS NULL THEN 0
    WHEN latest_risk.var_95 IS NULL THEN 50
    WHEN latest_risk.var_95 > 0.20 THEN 20  -- High risk
    WHEN latest_risk.var_95 > 0.10 THEN 50  -- Medium risk
    WHEN latest_risk.var_95 > 0.05 THEN 70  -- Low-medium risk
    ELSE 90  -- Low risk
  END as health_score,

  -- Health indicators
  CASE
    WHEN COUNTIF(recent_transactions.status = 'failed') > 2
    THEN FALSE
    ELSE TRUE
  END as transaction_health,

  CASE
    WHEN latest_balance.total_value_usd IS NOT NULL
         AND latest_balance.total_value_usd > 0
    THEN TRUE
    ELSE FALSE
  END as balance_health,

  CASE
    WHEN latest_risk.volatility IS NULL THEN NULL
    WHEN latest_risk.volatility < 0.30 THEN TRUE  -- Low volatility
    WHEN latest_risk.volatility < 0.60 THEN FALSE -- High volatility
    ELSE FALSE
  END as risk_health,

  -- Alerts
  ARRAY[
    IF(latest_risk.var_95 > 0.15, 'HIGH_VAR_DETECTED', NULL),
    IF(latest_risk.max_drawdown < -0.20, 'LARGE_DRAWDOWN_DETECTED', NULL),
    IF(latest_risk.volatility > 0.80, 'EXTREME_VOLATILITY_DETECTED', NULL),
    IF(COUNTIF(recent_transactions.status = 'failed') > 3, 'MULTIPLE_FAILED_TRANSACTIONS', NULL)
  ] as active_alerts

FROM latest_data
GROUP BY wallet_address, timestamp;