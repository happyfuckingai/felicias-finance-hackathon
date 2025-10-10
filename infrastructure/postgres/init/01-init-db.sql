-- Felicia's Finance Database Initialization
-- Detta skapar alla nödvändiga tabeller för lokal utveckling

-- Trading analytics tables (ersätter BigQuery)
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(255) NOT NULL,
    token_address VARCHAR(255) NOT NULL,
    token_symbol VARCHAR(50),
    amount DECIMAL(36,18) NOT NULL,
    price_usd DECIMAL(20,8),
    total_value_usd DECIMAL(20,2),
    transaction_hash VARCHAR(255) UNIQUE,
    blockchain VARCHAR(50) DEFAULT 'base',
    trade_type VARCHAR(20) DEFAULT 'buy', -- buy, sell, swap
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    gas_used BIGINT,
    gas_price DECIMAL(36,18),
    status VARCHAR(20) DEFAULT 'completed' -- pending, completed, failed
);

-- Portfolio snapshots
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(255) NOT NULL,
    total_value_usd DECIMAL(20,2) NOT NULL,
    btc_value DECIMAL(20,8),
    eth_value DECIMAL(20,8),
    risk_score DECIMAL(5,4),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily balances
CREATE TABLE IF NOT EXISTS daily_balances (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(255) NOT NULL,
    token_symbol VARCHAR(10) NOT NULL,
    balance DECIMAL(36,18) NOT NULL,
    value_usd DECIMAL(20,2),
    price_usd DECIMAL(20,8),
    date DATE NOT NULL,
    UNIQUE(wallet_address, token_symbol, date)
);

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(255),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20,8),
    date DATE NOT NULL,
    metadata JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_trades_wallet ON trades(wallet_address);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_portfolio_wallet ON portfolio_snapshots(wallet_address);
CREATE INDEX IF NOT EXISTS idx_daily_wallet ON daily_balances(wallet_address);
CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_balances(date);

-- Insert some sample data for testing
INSERT INTO trades (wallet_address, token_address, token_symbol, amount, price_usd, total_value_usd, transaction_hash, blockchain)
VALUES
    ('0x742d35Cc6634C0532925a3b8848c5C5F3b6e0c85', '0x4200000000000000000000000000000000000006', 'WETH', 0.5, 2800.00, 1400.00, '0x123abc', 'base'),
    ('0x742d35Cc6634C0532925a3b8848c5C5F3b6e0c85', '0x4200000000000000000000000000000000000006', 'WETH', 0.3, 2750.00, 825.00, '0x456def', 'base')
ON CONFLICT (transaction_hash) DO NOTHING;

