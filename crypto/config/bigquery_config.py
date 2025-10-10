"""
BigQuery Configuration för Trading Analytics
BigQuery datasets och tables för crypto trading system
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BigQueryTableSchema:
    """Schema för en BigQuery table"""

    table_name: str
    description: str
    schema: List[Dict[str, str]]
    partition_field: Optional[str] = None
    clustering_fields: Optional[List[str]] = None

@dataclass
class BigQueryDataset:
    """BigQuery dataset konfiguration"""

    dataset_id: str
    description: str
    location: str
    tables: List[BigQueryTableSchema]

@dataclass
class BigQueryConfig:
    """BigQuery konfiguration för crypto trading system"""

    # =============================================================================
    # DATASET CONFIGURATIONS
    # =============================================================================

    # Trading analytics dataset
    DATASET_TRADING: BigQueryDataset = None

    # Portfolio tracking dataset
    DATASET_PORTFOLIO: BigQueryDataset = None

    # Risk metrics dataset
    DATASET_RISK: BigQueryDataset = None

    # Market data dataset
    DATASET_MARKET_DATA: BigQueryDataset = None

    # =============================================================================
    # QUERY CONFIGURATIONS
    # =============================================================================

    # Default location för BigQuery
    DEFAULT_LOCATION: str = os.getenv("BIGQUERY_LOCATION", "EU")

    # Query timeout (sekunder)
    QUERY_TIMEOUT: int = int(os.getenv("BIGQUERY_QUERY_TIMEOUT", "300"))

    # Max bytes billed per query
    MAX_BYTES_BILLED: int = int(os.getenv("BIGQUERY_MAX_BYTES_BILLED", "1000000000"))  # 1GB

    # Use legacy SQL (default: False for standard SQL)
    USE_LEGACY_SQL: bool = os.getenv("BIGQUERY_USE_LEGACY_SQL", "false").lower() == "true"

    def __post_init__(self):
        """Initiera datasets"""
        if self.DATASET_TRADING is None:
            self.DATASET_TRADING = BigQueryDataset(
                dataset_id="trading_analytics",
                description="Dataset för trading analytics och performance metrics",
                location=self.DEFAULT_LOCATION,
                tables=[
                    BigQueryTableSchema(
                        table_name="trades",
                        description="Historik över alla trades",
                        schema=[
                            {"name": "trade_id", "type": "STRING", "mode": "REQUIRED", "description": "Unik trade identifierare"},
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Tidpunkt för traden"},
                            {"name": "token_symbol", "type": "STRING", "mode": "REQUIRED", "description": "Token symbol"},
                            {"name": "token_address", "type": "STRING", "mode": "REQUIRED", "description": "Token kontrakt address"},
                            {"name": "side", "type": "STRING", "mode": "REQUIRED", "description": "BUY eller SELL"},
                            {"name": "quantity", "type": "FLOAT64", "mode": "REQUIRED", "description": "Antal tokens"},
                            {"name": "price", "type": "FLOAT64", "mode": "REQUIRED", "description": "Pris per token"},
                            {"name": "total_value", "type": "FLOAT64", "mode": "REQUIRED", "description": "Totalt värde för traden"},
                            {"name": "fee", "type": "FLOAT64", "mode": "NULLABLE", "description": "Trading fee"},
                            {"name": "slippage", "type": "FLOAT64", "mode": "NULLABLE", "description": "Slippage i procent"},
                            {"name": "exchange", "type": "STRING", "mode": "REQUIRED", "description": "Exchange/Dex namn"},
                            {"name": "tx_hash", "type": "STRING", "mode": "NULLABLE", "description": "Transaction hash"},
                            {"name": "gas_used", "type": "INT64", "mode": "NULLABLE", "description": "Gas använt"},
                            {"name": "gas_price", "type": "FLOAT64", "mode": "NULLABLE", "description": "Gas pris"},
                            {"name": "strategy", "type": "STRING", "mode": "NULLABLE", "description": "Trading strategi"},
                            {"name": "signal_confidence", "type": "FLOAT64", "mode": "NULLABLE", "description": "Signal confidence"},
                            {"name": "status", "type": "STRING", "mode": "REQUIRED", "description": "Trade status (completed, failed, pending)"},
                            {"name": "profit_loss", "type": "FLOAT64", "mode": "NULLABLE", "description": "Profit/loss för traden"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["token_symbol", "exchange", "strategy"]
                    ),

                    BigQueryTableSchema(
                        table_name="positions",
                        description="Öppna och stängda positioner",
                        schema=[
                            {"name": "position_id", "type": "STRING", "mode": "REQUIRED", "description": "Unik position identifierare"},
                            {"name": "token_symbol", "type": "STRING", "mode": "REQUIRED", "description": "Token symbol"},
                            {"name": "token_address", "type": "STRING", "mode": "REQUIRED", "description": "Token kontrakt address"},
                            {"name": "entry_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Entry tidpunkt"},
                            {"name": "exit_timestamp", "type": "TIMESTAMP", "mode": "NULLABLE", "description": "Exit tidpunkt"},
                            {"name": "side", "type": "STRING", "mode": "REQUIRED", "description": "LONG eller SHORT"},
                            {"name": "entry_price", "type": "FLOAT64", "mode": "REQUIRED", "description": "Entry pris"},
                            {"name": "exit_price", "type": "FLOAT64", "mode": "NULLABLE", "description": "Exit pris"},
                            {"name": "quantity", "type": "FLOAT64", "mode": "REQUIRED", "description": "Antal tokens"},
                            {"name": "current_value", "type": "FLOAT64", "mode": "REQUIRED", "description": "Nuvarande värde"},
                            {"name": "unrealized_pnl", "type": "FLOAT64", "mode": "REQUIRED", "description": "Unrealized profit/loss"},
                            {"name": "realized_pnl", "type": "FLOAT64", "mode": "NULLABLE", "description": "Realized profit/loss"},
                            {"name": "status", "type": "STRING", "mode": "REQUIRED", "description": "OPEN, CLOSED, LIQUIDATED"},
                            {"name": "strategy", "type": "STRING", "mode": "NULLABLE", "description": "Trading strategi"},
                            {"name": "stop_loss", "type": "FLOAT64", "mode": "NULLABLE", "description": "Stop loss nivå"},
                            {"name": "take_profit", "type": "FLOAT64", "mode": "NULLABLE", "description": "Take profit nivå"}
                        ],
                        partition_field="entry_timestamp",
                        clustering_fields=["token_symbol", "strategy", "status"]
                    ),

                    BigQueryTableSchema(
                        table_name="daily_performance",
                        description="Daglig trading performance",
                        schema=[
                            {"name": "date", "type": "DATE", "mode": "REQUIRED", "description": "Datum"},
                            {"name": "total_trades", "type": "INT64", "mode": "REQUIRED", "description": "Totalt antal trades"},
                            {"name": "winning_trades", "type": "INT64", "mode": "REQUIRED", "description": "Vinnande trades"},
                            {"name": "losing_trades", "type": "INT64", "mode": "REQUIRED", "description": "Förlorande trades"},
                            {"name": "win_rate", "type": "FLOAT64", "mode": "REQUIRED", "description": "Win rate i procent"},
                            {"name": "total_pnl", "type": "FLOAT64", "mode": "REQUIRED", "description": "Total profit/loss"},
                            {"name": "total_fees", "type": "FLOAT64", "mode": "REQUIRED", "description": "Totala fees"},
                            {"name": "net_pnl", "type": "FLOAT64", "mode": "REQUIRED", "description": "Net profit/loss"},
                            {"name": "portfolio_value_start", "type": "FLOAT64", "mode": "REQUIRED", "description": "Portfolio värde vid start"},
                            {"name": "portfolio_value_end", "type": "FLOAT64", "mode": "REQUIRED", "description": "Portfolio värde vid slut"},
                            {"name": "daily_return", "type": "FLOAT64", "mode": "REQUIRED", "description": "Daglig avkastning i procent"},
                            {"name": "max_drawdown", "type": "FLOAT64", "mode": "REQUIRED", "description": "Max drawdown"},
                            {"name": "volatility", "type": "FLOAT64", "mode": "REQUIRED", "description": "Volatilitet"}
                        ],
                        partition_field="date"
                    )
                ]
            )

        if self.DATASET_PORTFOLIO is None:
            self.DATASET_PORTFOLIO = BigQueryDataset(
                dataset_id="portfolio_tracking",
                description="Portfolio tracking och asset allocation",
                location=self.DEFAULT_LOCATION,
                tables=[
                    BigQueryTableSchema(
                        table_name="portfolio_snapshots",
                        description="Portfolio snapshots över tid",
                        schema=[
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Snapshot tidpunkt"},
                            {"name": "total_value_usd", "type": "FLOAT64", "mode": "REQUIRED", "description": "Totalt portfolio värde i USD"},
                            {"name": "assets", "type": "STRING", "mode": "REPEATED", "description": "Lista av assets"},
                            {"name": "quantities", "type": "FLOAT64", "mode": "REPEATED", "description": "Mängd av varje asset"},
                            {"name": "values_usd", "type": "FLOAT64", "mode": "REPEATED", "description": "Värde av varje asset i USD"},
                            {"name": "weights", "type": "FLOAT64", "mode": "REPEATED", "description": "Vikt av varje asset i procent"},
                            {"name": "cash_position", "type": "FLOAT64", "mode": "REQUIRED", "description": "Cash position i USD"},
                            {"name": "total_allocated", "type": "FLOAT64", "mode": "REQUIRED", "description": "Totalt allokerat belopp"},
                            {"name": "unallocated_cash", "type": "FLOAT64", "mode": "REQUIRED", "description": "Oallokerad cash"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["timestamp"]
                    ),

                    BigQueryTableSchema(
                        table_name="asset_allocations",
                        description="Asset allocation över tid",
                        schema=[
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Tidpunkt"},
                            {"name": "asset_symbol", "type": "STRING", "mode": "REQUIRED", "description": "Asset symbol"},
                            {"name": "asset_address", "type": "STRING", "mode": "REQUIRED", "description": "Asset kontrakt address"},
                            {"name": "allocation_usd", "type": "FLOAT64", "mode": "REQUIRED", "description": "Allokerat belopp i USD"},
                            {"name": "weight", "type": "FLOAT64", "mode": "REQUIRED", "description": "Vikt i procent"},
                            {"name": "target_weight", "type": "FLOAT64", "mode": "NULLABLE", "description": "Målvikt"},
                            {"name": "rebalance_required", "type": "BOOL", "mode": "REQUIRED", "description": "Om rebalansering behövs"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["asset_symbol"]
                    )
                ]
            )

        if self.DATASET_RISK is None:
            self.DATASET_RISK = BigQueryDataset(
                dataset_id="risk_metrics",
                description="Risk metrics och risk management data",
                location=self.DEFAULT_LOCATION,
                tables=[
                    BigQueryTableSchema(
                        table_name="var_calculations",
                        description="Value at Risk beräkningar",
                        schema=[
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Beräkningstidpunkt"},
                            {"name": "portfolio_value", "type": "FLOAT64", "mode": "REQUIRED", "description": "Portfolio värde"},
                            {"name": "confidence_level", "type": "FLOAT64", "mode": "REQUIRED", "description": "Confidence level"},
                            {"name": "time_horizon", "type": "INT64", "mode": "REQUIRED", "description": "Time horizon i dagar"},
                            {"name": "var_absolute", "type": "FLOAT64", "mode": "REQUIRED", "description": "Absolute VaR"},
                            {"name": "var_relative", "type": "FLOAT64", "mode": "REQUIRED", "description": "Relative VaR i procent"},
                            {"name": "volatility", "type": "FLOAT64", "mode": "REQUIRED", "description": "Portfolio volatilitet"},
                            {"name": "sharpe_ratio", "type": "FLOAT64", "mode": "REQUIRED", "description": "Sharpe ratio"},
                            {"name": "max_drawdown", "type": "FLOAT64", "mode": "REQUIRED", "description": "Maximum drawdown"}
                        ],
                        partition_field="timestamp"
                    ),

                    BigQueryTableSchema(
                        table_name="risk_limits",
                        description="Risk limits och thresholds",
                        schema=[
                            {"name": "limit_id", "type": "STRING", "mode": "REQUIRED", "description": "Limit identifierare"},
                            {"name": "limit_type", "type": "STRING", "mode": "REQUIRED", "description": "Typ av limit"},
                            {"name": "threshold", "type": "FLOAT64", "mode": "REQUIRED", "description": "Threshold värde"},
                            {"name": "current_value", "type": "FLOAT64", "mode": "REQUIRED", "description": "Nuvarande värde"},
                            {"name": "is_breached", "type": "BOOL", "mode": "REQUIRED", "description": "Om limit är överskredet"},
                            {"name": "last_updated", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Senast uppdaterad"}
                        ]
                    )
                ]
            )

        if self.DATASET_MARKET_DATA is None:
            self.DATASET_MARKET_DATA = BigQueryDataset(
                dataset_id="market_data",
                description="Market data och price feeds",
                location=self.DEFAULT_LOCATION,
                tables=[
                    BigQueryTableSchema(
                        table_name="token_prices",
                        description="Token priser från olika källor",
                        schema=[
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Price tidpunkt"},
                            {"name": "token_symbol", "type": "STRING", "mode": "REQUIRED", "description": "Token symbol"},
                            {"name": "token_address", "type": "STRING", "mode": "REQUIRED", "description": "Token kontrakt address"},
                            {"name": "price_usd", "type": "FLOAT64", "mode": "REQUIRED", "description": "Pris i USD"},
                            {"name": "source", "type": "STRING", "mode": "REQUIRED", "description": "Data källa"},
                            {"name": "volume_24h", "type": "FLOAT64", "mode": "NULLABLE", "description": "24h volume"},
                            {"name": "market_cap", "type": "FLOAT64", "mode": "NULLABLE", "description": "Market cap"},
                            {"name": "price_change_24h", "type": "FLOAT64", "mode": "NULLABLE", "description": "24h prisändring"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["token_symbol", "source"]
                    ),

                    BigQueryTableSchema(
                        table_name="market_indicators",
                        description="Technical indicators och market metrics",
                        schema=[
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Indicator tidpunkt"},
                            {"name": "token_symbol", "type": "STRING", "mode": "REQUIRED", "description": "Token symbol"},
                            {"name": "indicator_name", "type": "STRING", "mode": "REQUIRED", "description": "Indicator namn"},
                            {"name": "indicator_value", "type": "FLOAT64", "mode": "REQUIRED", "description": "Indicator värde"},
                            {"name": "timeframe", "type": "STRING", "mode": "REQUIRED", "description": "Timeframe (1h, 4h, 1d)"},
                            {"name": "signal", "type": "STRING", "mode": "NULLABLE", "description": "BUY, SELL, NEUTRAL"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["token_symbol", "indicator_name"]
                    )
                ]
            )

        # T004: Blockchain Analytics Dataset för Google Cloud Web3
        if not hasattr(self, 'DATASET_BLOCKCHAIN_ANALYTICS'):
            self.DATASET_BLOCKCHAIN_ANALYTICS = BigQueryDataset(
                dataset_id="blockchain_analytics",
                description="Blockchain analytics och Google Cloud Web3 data",
                location=self.DEFAULT_LOCATION,
                tables=[
                    BigQueryTableSchema(
                        table_name="cross_chain_balances",
                        description="Cross-chain wallet balances från Google Cloud Web3",
                        schema=[
                            {"name": "wallet_address", "type": "STRING", "mode": "REQUIRED", "description": "Wallet address"},
                            {"name": "token_address", "type": "STRING", "mode": "NULLABLE", "description": "Token contract address"},
                            {"name": "token_symbol", "type": "STRING", "mode": "REQUIRED", "description": "Token symbol"},
                            {"name": "chain", "type": "STRING", "mode": "REQUIRED", "description": "Blockchain network"},
                            {"name": "balance", "type": "STRING", "mode": "REQUIRED", "description": "Raw balance"},
                            {"name": "balance_formatted", "type": "FLOAT64", "mode": "REQUIRED", "description": "Formatted balance"},
                            {"name": "decimals", "type": "INT64", "mode": "REQUIRED", "description": "Token decimals"},
                            {"name": "total_value_usd", "type": "FLOAT64", "mode": "NULLABLE", "description": "USD value"},
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Data tidpunkt"},
                            {"name": "provider", "type": "STRING", "mode": "REQUIRED", "description": "Data provider"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["wallet_address", "chain", "token_symbol"]
                    ),

                    BigQueryTableSchema(
                        table_name="blockchain_transactions",
                        description="Blockchain transactions från Google Cloud Web3",
                        schema=[
                            {"name": "tx_hash", "type": "STRING", "mode": "REQUIRED", "description": "Transaction hash"},
                            {"name": "block_number", "type": "INT64", "mode": "REQUIRED", "description": "Block number"},
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Transaction tidpunkt"},
                            {"name": "from_address", "type": "STRING", "mode": "REQUIRED", "description": "From address"},
                            {"name": "to_address", "type": "STRING", "mode": "NULLABLE", "description": "To address"},
                            {"name": "value", "type": "STRING", "mode": "REQUIRED", "description": "Transaction value"},
                            {"name": "gas_price", "type": "STRING", "mode": "NULLABLE", "description": "Gas price"},
                            {"name": "gas_used", "type": "STRING", "mode": "NULLABLE", "description": "Gas used"},
                            {"name": "status", "type": "STRING", "mode": "REQUIRED", "description": "Transaction status"},
                            {"name": "chain", "type": "STRING", "mode": "REQUIRED", "description": "Blockchain network"},
                            {"name": "value_usd", "type": "FLOAT64", "mode": "NULLABLE", "description": "USD value"},
                            {"name": "explorer_url", "type": "STRING", "mode": "NULLABLE", "description": "Block explorer URL"},
                            {"name": "wallet_address", "type": "STRING", "mode": "REQUIRED", "description": "Associated wallet"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["wallet_address", "chain", "status"]
                    ),

                    BigQueryTableSchema(
                        table_name="portfolio_snapshots",
                        description="Portfolio snapshots med cross-chain data",
                        schema=[
                            {"name": "wallet_address", "type": "STRING", "mode": "REQUIRED", "description": "Wallet address"},
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Snapshot tidpunkt"},
                            {"name": "total_value_usd", "type": "FLOAT64", "mode": "REQUIRED", "description": "Total portfolio value"},
                            {"name": "chain_balances", "type": "STRING", "mode": "REPEATED", "description": "Balance per chain"},
                            {"name": "chain_values", "type": "FLOAT64", "mode": "REPEATED", "description": "Value per chain"},
                            {"name": "token_allocations", "type": "STRING", "mode": "REPEATED", "description": "Token allocations"},
                            {"name": "token_values", "type": "FLOAT64", "mode": "REPEATED", "description": "Token values"},
                            {"name": "risk_metrics", "type": "STRING", "mode": "NULLABLE", "description": "Risk metrics JSON"},
                            {"name": "performance_metrics", "type": "STRING", "mode": "NULLABLE", "description": "Performance metrics JSON"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["wallet_address"]
                    ),

                    BigQueryTableSchema(
                        table_name="risk_metrics",
                        description="Real-tids risk metrics för portfolios",
                        schema=[
                            {"name": "wallet_address", "type": "STRING", "mode": "REQUIRED", "description": "Wallet address"},
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Calculation tidpunkt"},
                            {"name": "portfolio_value", "type": "FLOAT64", "mode": "REQUIRED", "description": "Portfolio value"},
                            {"name": "var_95", "type": "FLOAT64", "mode": "NULLABLE", "description": "95% Value at Risk"},
                            {"name": "var_99", "type": "FLOAT64", "mode": "NULLABLE", "description": "99% Value at Risk"},
                            {"name": "volatility", "type": "FLOAT64", "mode": "NULLABLE", "description": "Portfolio volatility"},
                            {"name": "sharpe_ratio", "type": "FLOAT64", "mode": "NULLABLE", "description": "Sharpe ratio"},
                            {"name": "max_drawdown", "type": "FLOAT64", "mode": "NULLABLE", "description": "Maximum drawdown"},
                            {"name": "beta", "type": "FLOAT64", "mode": "NULLABLE", "description": "Portfolio beta"},
                            {"name": "alpha", "type": "FLOAT64", "mode": "NULLABLE", "description": "Portfolio alpha"},
                            {"name": "chain_diversification", "type": "FLOAT64", "mode": "NULLABLE", "description": "Chain diversification score"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["wallet_address"]
                    ),

                    BigQueryTableSchema(
                        table_name="performance_benchmarks",
                        description="Performance benchmarks mot market indices",
                        schema=[
                            {"name": "wallet_address", "type": "STRING", "mode": "REQUIRED", "description": "Wallet address"},
                            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED", "description": "Benchmark tidpunkt"},
                            {"name": "portfolio_return_1d", "type": "FLOAT64", "mode": "NULLABLE", "description": "1-day portfolio return"},
                            {"name": "portfolio_return_7d", "type": "FLOAT64", "mode": "NULLABLE", "description": "7-day portfolio return"},
                            {"name": "portfolio_return_30d", "type": "FLOAT64", "mode": "NULLABLE", "description": "30-day portfolio return"},
                            {"name": "btc_return_1d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Bitcoin 1-day return"},
                            {"name": "btc_return_7d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Bitcoin 7-day return"},
                            {"name": "btc_return_30d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Bitcoin 30-day return"},
                            {"name": "eth_return_1d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Ethereum 1-day return"},
                            {"name": "eth_return_7d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Ethereum 7-day return"},
                            {"name": "eth_return_30d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Ethereum 30-day return"},
                            {"name": "market_return_1d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Market 1-day return"},
                            {"name": "relative_performance_1d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Relative vs market 1d"},
                            {"name": "relative_performance_7d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Relative vs market 7d"},
                            {"name": "relative_performance_30d", "type": "FLOAT64", "mode": "NULLABLE", "description": "Relative vs market 30d"}
                        ],
                        partition_field="timestamp",
                        clustering_fields=["wallet_address"]
                    )
                ]
            )

    # =============================================================================
    # SQL TEMPLATES
    # =============================================================================

    SQL_TEMPLATES = {
        "daily_performance_summary": """
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as total_trades,
                COUNTIF(profit_loss > 0) as winning_trades,
                COUNTIF(profit_loss < 0) as losing_trades,
                ROUND(COUNTIF(profit_loss > 0) / COUNT(*) * 100, 2) as win_rate,
                ROUND(SUM(profit_loss), 4) as total_pnl,
                ROUND(SUM(fee), 4) as total_fees,
                ROUND(SUM(profit_loss) - SUM(fee), 4) as net_pnl,
                ROUND(AVG(price), 4) as avg_price
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp) = DATE('{date}')
            GROUP BY DATE(timestamp)
        """,

        "portfolio_performance": """
            SELECT
                token_symbol,
                SUM(quantity) as total_quantity,
                SUM(total_value) as total_invested,
                SUM(profit_loss) as total_pnl,
                ROUND(SUM(profit_loss) / SUM(total_value) * 100, 2) as roi_percent
            FROM `{project_id}.{dataset}.{table}`
            WHERE status = 'completed'
            GROUP BY token_symbol
            ORDER BY total_invested DESC
        """,

        "risk_metrics_summary": """
            SELECT
                timestamp,
                var_absolute,
                var_relative,
                volatility,
                sharpe_ratio,
                max_drawdown
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            ORDER BY timestamp DESC
            LIMIT 1
        """
    }

# Global BigQuery configuration instance
bigquery_config = BigQueryConfig()

def get_bigquery_config() -> BigQueryConfig:
    """Returnera den globala BigQuery konfigurationen"""
    return bigquery_config

def get_dataset_config(dataset_name: str) -> Optional[BigQueryDataset]:
    """
    Hämta konfiguration för ett specifikt dataset

    Args:
        dataset_name: Namn på dataset (utan project prefix)

    Returns:
        BigQueryDataset eller None om inte hittad
    """
    if dataset_name == "trading_analytics":
        return bigquery_config.DATASET_TRADING
    elif dataset_name == "portfolio_tracking":
        return bigquery_config.DATASET_PORTFOLIO
    elif dataset_name == "risk_metrics":
        return bigquery_config.DATASET_RISK
    elif dataset_name == "market_data":
        return bigquery_config.DATASET_MARKET_DATA
    elif dataset_name == "blockchain_analytics":
        return bigquery_config.DATASET_BLOCKCHAIN_ANALYTICS
    return None

def get_table_schema(dataset_name: str, table_name: str) -> Optional[BigQueryTableSchema]:
    """
    Hämta schema för en specifik table

    Args:
        dataset_name: Namn på dataset
        table_name: Namn på table

    Returns:
        BigQueryTableSchema eller None om inte hittad
    """
    dataset = get_dataset_config(dataset_name)
    if dataset:
        for table in dataset.tables:
            if table.table_name == table_name:
                return table
    return None

def format_sql_template(template_name: str, project_id: str, dataset: str, table: str, **kwargs) -> str:
    """
    Formatera en SQL template med parametrar

    Args:
        template_name: Namn på template
        project_id: Google Cloud project ID
        dataset: Dataset namn
        table: Table namn
        **kwargs: Ytterligare parametrar

    Returns:
        str: Formaterad SQL query
    """
    template = bigquery_config.SQL_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Template '{template_name}' finns inte")

    # Replace placeholders
    formatted = template.replace("{project_id}", project_id)
    formatted = formatted.replace("{dataset}", dataset)
    formatted = formatted.replace("{table}", table)

    # Replace additional parameters
    for key, value in kwargs.items():
        formatted = formatted.replace(f"{{{key}}}", str(value))

    return formatted

def get_create_dataset_ddl(dataset: BigQueryDataset) -> str:
    """
    Generera DDL för att skapa dataset

    Args:
        dataset: Dataset konfiguration

    Returns:
        str: CREATE DATASET DDL
    """
    return f"""
    CREATE SCHEMA `{dataset.dataset_id}`
    OPTIONS(
        description = "{dataset.description}",
        location = "{dataset.location}"
    )
    """

def get_create_table_ddl(project_id: str, dataset: BigQueryDataset, table: BigQueryTableSchema) -> str:
    """
    Generera DDL för att skapa table

    Args:
        project_id: Google Cloud project ID
        dataset: Dataset konfiguration
        table: Table schema

    Returns:
        str: CREATE TABLE DDL
    """
    ddl = f"CREATE TABLE `{project_id}.{dataset.dataset_id}.{table.table_name}` (\n"

    # Add columns
    columns = []
    for col in table.schema:
        col_def = f"  {col['name']} {col['type']}"
        if col['mode'] == 'REQUIRED':
            col_def += " NOT NULL"
        elif col['mode'] == 'REPEATED':
            col_def += " ARRAY"
        columns.append(col_def)

    ddl += ",\n".join(columns)
    ddl += "\n)"

    # Add options
    if table.partition_field or table.clustering_fields:
        ddl += "\nPARTITION BY "
        if table.partition_field:
            ddl += f"DATE({table.partition_field})"
        else:
            ddl += "DATE(_PARTITIONTIME)"

        if table.clustering_fields:
            ddl += f"\nCLUSTER BY {', '.join(table.clustering_fields)}"

    ddl += f"\nOPTIONS(\n  description = \"{table.description}\"\n)"

    return ddl

def get_setup_instructions() -> str:
    """
    Generera instruktioner för att sätta upp BigQuery

    Returns:
        str: Setup instruktioner
    """
    instructions = """
# BigQuery Setup Instructions

## 1. Create Datasets
"""

    datasets = [
        bigquery_config.DATASET_TRADING,
        bigquery_config.DATASET_PORTFOLIO,
        bigquery_config.DATASET_RISK,
        bigquery_config.DATASET_MARKET_DATA,
        bigquery_config.DATASET_BLOCKCHAIN_ANALYTICS
    ]

    for dataset in datasets:
        instructions += f"\n### {dataset.dataset_id}\n"
        instructions += get_create_dataset_ddl(dataset)
        instructions += "\n"

    instructions += "\n## 2. Create Tables\n"

    for dataset in datasets:
        for table in dataset.tables:
            instructions += f"\n### {dataset.dataset_id}.{table.table_name}\n"
            instructions += get_create_table_ddl(os.getenv("GOOGLE_CLOUD_PROJECT_ID", "PROJECT_ID"), dataset, table)
            instructions += "\n"

    return instructions