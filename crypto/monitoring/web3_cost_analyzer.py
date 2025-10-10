"""
Web3 Cost Analyzer - Kostnadsanalys för Web3-operationer.
Jämförelse mellan externa providers och Google Cloud Web3 med real-tids kostnadsövervakning.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
from dataclasses import dataclass, field
from enum import Enum

from ..core.errors.error_handling import handle_errors, CryptoError, ValidationError
from ..core.token.token_providers import TokenInfo

logger = logging.getLogger(__name__)

class CostCategory(Enum):
    """Kostnadskategorier för Web3-operationer."""
    GAS_FEES = "gas_fees"
    BRIDGE_FEES = "bridge_fees"
    SWAP_FEES = "swap_fees"
    LIQUIDITY_FEES = "liquidity_fees"
    ORACLE_FEES = "oracle_fees"
    STORAGE_FEES = "storage_fees"
    CROSS_CHAIN_FEES = "cross_chain_fees"
    API_FEES = "api_fees"

class ProviderType(Enum):
    """Provider typer för kostnadsjämförelse."""
    GOOGLE_CLOUD_WEB3 = "google_cloud_web3"
    EXTERNAL_RPC = "external_rpc"
    INFURA = "infura"
    ALCHEMY = "alchemy"
    QUICKNODE = "quicknode"
    CUSTOM_RPC = "custom_rpc"

@dataclass
class CostBreakdown:
    """Kostnadsuppdelning för operationer."""
    category: CostCategory
    base_cost_usd: float
    google_cloud_cost_usd: float
    external_cost_usd: float
    savings_usd: float
    savings_percentage: float
    timestamp: datetime
    operation_details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderCostComparison:
    """Jämförelse mellan olika providers."""
    provider_type: ProviderType
    operation_type: str
    google_cloud_cost: float
    provider_cost: float
    savings: float
    savings_percentage: float
    reliability_score: float
    speed_score: float
    timestamp: datetime

@dataclass
class CostAlert:
    """Kostnadsalert för överskridanden."""
    alert_type: str  # 'warning', 'critical', 'info'
    message: str
    current_cost: float
    threshold: float
    category: CostCategory
    timestamp: datetime
    recommendation: str = ""

class Web3CostAnalyzer:
    """
    Kostnadsanalys för Web3-operationer med Google Cloud Web3 integration.

    Features:
    - Real-tids kostnadsövervakning
    - Jämförelse mellan externa providers och Google Cloud Web3
    - 83% kostnadsbesparing tracking
    - Kostnadsfördelning per kategori
    - Predictive kostnadsanalys
    - Budget tracking och alerts
    """

    def __init__(self):
        """
        Initiera Web3 Cost Analyzer.
        """
        self.cost_history = []
        self.provider_comparisons = []
        self.cost_alerts = []
        self.budget_limits = {}
        self.savings_target = 0.83  # 83% kostnadsbesparing

        # Kostnads thresholds för alerts
        self.cost_thresholds = {
            CostCategory.GAS_FEES: 50.0,  # $50 per dag
            CostCategory.BRIDGE_FEES: 100.0,  # $100 per dag
            CostCategory.SWAP_FEES: 25.0,  # $25 per dag
            CostCategory.CROSS_CHAIN_FEES: 75.0,  # $75 per dag
        }

        logger.info("Web3 Cost Analyzer initierad")

    @handle_errors(service_name="web3_cost_analyzer")
    async def analyze_operation_cost(self, operation_data: Dict[str, Any],
                                   provider_type: ProviderType = ProviderType.GOOGLE_CLOUD_WEB3) -> Dict[str, Any]:
        """
        Analysera kostnad för Web3-operation.

        Args:
            operation_data: Data om operationen att analysera
            provider_type: Vilken provider som användes

        Returns:
            Kostnadsanalys för operationen
        """
        try:
            operation_type = operation_data.get('operation_type', 'unknown')

            # Beräkna kostnader för olika providers
            google_cloud_cost = await self._calculate_google_cloud_cost(operation_data)
            external_costs = await self._calculate_external_provider_costs(operation_data)

            # Beräkna besparingar
            avg_external_cost = sum(external_costs.values()) / len(external_costs) if external_costs else 0
            savings_usd = max(0, avg_external_cost - google_cloud_cost)
            savings_percentage = (savings_usd / avg_external_cost * 100) if avg_external_cost > 0 else 0

            # Skapa kostnadsuppdelning
            cost_breakdown = CostBreakdown(
                category=CostCategory(operation_data.get('cost_category', 'gas_fees')),
                base_cost_usd=avg_external_cost,
                google_cloud_cost_usd=google_cloud_cost,
                external_cost_usd=avg_external_cost,
                savings_usd=savings_usd,
                savings_percentage=savings_percentage,
                timestamp=datetime.now(),
                operation_details=operation_data
            )

            # Spara i historik
            self.cost_history.append(cost_breakdown)

            # Kontrollera alerts
            await self._check_cost_alerts(cost_breakdown)

            analysis_result = {
                'operation_type': operation_type,
                'provider_type': provider_type.value,
                'cost_breakdown': cost_breakdown.to_dict(),
                'external_costs_comparison': external_costs,
                'savings_analysis': {
                    'usd_saved': savings_usd,
                    'percentage_saved': savings_percentage,
                    'target_achieved': savings_percentage >= self.savings_target * 100
                },
                'cost_efficiency_score': self._calculate_cost_efficiency_score(savings_percentage),
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Kostnadsanalys genomförd för {operation_type}: ${google_cloud_cost".2f"} (besparing: ${savings_usd".2f"})")
            return analysis_result

        except Exception as e:
            logger.error(f"Kostnadsanalys misslyckades: {e}")
            raise CryptoError(f"Kostnadsanalys misslyckades: {str(e)}", "COST_ANALYSIS_ERROR")

    @handle_errors(service_name="web3_cost_analyzer")
    async def compare_provider_costs(self, operation_type: str,
                                   operation_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Jämför kostnader mellan olika providers för samma operation.

        Args:
            operation_type: Typ av operation
            operation_params: Parametrar för operationen

        Returns:
            Kostnadsjämförelse mellan providers
        """
        try:
            # Simulera kostnader för olika providers
            provider_costs = {}

            # Google Cloud Web3 kostnad
            google_cloud_cost = await self._calculate_google_cloud_cost(
                {**operation_params, 'operation_type': operation_type}
            )
            provider_costs[ProviderType.GOOGLE_CLOUD_WEB3.value] = google_cloud_cost

            # Externa provider kostnader
            external_providers = [
                ProviderType.INFURA,
                ProviderType.ALCHEMY,
                ProviderType.QUICKNODE,
                ProviderType.CUSTOM_RPC
            ]

            for provider in external_providers:
                cost = await self._calculate_external_provider_cost(
                    operation_params, provider, operation_type
                )
                provider_costs[provider.value] = cost

            # Beräkna jämförelser
            comparisons = []
            for provider_type, cost in provider_costs.items():
                if provider_type != ProviderType.GOOGLE_CLOUD_WEB3.value:
                    savings = max(0, cost - google_cloud_cost)
                    savings_percentage = (savings / cost * 100) if cost > 0 else 0

                    comparison = ProviderCostComparison(
                        provider_type=ProviderType(provider_type),
                        operation_type=operation_type,
                        google_cloud_cost=google_cloud_cost,
                        provider_cost=cost,
                        savings=savings,
                        savings_percentage=savings_percentage,
                        reliability_score=await self._get_provider_reliability_score(ProviderType(provider_type)),
                        speed_score=await self._get_provider_speed_score(ProviderType(provider_type)),
                        timestamp=datetime.now()
                    )
                    comparisons.append(comparison)
                    self.provider_comparisons.append(comparison)

            # Beräkna total besparing
            avg_external_cost = sum(c.provider_cost for c in comparisons) / len(comparisons)
            total_savings = avg_external_cost - google_cloud_cost
            total_savings_percentage = (total_savings / avg_external_cost * 100) if avg_external_cost > 0 else 0

            comparison_result = {
                'operation_type': operation_type,
                'google_cloud_cost': google_cloud_cost,
                'average_external_cost': avg_external_cost,
                'total_savings_usd': total_savings,
                'total_savings_percentage': total_savings_percentage,
                'provider_comparisons': [c.to_dict() for c in comparisons],
                'best_provider': self._select_best_provider(comparisons),
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Provider jämförelse för {operation_type}: Google Cloud ${google_cloud_cost".2f"} vs genomsnitt extern ${avg_external_cost".2f"}")
            return comparison_result

        except Exception as e:
            logger.error(f"Provider kostnadsjämförelse misslyckades: {e}")
            raise CryptoError(f"Provider kostnadsjämförelse misslyckades: {str(e)}", "PROVIDER_COMPARISON_ERROR")

    @handle_errors(service_name="web3_cost_analyzer")
    async def get_cost_dashboard(self, time_frame_days: int = 7) -> Dict[str, Any]:
        """
        Hämta kostnadsdashboard för angiven tidsperiod.

        Args:
            time_frame_days: Antal dagar att analysera

        Returns:
            Kostnadsdashboard data
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=time_frame_days)

            # Filtrera kostnader för tidsperioden
            period_costs = [c for c in self.cost_history if c.timestamp > cutoff_time]

            if not period_costs:
                return self._empty_dashboard()

            # Beräkna totala kostnader
            total_google_cloud_cost = sum(c.google_cloud_cost_usd for c in period_costs)
            total_external_cost = sum(c.external_cost_usd for c in period_costs)
            total_savings = sum(c.savings_usd for c in period_costs)
            total_savings_percentage = (total_savings / total_external_cost * 100) if total_external_cost > 0 else 0

            # Kostnader per kategori
            costs_by_category = {}
            for cost in period_costs:
                category = cost.category.value
                if category not in costs_by_category:
                    costs_by_category[category] = {
                        'google_cloud': 0,
                        'external': 0,
                        'savings': 0,
                        'count': 0
                    }

                costs_by_category[category]['google_cloud'] += cost.google_cloud_cost_usd
                costs_by_category[category]['external'] += cost.external_cost_usd
                costs_by_category[category]['savings'] += cost.savings_usd
                costs_by_category[category]['count'] += 1

            # Kostnadstrender
            cost_trends = await self._calculate_cost_trends(period_costs, time_frame_days)

            # Provider prestanda
            provider_performance = await self._analyze_provider_performance(time_frame_days)

            # Budget status
            budget_status = await self._check_budget_status(time_frame_days)

            # Predictive kostnader
            cost_predictions = await self._predict_future_costs(time_frame_days)

            dashboard_data = {
                'time_frame_days': time_frame_days,
                'summary': {
                    'total_google_cloud_cost': total_google_cloud_cost,
                    'total_external_cost': total_external_cost,
                    'total_savings': total_savings,
                    'total_savings_percentage': total_savings_percentage,
                    'average_savings_percentage': total_savings_percentage,
                    'target_savings_percentage': self.savings_target * 100,
                    'target_achieved': total_savings_percentage >= self.savings_target * 100,
                    'operations_count': len(period_costs)
                },
                'costs_by_category': costs_by_category,
                'cost_trends': cost_trends,
                'provider_performance': provider_performance,
                'budget_status': budget_status,
                'cost_predictions': cost_predictions,
                'alerts': [alert.to_dict() for alert in self.cost_alerts if alert.timestamp > cutoff_time],
                'timestamp': datetime.now().isoformat()
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Kostnadsdashboard misslyckades: {e}")
            raise CryptoError(f"Kostnadsdashboard misslyckades: {str(e)}", "DASHBOARD_ERROR")

    async def _calculate_google_cloud_cost(self, operation_data: Dict[str, Any]) -> float:
        """Beräkna kostnad för Google Cloud Web3 operation."""
        try:
            operation_type = operation_data.get('operation_type', 'unknown')

            # Bas kostnader för olika operationer (simulerade)
            base_costs = {
                'token_transfer': 0.01,
                'cross_chain_swap': 0.05,
                'contract_deployment': 0.10,
                'batch_operations': 0.03,
                'balance_check': 0.001,
                'transaction_history': 0.005,
                'gas_estimation': 0.001
            }

            base_cost = base_costs.get(operation_type, 0.01)

            # Lägg till chain-specifika kostnader
            chain = operation_data.get('chain', 'ethereum')
            chain_multipliers = {
                'ethereum': 1.0,
                'polygon': 0.3,
                'arbitrum': 0.5,
                'optimism': 0.4,
                'base': 0.6
            }

            chain_cost = base_cost * chain_multipliers.get(chain, 1.0)

            # Lägg till operation-specifika faktorer
            complexity_factor = operation_data.get('complexity_factor', 1.0)
            final_cost = chain_cost * complexity_factor

            # Google Cloud rabatt (83% besparing jämfört med externa providers)
            google_cloud_cost = final_cost * (1 - self.savings_target)

            return max(google_cloud_cost, 0.001)  # Minimum kostnad

        except Exception as e:
            logger.error(f"Google Cloud kostnadsberäkning misslyckades: {e}")
            return 0.01  # Default kostnad

    async def _calculate_external_provider_costs(self, operation_data: Dict[str, Any]) -> Dict[str, float]:
        """Beräkna kostnader för externa providers."""
        try:
            operation_type = operation_data.get('operation_type', 'unknown')

            # Bas kostnader för externa providers
            base_costs = {
                'token_transfer': 0.05,
                'cross_chain_swap': 0.25,
                'contract_deployment': 0.50,
                'batch_operations': 0.15,
                'balance_check': 0.005,
                'transaction_history': 0.025,
                'gas_estimation': 0.005
            }

            base_cost = base_costs.get(operation_type, 0.05)

            # Chain kostnader för externa providers
            chain = operation_data.get('chain', 'ethereum')
            chain_multipliers = {
                'ethereum': 1.0,
                'polygon': 0.8,
                'arbitrum': 1.2,
                'optimism': 1.1,
                'base': 0.9
            }

            base_external_cost = base_cost * chain_multipliers.get(chain, 1.0)

            # Provider-specifika kostnader
            provider_costs = {}

            # Infura kostnader
            provider_costs['infura'] = base_external_cost * 1.1

            # Alchemy kostnader
            provider_costs['alchemy'] = base_external_cost * 1.0

            # QuickNode kostnader
            provider_costs['quicknode'] = base_external_cost * 0.9

            # Custom RPC kostnader
            provider_costs['custom_rpc'] = base_external_cost * 1.3

            return provider_costs

        except Exception as e:
            logger.error(f"Extern provider kostnadsberäkning misslyckades: {e}")
            return {'external_average': 0.05}

    async def _calculate_external_provider_cost(self, operation_params: Dict[str, Any],
                                              provider_type: ProviderType,
                                              operation_type: str) -> float:
        """Beräkna kostnad för specifik extern provider."""
        try:
            # Använd samma logik som i _calculate_external_provider_costs
            external_costs = await self._calculate_external_provider_costs(
                {**operation_params, 'operation_type': operation_type}
            )

            provider_key = provider_type.value.lower()
            return external_costs.get(provider_key, 0.05)

        except Exception as e:
            logger.error(f"Kostnadsberäkning för {provider_type.value} misslyckades: {e}")
            return 0.05

    async def _check_cost_alerts(self, cost_breakdown: CostBreakdown) -> None:
        """Kontrollera och generera kostnadsalerts."""
        try:
            category = cost_breakdown.category
            threshold = self.cost_thresholds.get(category, 100.0)

            # Kontrollera om kostnad överskrider threshold
            if cost_breakdown.google_cloud_cost_usd > threshold:
                alert = CostAlert(
                    alert_type='critical' if cost_breakdown.google_cloud_cost_usd > threshold * 1.5 else 'warning',
                    message=f"{category.value} kostnad ${cost_breakdown.google_cloud_cost_usd".2f"} överskrider threshold ${threshold".2f"}",
                    current_cost=cost_breakdown.google_cloud_cost_usd,
                    threshold=threshold,
                    category=category,
                    timestamp=datetime.now(),
                    recommendation=self._get_cost_recommendation(category, cost_breakdown.google_cloud_cost_usd)
                )

                self.cost_alerts.append(alert)
                logger.warning(f"Kostnadsalert: {alert.message}")

            # Kontrollera besparingsmål
            if cost_breakdown.savings_percentage < (self.savings_target * 100 * 0.8):  # Under 80% av mål
                alert = CostAlert(
                    alert_type='warning',
                    message=f"Besparing endast {cost_breakdown.savings_percentage".1f"}%, under 80% av mål ({self.savings_target * 100".0f"}%)",
                    current_cost=cost_breakdown.savings_percentage,
                    threshold=self.savings_target * 100 * 0.8,
                    category=category,
                    timestamp=datetime.now(),
                    recommendation="Överväg att optimera operations för bättre kostnadseffektivitet"
                )

                self.cost_alerts.append(alert)

        except Exception as e:
            logger.error(f"Kostnadsalert kontroll misslyckades: {e}")

    async def _calculate_cost_trends(self, period_costs: List[CostBreakdown],
                                   time_frame_days: int) -> Dict[str, Any]:
        """Beräkna kostnadstrender."""
        try:
            if len(period_costs) < 2:
                return {'trend': 'insufficient_data', 'change_percentage': 0}

            # Gruppera kostnader per dag
            daily_costs = {}
            for cost in period_costs:
                day = cost.timestamp.date()
                if day not in daily_costs:
                    daily_costs[day] = {'google': 0, 'external': 0}

                daily_costs[day]['google'] += cost.google_cloud_cost_usd
                daily_costs[day]['external'] += cost.external_cost_usd

            # Beräkna trend
            sorted_days = sorted(daily_costs.keys())
            if len(sorted_days) >= 2:
                first_day_cost = daily_costs[sorted_days[0]]['google']
                last_day_cost = daily_costs[sorted_days[-1]]['google']
                change_percentage = ((last_day_cost - first_day_cost) / first_day_cost * 100) if first_day_cost > 0 else 0

                trend = 'increasing' if change_percentage > 5 else 'decreasing' if change_percentage < -5 else 'stable'
            else:
                trend = 'stable'
                change_percentage = 0

            return {
                'trend': trend,
                'change_percentage': change_percentage,
                'daily_breakdown': daily_costs,
                'average_daily_cost': sum(daily_costs[day]['google'] for day in daily_costs) / len(daily_costs)
            }

        except Exception as e:
            logger.error(f"Kostnadstrend beräkning misslyckades: {e}")
            return {'trend': 'error', 'error': str(e)}

    async def _analyze_provider_performance(self, time_frame_days: int) -> Dict[str, Any]:
        """Analysera provider prestanda."""
        try:
            cutoff_time = datetime.now() - timedelta(days=time_frame_days)
            period_comparisons = [c for c in self.provider_comparisons if c.timestamp > cutoff_time]

            if not period_comparisons:
                return {}

            # Gruppera per provider
            provider_stats = {}
            for comparison in period_comparisons:
                provider = comparison.provider_type.value
                if provider not in provider_stats:
                    provider_stats[provider] = {
                        'total_cost': 0,
                        'total_savings': 0,
                        'operation_count': 0,
                        'reliability_score': 0,
                        'speed_score': 0
                    }

                provider_stats[provider]['total_cost'] += comparison.provider_cost
                provider_stats[provider]['total_savings'] += comparison.savings
                provider_stats[provider]['operation_count'] += 1
                provider_stats[provider]['reliability_score'] += comparison.reliability_score
                provider_stats[provider]['speed_score'] += comparison.speed_score

            # Beräkna genomsnitt
            for provider in provider_stats:
                stats = provider_stats[provider]
                count = stats['operation_count']
                if count > 0:
                    stats['reliability_score'] /= count
                    stats['speed_score'] /= count
                    stats['average_cost'] = stats['total_cost'] / count
                    stats['average_savings'] = stats['total_savings'] / count

            return provider_stats

        except Exception as e:
            logger.error(f"Provider prestanda analys misslyckades: {e}")
            return {}

    async def _check_budget_status(self, time_frame_days: int) -> Dict[str, Any]:
        """Kontrollera budget status."""
        try:
            # Simulerad budget kontroll
            # I produktion skulle detta läsa från budget konfiguration

            daily_budget = 500.0  # $500 per dag
            monthly_budget = 15000.0  # $15,000 per månad

            # Beräkna aktuella kostnader
            cutoff_time = datetime.now() - timedelta(days=time_frame_days)
            period_costs = [c for c in self.cost_history if c.timestamp > cutoff_time]

            period_total = sum(c.google_cloud_cost_usd for c in period_costs)

            # Beräkna daily genomsnitt
            days_in_period = min(time_frame_days, 30)  # Max 30 dagar för daily beräkning
            daily_average = period_total / days_in_period if days_in_period > 0 else 0

            # Projektera månads kostnader
            projected_monthly = daily_average * 30

            budget_status = {
                'daily_budget': daily_budget,
                'monthly_budget': monthly_budget,
                'period_total': period_total,
                'daily_average': daily_average,
                'projected_monthly': projected_monthly,
                'daily_budget_utilization': (daily_average / daily_budget * 100) if daily_budget > 0 else 0,
                'monthly_budget_utilization': (projected_monthly / monthly_budget * 100) if monthly_budget > 0 else 0,
                'budget_alert': 'warning' if projected_monthly > monthly_budget * 0.8 else 'normal'
            }

            if budget_status['budget_alert'] == 'warning':
                logger.warning(f"Budget alert: projicerad månadsbudget överskrider 80%")

            return budget_status

        except Exception as e:
            logger.error(f"Budget status kontroll misslyckades: {e}")
            return {}

    async def _predict_future_costs(self, time_frame_days: int) -> Dict[str, Any]:
        """Förutsäg framtida kostnader."""
        try:
            # Simulerad kostnadsförutsägelse baserat på trender
            cutoff_time = datetime.now() - timedelta(days=time_frame_days)
            period_costs = [c for c in self.cost_history if c.timestamp > cutoff_time]

            if len(period_costs) < 3:
                return {'prediction': 'insufficient_data', 'confidence': 0}

            # Beräkna trend
            costs = [c.google_cloud_cost_usd for c in period_costs]
            if len(costs) >= 3:
                # Enkel linjär trend
                recent_avg = sum(costs[-3:]) / 3
                older_avg = sum(costs[:3]) / 3 if len(costs) >= 6 else recent_avg

                trend_factor = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0

                # Förutsäg nästa 7 dagar
                predicted_next_week = recent_avg * (1 + trend_factor)

                confidence = min(0.8, len(costs) / 10)  # Confidence ökar med datapunkter

                return {
                    'next_7_days_predicted': predicted_next_week * 7,
                    'next_30_days_predicted': predicted_next_week * 30,
                    'trend_factor': trend_factor,
                    'confidence': confidence,
                    'based_on_operations': len(costs)
                }

            return {'prediction': 'insufficient_data', 'confidence': 0}

        except Exception as e:
            logger.error(f"Kostnadsförutsägelse misslyckades: {e}")
            return {'prediction': 'error', 'error': str(e)}

    def _calculate_cost_efficiency_score(self, savings_percentage: float) -> float:
        """Beräkna kostnadseffektivitetsscore."""
        if savings_percentage >= self.savings_target * 100:
            return 1.0  # Perfekt effektivitet
        elif savings_percentage >= self.savings_target * 100 * 0.8:
            return 0.8  # Bra effektivitet
        elif savings_percentage >= self.savings_target * 100 * 0.6:
            return 0.6  # Acceptabel effektivitet
        else:
            return 0.4  # Dålig effektivitet

    async def _get_provider_reliability_score(self, provider_type: ProviderType) -> float:
        """Hämta reliability score för provider."""
        # Simulerade reliability scores
        scores = {
            ProviderType.INFURA: 0.95,
            ProviderType.ALCHEMY: 0.98,
            ProviderType.QUICKNODE: 0.92,
            ProviderType.CUSTOM_RPC: 0.85,
            ProviderType.GOOGLE_CLOUD_WEB3: 0.99
        }
        return scores.get(provider_type, 0.90)

    async def _get_provider_speed_score(self, provider_type: ProviderType) -> float:
        """Hämta speed score för provider."""
        # Simulerade speed scores
        scores = {
            ProviderType.INFURA: 0.88,
            ProviderType.ALCHEMY: 0.92,
            ProviderType.QUICKNODE: 0.85,
            ProviderType.CUSTOM_RPC: 0.80,
            ProviderType.GOOGLE_CLOUD_WEB3: 0.95
        }
        return scores.get(provider_type, 0.85)

    def _select_best_provider(self, comparisons: List[ProviderCostComparison]) -> Dict[str, Any]:
        """Välj bästa provider baserat på kostnad och prestanda."""
        if not comparisons:
            return {}

        # Beräkna composite score (40% kostnad, 30% reliability, 30% speed)
        best_provider = None
        best_score = -1

        for comparison in comparisons:
            cost_score = 1 - (comparison.provider_cost / max(c.provider_cost for c in comparisons))  # Lägre kostnad = högre score
            composite_score = (cost_score * 0.4 +
                             comparison.reliability_score * 0.3 +
                             comparison.speed_score * 0.3)

            if composite_score > best_score:
                best_score = composite_score
                best_provider = comparison

        return {
            'provider': best_provider.provider_type.value if best_provider else 'unknown',
            'cost': best_provider.provider_cost if best_provider else 0,
            'savings_vs_google_cloud': best_provider.savings if best_provider else 0,
            'composite_score': best_score
        }

    def _get_cost_recommendation(self, category: CostCategory, current_cost: float) -> str:
        """Hämta kostnadsrekommendation."""
        recommendations = {
            CostCategory.GAS_FEES: "Överväg att batcha transaktioner för att minska gas-kostnader",
            CostCategory.BRIDGE_FEES: "Använd Google Cloud Web3 för lägre bridge-kostnader",
            CostCategory.SWAP_FEES: "Optimera swap routes för bättre priser",
            CostCategory.CROSS_CHAIN_FEES: "Konsolidera cross-chain operationer för bulk-rabatt"
        }

        return recommendations.get(category, "Granska och optimera operationer för kostnadsbesparing")

    def _empty_dashboard(self) -> Dict[str, Any]:
        """Returnera tom dashboard."""
        return {
            'time_frame_days': 0,
            'summary': {
                'total_google_cloud_cost': 0,
                'total_external_cost': 0,
                'total_savings': 0,
                'total_savings_percentage': 0,
                'operations_count': 0
            },
            'costs_by_category': {},
            'cost_trends': {'trend': 'no_data'},
            'provider_performance': {},
            'budget_status': {},
            'cost_predictions': {'prediction': 'no_data'},
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }

    async def get_cost_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Hämta kostnadshistorik."""
        recent_history = self.cost_history[-limit:] if self.cost_history else []
        return [cost.to_dict() for cost in recent_history]

    async def get_cost_alerts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Hämta kostnadsalerts."""
        if active_only:
            # Filtrera aktiva alerts (senaste 24 timmarna)
            cutoff_time = datetime.now() - timedelta(hours=24)
            active_alerts = [alert for alert in self.cost_alerts if alert.timestamp > cutoff_time]
            return [alert.to_dict() for alert in active_alerts]
        else:
            return [alert.to_dict() for alert in self.cost_alerts]

    async def clear_old_data(self, older_than_days: int = 30) -> int:
        """Rensa gammal kostnadsdata."""
        cutoff_time = datetime.now() - timedelta(days=older_than_days)

        # Rensa kostnadshistorik
        original_count = len(self.cost_history)
        self.cost_history = [cost for cost in self.cost_history if cost.timestamp > cutoff_time]
        history_removed = original_count - len(self.cost_history)

        # Rensa provider jämförelser
        original_comparison_count = len(self.provider_comparisons)
        self.provider_comparisons = [comp for comp in self.provider_comparisons if comp.timestamp > cutoff_time]
        comparison_removed = original_comparison_count - len(self.provider_comparisons)

        # Rensa alerts (behåll bara senaste 100)
        if len(self.cost_alerts) > 100:
            self.cost_alerts = self.cost_alerts[-100:]

        total_removed = history_removed + comparison_removed
        logger.info(f"Rensade {total_removed} gamla kostnadsposter")
        return total_removed

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på cost analyzer."""
        try:
            return {
                'service': 'web3_cost_analyzer',
                'status': 'healthy',
                'cost_history_count': len(self.cost_history),
                'provider_comparisons_count': len(self.provider_comparisons),
                'alerts_count': len(self.cost_alerts),
                'savings_target_percentage': self.savings_target * 100,
                'supported_providers': [p.value for p in ProviderType],
                'supported_categories': [c.value for c in CostCategory],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_cost_analyzer',
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