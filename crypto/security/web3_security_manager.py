"""
Web3 Security Manager - Central säkerhetshanterare för Web3-operationer.
Koordinerar säkerhet över multipla komponenter och integrerar med Google Cloud KMS.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading

from ..core.errors.error_handling import handle_errors, CryptoError, SecurityError, ValidationError
from .web3_security import Web3Security, SecurityLevel, KeyType, SecureTransaction

logger = logging.getLogger(__name__)

class SecurityOperation(Enum):
    """Typer av säkerhetsoperationer."""
    TRANSACTION = "transaction"
    WALLET_CREATION = "wallet_creation"
    KEY_MANAGEMENT = "key_management"
    ACCESS_CONTROL = "access_control"
    AUDIT_LOGGING = "audit_logging"
    THREAT_DETECTION = "threat_detection"

class RiskLevel(Enum):
    """Risknivåer för säkerhetsoperationer."""
    LOW = "låg"
    MEDIUM = "medium"
    HIGH = "hög"
    CRITICAL = "kritisk"

@dataclass
class SecurityContext:
    """Säkerhetskontext för operationer."""
    user_id: str
    operation: SecurityOperation
    resource: str
    risk_level: RiskLevel
    ip_address: str = ""
    user_agent: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SecurityPolicy:
    """Säkerhetspolicy för olika operationstyper."""
    operation: SecurityOperation
    min_security_level: SecurityLevel
    requires_approval: bool = False
    max_amount: Optional[float] = None
    allowed_addresses: Optional[Set[str]] = None
    rate_limit_per_hour: Optional[int] = None

class Web3SecurityManager:
    """
    Central säkerhetshanterare för Web3-operationer.

    Koordinerar:
    - Security policies och enforcement
    - Multi-level authentication och authorization
    - Threat detection och response
    - Audit logging och monitoring
    - Integration med Google Cloud KMS
    - Risk assessment och mitigation
    """

    def __init__(self, project_id: str, key_ring_id: str, location_id: str = "global"):
        """
        Initiera Web3 Security Manager.

        Args:
            project_id: Google Cloud project ID
            key_ring_id: KMS key ring ID
            location_id: KMS location
        """
        self.project_id = project_id
        self.key_ring_id = key_ring_id
        self.location_id = location_id

        # Initiera underliggande security service
        self.security_service = Web3Security(project_id, key_ring_id, location_id)

        # Security policies
        self.policies = {}
        self._initialize_default_policies()

        # Active security contexts
        self.active_contexts = {}

        # Security metrics
        self.security_metrics = {
            'total_operations': 0,
            'blocked_operations': 0,
            'high_risk_operations': 0,
            'security_incidents': 0,
            'average_response_time': 0.0
        }

        # Risk assessment cache
        self.risk_cache = {}
        self.risk_cache_ttl = 300  # 5 minuter

        # Security event handlers
        self.event_handlers = []

        logger.info(f"Web3 Security Manager initierad för project: {project_id}")

    def _initialize_default_policies(self):
        """Initiera default säkerhetspolicies."""
        policies = [
            SecurityPolicy(
                operation=SecurityOperation.TRANSACTION,
                min_security_level=SecurityLevel.MEDIUM,
                requires_approval=True,
                max_amount=10000.0,
                rate_limit_per_hour=100
            ),
            SecurityPolicy(
                operation=SecurityOperation.WALLET_CREATION,
                min_security_level=SecurityLevel.HIGH,
                requires_approval=True,
                allowed_addresses=set()  # Alla adresser tillåtna initialt
            ),
            SecurityPolicy(
                operation=SecurityOperation.KEY_MANAGEMENT,
                min_security_level=SecurityLevel.CRITICAL,
                requires_approval=True,
                rate_limit_per_hour=10
            ),
            SecurityPolicy(
                operation=SecurityOperation.ACCESS_CONTROL,
                min_security_level=SecurityLevel.HIGH,
                requires_approval=False,
                rate_limit_per_hour=1000
            ),
            SecurityPolicy(
                operation=SecurityOperation.THREAT_DETECTION,
                min_security_level=SecurityLevel.HIGH,
                requires_approval=False,
                rate_limit_per_hour=10000
            )
        ]

        for policy in policies:
            self.policies[policy.operation] = policy

    @handle_errors(service_name="web3_security_manager")
    async def secure_operation(self, operation: SecurityOperation, context: SecurityContext,
                             operation_func, *args, **kwargs) -> Any:
        """
        Utför säker operation med policy enforcement.

        Args:
            operation: Typ av säkerhetsoperation
            context: Säkerhetskontext
            operation_func: Funktion att utföra säkert
            *args, **kwargs: Arguments till funktionen

        Returns:
            Resultat från operationen
        """
        start_time = datetime.now()

        try:
            # Validera säkerhetspolicy
            await self._validate_security_policy(operation, context)

            # Skapa säkerhetskontext
            context_id = f"{context.user_id}_{context.operation.value}_{start_time.timestamp()}"
            self.active_contexts[context_id] = context

            # Utför risk assessment
            risk_score = await self._assess_risk(context)

            # Kontrollera rate limiting
            await self._check_rate_limit(context)

            # Logga säkerhetsoperation
            await self._log_security_operation(context, risk_score)

            # Utför operationen
            result = await operation_func(*args, **kwargs)

            # Validera resultat
            await self._validate_operation_result(result, context)

            # Uppdatera metrics
            response_time = (datetime.now() - start_time).total_seconds()
            await self._update_security_metrics(operation, risk_score, response_time, True)

            # Rensa säkerhetskontext
            del self.active_contexts[context_id]

            logger.info(f"Säker operation genomförd: {operation.value} för användare {context.user_id}")
            return result

        except Exception as e:
            # Uppdatera metrics för misslyckad operation
            response_time = (datetime.now() - start_time).total_seconds()
            await self._update_security_metrics(operation, 0, response_time, False)

            # Rensa säkerhetskontext
            context_id = f"{context.user_id}_{context.operation.value}_{start_time.timestamp()}"
            if context_id in self.active_contexts:
                del self.active_contexts[context_id]

            logger.error(f"Säker operation misslyckades: {operation.value} - {e}")
            raise

    async def _validate_security_policy(self, operation: SecurityOperation, context: SecurityContext):
        """Validera säkerhetspolicy för operation."""
        if operation not in self.policies:
            raise SecurityError(f"Ingen policy definierad för operation: {operation.value}",
                              "POLICY_NOT_FOUND")

        policy = self.policies[operation]

        # Kontrollera säkerhetsnivå
        if context.risk_level == RiskLevel.CRITICAL and policy.min_security_level != SecurityLevel.CRITICAL:
            raise SecurityError("Kritiska operationer kräver högsta säkerhetsnivå",
                              "INSUFFICIENT_SECURITY_LEVEL")

        # Kontrollera beloppsgräns
        if policy.max_amount and context.metadata.get('amount', 0) > policy.max_amount:
            raise SecurityError(f"Belopp överskrider maxgräns: {policy.max_amount}",
                              "AMOUNT_EXCEEDS_LIMIT")

        # Kontrollera tillåtna adresser
        if policy.allowed_addresses and context.metadata.get('address') not in policy.allowed_addresses:
            raise SecurityError("Adress inte tillåten enligt policy",
                              "ADDRESS_NOT_ALLOWED")

        logger.debug(f"Security policy validerad för: {operation.value}")

    async def _assess_risk(self, context: SecurityContext) -> float:
        """Bedöm risk för säkerhetskontext."""
        cache_key = f"{context.user_id}_{context.operation.value}_{context.resource}"

        # Kontrollera risk cache
        if cache_key in self.risk_cache:
            cached_risk = self.risk_cache[cache_key]
            if datetime.now() - cached_risk['timestamp'] < timedelta(seconds=self.risk_cache_ttl):
                return cached_risk['score']

        # Beräkna risk score baserat på faktorer
        risk_score = 0.0

        # Risk baserat på operationstyp
        operation_risks = {
            SecurityOperation.TRANSACTION: 0.3,
            SecurityOperation.WALLET_CREATION: 0.8,
            SecurityOperation.KEY_MANAGEMENT: 0.9,
            SecurityOperation.ACCESS_CONTROL: 0.2,
            SecurityOperation.THREAT_DETECTION: 0.5
        }

        risk_score += operation_risks.get(context.operation, 0.5)

        # Risk baserat på belopp
        amount = context.metadata.get('amount', 0)
        if amount > 10000:
            risk_score += 0.4
        elif amount > 1000:
            risk_score += 0.2

        # Risk baserat på tidigare incidents
        user_incidents = await self._get_user_security_incidents(context.user_id)
        risk_score += min(user_incidents * 0.1, 0.5)

        # Risk baserat på tid på dygnet
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Nattetid
            risk_score += 0.2

        risk_score = min(risk_score, 1.0)

        # Cache risk score
        self.risk_cache[cache_key] = {
            'score': risk_score,
            'timestamp': datetime.now()
        }

        # Rensa gammal cache
        expired_keys = [k for k, v in self.risk_cache.items()
                       if datetime.now() - v['timestamp'] > timedelta(seconds=self.risk_cache_ttl)]
        for key in expired_keys:
            del self.risk_cache[key]

        return risk_score

    async def _check_rate_limit(self, context: SecurityContext):
        """Kontrollera rate limiting för användare och operation."""
        policy = self.policies.get(context.operation)
        if not policy or not policy.rate_limit_per_hour:
            return

        # Rate limit cache per användare och operation
        rate_limit_key = f"rate_limit_{context.user_id}_{context.operation.value}"
        current_time = datetime.now()

        # Rensa gamla entries (äldre än 1 timme)
        cutoff_time = current_time - timedelta(hours=1)
        # (I praktiken skulle detta hanteras av en riktig cache)

        # Enkel rate limiting implementation
        # I produktion skulle detta använda Redis eller liknande
        if hasattr(self, '_rate_limit_cache'):
            user_operations = [op for op in self._rate_limit_cache
                             if op['user_id'] == context.user_id and
                             op['operation'] == context.operation and
                             op['timestamp'] > cutoff_time]
        else:
            self._rate_limit_cache = []
            user_operations = []

        if len(user_operations) >= policy.rate_limit_per_hour:
            raise ValidationError(
                f"Rate limit överskreds för {context.operation.value}: {policy.rate_limit_per_hour}/timme",
                "RATE_LIMIT_EXCEEDED"
            )

        # Lägg till ny operation
        self._rate_limit_cache.append({
            'user_id': context.user_id,
            'operation': context.operation,
            'timestamp': current_time
        })

    async def _log_security_operation(self, context: SecurityContext, risk_score: float):
        """Logga säkerhetsoperation."""
        log_entry = {
            'timestamp': datetime.now(),
            'user_id': context.user_id,
            'operation': context.operation.value,
            'resource': context.resource,
            'risk_level': context.risk_level.value,
            'risk_score': risk_score,
            'ip_address': context.ip_address,
            'user_agent': context.user_agent,
            'metadata': context.metadata
        }

        # Logga till security service
        await self.security_service._log_security_event(
            'security_operation',
            'info',
            context.user_id,
            context.resource,
            context.operation.value,
            {
                'risk_score': risk_score,
                'policy_applied': self.policies[context.operation].__dict__ if context.operation in self.policies else None
            },
            context.ip_address,
            context.user_agent
        )

        logger.info(f"Security operation loggad: {context.operation.value} med risk score {risk_score}")

    async def _validate_operation_result(self, result: Any, context: SecurityContext):
        """Validera resultat från säkerhetsoperation."""
        # Enkel validering - kan utökas baserat på operationstyp
        if result is None:
            raise ValidationError("Operation returnerade None resultat",
                                "OPERATION_RESULT_INVALID")

        logger.debug(f"Operation resultat validerat för: {context.operation.value}")

    async def _update_security_metrics(self, operation: SecurityOperation, risk_score: float,
                                      response_time: float, success: bool):
        """Uppdatera säkerhetsmetrics."""
        self.security_metrics['total_operations'] += 1

        if not success:
            self.security_metrics['blocked_operations'] += 1

        if risk_score > 0.7:
            self.security_metrics['high_risk_operations'] += 1

        # Uppdatera genomsnittlig svarstid
        total_time = self.security_metrics['average_response_time'] * (self.security_metrics['total_operations'] - 1)
        total_time += response_time
        self.security_metrics['average_response_time'] = total_time / self.security_metrics['total_operations']

    async def _get_user_security_incidents(self, user_id: str) -> int:
        """Hämta antal säkerhetsincidents för användare."""
        # Simulerad implementation
        # I produktion skulle detta hämta från security audit log
        return 0

    @handle_errors(service_name="web3_security_manager")
    async def create_secure_wallet(self, user_id: str, wallet_type: str = "ethereum") -> Dict[str, Any]:
        """
        Skapa säker wallet med fullständig säkerhetsintegration.

        Args:
            user_id: Användar-ID
            wallet_type: Typ av wallet

        Returns:
            Wallet information
        """
        context = SecurityContext(
            user_id=user_id,
            operation=SecurityOperation.WALLET_CREATION,
            resource=f"wallet_{wallet_type}",
            risk_level=RiskLevel.HIGH,
            metadata={'wallet_type': wallet_type}
        )

        async def _create_wallet():
            # Skapa wallet genom security service
            wallet_info = await self.security_service.create_secure_key_pair(
                KeyType.AUTHENTICATION,
                f"wallet_{user_id}_{datetime.now().timestamp()}"
            )

            # Lägg till wallet metadata
            wallet_info.update({
                'wallet_type': wallet_type,
                'created_at': datetime.now(),
                'user_id': user_id,
                'status': 'active'
            })

            return wallet_info

        return await self.secure_operation(context.operation, context, _create_wallet)

    @handle_errors(service_name="web3_security_manager")
    async def secure_transaction(self, user_id: str, transaction_data: Dict[str, Any],
                               amount: float, to_address: str) -> SecureTransaction:
        """
        Genomför säker transaction med full validering.

        Args:
            user_id: Användar-ID
            transaction_data: Transaction data
            amount: Belopp
            to_address: Mottagaradress

        Returns:
            SecureTransaction
        """
        risk_level = RiskLevel.HIGH if amount > 1000 else RiskLevel.MEDIUM

        context = SecurityContext(
            user_id=user_id,
            operation=SecurityOperation.TRANSACTION,
            resource=f"transaction_{to_address}",
            risk_level=risk_level,
            metadata={
                'amount': amount,
                'to_address': to_address,
                'transaction_type': transaction_data.get('type', 'transfer')
            }
        )

        async def _process_transaction():
            return await self.security_service.encrypt_transaction_data(
                transaction_data,
                SecurityLevel.HIGH if risk_level == RiskLevel.CRITICAL else SecurityLevel.MEDIUM
            )

        return await self.secure_operation(context.operation, context, _process_transaction)

    @handle_errors(service_name="web3_security_manager")
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Hämta säkerhetsdashboard."""
        try:
            # Hämta metrics från underliggande service
            service_dashboard = await self.security_service.get_security_dashboard()

            # Kombinera metrics
            dashboard = {
                'security_manager_metrics': self.security_metrics,
                'security_service_dashboard': service_dashboard,
                'active_policies': {
                    op.value: policy.__dict__ for op, policy in self.policies.items()
                },
                'active_contexts': len(self.active_contexts),
                'risk_cache_size': len(self.risk_cache),
                'supported_operations': [op.value for op in SecurityOperation],
                'supported_risk_levels': [rl.value for rl in RiskLevel],
                'timestamp': datetime.now().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Security dashboard misslyckades: {e}")
            return {'error': str(e)}

    async def add_security_policy(self, policy: SecurityPolicy):
        """Lägg till säkerhetspolicy."""
        self.policies[policy.operation] = policy
        logger.info(f"Security policy tillagd för: {policy.operation.value}")

    async def update_security_policy(self, operation: SecurityOperation, updates: Dict[str, Any]):
        """Uppdatera säkerhetspolicy."""
        if operation not in self.policies:
            raise ValueError(f"Ingen policy för operation: {operation.value}")

        policy = self.policies[operation]
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

        logger.info(f"Security policy uppdaterad för: {operation.value}")

    async def register_event_handler(self, handler_func):
        """Registrera event handler för säkerhetshändelser."""
        self.event_handlers.append(handler_func)
        logger.info("Security event handler registrerad")

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på security manager."""
        try:
            service_health = await self.security_service.health_check()

            return {
                'service': 'web3_security_manager',
                'status': 'healthy',
                'active_contexts': len(self.active_contexts),
                'policies_count': len(self.policies),
                'security_metrics': self.security_metrics,
                'security_service': service_health,
                'supported_operations': [op.value for op in SecurityOperation],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_security_manager',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }