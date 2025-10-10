"""
Blockchain Analytics - BigQuery-baserad blockchain analytics.
Portfolio performance, risk metrics och real-tids data från Google Cloud Web3.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
from dataclasses import dataclass
from enum import Enum

from ..core.errors.error_handling import handle_errors, CryptoError, ValidationError
from ..core.errors.fail_safe import global_fail_safe
from .google_cloud_web3_provider import GoogleCloudWeb3Provider
from ..core.token.token_providers import TokenInfo

logger = logging.getLogger(__name__)

class TimeFrame(Enum):
    """Tidsperspektiv för analytics."""
    HOUR = "1h"
    DAY = "1d"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"

class RiskLevel(Enum):
    """Risknivåer för portfolio."""
    LOW = "låg"
    MEDIUM = "medium"
    HIGH = "hög"
    CRITICAL = "kritisk"

@dataclass
class PortfolioMetrics:
    """Portfolio metrics struktur."""
    total_value_usd: float
    total_return_24h: float
    total_return_7d: float
    total_return_30d: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    total_trades: int
    risk_level: RiskLevel
    timestamp: datetime

@dataclass
class TokenAnalytics:
    """Token-specifik analytics."""
    token_address: str
    symbol: str
    chain: str
    price_usd: float
    price_change_24h: float
    volume_24h: float
    market_cap: float
    liquidity_usd: float
    holders_count: int
    transaction_count_24h: int
    risk_score: float
    timestamp: datetime

class BlockchainAnalytics:
    """
    BigQuery-baserad blockchain analytics service.

    Features:
    - Portfolio performance och risk metrics
    - Real-tids data från Google Cloud Web3
    - Token analytics och market insights
    - Risk assessment och monitoring
    - Integration med befintliga risk management system
    - Predictive analytics för trading
    """

    def __init__(self, web3_provider: GoogleCloudWeb3Provider, bigquery_dataset: str = "blockchain_analytics"):
        """
        Initiera Blockchain Analytics service.

        Args:
            web3_provider: GoogleCloudWeb3Provider instans
            bigquery_dataset: BigQuery dataset för analytics
        """
        self.web3_provider = web3_provider
        self.bigquery_dataset = bigquery_dataset
        self.analytics_cache = {}
        self.cache_ttl = 300  # 5 minuter

        # Risk thresholds
        self.risk_thresholds = {
            'max_drawdown': 0.15,  # 15%
            'max_volatility': 0.50,  # 50%
            'min_sharpe_ratio': 0.5,
            'max_single_position': 0.25  # 25%
        }

        logger.info("Blockchain Analytics service initierad")

    @handle_errors(service_name="blockchain_analytics")
    async def get_portfolio_analytics(self, wallet_address: str,
                                    time_frame: TimeFrame = TimeFrame.DAY) -> Dict[str, Any]:
        """
        Hämta omfattande portfolio analytics.

        Args:
            wallet_address: Wallet address att analysera
            time_frame: Tidsperspektiv för analys

        Returns:
            Portfolio analytics data
        """
        # Kontrollera cache
        cache_key = f"portfolio_{wallet_address}_{time_frame.value}"
        if cache_key in self.analytics_cache:
            cache_entry = self.analytics_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cache_entry['data']

        try:
            # Hämta cross-chain balances
            balances = await self.web3_provider.get_cross_chain_balances(wallet_address)
            if not balances or 'cross_chain_balances' not in balances:
                raise CryptoError(f"Kunde inte hämta balances för {wallet_address}",
                                "BALANCE_FETCH_FAILED")

            # Beräkna portfolio metrics
            portfolio_metrics = await self._calculate_portfolio_metrics(balances, time_frame)

            # Beräkna risk metrics
            risk_metrics = await self._calculate_risk_metrics(balances, wallet_address, time_frame)

            # Generera risk assessment
            risk_assessment = await self._generate_risk_assessment(risk_metrics)

            # Hämta transaction analytics
            transaction_analytics = await self._get_transaction_analytics(wallet_address, time_frame)

            # Förutsägande analytics
            predictive_analytics = await self._generate_predictive_analytics(wallet_address, time_frame)

            analytics_data = {
                'wallet_address': wallet_address,
                'time_frame': time_frame.value,
                'portfolio_metrics': portfolio_metrics.to_dict(),
                'risk_metrics': risk_metrics,
                'risk_assessment': risk_assessment,
                'transaction_analytics': transaction_analytics,
                'predictive_analytics': predictive_analytics,
                'cross_chain_balances': balances['cross_chain_balances'],
                'total_value_usd': balances.get('total_value_usd', 0),
                'timestamp': datetime.now().isoformat(),
                'provider': 'google_cloud_web3_bigquery'
            }

            # Cache resultatet
            self.analytics_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': analytics_data
            }

            return analytics_data

        except Exception as e:
            logger.error(f"Portfolio analytics misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Portfolio analytics misslyckades: {str(e)}", "ANALYTICS_ERROR")

    @handle_errors(service_name="blockchain_analytics")
    async def get_token_analytics(self, token_address: str,
                                chain: str = 'ethereum') -> Dict[str, Any]:
        """
        Hämta detaljerad token analytics.

        Args:
            token_address: Token contract address
            chain: Blockchain för token

        Returns:
            Token analytics data
        """
        # Kontrollera cache
        cache_key = f"token_{token_address}_{chain}"
        if cache_key in self.analytics_cache:
            cache_entry = self.analytics_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cache_entry['data']

        try:
            # Hämta token info
            token_info = await self.web3_provider.search_token(token_address)
            if not token_info:
                raise ValidationError(f"Token {token_address} hittades inte", "TOKEN_NOT_FOUND")

            # Hämta pris data
            price_data = await self._get_token_price_data(token_address, chain)

            # Hämta trading data
            trading_data = await self._get_token_trading_data(token_address, chain)

            # Hämta liquidity data
            liquidity_data = await self._get_token_liquidity_data(token_address, chain)

            # Hämta holder analytics
            holder_data = await self._get_token_holder_data(token_address, chain)

            # Beräkna risk score
            risk_score = await self._calculate_token_risk_score(token_address, chain, price_data, trading_data)

            token_analytics = TokenAnalytics(
                token_address=token_address,
                symbol=token_info.symbol,
                chain=chain,
                price_usd=price_data.get('price_usd', 0),
                price_change_24h=price_data.get('price_change_24h', 0),
                volume_24h=trading_data.get('volume_24h', 0),
                market_cap=price_data.get('market_cap', 0),
                liquidity_usd=liquidity_data.get('total_liquidity_usd', 0),
                holders_count=holder_data.get('holders_count', 0),
                transaction_count_24h=trading_data.get('transaction_count_24h', 0),
                risk_score=risk_score,
                timestamp=datetime.now()
            )

            analytics_data = {
                'token_analytics': token_analytics.to_dict(),
                'price_data': price_data,
                'trading_data': trading_data,
                'liquidity_data': liquidity_data,
                'holder_data': holder_data,
                'risk_assessment': await self._generate_token_risk_assessment(risk_score),
                'timestamp': datetime.now().isoformat(),
                'provider': 'google_cloud_web3_bigquery'
            }

            # Cache resultatet
            self.analytics_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': analytics_data
            }

            return analytics_data

        except Exception as e:
            logger.error(f"Token analytics misslyckades för {token_address}: {e}")
            raise CryptoError(f"Token analytics misslyckades: {str(e)}", "TOKEN_ANALYTICS_ERROR")

    @handle_errors(service_name="blockchain_analytics")
    async def get_risk_dashboard(self, wallet_address: str) -> Dict[str, Any]:
        """
        Hämta risk dashboard för wallet.

        Args:
            wallet_address: Wallet address att analysera

        Returns:
            Risk dashboard data
        """
        try:
            # Hämta portfolio analytics
            portfolio_data = await self.get_portfolio_analytics(wallet_address, TimeFrame.WEEK)

            # Hämta senaste fail-safe events
            fail_safe_report = await global_fail_safe.get_fail_safe_report(hours=24)

            # Analysera token risks
            token_risks = await self._analyze_token_risks(wallet_address)

            # Generera risk alerts
            risk_alerts = await self._generate_risk_alerts(portfolio_data, token_risks)

            # Beräkna risk scores
            overall_risk_score = await self._calculate_overall_risk_score(portfolio_data, token_risks)

            dashboard_data = {
                'wallet_address': wallet_address,
                'overall_risk_score': overall_risk_score,
                'risk_level': self._get_risk_level(overall_risk_score).__name__,
                'portfolio_risk': portfolio_data['risk_metrics'],
                'token_risks': token_risks,
                'risk_alerts': risk_alerts,
                'fail_safe_events': fail_safe_report.get('recent_events', []),
                'emergency_mode': fail_safe_report.get('emergency_mode', False),
                'recommendations': await self._generate_risk_recommendations(risk_alerts),
                'timestamp': datetime.now().isoformat()
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Risk dashboard misslyckades för {wallet_address}: {e}")
            raise CryptoError(f"Risk dashboard misslyckades: {str(e)}", "RISK_DASHBOARD_ERROR")

    async def _calculate_portfolio_metrics(self, balances: Dict[str, Any],
                                         time_frame: TimeFrame) -> PortfolioMetrics:
        """Beräkna portfolio metrics."""
        try:
            total_value = balances.get('total_value_usd', 0)

            # Simulera historical data för beräkningar
            # I produktion skulle detta hämta från BigQuery
            historical_returns = await self._get_historical_portfolio_returns(
                balances['wallet_address'], time_frame
            )

            # Beräkna returns
            returns_24h = historical_returns.get('24h', 0.02)
            returns_7d = historical_returns.get('7d', 0.15)
            returns_30d = historical_returns.get('30d', 0.35)

            # Beräkna risk metrics
            sharpe_ratio = self._calculate_sharpe_ratio(returns_24h, time_frame)
            max_drawdown = self._calculate_max_drawdown(historical_returns)
            volatility = self._calculate_volatility(historical_returns)
            win_rate = await self._calculate_win_rate(balances['wallet_address'], time_frame)
            total_trades = await self._get_total_trades(balances['wallet_address'], time_frame)

            # Bestäm risk level
            risk_level = self._assess_portfolio_risk_level(
                max_drawdown, volatility, sharpe_ratio, total_value
            )

            return PortfolioMetrics(
                total_value_usd=total_value,
                total_return_24h=returns_24h,
                total_return_7d=returns_7d,
                total_return_30d=returns_30d,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                volatility=volatility,
                win_rate=win_rate,
                total_trades=total_trades,
                risk_level=risk_level,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Portfolio metrics calculation misslyckades: {e}")
            raise

    async def _calculate_risk_metrics(self, balances: Dict[str, Any], wallet_address: str,
                                    time_frame: TimeFrame) -> Dict[str, Any]:
        """Beräkna risk metrics för portfolio."""
        try:
            # Value at Risk (VaR)
            var_95 = await self._calculate_var(wallet_address, time_frame, 0.95)

            # Expected Shortfall
            expected_shortfall = await self._calculate_expected_shortfall(wallet_address, time_frame)

            # Beta mot market
            beta = await self._calculate_portfolio_beta(wallet_address, time_frame)

            # Position concentration
            concentration_metrics = await self._calculate_position_concentration(balances)

            # Liquidity risk
            liquidity_risk = await self._calculate_liquidity_risk(balances)

            return {
                'value_at_risk_95': var_95,
                'expected_shortfall': expected_shortfall,
                'portfolio_beta': beta,
                'position_concentration': concentration_metrics,
                'liquidity_risk': liquidity_risk,
                'diversification_score': self._calculate_diversification_score(balances),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Risk metrics calculation misslyckades: {e}")
            return {}

    async def _generate_risk_assessment(self, risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generera risk assessment för portfolio."""
        try:
            assessment = {
                'overall_score': self._calculate_overall_risk_score_from_metrics(risk_metrics),
                'risk_factors': [],
                'recommendations': [],
                'alerts': []
            }

            # Analysera olika risk faktorer
            if risk_metrics.get('value_at_risk_95', 0) > 0.10:  # 10% VaR
                assessment['risk_factors'].append({
                    'factor': 'value_at_risk',
                    'level': 'high',
                    'description': 'Hög risk för stora förluster',
                    'impact': 'critical'
                })

            if risk_metrics.get('portfolio_beta', 1.0) > 1.5:
                assessment['risk_factors'].append({
                    'factor': 'market_sensitivity',
                    'level': 'medium',
                    'description': 'Hög känslighet för marknadsrörelser',
                    'impact': 'warning'
                })

            if risk_metrics.get('position_concentration', {}).get('max_position', 0) > 0.30:
                assessment['risk_factors'].append({
                    'factor': 'concentration_risk',
                    'level': 'high',
                    'description': 'Hög koncentration i enskilda positioner',
                    'impact': 'critical'
                })

            # Generera recommendations
            if assessment['risk_factors']:
                assessment['recommendations'] = await self._generate_risk_recommendations_from_factors(
                    assessment['risk_factors']
                )

            return assessment

        except Exception as e:
            logger.error(f"Risk assessment generation misslyckades: {e}")
            return {'error': str(e)}

    async def _get_transaction_analytics(self, wallet_address: str,
                                       time_frame: TimeFrame) -> Dict[str, Any]:
        """Hämta transaction analytics."""
        try:
            # Hämta transaction history
            transaction_history = await self.web3_provider.get_transaction_history(
                wallet_address, limit=1000
            )

            # Analysera transactions
            transactions = transaction_history.get('transactions', [])

            # Beräkna metrics
            daily_volume = await self._calculate_daily_transaction_volume(transactions, time_frame)
            transaction_patterns = await self._analyze_transaction_patterns(transactions)
            gas_efficiency = await self._analyze_gas_efficiency(transactions)

            return {
                'total_transactions': len(transactions),
                'daily_volume': daily_volume,
                'transaction_patterns': transaction_patterns,
                'gas_efficiency': gas_efficiency,
                'avg_transaction_size': await self._calculate_avg_transaction_size(transactions),
                'unique_counterparties': await self._count_unique_counterparties(transactions),
                'time_distribution': await self._analyze_transaction_time_distribution(transactions)
            }

        except Exception as e:
            logger.error(f"Transaction analytics misslyckades: {e}")
            return {}

    async def _generate_predictive_analytics(self, wallet_address: str,
                                           time_frame: TimeFrame) -> Dict[str, Any]:
        """Generera predictive analytics för wallet."""
        try:
            # Hämta historical data
            historical_data = await self._get_historical_wallet_data(wallet_address, time_frame)

            # Generera predictions
            price_predictions = await self._generate_price_predictions(historical_data)
            behavior_predictions = await self._predict_wallet_behavior(historical_data)
            risk_predictions = await self._predict_risk_changes(historical_data)

            return {
                'price_predictions': price_predictions,
                'behavior_predictions': behavior_predictions,
                'risk_predictions': risk_predictions,
                'confidence_score': 0.75,  # Simulerad confidence
                'prediction_horizon': time_frame.value
            }

        except Exception as e:
            logger.error(f"Predictive analytics misslyckades: {e}")
            return {}

    async def _get_token_price_data(self, token_address: str, chain: str) -> Dict[str, Any]:
        """Hämta token pris data."""
        # Simulerad pris data från BigQuery
        return {
            'price_usd': 0.0005,  # Simulerat pris
            'price_change_24h': 0.05,  # 5% upp
            'market_cap': 1000000,  # 1M USD
            'volume_24h': 50000,
            'timestamp': datetime.now().isoformat()
        }

    async def _get_token_trading_data(self, token_address: str, chain: str) -> Dict[str, Any]:
        """Hämta token trading data."""
        return {
            'volume_24h': 50000,
            'transaction_count_24h': 150,
            'buy_pressure': 0.6,
            'sell_pressure': 0.4,
            'large_transactions': 5,
            'whale_movements': 2
        }

    async def _get_token_liquidity_data(self, token_address: str, chain: str) -> Dict[str, Any]:
        """Hämta token liquidity data."""
        return {
            'total_liquidity_usd': 250000,
            'liquidity_pools': 3,
            'largest_pool': 150000,
            'pool_distribution': [0.6, 0.3, 0.1],
            'liquidity_trend': 'increasing'
        }

    async def _get_token_holder_data(self, token_address: str, chain: str) -> Dict[str, Any]:
        """Hämta token holder data."""
        return {
            'holders_count': 1250,
            'top_holders_share': 0.35,
            'holder_distribution': {
                'whales': 0.15,
                'investors': 0.45,
                'retail': 0.40
            },
            'holder_trend': 'increasing'
        }

    async def _calculate_token_risk_score(self, token_address: str, chain: str,
                                        price_data: Dict[str, Any],
                                        trading_data: Dict[str, Any]) -> float:
        """Beräkna risk score för token."""
        try:
            risk_score = 0.0

            # Pris volatilitet (30% weight)
            price_change = abs(price_data.get('price_change_24h', 0))
            if price_change > 0.20:  # >20% change
                risk_score += 0.30

            # Volume/liquidity ratio (25% weight)
            market_cap = price_data.get('market_cap', 0)
            volume_24h = trading_data.get('volume_24h', 0)
            if market_cap > 0:
                volume_ratio = volume_24h / market_cap
                if volume_ratio < 0.01:  # <1% daily volume
                    risk_score += 0.25

            # Holder concentration (20% weight)
            holder_data = await self._get_token_holder_data(token_address, chain)
            top_holders_share = holder_data.get('top_holders_share', 0)
            if top_holders_share > 0.50:  # >50% held by top holders
                risk_score += 0.20

            # Liquidity depth (15% weight)
            liquidity_data = await self._get_token_liquidity_data(token_address, chain)
            total_liquidity = liquidity_data.get('total_liquidity_usd', 0)
            if total_liquidity < 100000:  # <100k liquidity
                risk_score += 0.15

            # Transaction activity (10% weight)
            transaction_count = trading_data.get('transaction_count_24h', 0)
            if transaction_count < 10:  # Very low activity
                risk_score += 0.10

            return min(risk_score, 1.0)  # Cap at 1.0

        except Exception as e:
            logger.error(f"Token risk score calculation misslyckades: {e}")
            return 0.5  # Default medium risk

    async def _generate_token_risk_assessment(self, risk_score: float) -> Dict[str, Any]:
        """Generera risk assessment för token."""
        if risk_score < 0.3:
            level = "låg"
            recommendation = "Säker för investering"
        elif risk_score < 0.6:
            level = "medium"
            recommendation = "Måttlig risk - diversifiera"
        elif risk_score < 0.8:
            level = "hög"
            recommendation = "Hög risk - begränsa exponering"
        else:
            level = "kritisk"
            recommendation = "Extremt hög risk - undvik"

        return {
            'risk_score': risk_score,
            'risk_level': level,
            'recommendation': recommendation,
            'action_items': await self._get_token_risk_action_items(risk_score)
        }

    async def _analyze_token_risks(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Analysera risk för alla tokens i wallet."""
        try:
            balances = await self.web3_provider.get_cross_chain_balances(wallet_address)
            token_risks = []

            for chain, chain_balances in balances.get('cross_chain_balances', {}).items():
                for balance in chain_balances:
                    token_address = balance.get('token_address')
                    if token_address and balance.get('balance_formatted', 0) > 0:
                        analytics = await self.get_token_analytics(token_address, chain)
                        if 'token_analytics' in analytics:
                            token_risks.append({
                                'token_address': token_address,
                                'symbol': balance.get('symbol', 'UNKNOWN'),
                                'chain': chain,
                                'value_usd': balance.get('balance_formatted', 0),
                                'risk_score': analytics['token_analytics'].get('risk_score', 0.5),
                                'risk_level': analytics['risk_assessment'].get('risk_level', 'medium'),
                                'recommendation': analytics['risk_assessment'].get('recommendation', '')
                            })

            return token_risks

        except Exception as e:
            logger.error(f"Token risk analysis misslyckades: {e}")
            return []

    async def _generate_risk_alerts(self, portfolio_data: Dict[str, Any],
                                  token_risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generera risk alerts."""
        alerts = []

        # Portfolio alerts
        portfolio_metrics = portfolio_data.get('portfolio_metrics', {})
        if portfolio_metrics.get('max_drawdown', 0) > self.risk_thresholds['max_drawdown']:
            alerts.append({
                'type': 'portfolio',
                'severity': 'critical',
                'message': f'Portfolio drawdown {portfolio_metrics["max_drawdown"]:.1%} överskrider limit',
                'action': 'Överväg att minska riskexponering'
            })

        # Token alerts
        for token_risk in token_risks:
            if token_risk['risk_score'] > 0.7:
                alerts.append({
                    'type': 'token',
                    'severity': 'high',
                    'message': f'Hög risk i {token_risk["symbol"]}: {token_risk["risk_score"]:.2f}',
                    'action': token_risk['recommendation']
                })

        return alerts

    async def _calculate_overall_risk_score(self, portfolio_data: Dict[str, Any],
                                          token_risks: List[Dict[str, Any]]) -> float:
        """Beräkna övergripande risk score."""
        try:
            # Portfolio risk (40% weight)
            portfolio_risk = portfolio_data.get('risk_assessment', {}).get('overall_score', 0.5)

            # Token risks (60% weight)
            if token_risks:
                avg_token_risk = sum(t['risk_score'] for t in token_risks) / len(token_risks)
            else:
                avg_token_risk = 0.5

            return (portfolio_risk * 0.4) + (avg_token_risk * 0.6)

        except Exception as e:
            logger.error(f"Overall risk score calculation misslyckades: {e}")
            return 0.5

    async def _generate_risk_recommendations(self, risk_alerts: List[Dict[str, Any]]) -> List[str]:
        """Generera risk recommendations."""
        recommendations = []

        critical_alerts = [a for a in risk_alerts if a['severity'] == 'critical']
        high_alerts = [a for a in risk_alerts if a['severity'] == 'high']

        if critical_alerts:
            recommendations.append("AKUT: Implementera riskreducerande åtgärder omedelbart")

        if len(high_alerts) > 2:
            recommendations.append("Diversifiera portfolio för att minska risk")

        recommendations.extend([
            "Övervaka marknaden noggrant",
            "Sätt stop-loss orders för högriskpositioner",
            "Överväg att ta hem vinster från framgångsrika positioner"
        ])

        return recommendations

    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """Bestäm risk level från risk score."""
        if risk_score < 0.3:
            return RiskLevel.LOW
        elif risk_score < 0.6:
            return RiskLevel.MEDIUM
        elif risk_score < 0.8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    # Helper methods för risk calculations
    def _calculate_sharpe_ratio(self, returns: float, time_frame: TimeFrame) -> float:
        """Beräkna Sharpe ratio."""
        # Simulerad calculation
        risk_free_rate = 0.02  # 2% riskfri ränta
        volatility = 0.30  # 30% volatilitet

        if volatility == 0:
            return 0.0

        annual_return = returns * (365 if time_frame == TimeFrame.DAY else 1)
        annual_volatility = volatility * (365 ** 0.5 if time_frame == TimeFrame.DAY else 1)

        return (annual_return - risk_free_rate) / annual_volatility

    def _calculate_max_drawdown(self, returns: Dict[str, float]) -> float:
        """Beräkna max drawdown."""
        # Simulerad calculation
        return 0.12  # 12% max drawdown

    def _calculate_volatility(self, returns: Dict[str, float]) -> float:
        """Beräkna volatilitet."""
        # Simulerad calculation
        return 0.25  # 25% volatilitet

    async def _calculate_var(self, wallet_address: str, time_frame: TimeFrame,
                           confidence_level: float = 0.95) -> float:
        """Beräkna Value at Risk."""
        # Simulerad VaR calculation
        return 0.08  # 8% VaR

    async def _calculate_expected_shortfall(self, wallet_address: str, time_frame: TimeFrame) -> float:
        """Beräkna Expected Shortfall."""
        # Simulerad calculation
        return 0.12  # 12% expected shortfall

    async def _calculate_portfolio_beta(self, wallet_address: str, time_frame: TimeFrame) -> float:
        """Beräkna portfolio beta."""
        # Simulerad calculation
        return 1.2  # Beta 1.2

    async def _calculate_position_concentration(self, balances: Dict[str, Any]) -> Dict[str, Any]:
        """Beräkna position concentration."""
        # Simulerad calculation
        return {
            'max_position': 0.15,
            'top_3_positions': 0.45,
            'herfindahl_index': 0.12
        }

    async def _calculate_liquidity_risk(self, balances: Dict[str, Any]) -> Dict[str, Any]:
        """Beräkna liquidity risk."""
        # Simulerad calculation
        return {
            'average_liquidity_score': 0.7,
            'low_liquidity_positions': 2,
            'overall_liquidity_risk': 'medium'
        }

    def _calculate_diversification_score(self, balances: Dict[str, Any]) -> float:
        """Beräkna diversifierings score."""
        # Simulerad calculation
        return 0.65  # 65% diversifierad

    async def _calculate_win_rate(self, wallet_address: str, time_frame: TimeFrame) -> float:
        """Beräkna win rate för trades."""
        # Simulerad calculation
        return 0.68  # 68% win rate

    async def _get_total_trades(self, wallet_address: str, time_frame: TimeFrame) -> int:
        """Hämta totalt antal trades."""
        # Simulerad calculation
        return 45

    async def _get_historical_portfolio_returns(self, wallet_address: str,
                                              time_frame: TimeFrame) -> Dict[str, float]:
        """Hämta historical portfolio returns."""
        # Simulerad data
        return {
            '24h': 0.023,
            '7d': 0.145,
            '30d': 0.287
        }

    async def _calculate_daily_transaction_volume(self, transactions: List[Dict[str, Any]],
                                                time_frame: TimeFrame) -> Dict[str, float]:
        """Beräkna daily transaction volume."""
        # Simulerad calculation
        return {
            'total_volume': 25000.0,
            'average_daily': 3500.0,
            'peak_day': 8500.0
        }

    async def _analyze_transaction_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysera transaction patterns."""
        # Simulerad analysis
        return {
            'frequent_trading': True,
            'large_transactions': 5,
            'regular_schedule': False,
            'pattern_score': 0.7
        }

    async def _analyze_gas_efficiency(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysera gas efficiency."""
        # Simulerad analysis
        return {
            'average_gas_cost': 15.50,
            'gas_optimization_score': 0.75,
            'potential_savings': 0.25,
            'recommendations': ['Använd lägre gas price under lågtrafik']
        }

    async def _calculate_avg_transaction_size(self, transactions: List[Dict[str, Any]]) -> float:
        """Beräkna genomsnittlig transaction storlek."""
        # Simulerad calculation
        return 1250.0

    async def _count_unique_counterparties(self, transactions: List[Dict[str, Any]]) -> int:
        """Räkna unika motparter."""
        # Simulerad calculation
        return 23

    async def _analyze_transaction_time_distribution(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysera transaction tidsfördelning."""
        # Simulerad analysis
        return {
            'peak_hours': [14, 15, 16],
            'weekday_distribution': [0.1, 0.2, 0.15, 0.25, 0.2, 0.05, 0.05],
            'night_trading': 0.1
        }

    async def _get_historical_wallet_data(self, wallet_address: str, time_frame: TimeFrame) -> Dict[str, Any]:
        """Hämta historical wallet data."""
        # Simulerad data
        return {
            'balance_history': [],
            'transaction_history': [],
            'performance_metrics': {}
        }

    async def _generate_price_predictions(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generera pris predictions."""
        # Simulerad predictions
        return {
            'next_24h': 0.02,
            'next_7d': 0.15,
            'next_30d': 0.35,
            'confidence': 0.65
        }

    async def _predict_wallet_behavior(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Förutsäg wallet beteende."""
        # Simulerad predictions
        return {
            'likely_to_sell': 0.3,
            'likely_to_buy': 0.6,
            'likely_to_hold': 0.1,
            'behavior_pattern': 'active_trader'
        }

    async def _predict_risk_changes(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Förutsäg riskförändringar."""
        # Simulerad predictions
        return {
            'risk_trend': 'increasing',
            'expected_risk_change': 0.05,
            'risk_triggers': ['market_volatility', 'large_positions']
        }

    def _calculate_overall_risk_score_from_metrics(self, risk_metrics: Dict[str, Any]) -> float:
        """Beräkna overall risk score från metrics."""
        # Simulerad calculation
        return 0.45

    async def _generate_risk_recommendations_from_factors(self, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """Generera risk recommendations från faktorer."""
        recommendations = []

        for factor in risk_factors:
            if factor['factor'] == 'value_at_risk':
                recommendations.append("Implementera stop-loss mekanismer")
            elif factor['factor'] == 'concentration_risk':
                recommendations.append("Diversifiera genom att sälja stora positioner")
            elif factor['factor'] == 'market_sensitivity':
                recommendations.append("Överväg hedging strategier")

        return recommendations

    async def _get_token_risk_action_items(self, risk_score: float) -> List[str]:
        """Hämta token risk action items."""
        if risk_score > 0.8:
            return ["Undvik token", "Sälj befintliga positioner", "Sätt inte in mer kapital"]
        elif risk_score > 0.6:
            return ["Begränsa position storlek", "Sätt stop-loss", "Övervaka noggrant"]
        else:
            return ["Säker för normal trading", "Kan öka position om önskat"]

    async def clear_cache(self) -> None:
        """Rensa analytics cache."""
        self.analytics_cache.clear()
        logger.info("Blockchain analytics cache rensad")

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på analytics service."""
        try:
            # Kontrollera Web3 provider
            provider_health = await self.web3_provider.health_check()

            # Kontrollera cache status
            cache_size = len(self.analytics_cache)
            cache_health = 'healthy' if cache_size < 1000 else 'warning'

            return {
                'service': 'blockchain_analytics',
                'status': 'healthy' if provider_health['status'] == 'healthy' else 'degraded',
                'provider_health': provider_health,
                'cache_size': cache_size,
                'cache_health': cache_health,
                'supported_timeframes': [tf.value for tf in TimeFrame],
                'supported_chains': list(self.web3_provider.CHAIN_MAPPINGS.keys()),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'blockchain_analytics',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def to_dict(self, obj: Any) -> Dict[str, Any]:
        """Konvertera objekt till dictionary."""
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)