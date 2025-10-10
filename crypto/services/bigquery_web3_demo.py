#!/usr/bin/env python3
"""
BigQuery Google Cloud Web3 Integration Demo
Demonstrerar användning av hela integration systemet för blockchain analytics
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import integration services
from .web3_bigquery_integration import get_web3_bigquery_integration
from .portfolio_analytics import PortfolioAnalyticsService
from .bigquery_service import get_bigquery_service

class BigQueryWeb3Demo:
    """Demo klass för BigQuery Web3 integration."""

    def __init__(self, project_id: str, credentials_path: str = None):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.integration = None

    async def initialize(self):
        """Initiera demo med alla services."""
        try:
            logger.info("🚀 Initierar BigQuery Web3 Integration Demo...")

            # Initiera integration service
            self.integration = get_web3_bigquery_integration(
                self.project_id,
                credentials_path=self.credentials_path
            )

            await self.integration.initialize()

            logger.info("✅ Demo initierad framgångsrikt!")
            return True

        except Exception as e:
            logger.error(f"❌ Demo initialization misslyckades: {e}")
            return False

    async def run_comprehensive_demo(self, wallet_address: str = "0x123456789abcdef123456789abcdef1234567890"):
        """Kör comprehensive demo för wallet analysis."""
        try:
            logger.info(f"🔍 Kör comprehensive wallet analysis för {wallet_address[:10]}...")

            if not self.integration:
                logger.error("❌ Integration inte initierad")
                return

            # 1. Comprehensive Wallet Analysis
            logger.info("📊 1. Hämta comprehensive wallet analysis...")
            analysis = await self.integration.get_comprehensive_wallet_analysis(
                wallet_address=wallet_address,
                include_live_data=True,
                include_risk_analysis=True
            )

            self._print_wallet_overview(analysis)

            # 2. Portfolio Performance
            logger.info("📈 2. Analysera portfolio performance...")
            portfolio_service = PortfolioAnalyticsService(self.project_id)
            await portfolio_service.initialize()

            performance = await portfolio_service.get_performance_analytics(wallet_address, days=30)
            self._print_performance_analysis(performance)

            # 3. Risk Dashboard
            logger.info("⚠️  3. Visa risk dashboard...")
            risk_dashboard = await portfolio_service.get_risk_dashboard(wallet_address)
            self._print_risk_dashboard(risk_dashboard)

            # 4. Rebalancing Analysis
            logger.info("🔄 4. Generera rebalancing recommendations...")
            optimization = await self.integration.get_portfolio_optimization_recommendations(wallet_address)
            self._print_optimization_recommendations(optimization)

            # 5. Real-tids Monitoring
            logger.info("📡 5. Visa real-tids monitoring...")
            monitoring = await self.integration.get_real_time_portfolio_monitoring(wallet_address)
            self._print_monitoring_status(monitoring)

            # 6. Health Check
            logger.info("💚 6. Kontrollera system health...")
            health_check = await self.integration.health_check()
            self._print_health_check(health_check)

            # Summary
            self._print_demo_summary(analysis, performance, risk_dashboard, optimization)

        except Exception as e:
            logger.error(f"❌ Demo misslyckades: {e}")
            raise

    def _print_wallet_overview(self, analysis: Dict[str, Any]):
        """Print wallet overview."""
        print("\n" + "="*60)
        print("📊 WALLET OVERVIEW")
        print("="*60)

        if 'portfolio_data' in analysis:
            portfolio = analysis['portfolio_data']
            print(f"💰 Portfolio Value: ${portfolio.get('total_value_usd', 0):,.2f}")

            balances = portfolio.get('balances', [])
            print(f"🔗 Chains: {len(set(b.get('chain', '') for b in balances))}")
            print(f"🪙 Tokens: {len(balances)}")

        if 'risk_analysis' in analysis:
            risk = analysis['risk_analysis']
            print(f"⚠️  Risk Score: {risk.get('overall_risk_score', 0):.2".2f")
            print(f"📊 Risk Level: {risk.get('risk_level', 'UNKNOWN')}")

        print("="*60)

    def _print_performance_analysis(self, performance: Dict[str, Any]):
        """Print performance analysis."""
        print("\n" + "="*60)
        print("📈 PERFORMANCE ANALYSIS (30 days)")
        print("="*60)

        if performance.get('success') and 'performance_data' in performance:
            data = performance['performance_data']

            print(f"📈 Total Return: {data.get('total_return_percent', 0):.2".2f")
            print(f"📊 Avg Daily Return: {data.get('avg_daily_return_percent', 0):.2".2f")
            print(f"⚡ Sharpe Ratio: {data.get('annual_sharpe_ratio', 0):.2".2f")
            print(f"📉 Max Drawdown: {data.get('max_drawdown', 0):.2".2f")
            print(f"📊 Volatility: {data.get('volatility', 0):.2".2f")

        if 'advanced_metrics' in performance:
            metrics = performance['advanced_metrics']
            risk_metrics = metrics.get('risk_metrics', {})

            print("
🎯 ADVANCED METRICS:"            print(f"   📈 Sharpe Ratio: {risk_metrics.get('sharpe_ratio', 0):.2".2f")
            print(f"   📉 Sortino Ratio: {risk_metrics.get('sortino_ratio', 0):.2".2f")
            print(f"   📊 Calmar Ratio: {risk_metrics.get('calmar_ratio', 0):.2".2f")
            print(f"   🎲 VaR 95%: {risk_metrics.get('value_at_risk', 0):.2".2f")

        print("="*60)

    def _print_risk_dashboard(self, risk_dashboard: Dict[str, Any]):
        """Print risk dashboard."""
        print("\n" + "="*60)
        print("⚠️  RISK DASHBOARD")
        print("="*60)

        if risk_dashboard.get('success'):
            risk_data = risk_dashboard.get('risk_data', {})
            alerts = risk_dashboard.get('risk_alerts', [])

            print(f"🎯 Overall Risk Score: {risk_dashboard.get('overall_risk_score', 0):.2".2f")
            print(f"📊 Risk Level: {risk_dashboard.get('risk_level', 'UNKNOWN')}")

            if 'live_risk_metrics' in risk_dashboard:
                live = risk_dashboard['live_risk_metrics']
                print(f"📈 Real-time Volatility: {live.get('real_time_volatility', 0):.2".2f")
                print(f"🎲 VaR 95%: {live.get('var_95', 0):.2".2f")

            print(f"\n🚨 Active Alerts: {len(alerts)}")
            for alert in alerts[:3]:  # Visa bara första 3 alerts
                print(f"   • {alert.get('severity', 'unknown').upper()}: {alert.get('message', '')}")

        print("="*60)

    def _print_optimization_recommendations(self, optimization: Dict[str, Any]):
        """Print optimization recommendations."""
        print("\n" + "="*60)
        print("🔄 PORTFOLIO OPTIMIZATION")
        print("="*60)

        if optimization.get('success'):
            actions = optimization.get('optimization_actions', [])
            expected_impact = optimization.get('expected_impact', {})

            print(f"🎯 Total Actions: {len(actions)}")
            print(f"💰 Expected Impact: ${expected_impact.get('total_portfolio_impact_usd', 0):,.2f}")

            summary = optimization.get('recommendations_summary', {})
            print(f"📋 Summary: {summary.get('summary', '')}")
            print(f"⚡ Urgency: {summary.get('urgency', 'unknown')}")

            print("
🔄 RECOMMENDED ACTIONS:"            for action in actions[:5]:  # Visa bara första 5 actions
                symbol = action.get('token_symbol', 'UNKNOWN')
                action_type = action.get('action', 'hold').upper()
                amount = action.get('amount_usd', 0)
                reason = action.get('reason', '')

                print(f"   • {action_type} ${amount:.2",.2f"of {symbol}")
                print(f"     Reason: {reason}")

        print("="*60)

    def _print_monitoring_status(self, monitoring: Dict[str, Any]):
        """Print monitoring status."""
        print("\n" + "="*60)
        print("📡 REAL-TIME MONITORING")
        print("="*60)

        metrics = monitoring.get('real_time_metrics', {})
        alerts = monitoring.get('alerts', [])

        print(f"💰 Current Portfolio Value: ${metrics.get('portfolio_value', 0):,.2f}")
        print(f"📊 Risk Status: {metrics.get('risk_status', 0):.2".2f")
        print(f"🚨 Active Alerts: {metrics.get('active_alerts_count', 0)}")
        print(f"🔄 Data Freshness: {metrics.get('data_freshness', 'unknown')}")

        if alerts:
            print("
🚨 RECENT ALERTS:"            for alert in alerts[:3]:
                print(f"   • {alert.get('severity', 'info').upper()}: {alert.get('message', '')}")

        print("="*60)

    def _print_health_check(self, health_check: Dict[str, Any]):
        """Print health check."""
        print("\n" + "="*60)
        print("💚 SYSTEM HEALTH CHECK")
        print("="*60)

        status = health_check.get('overall_status', 'unknown')
        status_icon = "✅" if status == 'healthy' else "⚠️" if status == 'degraded' else "❌"

        print(f"{status_icon} Overall Status: {status.upper()}")

        services = health_check.get('service_statuses', {})
        for service_name, service_info in services.items():
            service_status = service_info.get('status', 'unknown')
            print(f"   • {service_name}: {service_status}")

        print(f"🔗 Supported Chains: {', '.join(health_check.get('supported_chains', []))}")
        print(f"💾 Cache Size: {health_check.get('cache_size', 0)} items")

        print("="*60)

    def _print_demo_summary(self, analysis: Dict[str, Any], performance: Dict[str, Any],
                          risk_dashboard: Dict[str, Any], optimization: Dict[str, Any]):
        """Print demo summary."""
        print("\n" + "="*80)
        print("🎉 BIGQUERY WEB3 INTEGRATION DEMO - SUMMARY")
        print("="*80)

        # Portfolio Summary
        if 'portfolio_data' in analysis:
            portfolio = analysis['portfolio_data']
            print(f"💰 Portfolio Value: ${portfolio.get('total_value_usd', 0):,.2f}")

        # Risk Summary
        if 'risk_analysis' in analysis:
            risk = analysis['risk_analysis']
            print(f"⚠️  Overall Risk: {risk.get('overall_risk_score', 0):.2".2f"/1.00 ({risk.get('risk_level', 'UNKNOWN')})")

        # Performance Summary
        if performance.get('success') and 'performance_data' in performance:
            perf = performance['performance_data']
            print(f"📈 Performance: {perf.get('total_return_percent', 0):+.2".2f")

        # Optimization Summary
        if optimization.get('success'):
            actions = optimization.get('optimization_actions', [])
            impact = optimization.get('expected_impact', {})
            print(f"🔄 Optimization: {len(actions)} actions, ${impact.get('total_portfolio_impact_usd', 0):,.2f".2f"pact")

        print("
✅ INTEGRATION FEATURES DEMONSTRATED:"        print("   • 📊 Comprehensive wallet analysis"        print("   • 📈 Portfolio performance tracking"        print("   • ⚠️  Risk analysis och monitoring"        print("   • 🔄 Rebalancing recommendations"        print("   • 📡 Real-tids data integration"        print("   • 💚 System health monitoring"        print("   • 🔗 Multi-chain support"        print("   • 📋 BigQuery materialized views"

        print("
🎯 KEY BENEFITS:"        print("   • ⚡ Real-tids blockchain data från Google Cloud Web3"        print("   • 📊 Historical analytics från BigQuery"        print("   • 🤖 Automated risk management"        print("   • 📈 Performance benchmarking"        print("   • 🔄 Portfolio optimization"        print("   • 🚨 Real-tids alerting"
        print("="*80)

async def main():
    """Main demo function."""
    print("🚀 BigQuery Google Cloud Web3 Integration Demo")
    print("="*60)

    # Demo configuration
    PROJECT_ID = "felicia-finance-blockchain"
    CREDENTIALS_PATH = "credentials.json"  # Optional
    DEMO_WALLET = "0x123456789abcdef123456789abcdef1234567890"

    # Initiera och kör demo
    demo = BigQueryWeb3Demo(PROJECT_ID, CREDENTIALS_PATH)

    if await demo.initialize():
        print("✅ Demo ready to run!")
        print(f"📝 Using wallet: {DEMO_WALLET[:10]}...")
        print()

        try:
            # Kör comprehensive demo
            await demo.run_comprehensive_demo(DEMO_WALLET)

            print("\n🎉 Demo completed successfully!")
            print("📖 Check the logs above for detailed results.")
            print("📋 Review README_BigQuery_Web3_Integration.md for complete documentation.")

        except KeyboardInterrupt:
            print("\n⏹️  Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            logger.exception("Demo error details:")
    else:
        print("❌ Failed to initialize demo")
        print("💡 Make sure:")
        print("   • Google Cloud project is created")
        print("   • BigQuery API is enabled")
        print("   • Credentials are properly configured")
        print("   • Web3 Gateway API is enabled (if using live data)")

if __name__ == "__main__":
    # Kör demo
    asyncio.run(main())