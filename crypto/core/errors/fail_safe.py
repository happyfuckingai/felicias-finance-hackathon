"""
Fail-Safe System för HappyOS Crypto - Risk management och säkerhetsgränser.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import json

logger = logging.getLogger(__name__)

@dataclass
class RiskLimits:
    """Risk management gränser."""
    max_drawdown_daily: float = 0.05  # 5% max drawdown per dag
    max_drawdown_weekly: float = 0.15  # 15% max drawdown per vecka
    max_spend_per_wallet: float = 1000.0  # Max $1000 per wallet
    max_spend_daily: float = 100.0  # Max $100 per dag
    max_position_size: float = 0.25  # Max 25% av portfolio per position
    max_gas_per_transaction: float = 50.0  # Max $50 gas per transaktion
    max_slippage: float = 0.05  # Max 5% slippage
    min_liquidity_threshold: float = 10000.0  # Min $10k likviditet för trading
    emergency_stop_loss: float = 0.20  # 20% total portfolio loss = emergency stop

@dataclass
class FailSafeEvent:
    """Fail-safe event för logging."""
    timestamp: datetime
    event_type: str
    severity: str  # 'warning', 'critical', 'emergency'
    message: str
    wallet_address: str
    action_taken: str
    data: Dict[str, Any]

class FailSafeMonitor:
    """Övervakar och genomdriver fail-safe regler."""
    
    def __init__(self, risk_limits: RiskLimits = None):
        self.risk_limits = risk_limits or RiskLimits()
        self.events: List[FailSafeEvent] = []
        self.wallet_states: Dict[str, Dict[str, Any]] = {}
        self.emergency_mode = False
        
    async def check_transaction_safety(
        self,
        wallet_address: str,
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Kontrollera om en transaktion är säker att utföra.
        
        Args:
            wallet_address: Wallet address
            transaction_data: Transaction data
            
        Returns:
            Safety check result
        """
        try:
            # Hämta wallet state
            wallet_state = await self._get_wallet_state(wallet_address)
            
            # Kontrollera alla säkerhetsgränser
            checks = []
            
            # 1. Daily spending limit
            daily_spend_check = await self._check_daily_spending(
                wallet_address, transaction_data.get('amount_usd', 0)
            )
            checks.append(daily_spend_check)
            
            # 2. Gas limit check
            gas_check = await self._check_gas_limit(transaction_data)
            checks.append(gas_check)
            
            # 3. Slippage check
            slippage_check = await self._check_slippage(transaction_data)
            checks.append(slippage_check)
            
            # 4. Liquidity check
            liquidity_check = await self._check_liquidity(transaction_data)
            checks.append(liquidity_check)
            
            # 5. Position size check
            position_check = await self._check_position_size(
                wallet_address, transaction_data
            )
            checks.append(position_check)
            
            # 6. Emergency mode check
            emergency_check = await self._check_emergency_mode()
            checks.append(emergency_check)
            
            # Sammanställ resultat
            all_passed = all(check['passed'] for check in checks)
            failed_checks = [check for check in checks if not check['passed']]
            
            if not all_passed:
                # Logga fail-safe event
                await self._log_fail_safe_event(
                    wallet_address,
                    'transaction_blocked',
                    'warning' if len(failed_checks) == 1 else 'critical',
                    f"Transaction blocked: {', '.join([c['reason'] for c in failed_checks])}",
                    'block_transaction',
                    {'failed_checks': failed_checks, 'transaction': transaction_data}
                )
            
            return {
                'safe': all_passed,
                'checks': checks,
                'failed_checks': failed_checks,
                'action': 'allow' if all_passed else 'block'
            }
            
        except Exception as e:
            logger.error(f"Safety check error: {e}")
            return {
                'safe': False,
                'error': str(e),
                'action': 'block'
            }
    
    async def check_portfolio_health(self, wallet_address: str) -> Dict[str, Any]:
        """
        Kontrollera portfolio hälsa och drawdown.
        
        Args:
            wallet_address: Wallet address
            
        Returns:
            Portfolio health status
        """
        try:
            wallet_state = await self._get_wallet_state(wallet_address)
            
            # Beräkna drawdown
            current_value = wallet_state.get('current_value', 0)
            peak_value = wallet_state.get('peak_value', current_value)
            daily_start_value = wallet_state.get('daily_start_value', current_value)
            weekly_start_value = wallet_state.get('weekly_start_value', current_value)
            
            # Drawdown calculations
            total_drawdown = (peak_value - current_value) / peak_value if peak_value > 0 else 0
            daily_drawdown = (daily_start_value - current_value) / daily_start_value if daily_start_value > 0 else 0
            weekly_drawdown = (weekly_start_value - current_value) / weekly_start_value if weekly_start_value > 0 else 0
            
            # Check limits
            health_status = 'healthy'
            alerts = []
            
            if daily_drawdown > self.risk_limits.max_drawdown_daily:
                health_status = 'warning'
                alerts.append(f"Daily drawdown {daily_drawdown:.2%} exceeds limit {self.risk_limits.max_drawdown_daily:.2%}")
            
            if weekly_drawdown > self.risk_limits.max_drawdown_weekly:
                health_status = 'critical'
                alerts.append(f"Weekly drawdown {weekly_drawdown:.2%} exceeds limit {self.risk_limits.max_drawdown_weekly:.2%}")
            
            if total_drawdown > self.risk_limits.emergency_stop_loss:
                health_status = 'emergency'
                alerts.append(f"Emergency stop loss triggered: {total_drawdown:.2%}")
                await self._trigger_emergency_mode(wallet_address, total_drawdown)
            
            # Logga om det finns problem
            if health_status != 'healthy':
                await self._log_fail_safe_event(
                    wallet_address,
                    'portfolio_health_alert',
                    health_status,
                    f"Portfolio health: {health_status}. Alerts: {'; '.join(alerts)}",
                    'monitor' if health_status == 'warning' else 'emergency_stop',
                    {
                        'total_drawdown': total_drawdown,
                        'daily_drawdown': daily_drawdown,
                        'weekly_drawdown': weekly_drawdown,
                        'current_value': current_value,
                        'peak_value': peak_value
                    }
                )
            
            return {
                'status': health_status,
                'total_drawdown': total_drawdown,
                'daily_drawdown': daily_drawdown,
                'weekly_drawdown': weekly_drawdown,
                'alerts': alerts,
                'emergency_mode': self.emergency_mode
            }
            
        except Exception as e:
            logger.error(f"Portfolio health check error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _check_daily_spending(self, wallet_address: str, amount_usd: float) -> Dict[str, Any]:
        """Kontrollera daily spending limit."""
        wallet_state = await self._get_wallet_state(wallet_address)
        daily_spent = wallet_state.get('daily_spent', 0)
        
        if daily_spent + amount_usd > self.risk_limits.max_spend_daily:
            return {
                'passed': False,
                'check': 'daily_spending',
                'reason': f"Daily spending limit exceeded: ${daily_spent + amount_usd:.2f} > ${self.risk_limits.max_spend_daily:.2f}"
            }
        
        return {'passed': True, 'check': 'daily_spending'}
    
    async def _check_gas_limit(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kontrollera gas limit."""
        estimated_gas_usd = transaction_data.get('estimated_gas_usd', 0)
        
        if estimated_gas_usd > self.risk_limits.max_gas_per_transaction:
            return {
                'passed': False,
                'check': 'gas_limit',
                'reason': f"Gas cost too high: ${estimated_gas_usd:.2f} > ${self.risk_limits.max_gas_per_transaction:.2f}"
            }
        
        return {'passed': True, 'check': 'gas_limit'}
    
    async def _check_slippage(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kontrollera slippage."""
        slippage = transaction_data.get('slippage', 0)
        
        if slippage > self.risk_limits.max_slippage:
            return {
                'passed': False,
                'check': 'slippage',
                'reason': f"Slippage too high: {slippage:.2%} > {self.risk_limits.max_slippage:.2%}"
            }
        
        return {'passed': True, 'check': 'slippage'}
    
    async def _check_liquidity(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kontrollera liquidity."""
        liquidity_usd = transaction_data.get('liquidity_usd', 0)
        
        if liquidity_usd < self.risk_limits.min_liquidity_threshold:
            return {
                'passed': False,
                'check': 'liquidity',
                'reason': f"Insufficient liquidity: ${liquidity_usd:.2f} < ${self.risk_limits.min_liquidity_threshold:.2f}"
            }
        
        return {'passed': True, 'check': 'liquidity'}
    
    async def _check_position_size(self, wallet_address: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kontrollera position size."""
        wallet_state = await self._get_wallet_state(wallet_address)
        portfolio_value = wallet_state.get('current_value', 0)
        position_value = transaction_data.get('amount_usd', 0)
        
        if portfolio_value > 0:
            position_percentage = position_value / portfolio_value
            
            if position_percentage > self.risk_limits.max_position_size:
                return {
                    'passed': False,
                    'check': 'position_size',
                    'reason': f"Position too large: {position_percentage:.2%} > {self.risk_limits.max_position_size:.2%}"
                }
        
        return {'passed': True, 'check': 'position_size'}
    
    async def _check_emergency_mode(self) -> Dict[str, Any]:
        """Kontrollera emergency mode."""
        if self.emergency_mode:
            return {
                'passed': False,
                'check': 'emergency_mode',
                'reason': "System is in emergency mode - all trading suspended"
            }
        
        return {'passed': True, 'check': 'emergency_mode'}
    
    async def _trigger_emergency_mode(self, wallet_address: str, drawdown: float):
        """Aktivera emergency mode."""
        self.emergency_mode = True
        
        await self._log_fail_safe_event(
            wallet_address,
            'emergency_mode_activated',
            'emergency',
            f"Emergency mode activated due to {drawdown:.2%} drawdown",
            'emergency_stop_all_trading',
            {'drawdown': drawdown, 'timestamp': datetime.now().isoformat()}
        )
        
        # Här skulle man stänga alla öppna positioner
        logger.critical(f"EMERGENCY MODE ACTIVATED for {wallet_address} - {drawdown:.2%} drawdown")
    
    async def _get_wallet_state(self, wallet_address: str) -> Dict[str, Any]:
        """Hämta wallet state (simulerat)."""
        if wallet_address not in self.wallet_states:
            self.wallet_states[wallet_address] = {
                'current_value': 10000.0,  # Simulerat
                'peak_value': 10000.0,
                'daily_start_value': 10000.0,
                'weekly_start_value': 10000.0,
                'daily_spent': 0.0,
                'last_updated': datetime.now()
            }
        
        return self.wallet_states[wallet_address]
    
    async def _log_fail_safe_event(
        self,
        wallet_address: str,
        event_type: str,
        severity: str,
        message: str,
        action_taken: str,
        data: Dict[str, Any]
    ):
        """Logga fail-safe event."""
        event = FailSafeEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            message=message,
            wallet_address=wallet_address,
            action_taken=action_taken,
            data=data
        )
        
        self.events.append(event)
        
        # Logga till fil/database
        logger.warning(f"FAIL-SAFE [{severity.upper()}]: {message}")
        
        # Skicka alerts för kritiska events
        if severity in ['critical', 'emergency']:
            await self._send_alert(event)
    
    async def _send_alert(self, event: FailSafeEvent):
        """Skicka alert för kritiska events."""
        # Här skulle man skicka email, SMS, Discord notification etc.
        logger.critical(f"CRITICAL ALERT: {event.message}")
    
    async def get_fail_safe_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generera fail-safe rapport."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.events if e.timestamp > cutoff_time]
        
        # Gruppera events
        events_by_severity = {}
        events_by_type = {}
        
        for event in recent_events:
            # By severity
            if event.severity not in events_by_severity:
                events_by_severity[event.severity] = []
            events_by_severity[event.severity].append(event)
            
            # By type
            if event.event_type not in events_by_type:
                events_by_type[event.event_type] = []
            events_by_type[event.event_type].append(event)
        
        return {
            'period_hours': hours,
            'total_events': len(recent_events),
            'emergency_mode': self.emergency_mode,
            'events_by_severity': {
                severity: len(events) for severity, events in events_by_severity.items()
            },
            'events_by_type': {
                event_type: len(events) for event_type, events in events_by_type.items()
            },
            'recent_events': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'type': e.event_type,
                    'severity': e.severity,
                    'message': e.message,
                    'wallet': e.wallet_address,
                    'action': e.action_taken
                }
                for e in recent_events[-10:]  # Senaste 10 events
            ]
        }

class CircuitBreaker:
    """Circuit breaker för att stoppa trading vid problem."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    async def call(self, func, *args, **kwargs):
        """Anropa funktion genom circuit breaker."""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half_open'
            else:
                raise Exception("Circuit breaker is OPEN - trading suspended")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Kontrollera om vi ska försöka återställa."""
        if self.last_failure_time is None:
            return True
        
        return (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout
    
    async def _on_success(self):
        """Hantera lyckad operation."""
        self.failure_count = 0
        self.state = 'closed'
    
    async def _on_failure(self):
        """Hantera misslyckad operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.critical(f"Circuit breaker OPENED after {self.failure_count} failures")

# Global fail-safe instance
global_fail_safe = FailSafeMonitor()
global_circuit_breaker = CircuitBreaker()
