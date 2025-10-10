"""
HappyOS Crypto Module - AI-driven krypto/DeFi-funktionalitet.
Standalone version efter disconnect från större system.

Innehåller:
- Security: Web3 säkerhetskomponenter med Google Cloud KMS integration
- Cache: Multi-level cache system med Redis och Firestore
- Services: Integrationstjänster för security och cache
- Agents: AI-agenter för krypto-operationer
- Handlers: Web3 operation handlers
- Trading: Trading system och strategier
"""

# Security Components
from .security import (
    Web3Security, SecurityLevel, KeyType, SecureTransaction,
    Web3SecurityManager, SecurityContext, SecurityOperation, RiskLevel,
    Web3AccessControl, Permission, Role, ApprovalStatus, TransactionApproval,
    Web3Firewall, ThreatDetection, ThreatLevel, ThreatType
)

# Cache Components
from .cache import (
    Web3Cache, CacheLevel, CacheType, CacheEntry,
    Web3CacheManager, CacheStrategy, CacheInvalidationType, CachePolicy, CacheDependency,
    Web3RedisCache, RedisConnectionConfig
)

# Service Integration Components
from .services import (
    Web3SecurityIntegration, SecurityEvent, SecurityEventType, SecurityAlert,
    Web3CacheIntegration, CachePerformanceLevel, CacheOptimizationRecommendation
)

# __all__ = ['CryptoSkill']
__all__ = [
    # Security Components
    'Web3Security', 'SecurityLevel', 'KeyType', 'SecureTransaction',
    'Web3SecurityManager', 'SecurityContext', 'SecurityOperation', 'RiskLevel',
    'Web3AccessControl', 'Permission', 'Role', 'ApprovalStatus', 'TransactionApproval',
    'Web3Firewall', 'ThreatDetection', 'ThreatLevel', 'ThreatType',

    # Cache Components
    'Web3Cache', 'CacheLevel', 'CacheType', 'CacheEntry',
    'Web3CacheManager', 'CacheStrategy', 'CacheInvalidationType', 'CachePolicy', 'CacheDependency',
    'Web3RedisCache', 'RedisConnectionConfig',

    # Service Integration Components
    'Web3SecurityIntegration', 'SecurityEvent', 'SecurityEventType', 'SecurityAlert',
    'Web3CacheIntegration', 'CachePerformanceLevel', 'CacheOptimizationRecommendation',
]
