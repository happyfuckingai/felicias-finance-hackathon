"""
BigQuery Query Templates för Google Cloud Web3 Blockchain Analytics
Portfolio performance, risk analysis, och cross-chain balance queries
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BigQueryQueries:
    """
    BigQuery query templates för blockchain analytics
    """

    # =============================================================================
    # PORTFOLIO PERFORMANCE QUERIES
    # =============================================================================

    @staticmethod
    def get_portfolio_performance_query(
        wallet_address: str,
        days: int = 30,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta portfolio performance query för specifik wallet."""
        return f"""
        WITH portfolio_history AS (
            SELECT
                wallet_address,
                timestamp,
                total_portfolio_value_usd,
                LAG(total_portfolio_value_usd) OVER (
                    PARTITION BY wallet_address
                    ORDER BY timestamp
                ) as prev_value
            FROM `{project_id}.{dataset}.wallet_portfolio_summary_mv`
            WHERE wallet_address = '{wallet_address}'
                AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        ),

        daily_returns AS (
            SELECT
                wallet_address,
                DATE(timestamp) as date,
                total_portfolio_value_usd,
                CASE
                    WHEN prev_value IS NOT NULL AND prev_value > 0
                    THEN (total_portfolio_value_usd - prev_value) / prev_value
                    ELSE 0
                END as daily_return
            FROM portfolio_history
            WHERE total_portfolio_value_usd IS NOT NULL
        )

        SELECT
            wallet_address,

            -- Performance metrics
            COUNT(*) as days_analyzed,
            MIN(total_portfolio_value_usd) as min_value,
            MAX(total_portfolio_value_usd) as max_value,
            AVG(total_portfolio_value_usd) as avg_value,
            ROUND(
                (MAX(total_portfolio_value_usd) - MIN(total_portfolio_value_usd)) /
                NULLIF(MIN(total_portfolio_value_usd), 0) * 100, 4
            ) as total_return_percent,

            -- Return statistics
            ROUND(AVG(daily_return) * 100, 4) as avg_daily_return_percent,
            ROUND(STDDEV(daily_return) * 100, 4) as daily_return_stddev_percent,
            ROUND(
                AVG(daily_return) / NULLIF(STDDEV(daily_return), 0) * SQRT(365), 4
            ) as annual_sharpe_ratio,

            -- Risk metrics
            ROUND(
                PERCENTILE_CONT(daily_return, 0.05) OVER() * 100, 4
            ) as var_95_daily_percent,

            -- Best and worst days
            MAX_BY(
                STRUCT(DATE(timestamp), total_portfolio_value_usd, daily_return),
                daily_return
            ) as best_day,

            MIN_BY(
                STRUCT(DATE(timestamp), total_portfolio_value_usd, daily_return),
                daily_return
            ) as worst_day

        FROM daily_returns
        GROUP BY wallet_address
        """

    @staticmethod
    def get_cross_chain_balance_query(
        wallet_address: str,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta cross-chain balance query för specifik wallet."""
        return f"""
        WITH latest_balances AS (
            SELECT
                wallet_address,
                chain,
                token_symbol,
                token_address,
                balance_formatted,
                decimals,
                total_value_usd,
                timestamp,
                ROW_NUMBER() OVER (
                    PARTITION BY wallet_address, chain, token_symbol
                    ORDER BY timestamp DESC
                ) as rn
            FROM `{project_id}.{dataset}.cross_chain_balances_mv`
            WHERE wallet_address = '{wallet_address}'
                AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        )

        SELECT
            wallet_address,
            chain,
            token_symbol,
            token_address,
            balance_formatted,
            decimals,
            COALESCE(total_value_usd, balance_formatted * 1.0) as value_usd,
            timestamp,
            ROUND(
                COALESCE(total_value_usd, balance_formatted * 1.0) /
                SUM(COALESCE(total_value_usd, balance_formatted * 1.0)) OVER (
                    PARTITION BY wallet_address
                ) * 100, 4
            ) as portfolio_weight_percent

        FROM latest_balances
        WHERE rn = 1
            AND balance_formatted > 0
        ORDER BY value_usd DESC
        """

    @staticmethod
    def get_transaction_history_query(
        wallet_address: str,
        chain: str = None,
        days: int = 7,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta transaction history query för specifik wallet."""
        chain_filter = f"AND chain = '{chain}'" if chain else ""

        return f"""
        SELECT
            tx_hash,
            block_number,
            timestamp,
            from_address,
            to_address,
            CAST(value AS FLOAT64) / POWER(10, 18) as value_eth,
            gas_price,
            gas_used,
            status,
            chain,
            explorer_url,
            wallet_address

        FROM `{project_id}.{dataset}.blockchain_transactions`
        WHERE wallet_address = '{wallet_address}'
            {chain_filter}
            AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        ORDER BY timestamp DESC
        LIMIT 1000
        """

    # =============================================================================
    # RISK ANALYSIS QUERIES
    # =============================================================================

    @staticmethod
    def get_risk_metrics_query(
        wallet_address: str,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta risk metrics query för specifik wallet."""
        return f"""
        WITH risk_data AS (
            SELECT
                wallet_address,
                DATE(timestamp) as date,
                var_95,
                var_99,
                volatility,
                sharpe_ratio,
                max_drawdown,
                beta,
                alpha,
                chain_diversification,
                portfolio_value
            FROM `{project_id}.{dataset}.risk_metrics_aggregated_mv`
            WHERE wallet_address = '{wallet_address}'
                AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        )

        SELECT
            wallet_address,

            -- Current risk metrics
            ARRAY_AGG(
                STRUCT(
                    var_95,
                    var_99,
                    volatility,
                    sharpe_ratio,
                    max_drawdown,
                    beta,
                    alpha,
                    chain_diversification
                )
                ORDER BY date DESC
                LIMIT 1
            )[OFFSET(0)].*,

            -- Risk statistics
            AVG(var_95) as avg_var_95,
            STDDEV(var_95) as stddev_var_95,
            AVG(volatility) as avg_volatility,
            MAX(max_drawdown) as worst_drawdown,

            -- Risk trends
            ARRAY_AGG(var_95 ORDER BY date) as var_trend,
            ARRAY_AGG(volatility ORDER BY date) as volatility_trend,

            -- Risk classification
            CASE
                WHEN ARRAY_AGG(var_95 ORDER BY date DESC LIMIT 1)[OFFSET(0)] > 0.15
                THEN 'HIGH_RISK'
                WHEN ARRAY_AGG(var_95 ORDER BY date DESC LIMIT 1)[OFFSET(0)] > 0.08
                THEN 'MEDIUM_RISK'
                WHEN ARRAY_AGG(var_95 ORDER BY date DESC LIMIT 1)[OFFSET(0)] > 0.05
                THEN 'MEDIUM_LOW_RISK'
                ELSE 'LOW_RISK'
            END as risk_category

        FROM risk_data
        GROUP BY wallet_address
        """

    @staticmethod
    def get_performance_benchmarking_query(
        wallet_address: str,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta performance benchmarking query."""
        return f"""
        SELECT
            wallet_address,
            date,

            -- Portfolio performance
            portfolio_1d,
            portfolio_7d,
            portfolio_30d,

            -- Market benchmarks
            btc_1d,
            btc_7d,
            btc_30d,
            eth_1d,
            eth_7d,
            eth_30d,

            -- Relative performance
            relative_vs_btc_1d,
            relative_vs_btc_7d,
            relative_vs_btc_30d,

            -- Performance categories
            btc_performance_category,
            eth_performance_category

        FROM `{project_id}.{dataset}.performance_benchmarking_mv`
        WHERE wallet_address = '{wallet_address}'
            AND DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        ORDER BY date DESC
        """

    # =============================================================================
    # REAL-TIME ANALYTICS QUERIES
    # =============================================================================

    @staticmethod
    def get_realtime_wallet_health_query(
        wallet_address: str,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta real-time wallet health query."""
        return f"""
        SELECT
            wallet_address,
            timestamp,
            health_score,
            transaction_health,
            balance_health,
            risk_health,
            active_alerts

        FROM `{project_id}.{dataset}.realtime_wallet_health_mv`
        WHERE wallet_address = '{wallet_address}'
            AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        ORDER BY timestamp DESC
        LIMIT 1
        """

    @staticmethod
    def get_daily_portfolio_values_query(
        wallet_address: str,
        days: int = 30,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta daily portfolio values query."""
        return f"""
        SELECT
            wallet_address,
            snapshot_date,
            end_of_day_value,
            daily_return,
            weekly_avg_value,
            monthly_avg_value

        FROM `{project_id}.{dataset}.daily_portfolio_values_mv`
        WHERE wallet_address = '{wallet_address}'
            AND snapshot_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        ORDER BY snapshot_date DESC
        """

    # =============================================================================
    # ADVANCED ANALYTICS QUERIES
    # =============================================================================

    @staticmethod
    def get_portfolio_optimization_query(
        wallet_address: str,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta portfolio optimization suggestions."""
        return f"""
        WITH current_allocation AS (
            SELECT
                wallet_address,
                chain,
                token_symbol,
                value_usd,
                ROUND(
                    value_usd / SUM(value_usd) OVER (PARTITION BY wallet_address) * 100, 2
                ) as current_weight
            FROM (
                SELECT
                    wallet_address,
                    chain,
                    token_symbol,
                    SUM(COALESCE(total_value_usd, balance_formatted * 1.0)) as value_usd
                FROM `{project_id}.{dataset}.cross_chain_balances_mv`
                WHERE wallet_address = '{wallet_address}'
                    AND balance_formatted > 0
                GROUP BY wallet_address, chain, token_symbol
            )
        ),

        risk_analysis AS (
            SELECT
                wallet_address,
                AVG(var_95) as avg_risk,
                AVG(volatility) as avg_volatility,
                COUNT(DISTINCT chain) as chain_diversity
            FROM `{project_id}.{dataset}.risk_metrics_aggregated_mv`
            WHERE wallet_address = '{wallet_address}'
                AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY wallet_address
        )

        SELECT
            ca.wallet_address,
            ca.chain,
            ca.token_symbol,
            ca.current_weight,
            ca.value_usd,

            -- Risk-adjusted weights (simplified)
            CASE
                WHEN ra.avg_risk > 0.10 THEN ca.current_weight * 0.8  -- Reduce for high risk
                WHEN ra.avg_risk < 0.05 THEN ca.current_weight * 1.2  -- Increase for low risk
                ELSE ca.current_weight
            END as suggested_weight,

            -- Rebalancing recommendation
            CASE
                WHEN ABS(
                    CASE
                        WHEN ra.avg_risk > 0.10 THEN ca.current_weight * 0.8
                        WHEN ra.avg_risk < 0.05 THEN ca.current_weight * 1.2
                        ELSE ca.current_weight
                    END - ca.current_weight
                ) > 5 THEN 'REBALANCE_NEEDED'
                ELSE 'HOLD'
            END as recommendation,

            ra.avg_risk,
            ra.avg_volatility,
            ra.chain_diversity

        FROM current_allocation ca
        CROSS JOIN risk_analysis ra
        ORDER BY ca.value_usd DESC
        """

    @staticmethod
    def get_transaction_pattern_analysis_query(
        wallet_address: str,
        days: int = 7,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta transaction pattern analysis query."""
        return f"""
        SELECT
            wallet_address,
            chain,
            total_transactions,
            avg_time_between_transactions,
            transaction_size_stddev,
            large_transactions,
            success_rate,

            -- Pattern classification
            CASE
                WHEN total_transactions > 100 THEN 'HIGHLY_ACTIVE'
                WHEN total_transactions > 50 THEN 'ACTIVE'
                WHEN total_transactions > 10 THEN 'MODERATE'
                ELSE 'LOW_ACTIVITY'
            END as activity_level,

            CASE
                WHEN success_rate > 0.95 THEN 'RELIABLE'
                WHEN success_rate > 0.85 THEN 'MOSTLY_RELIABLE'
                WHEN success_rate > 0.70 THEN 'UNRELIABLE'
                ELSE 'HIGHLY_UNRELIABLE'
            END as reliability_score,

            CASE
                WHEN transaction_size_stddev > 1000 THEN 'HIGH_VARIANCE'
                WHEN transaction_size_stddev > 100 THEN 'MEDIUM_VARIANCE'
                ELSE 'LOW_VARIANCE'
            END as transaction_variance

        FROM `{project_id}.{dataset}.transaction_patterns_mv`
        WHERE wallet_address = '{wallet_address}'
            AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        """

    # =============================================================================
    # AGGREGATED REPORTING QUERIES
    # =============================================================================

    @staticmethod
    def get_wallet_overview_query(
        wallet_address: str,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta comprehensive wallet overview query."""
        return f"""
        WITH latest_portfolio AS (
            SELECT * FROM `{project_id}.{dataset}.wallet_portfolio_summary_mv`
            WHERE wallet_address = '{wallet_address}'
            ORDER BY timestamp DESC
            LIMIT 1
        ),

        latest_risk AS (
            SELECT * FROM `{project_id}.{dataset}.risk_metrics_aggregated_mv`
            WHERE wallet_address = '{wallet_address}'
            ORDER BY timestamp DESC
            LIMIT 1
        ),

        latest_health AS (
            SELECT * FROM `{project_id}.{dataset}.realtime_wallet_health_mv`
            WHERE wallet_address = '{wallet_address}'
            ORDER BY timestamp DESC
            LIMIT 1
        ),

        recent_performance AS (
            SELECT * FROM `{project_id}.{dataset}.performance_benchmarking_mv`
            WHERE wallet_address = '{wallet_address}'
            ORDER BY date DESC
            LIMIT 30
        )

        SELECT
            lp.wallet_address,
            lp.total_portfolio_value_usd,
            lp.num_chains,
            lp.num_tokens,
            lp.total_positions,

            lr.var_95,
            lr.volatility,
            lr.sharpe_ratio,
            lr.risk_category,

            lh.health_score,
            lh.transaction_health,
            lh.balance_health,
            lh.risk_health,

            rp.portfolio_1d,
            rp.portfolio_7d,
            rp.portfolio_30d,
            rp.btc_performance_category,

            ARRAY_LENGTH(lh.active_alerts) as active_alerts_count

        FROM latest_portfolio lp
        LEFT JOIN latest_risk lr ON lp.wallet_address = lr.wallet_address
        LEFT JOIN latest_health lh ON lp.wallet_address = lh.wallet_address
        LEFT JOIN recent_performance rp ON lp.wallet_address = rp.wallet_address
        """

    # =============================================================================
    # ALERTING QUERIES
    # =============================================================================

    @staticmethod
    def get_risk_alerts_query(
        wallet_address: str,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta risk alerts query för specifik wallet."""
        return f"""
        SELECT
            wallet_address,
            timestamp,
            health_score,

            -- Critical alerts
            CASE
                WHEN health_score < 30 THEN 'CRITICAL_RISK_DETECTED'
                WHEN health_score < 50 THEN 'HIGH_RISK_DETECTED'
                WHEN health_score < 70 THEN 'MEDIUM_RISK_DETECTED'
                ELSE 'LOW_RISK'
            END as risk_level,

            -- Specific alerts
            CASE
                WHEN transaction_health = FALSE THEN 'TRANSACTION_ISSUES_DETECTED'
                WHEN balance_health = FALSE THEN 'BALANCE_ANOMALIES_DETECTED'
                WHEN risk_health = FALSE THEN 'RISK_METRICS_DEGRADED'
                ELSE 'NORMAL_OPERATIONS'
            END as alert_type,

            active_alerts

        FROM `{project_id}.{dataset}.realtime_wallet_health_mv`
        WHERE wallet_address = '{wallet_address}'
            AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
            AND (
                health_score < 70
                OR transaction_health = FALSE
                OR balance_health = FALSE
                OR risk_health = FALSE
                OR ARRAY_LENGTH(active_alerts) > 0
            )
        ORDER BY timestamp DESC
        """

    @staticmethod
    def get_performance_alerts_query(
        wallet_address: str,
        project_id: str = "PROJECT_ID",
        dataset: str = "blockchain_analytics"
    ) -> str:
        """Hämta performance alerts query för specifik wallet."""
        return f"""
        WITH performance_data AS (
            SELECT
                wallet_address,
                date,
                portfolio_1d,
                portfolio_7d,
                portfolio_30d,
                relative_vs_btc_1d,
                relative_vs_btc_7d,
                relative_vs_btc_30d
            FROM `{project_id}.{dataset}.performance_benchmarking_mv`
            WHERE wallet_address = '{wallet_address}'
                AND DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        )

        SELECT
            wallet_address,
            date,

            -- Performance alerts
            CASE
                WHEN portfolio_1d < -0.20 THEN 'SEVERE_LOSS_1D'
                WHEN portfolio_1d < -0.10 THEN 'SIGNIFICANT_LOSS_1D'
                WHEN portfolio_7d < -0.30 THEN 'SEVERE_LOSS_7D'
                WHEN portfolio_7d < -0.15 THEN 'SIGNIFICANT_LOSS_7D'
                WHEN portfolio_30d < -0.40 THEN 'SEVERE_LOSS_30D'
                WHEN portfolio_30d < -0.20 THEN 'SIGNIFICANT_LOSS_30D'
                ELSE 'NORMAL_PERFORMANCE'
            END as performance_alert,

            -- Benchmark alerts
            CASE
                WHEN relative_vs_btc_30d < -0.50 THEN 'SIGNIFICANTLY_UNDERPERFORMING_MARKET'
                WHEN relative_vs_btc_30d < -0.20 THEN 'UNDERPERFORMING_MARKET'
                WHEN relative_vs_btc_30d > 0.50 THEN 'SIGNIFICANTLY_OUTPERFORMING_MARKET'
                WHEN relative_vs_btc_30d > 0.20 THEN 'OUTPERFORMING_MARKET'
                ELSE 'MARKET_PERFORMING'
            END as benchmark_alert,

            portfolio_1d,
            portfolio_7d,
            portfolio_30d,
            relative_vs_btc_30d

        FROM performance_data
        WHERE (
            portfolio_1d < -0.10 OR
            portfolio_7d < -0.15 OR
            portfolio_30d < -0.20 OR
            ABS(relative_vs_btc_30d) > 0.20
        )
        ORDER BY date DESC
        """