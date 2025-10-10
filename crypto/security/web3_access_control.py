"""
Web3 Access Control - Role-based access control för Web3-operationer.
Wallet permission management och transaction approval workflows.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from ..core.errors.error_handling import handle_errors, CryptoError, SecurityError, ValidationError

logger = logging.getLogger(__name__)

class Permission(Enum):
    """Behörigheter för Web3-operationer."""
    READ_BALANCE = "read_balance"
    SEND_TRANSACTION = "send_transaction"
    CREATE_WALLET = "create_wallet"
    MANAGE_KEYS = "manage_keys"
    VIEW_AUDIT_LOG = "view_audit_log"
    ADMIN_ACCESS = "admin_access"
    APPROVE_TRANSACTIONS = "approve_transactions"
    MANAGE_PERMISSIONS = "manage_permissions"

class Role(Enum):
    """Användarroller med olika behörighetsnivåer."""
    VIEWER = "viewer"
    TRADER = "trader"
    WALLET_MANAGER = "wallet_manager"
    SECURITY_OFFICER = "security_officer"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class ApprovalStatus(Enum):
    """Status för transaktionsgodkännanden."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class UserPermission:
    """Användarbehörigheter."""
    user_id: str
    permissions: Set[Permission]
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TransactionApproval:
    """Transaktionsgodkännande."""
    approval_id: str
    transaction_hash: str
    requester_id: str
    approver_id: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    amount: float = 0.0
    to_address: str = ""
    reason: str = ""
    approval_notes: str = ""

@dataclass
class AccessRule:
    """Åtkomstregel för resurser."""
    resource_pattern: str
    allowed_roles: Set[Role]
    required_permissions: Set[Permission]
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0

