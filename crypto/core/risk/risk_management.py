"""
Risk Management för automatisk trading.
Implementerar olika riskkontroller och position sizing strategier.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

logger = logging.getLogger(__name__)

class RiskManager:
    """Hanterar risk för trading portfölj."""

    def __init__(self):
        self.config = {
            'max_portfolio_risk': 0.1,      # 10% max portfolio risk
            'max_single_trade_risk': 0.02,  # 2% max risk per trade
            'max_daily_loss': 0.05,         # 5% max daily loss
            'max_drawdown': 0.15,           # 15% max drawdown
            'max_positions': 5,             # Max 5 öppna positioner
            'min_position_size': 0.001,     # Min 0.1% position size
            'max_position_size': 0.1,       # Max 10% position size
            'max_correlation': 0.7,         # Max correlation mellan positioner
            'volatility_adjustment': True,  # Justera för volatilitet
            'stress_test_enabled': True     # Kör stress tests
        }

        # Risk tracking
        self.portfolio_value = 1000.0  # Default $1000
        self.daily_start_value = self.portfolio_value
        self.peak_value = self.portfolio_value
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.max_drawdown_value = 0.0

        # Position tracking
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.correlation_matrix: Dict[Tuple[str, str], float] = {}

        logger.info("Risk Manager initialized")

    def calculate_position_size(self,
                               signal_confidence: float,
                               current_price: float,
                               volatility: float,
                               portfolio_value: float,
                               stop_loss_percent: float = 0.05) -> float:
        """
        Beräkna optimal position size baserat på risk management principer.

        Args:
            signal_confidence: Signal confidence (0-1)
            current_price: Current asset price
            volatility: Asset volatility (0-1)
            portfolio_value: Current portfolio value
            stop_loss_percent: Stop loss percentage

        Returns:
            Optimal position size i USD
        """
        try:
            # Kelly Criterion inspired position sizing
            risk_per_trade = self.config['max_single_trade_risk']

            # Justera för confidence
            confidence_multiplier = min(signal_confidence, 1.0)

            # Justera för volatilitet (högre volatilitet = mindre position)
            if self.config['volatility_adjustment']:
                vol_adjustment = max(0.1, 1.0 - volatility)  # Min 10% av normal size
                confidence_multiplier *= vol_adjustment

            # Beräkna base risk amount
            risk_amount = portfolio_value * risk_per_trade * confidence_multiplier

            # Stop loss distance
            stop_loss_distance = current_price * stop_loss_percent

            # Position size i tokens
            if stop_loss_distance > 0:
                position_size_tokens = risk_amount / stop_loss_distance
                position_size_usd = position_size_tokens * current_price
            else:
                position_size_usd = 0

            # Säkerhetsgränser
            min_size = portfolio_value * self.config['min_position_size']
            max_size = portfolio_value * self.config['max_position_size']

            position_size_usd = max(min_size, min(position_size_usd, max_size))

            # Kontrollera att vi inte överskrider portfolio risk
            total_risk_used = sum(pos.get('risk_amount', 0) for pos in self.positions.values())
            max_additional_risk = portfolio_value * self.config['max_portfolio_risk'] - total_risk_used

            position_size_usd = min(position_size_usd, max_additional_risk)

            return position_size_usd

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0

    def assess_portfolio_risk(self) -> Dict[str, Any]:
        """
        Bedöm total portfolio risk.

        Returns:
            Risk assessment dict
        """
        try:
            assessment = {
                'total_positions': len(self.positions),
                'total_exposure': 0.0,
                'total_risk': 0.0,
                'concentration_risk': 0.0,
                'correlation_risk': 0.0,
                'volatility_risk': 0.0,
                'overall_risk_level': 'low',
                'risk_warnings': []
            }

            if not self.positions:
                return assessment

            # Beräkna total exposure och risk
            for pos in self.positions.values():
                assessment['total_exposure'] += pos.get('value', 0)
                assessment['total_risk'] += pos.get('risk_amount', 0)

            # Koncentrationsrisk (högsta position som % av portfolio)
            if assessment['total_exposure'] > 0:
                max_position = max(pos.get('value', 0) for pos in self.positions.values())
                assessment['concentration_risk'] = max_position / assessment['total_exposure']

            # Korrelationsrisk
            assessment['correlation_risk'] = self._calculate_correlation_risk()

            # Volatilitetsrisk
            assessment['volatility_risk'] = self._calculate_volatility_risk()

            # Övergripande riskbedömning
            risk_score = (
                assessment['concentration_risk'] * 0.3 +
                assessment['correlation_risk'] * 0.3 +
                assessment['volatility_risk'] * 0.4
            )

            if risk_score > 0.8:
                assessment['overall_risk_level'] = 'high'
            elif risk_score > 0.5:
                assessment['overall_risk_level'] = 'medium'
            else:
                assessment['overall_risk_level'] = 'low'

            # Risk warnings
            if assessment['total_positions'] >= self.config['max_positions']:
                assessment['risk_warnings'].append("Maximum positions reached")

            if assessment['concentration_risk'] > 0.3:
                assessment['risk_warnings'].append("High concentration risk detected")

            if assessment['correlation_risk'] > 0.7:
                assessment['risk_warnings'].append("High correlation risk detected")

            return assessment

        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}")
            return {'error': str(e)}

    def _calculate_correlation_risk(self) -> float:
        """Beräkna korrelationsrisk för portfölj."""
        try:
            if len(self.positions) < 2:
                return 0.0

            # Enkel korrelationsberäkning baserat på tillgångstyp
            # I en verklig implementation skulle detta använda historiska prisdata
            crypto_tokens = [pos for pos in self.positions.keys() if 'bitcoin' in pos.lower() or 'ethereum' in pos.lower()]
            altcoins = [pos for pos in self.positions.keys() if pos not in crypto_tokens]

            if crypto_tokens and altcoins:
                # Antag högre korrelation mellan altcoins
                return 0.6
            elif len(crypto_tokens) > 1:
                return 0.4  # Lägre korrelation mellan BTC/ETH
            else:
                return 0.2

        except Exception as e:
            logger.error(f"Error calculating correlation risk: {e}")
            return 0.5

    def _calculate_volatility_risk(self) -> float:
        """Beräkna volatilitetsrisk för portfölj."""
        try:
            if not self.positions:
                return 0.0

            # Beräkna genomsnittlig volatilitet
            total_volatility = 0.0
            count = 0

            for pos in self.positions.values():
                vol = pos.get('volatility', 0.5)  # Default 50% volatility
                total_volatility += vol
                count += 1

            avg_volatility = total_volatility / count if count > 0 else 0.0

            # Normalisera till 0-1 skala
            return min(avg_volatility, 1.0)

        except Exception as e:
            logger.error(f"Error calculating volatility risk: {e}")
            return 0.5

    def check_risk_limits(self, new_position_value: float, asset_volatility: float) -> Tuple[bool, str]:
        """
        Kontrollera att nya positioner inte överskrider risk limits.

        Args:
            new_position_value: Värde av nya positionen
            asset_volatility: Volatilitet för tillgången

        Returns:
            (allowed: bool, reason: str)
        """
        try:
            # Kontrollera max positioner
            if len(self.positions) >= self.config['max_positions']:
                return False, "Maximum positions limit reached"

            # Kontrollera portfolio risk
            current_risk = sum(pos.get('risk_amount', 0) for pos in self.positions.values())
            new_total_risk = current_risk + (new_position_value * asset_volatility * 0.05)  # Antag 5% risk
            max_risk = self.portfolio_value * self.config['max_portfolio_risk']

            if new_total_risk > max_risk:
                return False, f"Portfolio risk limit exceeded: {new_total_risk:.2f} > {max_risk:.2f}"

            # Kontrollera daily loss limit
            if self.daily_pnl < -self.portfolio_value * self.config['max_daily_loss']:
                return False, "Daily loss limit exceeded"

            # Kontrollera drawdown limit
            current_drawdown = (self.peak_value - self.portfolio_value) / self.peak_value
            if current_drawdown > self.config['max_drawdown']:
                return False, f"Drawdown limit exceeded: {current_drawdown:.2%}"

            return True, "Risk check passed"

        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return False, f"Risk check error: {str(e)}"

    def update_portfolio_metrics(self, current_value: float):
        """
        Uppdatera portfolio metrics med nytt värde.

        Args:
            current_value: Aktuellt portfolio värde
        """
        try:
            old_value = self.portfolio_value
            self.portfolio_value = current_value

            # Uppdatera P&L
            pnl_change = current_value - old_value
            self.daily_pnl += pnl_change
            self.total_pnl += pnl_change

            # Uppdatera peak value och drawdown
            if current_value > self.peak_value:
                self.peak_value = current_value
                self.max_drawdown_value = 0.0
            else:
                current_drawdown = (self.peak_value - current_value) / self.peak_value
                self.max_drawdown_value = max(self.max_drawdown_value, current_drawdown)

        except Exception as e:
            logger.error(f"Error updating portfolio metrics: {e}")

    def add_position(self, token_id: str, position_data: Dict[str, Any]):
        """
        Lägg till ny position till risk tracking.

        Args:
            token_id: Token identifier
            position_data: Position information
        """
        try:
            self.positions[token_id] = position_data.copy()
            logger.info(f"Added position tracking for {token_id}")

        except Exception as e:
            logger.error(f"Error adding position {token_id}: {e}")

    def remove_position(self, token_id: str):
        """
        Ta bort position från risk tracking.

        Args:
            token_id: Token identifier
        """
        try:
            if token_id in self.positions:
                del self.positions[token_id]
                logger.info(f"Removed position tracking for {token_id}")

        except Exception as e:
            logger.error(f"Error removing position {token_id}: {e}")

    def get_stress_test_results(self, scenarios: List[str] = None) -> Dict[str, Any]:
        """
        Kör stress tests för olika marknads scenarier.

        Args:
            scenarios: Lista med test scenarier

        Returns:
            Stress test results
        """
        if not self.config['stress_test_enabled']:
            return {'enabled': False}

        if scenarios is None:
            scenarios = ['flash_crash', 'high_volatility', 'correlated_selloff']

        results = {
            'scenarios_tested': [],
            'worst_case_loss': 0.0,
            'recommended_actions': []
        }

        try:
            for scenario in scenarios:
                scenario_result = self._run_scenario_test(scenario)
                results['scenarios_tested'].append(scenario_result)

                if scenario_result['portfolio_loss'] > results['worst_case_loss']:
                    results['worst_case_loss'] = scenario_result['portfolio_loss']

            # Rekommendationer baserat på stress tests
            if results['worst_case_loss'] > 0.2:  # 20% loss
                results['recommended_actions'].append("Reduce position sizes")
                results['recommended_actions'].append("Increase diversification")
            elif results['worst_case_loss'] > 0.1:  # 10% loss
                results['recommended_actions'].append("Monitor closely")
            else:
                results['recommended_actions'].append("Current risk acceptable")

        except Exception as e:
            logger.error(f"Error running stress tests: {e}")
            results['error'] = str(e)

        return results

    def _run_scenario_test(self, scenario: str) -> Dict[str, Any]:
        """Kör enskilt scenario test."""
        # Enkel scenario modeling - i verkligheten skulle detta använda historiska data
        scenario_impacts = {
            'flash_crash': {'price_impact': -0.3, 'duration_hours': 2},
            'high_volatility': {'price_impact': -0.15, 'duration_hours': 24},
            'correlated_selloff': {'price_impact': -0.25, 'duration_hours': 6}
        }

        impact = scenario_impacts.get(scenario, {'price_impact': -0.1, 'duration_hours': 12})

        # Beräkna förväntad portfolio loss
        portfolio_loss = 0.0
        for pos in self.positions.values():
            position_value = pos.get('value', 0)
            loss = position_value * abs(impact['price_impact'])
            portfolio_loss += loss

        return {
            'scenario': scenario,
            'price_impact': impact['price_impact'],
            'duration_hours': impact['duration_hours'],
            'portfolio_loss': portfolio_loss,
            'portfolio_loss_percent': portfolio_loss / self.portfolio_value if self.portfolio_value > 0 else 0
        }

    def get_risk_report(self) -> Dict[str, Any]:
        """
        Generera komplett risk rapport.

        Returns:
            Comprehensive risk report
        """
        try:
            assessment = self.assess_portfolio_risk()
            stress_tests = self.get_stress_test_results()

            report = {
                'timestamp': datetime.now().isoformat(),
                'portfolio_value': self.portfolio_value,
                'daily_pnl': self.daily_pnl,
                'total_pnl': self.total_pnl,
                'peak_value': self.peak_value,
                'max_drawdown': self.max_drawdown_value,
                'risk_assessment': assessment,
                'stress_test_results': stress_tests,
                'positions': self.positions.copy(),
                'recommendations': []
            }

            # Generera rekommendationer
            if assessment['overall_risk_level'] == 'high':
                report['recommendations'].append("Reduce position sizes immediately")
                report['recommendations'].append("Consider closing high-risk positions")
            elif assessment['overall_risk_level'] == 'medium':
                report['recommendations'].append("Monitor positions closely")
                report['recommendations'].append("Consider rebalancing portfolio")

            if stress_tests.get('worst_case_loss', 0) > 0.15:
                report['recommendations'].append("Implement additional risk controls")

            return report

        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {'error': str(e)}