class Web3AccessControl:
    """
    Role-based access control för Web3-operationer.

    Funktioner:
    - Användarroller och behörigheter
    - Transaktionsgodkännande workflows
    - Wallet permission management
    - Integration med befintliga auth-system
    - Audit logging för alla åtkomstbeslut
    """

    def __init__(self):
        """Initiera Web3 Access Control."""
        # Användare -> roller mapping
        self.user_roles = {}

        # Roller -> behörigheter mapping
        self.role_permissions = {}
        self._initialize_default_roles()

        # Användarspecifika behörigheter
        self.user_permissions = {}

        # Transaktionsgodkännanden
        self.pending_approvals = {}
        self.approval_history = {}

        # Åtkomstregler
        self.access_rules = []
        self._initialize_default_rules()

        # Sessionshantering
        self.active_sessions = {}
        self.session_timeout = 3600  # 1 timme

        # Multi-signature wallets
        self.multisig_wallets = {}

        logger.info("Web3 Access Control initierad")

    def _initialize_default_roles(self):
        """Initiera default roller och behörigheter."""
        role_configs = {
            Role.VIEWER: {
                Permission.READ_BALANCE,
                Permission.VIEW_AUDIT_LOG
            },
            Role.TRADER: {
                Permission.READ_BALANCE,
                Permission.SEND_TRANSACTION,
                Permission.VIEW_AUDIT_LOG
            },
            Role.WALLET_MANAGER: {
                Permission.READ_BALANCE,
                Permission.SEND_TRANSACTION,
                Permission.CREATE_WALLET,
                Permission.VIEW_AUDIT_LOG,
                Permission.APPROVE_TRANSACTIONS
            },
            Role.SECURITY_OFFICER: {
                Permission.READ_BALANCE,
                Permission.SEND_TRANSACTION,
                Permission.CREATE_WALLET,
                Permission.MANAGE_KEYS,
                Permission.VIEW_AUDIT_LOG,
                Permission.APPROVE_TRANSACTIONS
            },
            Role.ADMIN: {
                Permission.READ_BALANCE,
                Permission.SEND_TRANSACTION,
                Permission.CREATE_WALLET,
                Permission.MANAGE_KEYS,
                Permission.VIEW_AUDIT_LOG,
                Permission.APPROVE_TRANSACTIONS,
                Permission.MANAGE_PERMISSIONS
            },
            Role.SUPER_ADMIN: set(Permission)  # Alla behörigheter
        }

        for role, permissions in role_configs.items():
            self.role_permissions[role] = permissions

    def _initialize_default_rules(self):
        """Initiera default åtkomstregler."""
        default_rules = [
            AccessRule(
                resource_pattern="balance_*",
                allowed_roles={Role.VIEWER, Role.TRADER, Role.WALLET_MANAGER, Role.SECURITY_OFFICER, Role.ADMIN, Role.SUPER_ADMIN},
                required_permissions={Permission.READ_BALANCE}
            ),
            AccessRule(
                resource_pattern="transaction_*",
                allowed_roles={Role.TRADER, Role.WALLET_MANAGER, Role.SECURITY_OFFICER, Role.ADMIN, Role.SUPER_ADMIN},
                required_permissions={Permission.SEND_TRANSACTION},
                conditions={"max_amount": 1000.0}
            ),
            AccessRule(
                resource_pattern="wallet_*",
                allowed_roles={Role.WALLET_MANAGER, Role.SECURITY_OFFICER, Role.ADMIN, Role.SUPER_ADMIN},
                required_permissions={Permission.CREATE_WALLET}
            ),
            AccessRule(
                resource_pattern="admin_*",
                allowed_roles={Role.ADMIN, Role.SUPER_ADMIN},
                required_permissions={Permission.ADMIN_ACCESS}
            )
        ]

        self.access_rules = default_rules

    @handle_errors(service_name="web3_access_control")
    async def check_access(self, user_id: str, resource: str, required_permission: Permission,
                         context: Dict[str, Any] = None) -> bool:
        """
        Kontrollera åtkomst för användare och resurs.

        Args:
            user_id: Användar-ID
            resource: Resurs att komma åt
            required_permission: Nödvändig behörighet
            context: Ytterligare kontext

        Returns:
            True om åtkomst tillåten
        """
        try:
            context = context or {}

            # Kontrollera session
            if not await self._validate_session(user_id):
                logger.warning(f"Ogiltig session för användare: {user_id}")
                return False

            # Hitta matchande åtkomstregel
            access_rule = await self._find_matching_rule(resource, required_permission)
            if not access_rule:
                logger.warning(f"Ingen åtkomstregel hittad för resurs: {resource}")
                return False

            # Kontrollera om användarens roll är tillåten
            user_roles = await self.get_user_roles(user_id)
            if not any(role in access_rule.allowed_roles for role in user_roles):
                logger.warning(f"Användare {user_id} har inte tillåten roll för resurs: {resource}")
                return False

            # Kontrollera specifika behörigheter
            if not await self._check_specific_permissions(user_id, access_rule.required_permissions):
                logger.warning(f"Användare {user_id} saknar nödvändiga behörigheter för resurs: {resource}")
                return False

            # Kontrollera villkor
            if not await self._evaluate_conditions(access_rule.conditions, context):
                logger.warning(f"Villkor inte uppfyllda för resurs: {resource}")
                return False

            # Logga åtkomstkontroll
            await self._log_access_control_event(user_id, resource, required_permission, True, context)

            logger.info(f"Åtkomst tillåten för användare {user_id} till resurs {resource}")
            return True

        except Exception as e:
            logger.error(f"Åtkomstkontroll misslyckades för {user_id}: {e}")
            await self._log_access_control_event(user_id, resource, required_permission, False, context)
            return False

    async def _find_matching_rule(self, resource: str, required_permission: Permission) -> Optional[AccessRule]:
        """Hitta matchande åtkomstregel."""
        matching_rules = []

        for rule in self.access_rules:
            if required_permission in rule.required_permissions:
                # Enkel pattern matching - kan utökas med regex
                if rule.resource_pattern.endswith('*'):
                    pattern_base = rule.resource_pattern[:-1]
                    if resource.startswith(pattern_base):
                        matching_rules.append(rule)
                elif resource == rule.resource_pattern:
                    matching_rules.append(rule)

        if not matching_rules:
            return None

        # Returnera regel med högst prioritet
        return max(matching_rules, key=lambda r: r.priority)

    async def _check_specific_permissions(self, user_id: str, required_permissions: Set[Permission]) -> bool:
        """Kontrollera specifika behörigheter."""
        user_roles = await self.get_user_roles(user_id)

        # Kontrollera rollbaserade behörigheter
        for role in user_roles:
            if role in self.role_permissions:
                role_perms = self.role_permissions[role]
                if required_permissions.issubset(role_perms):
                    return True

        # Kontrollera användarspecifika behörigheter
        if user_id in self.user_permissions:
            user_perms = self.user_permissions[user_id]
            for perm_entry in user_perms:
                if required_permissions.issubset(perm_entry.permissions):
                    # Kontrollera utgångsdatum
                    if perm_entry.expires_at and datetime.now() > perm_entry.expires_at:
                        continue
                    return True

        return False

    async def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Utvärdera åtkomstvillkor."""
        try:
            for condition_key, condition_value in conditions.items():
                context_value = context.get(condition_key)

                if context_value is None:
                    logger.warning(f"Saknat kontextvärde för villkor: {condition_key}")
                    return False

                # Enkel villkorsutvärdering
                if condition_key == "max_amount" and context_value > condition_value:
                    return False

                elif condition_key == "allowed_addresses":
                    if context_value not in condition_value:
                        return False

                elif condition_key == "time_range":
                    current_time = datetime.now().time()
                    if not (condition_value[0] <= current_time <= condition_value[1]):
                        return False

            return True

        except Exception as e:
            logger.error(f"Villkorsutvärdering misslyckades: {e}")
            return False

    async def _validate_session(self, user_id: str) -> bool:
        """Validera användarsession."""
        if user_id not in self.active_sessions:
            return False

        session = self.active_sessions[user_id]
        if datetime.now() > session['expires_at']:
            del self.active_sessions[user_id]
            return False

        return True

    async def _log_access_control_event(self, user_id: str, resource: str, permission: Permission,
                                      granted: bool, context: Dict[str, Any]):
        """Logga åtkomstkontrollhändelse."""
        log_entry = {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'resource': resource,
            'permission': permission.value,
            'granted': granted,
            'context': context
        }

        logger.info(f"Access control - User: {user_id}, Resource: {resource}, "
                   f"Permission: {permission.value}, Granted: {granted}")

    @handle_errors(service_name="web3_access_control")
    async def assign_role(self, user_id: str, role: Role, assigned_by: str) -> bool:
        """
        Tilldela roll till användare.

        Args:
            user_id: Användar-ID
            role: Roll att tilldela
            assigned_by: Användare som tilldelar rollen

        Returns:
            True om lyckades
        """
        try:
            if user_id not in self.user_roles:
                self.user_roles[user_id] = set()

            self.user_roles[user_id].add(role)

            # Logga rolltilldelning
            await self._log_role_assignment(user_id, role, assigned_by, True)

            logger.info(f"Roll {role.value} tilldelad till användare {user_id}")
            return True

        except Exception as e:
            logger.error(f"Roll tilldelning misslyckades för {user_id}: {e}")
            await self._log_role_assignment(user_id, role, assigned_by, False)
            return False

    async def _log_role_assignment(self, user_id: str, role: Role, assigned_by: str, success: bool):
        """Logga rolltilldelning."""
        logger.info(f"Role assignment - User: {user_id}, Role: {role.value}, "
                   f"Assigned by: {assigned_by}, Success: {success}")

    @handle_errors(service_name="web3_access_control")
    async def revoke_role(self, user_id: str, role: Role, revoked_by: str) -> bool:
        """
        Återkalla roll från användare.

        Args:
            user_id: Användar-ID
            role: Roll att återkalla
            revoked_by: Användare som återkallar rollen

        Returns:
            True om lyckades
        """
        try:
            if user_id in self.user_roles and role in self.user_roles[user_id]:
                self.user_roles[user_id].remove(role)

                # Logga rollåterkallning
                await self._log_role_revocation(user_id, role, revoked_by, True)

                logger.info(f"Roll {role.value} återkallad från användare {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Roll återkallning misslyckades för {user_id}: {e}")
            await self._log_role_revocation(user_id, role, revoked_by, False)
            return False

    async def _log_role_revocation(self, user_id: str, role: Role, revoked_by: str, success: bool):
        """Logga rollåterkallning."""
        logger.info(f"Role revocation - User: {user_id}, Role: {role.value}, "
                   f"Revoked by: {revoked_by}, Success: {success}")

    @handle_errors(service_name="web3_access_control")
    async def grant_permission(self, user_id: str, permission: Permission, granted_by: str,
                             expires_at: Optional[datetime] = None, metadata: Dict[str, Any] = None) -> bool:
        """
        Ge specifik behörighet till användare.

        Args:
            user_id: Användar-ID
            permission: Behörighet att ge
            granted_by: Användare som ger behörigheten
            expires_at: Utgångsdatum för behörigheten
            metadata: Ytterligare metadata

        Returns:
            True om lyckades
        """
        try:
            if user_id not in self.user_permissions:
                self.user_permissions[user_id] = []

            permission_entry = UserPermission(
                user_id=user_id,
                permissions={permission},
                granted_by=granted_by,
                granted_at=datetime.now(),
                expires_at=expires_at,
                metadata=metadata or {}
            )

            self.user_permissions[user_id].append(permission_entry)

            # Logga behörighetstilldelning
            await self._log_permission_grant(user_id, permission, granted_by, True)

            logger.info(f"Behörighet {permission.value} given till användare {user_id}")
            return True

        except Exception as e:
            logger.error(f"Behörighetstilldelning misslyckades för {user_id}: {e}")
            await self._log_permission_grant(user_id, permission, granted_by, False)
            return False

    async def _log_permission_grant(self, user_id: str, permission: Permission, granted_by: str, success: bool):
        """Logga behörighetstilldelning."""
        logger.info(f"Permission grant - User: {user_id}, Permission: {permission.value}, "
                   f"Granted by: {granted_by}, Success: {success}")

    @handle_errors(service_name="web3_access_control")
    async def request_transaction_approval(self, requester_id: str, transaction_hash: str,
                                        amount: float, to_address: str, reason: str) -> str:
        """
        Begär godkännande för transaktion.

        Args:
            requester_id: Användare som begär godkännande
            transaction_hash: Transaction hash
            amount: Belopp
            to_address: Mottagaradress
            reason: Anledning

        Returns:
            Approval ID
        """
        try:
            approval_id = hashlib.sha256(
                f"{requester_id}_{transaction_hash}_{datetime.now().timestamp()}".encode()
            ).hexdigest()[:16]

            approval = TransactionApproval(
                approval_id=approval_id,
                transaction_hash=transaction_hash,
                requester_id=requester_id,
                amount=amount,
                to_address=to_address,
                reason=reason
            )

            self.pending_approvals[approval_id] = approval

            # Logga godkännandebegäran
            await self._log_approval_request(requester_id, approval_id, True)

            logger.info(f"Transaktionsgodkännande begärt: {approval_id} för {amount} till {to_address}")
            return approval_id

        except Exception as e:
            logger.error(f"Godkännandebegäran misslyckades för {requester_id}: {e}")
            await self._log_approval_request(requester_id, approval_id, False)
            return ""

    async def _log_approval_request(self, requester_id: str, approval_id: str, success: bool):
        """Logga godkännandebegäran."""
        logger.info(f"Approval request - Requester: {requester_id}, Approval ID: {approval_id}, Success: {success}")

    @handle_errors(service_name="web3_access_control")
    async def approve_transaction(self, approval_id: str, approver_id: str, approval_notes: str = "") -> bool:
        """
        Godkänn transaktion.

        Args:
            approval_id: Approval ID
            approver_id: Användare som godkänner
            approval_notes: Godkännandenoteringar

        Returns:
            True om lyckades
        """
        try:
            if approval_id not in self.pending_approvals:
                return False

            approval = self.pending_approvals[approval_id]

            # Kontrollera att approver har rätt behörigheter
            approver_roles = await self.get_user_roles(approver_id)
            if not any(role in [Role.WALLET_MANAGER, Role.SECURITY_OFFICER, Role.ADMIN, Role.SUPER_ADMIN]
                      for role in approver_roles):
                logger.warning(f"Användare {approver_id} har inte rätt att godkänna transaktioner")
                return False

            # Kontrollera beloppsgräns för approver
            if approval.amount > 10000 and Role.ADMIN not in approver_roles:
                logger.warning(f"Användare {approver_id} kan inte godkänna transaktioner över 10000")
                return False

            # Uppdatera godkännande
            approval.approver_id = approver_id
            approval.status = ApprovalStatus.APPROVED
            approval.approved_at = datetime.now()
            approval.approval_notes = approval_notes

            # Flytta till historik
            self.approval_history[approval_id] = approval
            del self.pending_approvals[approval_id]

            # Logga godkännande
            await self._log_transaction_approval(approval_id, approver_id, True)

            logger.info(f"Transaktion godkänd: {approval_id} av {approver_id}")
            return True

        except Exception as e:
            logger.error(f"Transaktionsgodkännande misslyckades för {approval_id}: {e}")
            await self._log_transaction_approval(approval_id, approver_id, False)
            return False

    async def _log_transaction_approval(self, approval_id: str, approver_id: str, success: bool):
        """Logga transaktionsgodkännande."""
        logger.info(f"Transaction approval - Approval ID: {approval_id}, Approver: {approver_id}, Success: {success}")

    async def get_user_roles(self, user_id: str) -> Set[Role]:
        """Hämta användarens roller."""
        return self.user_roles.get(user_id, set())

    async def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Hämta användarens behörigheter."""
        permissions = set()

        # Rollbaserade behörigheter
        user_roles = await self.get_user_roles(user_id)
        for role in user_roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])

        # Användarspecifika behörigheter
        if user_id in self.user_permissions:
            for perm_entry in self.user_permissions[user_id]:
                if not perm_entry.expires_at or datetime.now() <= perm_entry.expires_at:
                    permissions.update(perm_entry.permissions)

        return permissions

    async def get_access_control_dashboard(self) -> Dict[str, Any]:
        """Hämta åtkomstkontrolldashboard."""
        try:
            dashboard = {
                'total_users': len(self.user_roles),
                'total_roles': len(self.role_permissions),
                'pending_approvals': len(self.pending_approvals),
                'approval_history_count': len(self.approval_history),
                'active_sessions': len(self.active_sessions),
                'user_roles_distribution': {
                    user_id: [role.value for role in roles]
                    for user_id, roles in self.user_roles.items()
                },
                'role_permissions': {
                    role.value: [perm.value for perm in permissions]
                    for role, permissions in self.role_permissions.items()
                },
                'recent_approvals': [
                    {
                        'approval_id': approval.approval_id,
                        'requester_id': approval.requester_id,
                        'amount': approval.amount,
                        'status': approval.status.value,
                        'requested_at': approval.requested_at.isoformat()
                    }
                    for approval in list(self.approval_history.values())[-10:]  # Senaste 10
                ],
                'supported_permissions': [perm.value for perm in Permission],
                'supported_roles': [role.value for role in Role],
                'timestamp': datetime.now().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Access control dashboard misslyckades: {e}")
            return {'error': str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på access control."""
        try:
            return {
                'service': 'web3_access_control',
                'status': 'healthy',
                'total_users': len(self.user_roles),
                'total_roles': len(self.role_permissions),
                'pending_approvals': len(self.pending_approvals),
                'active_sessions': len(self.active_sessions),
                'supported_permissions': [perm.value for perm in Permission],
                'supported_roles': [role.value for role in Role],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_access_control',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }