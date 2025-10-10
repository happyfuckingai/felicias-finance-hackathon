"""
Web3 Firewall - Blockchain address firewall och real-tids threat prevention.
Transaction pattern detection och malicious contract detection.
"""
import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Union, Set, Tuple, Pattern
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import ipaddress

from ..core.errors.error_handling import handle_errors, CryptoError, SecurityError, ValidationError

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Hotnivåer för säkerhetshot."""
    LOW = "låg"
    MEDIUM = "medium"
    HIGH = "hög"
    CRITICAL = "kritisk"

class ThreatType(Enum):
    """Typer av säkerhetshot."""
    MALICIOUS_ADDRESS = "malicious_address"
    SUSPICIOUS_TRANSACTION = "suspicious_transaction"
    UNUSUAL_PATTERN = "unusual_pattern"
    MALICIOUS_CONTRACT = "malicious_contract"
    PHISHING_ATTEMPT = "phishing_attempt"
    SYBIL_ATTACK = "sybil_attack"
    FLASH_LOAN_ATTACK = "flash_loan_attack"
    RUG_PULL = "rug_pull"

class FirewallRule:
    """Brandväggsregel för blockering."""
    def __init__(self, rule_id: str, pattern: str, threat_type: ThreatType,
                 threat_level: ThreatLevel, description: str, enabled: bool = True):
        self.rule_id = rule_id
        self.pattern = pattern
        self.threat_type = threat_type
        self.threat_level = threat_level
        self.description = description
        self.enabled = enabled
        self.created_at = datetime.now()
        self.hit_count = 0
        self.last_hit = None

@dataclass
class ThreatDetection:
    """Hotdetektion."""
    detection_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    source_address: str
    target_address: str
    transaction_hash: str = ""
    contract_address: str = ""
    amount: float = 0.0
    confidence_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)
    blocked: bool = False
    false_positive: bool = False

@dataclass
class AddressReputation:
    """Adressreputation."""
    address: str
    reputation_score: float = 0.0  # 0.0 = okänd, 1.0 = misstänkt
    threat_history: List[ThreatDetection] = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.now)
    flagged: bool = False
    whitelist: bool = False
    blacklist: bool = False

class Web3Firewall:
    """
    Blockchain firewall för real-tids threat prevention.

    Funktioner:
    - Blockchain address firewall
    - Transaction pattern detection
    - Malicious contract detection
    - Real-tids threat prevention
    - Address reputation system
    - Automated threat response
    """

    def __init__(self):
        """Initiera Web3 Firewall."""
        # Brandväggsregler
        self.firewall_rules = {}
        self._initialize_default_rules()

        # Adressreputation
        self.address_reputation = {}

        # Hotdetektioner
        self.threat_detections = []

        # Rate limiting per adress
        self.address_rate_limits = {}
        self.rate_limit_window = 60  # 1 minut
        self.max_transactions_per_window = 10

        # Pattern recognition
        self.suspicious_patterns = {}
        self._initialize_suspicious_patterns()

        # Whitelist/Blacklist
        self.whitelist_addresses = set()
        self.blacklist_addresses = set()

        # Threat intelligence feeds
        self.threat_feeds = {}

        logger.info("Web3 Firewall initierad")

    def _initialize_default_rules(self):
        """Initiera default brandväggsregler."""
        default_rules = [
            FirewallRule(
                rule_id="suspicious_amount",
                pattern=r"amount_>100000",
                threat_type=ThreatType.SUSPICIOUS_TRANSACTION,
                threat_level=ThreatLevel.HIGH,
                description="Transaktioner över 100,000 USD"
            ),
            FirewallRule(
                rule_id="unusual_frequency",
                pattern=r"freq_>5_per_minute",
                threat_type=ThreatType.SUSPICIOUS_TRANSACTION,
                threat_level=ThreatLevel.MEDIUM,
                description="Ovanligt hög transaktionsfrekvens"
            ),
            FirewallRule(
                rule_id="known_scam_address",
                pattern=r"known_scam_.*",
                threat_type=ThreatType.MALICIOUS_ADDRESS,
                threat_level=ThreatLevel.CRITICAL,
                description="Kända scam-adresser"
            ),
            FirewallRule(
                rule_id="malicious_contract",
                pattern=r"contract_.*honeypot.*",
                threat_type=ThreatType.MALICIOUS_CONTRACT,
                threat_level=ThreatLevel.CRITICAL,
                description="Misstänkta honeypot-kontrakt"
            ),
            FirewallRule(
                rule_id="flash_loan_pattern",
                pattern=r"flash_loan_.*",
                threat_type=ThreatType.FLASH_LOAN_ATTACK,
                threat_level=ThreatLevel.HIGH,
                description="Flash loan attack patterns"
            )
        ]

        for rule in default_rules:
            self.firewall_rules[rule.rule_id] = rule

    def _initialize_suspicious_patterns(self):
        """Initiera misstänkta patterns."""
        self.suspicious_patterns = {
            'drain_pattern': re.compile(r'.*drain.*|.*withdraw.*all.*'),
            'unlimited_approve': re.compile(r'.*approve.*unlimited.*|.*approve.*max.*'),
            'sos_pattern': re.compile(r'.*sos.*|.*help.*|.*emergency.*'),
            'honeypot_indicators': re.compile(r'.*honeypot.*|.*trap.*|.*scam.*'),
            'rug_pull_signals': re.compile(r'.*rug.*|.*pull.*|.*exit.*scam.*')
        }

    @handle_errors(service_name="web3_firewall")
    async def analyze_transaction(self, transaction_data: Dict[str, Any],
                                source_address: str, context: Dict[str, Any] = None) -> ThreatDetection:
        """
        Analysera transaktion för hot.

        Args:
            transaction_data: Transaction data
            source_address: Källaadress
            context: Ytterligare kontext

        Returns:
            ThreatDetection resultat
        """
        try:
            context = context or {}
            detection_id = hashlib.sha256(
                f"{source_address}_{json.dumps(transaction_data)}_{datetime.now().timestamp()}".encode()
            ).hexdigest()[:16]

            threats_found = []
            max_threat_level = ThreatLevel.LOW
            total_confidence = 0.0

            # Kontrollera mot brandväggsregler
            for rule in self.firewall_rules.values():
                if rule.enabled:
                    threat = await self._check_firewall_rule(rule, transaction_data, source_address)
                    if threat:
                        threats_found.append(threat)
                        if threat.threat_level.value > max_threat_level.value:
                            max_threat_level = threat.threat_level
                        total_confidence += threat.confidence_score

            # Kontrollera adressreputation
            reputation_threat = await self._check_address_reputation(source_address, transaction_data)
            if reputation_threat:
                threats_found.append(reputation_threat)
                if reputation_threat.threat_level.value > max_threat_level.value:
                    max_threat_level = reputation_threat.threat_level
                total_confidence += reputation_threat.confidence_score

            # Kontrollera misstänkta patterns
            pattern_threat = await self._check_suspicious_patterns(transaction_data)
            if pattern_threat:
                threats_found.append(pattern_threat)
                if pattern_threat.threat_level.value > max_threat_level.value:
                    max_threat_level = pattern_threat.threat_level
                total_confidence += pattern_threat.confidence_score

            # Kontrollera rate limiting
            rate_threat = await self._check_rate_limit(source_address)
            if rate_threat:
                threats_found.append(rate_threat)
                if rate_threat.threat_level.value > max_threat_level.value:
                    max_threat_level = rate_threat.threat_level
                total_confidence += rate_threat.confidence_score

            # Beräkna total hotscore
            average_confidence = total_confidence / max(len(threats_found), 1)

            # Skapa threat detection
            detection = ThreatDetection(
                detection_id=detection_id,
                threat_type=ThreatType.SUSPICIOUS_TRANSACTION if len(threats_found) > 0 else ThreatType.MALICIOUS_ADDRESS,
                threat_level=max_threat_level,
                source_address=source_address,
                target_address=transaction_data.get('to', ''),
                transaction_hash=transaction_data.get('hash', ''),
                amount=transaction_data.get('amount', 0),
                confidence_score=average_confidence,
                details={
                    'threats_found': [t.threat_type.value for t in threats_found],
                    'rule_hits': [t.details.get('rule_id', '') for t in threats_found if t.details.get('rule_id')],
                    'reputation_score': self.address_reputation.get(source_address, AddressReputation(source_address)).reputation_score
                },
                blocked=len(threats_found) > 0
            )

            # Uppdatera hotstatistik
            self.threat_detections.append(detection)
            await self._update_threat_statistics(threats_found)

            # Logga threat detection
            await self._log_threat_detection(detection)

            logger.info(f"Threat analysis genomförd för {source_address}: {len(threats_found)} hot hittade")
            return detection

        except Exception as e:
            logger.error(f"Threat analysis misslyckades för {source_address}: {e}")
            raise SecurityError(f"Threat analysis misslyckades: {str(e)}", "THREAT_ANALYSIS_FAILED")

    async def _check_firewall_rule(self, rule: FirewallRule, transaction_data: Dict[str, Any],
                                 source_address: str) -> Optional[ThreatDetection]:
        """Kontrollera mot specifik brandväggsregel."""
        try:
            # Enkel pattern matching - kan utökas med mer sofistikerad logik
            amount = transaction_data.get('amount', 0)

            if rule.rule_id == "suspicious_amount" and amount > 100000:
                return ThreatDetection(
                    detection_id=f"rule_{rule.rule_id}_{datetime.now().timestamp()}",
                    threat_type=rule.threat_type,
                    threat_level=rule.threat_level,
                    source_address=source_address,
                    target_address=transaction_data.get('to', ''),
                    amount=amount,
                    confidence_score=0.8,
                    details={'rule_id': rule.rule_id, 'trigger': f'amount_{amount}'}
                )

            elif rule.rule_id == "unusual_frequency":
                # Kontrollera transaktionsfrekvens
                recent_tx_count = await self._get_recent_transaction_count(source_address)
                if recent_tx_count > 5:
                    return ThreatDetection(
                        detection_id=f"rule_{rule.rule_id}_{datetime.now().timestamp()}",
                        threat_type=rule.threat_type,
                        threat_level=rule.threat_level,
                        source_address=source_address,
                        target_address=transaction_data.get('to', ''),
                        amount=amount,
                        confidence_score=0.6,
                        details={'rule_id': rule.rule_id, 'frequency': recent_tx_count}
                    )

            return None

        except Exception as e:
            logger.error(f"Firewall rule check misslyckades för {rule.rule_id}: {e}")
            return None

    async def _check_address_reputation(self, address: str, transaction_data: Dict[str, Any]) -> Optional[ThreatDetection]:
        """Kontrollera adressreputation."""
        try:
            if address not in self.address_reputation:
                self.address_reputation[address] = AddressReputation(address)

            reputation = self.address_reputation[address]

            # Uppdatera senaste aktivitet
            reputation.last_activity = datetime.now()

            # Kontrollera whitelist/blacklist
            if address in self.whitelist_addresses:
                return None

            if address in self.blacklist_addresses:
                return ThreatDetection(
                    detection_id=f"blacklist_{address}_{datetime.now().timestamp()}",
                    threat_type=ThreatType.MALICIOUS_ADDRESS,
                    threat_level=ThreatLevel.CRITICAL,
                    source_address=address,
                    target_address=transaction_data.get('to', ''),
                    amount=transaction_data.get('amount', 0),
                    confidence_score=1.0,
                    details={'reason': 'blacklisted_address'},
                    blocked=True
                )

            # Beräkna reputation score baserat på hot-historik
            if reputation.threat_history:
                recent_threats = [t for t in reputation.threat_history
                                if datetime.now() - t.detected_at < timedelta(days=30)]
                if recent_threats:
                    reputation.reputation_score = min(sum(t.confidence_score for t in recent_threats) / len(recent_threats), 1.0)
                    reputation.flagged = reputation.reputation_score > 0.7

                    if reputation.flagged:
                        return ThreatDetection(
                            detection_id=f"reputation_{address}_{datetime.now().timestamp()}",
                            threat_type=ThreatType.MALICIOUS_ADDRESS,
                            threat_level=ThreatLevel.HIGH,
                            source_address=address,
                            target_address=transaction_data.get('to', ''),
                            amount=transaction_data.get('amount', 0),
                            confidence_score=reputation.reputation_score,
                            details={'reputation_score': reputation.reputation_score},
                            blocked=True
                        )

            return None

        except Exception as e:
            logger.error(f"Address reputation check misslyckades för {address}: {e}")
            return None

    async def _check_suspicious_patterns(self, transaction_data: Dict[str, Any]) -> Optional[ThreatDetection]:
        """Kontrollera misstänkta patterns."""
        try:
            transaction_text = json.dumps(transaction_data).lower()

            for pattern_name, pattern_regex in self.suspicious_patterns.items():
                if pattern_regex.search(transaction_text):
                    return ThreatDetection(
                        detection_id=f"pattern_{pattern_name}_{datetime.now().timestamp()}",
                        threat_type=ThreatType.SUSPICIOUS_TRANSACTION,
                        threat_level=ThreatLevel.HIGH,
                        source_address=transaction_data.get('from', ''),
                        target_address=transaction_data.get('to', ''),
                        amount=transaction_data.get('amount', 0),
                        confidence_score=0.9,
                        details={'pattern': pattern_name, 'matched_text': pattern_regex.search(transaction_text).group()},
                        blocked=True
                    )

            return None

        except Exception as e:
            logger.error(f"Suspicious pattern check misslyckades: {e}")
            return None

    async def _check_rate_limit(self, address: str) -> Optional[ThreatDetection]:
        """Kontrollera rate limiting."""
        try:
            current_time = datetime.now()

            # Rensa gammal rate limit data
            cutoff_time = current_time - timedelta(seconds=self.rate_limit_window)
            if address in self.address_rate_limits:
                self.address_rate_limits[address] = [
                    tx for tx in self.address_rate_limits[address]
                    if tx > cutoff_time
                ]

            # Lägg till nuvarande transaktion
            if address not in self.address_rate_limits:
                self.address_rate_limits[address] = []

            self.address_rate_limits[address].append(current_time)

            # Kontrollera rate limit
            recent_count = len(self.address_rate_limits[address])
            if recent_count > self.max_transactions_per_window:
                return ThreatDetection(
                    detection_id=f"ratelimit_{address}_{datetime.now().timestamp()}",
                    threat_type=ThreatType.SUSPICIOUS_TRANSACTION,
                    threat_level=ThreatLevel.MEDIUM,
                    source_address=address,
                    target_address="",
                    confidence_score=0.7,
                    details={'rate_limit_exceeded': recent_count},
                    blocked=True
                )

            return None

        except Exception as e:
            logger.error(f"Rate limit check misslyckades för {address}: {e}")
            return None

    async def _get_recent_transaction_count(self, address: str) -> int:
        """Hämta antal senaste transaktioner för adress."""
        # Simulerad implementation
        return len(self.address_rate_limits.get(address, []))

    async def _update_threat_statistics(self, threats_found: List[ThreatDetection]):
        """Uppdatera hotstatistik."""
        for threat in threats_found:
            if threat.details.get('rule_id'):
                rule_id = threat.details['rule_id']
                if rule_id in self.firewall_rules:
                    self.firewall_rules[rule_id].hit_count += 1
                    self.firewall_rules[rule_id].last_hit = datetime.now()

    async def _log_threat_detection(self, detection: ThreatDetection):
        """Logga threat detection."""
        logger.warning(f"THREAT DETECTED - Level: {detection.threat_level.value}, "
                      f"Type: {detection.threat_type.value}, Address: {detection.source_address}, "
                      f"Confidence: {detection.confidence_score}")

    @handle_errors(service_name="web3_firewall")
    async def should_block_transaction(self, transaction_data: Dict[str, Any],
                                     source_address: str) -> Tuple[bool, Optional[ThreatDetection]]:
        """
        Avgör om transaktion ska blockeras.

        Args:
            transaction_data: Transaction data
            source_address: Källaadress

        Returns:
            Tuple (should_block, threat_detection)
        """
        try:
            detection = await self.analyze_transaction(transaction_data, source_address)

            # Blockera om hotnivå är hög eller kritisk
            should_block = (detection.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL] or
                          detection.confidence_score > 0.8 or
                          detection.blocked)

            logger.info(f"Block decision för {source_address}: {should_block} "
                       f"(threat_level: {detection.threat_level.value}, confidence: {detection.confidence_score})")

            return should_block, detection

        except Exception as e:
            logger.error(f"Block decision misslyckades för {source_address}: {e}")
            return True, None  # Blockera vid fel

    async def add_to_whitelist(self, address: str, added_by: str) -> bool:
        """Lägg till adress i whitelist."""
        try:
            self.whitelist_addresses.add(address)

            # Uppdatera reputation
            if address in self.address_reputation:
                self.address_reputation[address].whitelist = True
                self.address_reputation[address].reputation_score = 0.0

            logger.info(f"Adress {address} tillagd i whitelist av {added_by}")
            return True

        except Exception as e:
            logger.error(f"Whitelist addition misslyckades för {address}: {e}")
            return False

    async def add_to_blacklist(self, address: str, added_by: str, reason: str = "") -> bool:
        """Lägg till adress i blacklist."""
        try:
            self.blacklist_addresses.add(address)

            # Uppdatera reputation
            if address in self.address_reputation:
                self.address_reputation[address].blacklist = True
                self.address_reputation[address].reputation_score = 1.0
                self.address_reputation[address].flagged = True

            logger.warning(f"Adress {address} tillagd i blacklist av {added_by}: {reason}")
            return True

        except Exception as e:
            logger.error(f"Blacklist addition misslyckades för {address}: {e}")
            return False

    async def add_firewall_rule(self, rule: FirewallRule) -> bool:
        """Lägg till brandväggsregel."""
        try:
            self.firewall_rules[rule.rule_id] = rule
            logger.info(f"Firewall rule tillagd: {rule.rule_id}")
            return True

        except Exception as e:
            logger.error(f"Firewall rule addition misslyckades: {e}")
            return False

    async def get_firewall_dashboard(self) -> Dict[str, Any]:
        """Hämta firewall dashboard."""
        try:
            # Beräkna statistik
            total_rules = len(self.firewall_rules)
            active_rules = sum(1 for r in self.firewall_rules.values() if r.enabled)
            total_threats = len(self.threat_detections)

            recent_threats = [t for t in self.threat_detections
                            if datetime.now() - t.detected_at < timedelta(hours=24)]

            # Hot distribution
            threat_distribution = {}
            for threat in self.threat_detections:
                threat_type = threat.threat_type.value
                threat_distribution[threat_type] = threat_distribution.get(threat_type, 0) + 1

            # Mest träffade regler
            rule_hits = {rule_id: rule.hit_count for rule_id, rule in self.firewall_rules.items()}
            top_rules = sorted(rule_hits.items(), key=lambda x: x[1], reverse=True)[:10]

            dashboard = {
                'total_rules': total_rules,
                'active_rules': active_rules,
                'total_threats': total_threats,
                'recent_threats': len(recent_threats),
                'whitelist_count': len(self.whitelist_addresses),
                'blacklist_count': len(self.blacklist_addresses),
                'threat_distribution': threat_distribution,
                'top_rules': top_rules,
                'supported_threat_types': [tt.value for tt in ThreatType],
                'supported_threat_levels': [tl.value for tl in ThreatLevel],
                'timestamp': datetime.now().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Firewall dashboard misslyckades: {e}")
            return {'error': str(e)}

    async def get_address_reputation(self, address: str) -> Dict[str, Any]:
        """Hämta adressreputation."""
        if address not in self.address_reputation:
            self.address_reputation[address] = AddressReputation(address)

        reputation = self.address_reputation[address]

        return {
            'address': address,
            'reputation_score': reputation.reputation_score,
            'flagged': reputation.flagged,
            'whitelist': reputation.whitelist,
            'blacklist': reputation.blacklist,
            'threat_history_count': len(reputation.threat_history),
            'last_activity': reputation.last_activity.isoformat(),
            'recent_threats': [
                {
                    'threat_type': t.threat_type.value,
                    'threat_level': t.threat_level.value,
                    'confidence': t.confidence_score,
                    'detected_at': t.detected_at.isoformat()
                }
                for t in reputation.threat_history[-5:]  # Senaste 5
            ]
        }

    async def mark_false_positive(self, detection_id: str, reviewed_by: str) -> bool:
        """Markera threat som false positive."""
        try:
            for detection in self.threat_detections:
                if detection.detection_id == detection_id:
                    detection.false_positive = True

                    # Minska reputation score för källadress
                    address = detection.source_address
                    if address in self.address_reputation:
                        self.address_reputation[address].reputation_score = max(
                            self.address_reputation[address].reputation_score - 0.2, 0.0
                        )

                    logger.info(f"Threat {detection_id} markerad som false positive av {reviewed_by}")
                    return True

            return False

        except Exception as e:
            logger.error(f"False positive marking misslyckades för {detection_id}: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på firewall."""
        try:
            return {
                'service': 'web3_firewall',
                'status': 'healthy',
                'total_rules': len(self.firewall_rules),
                'active_rules': sum(1 for r in self.firewall_rules.values() if r.enabled),
                'total_threats': len(self.threat_detections),
                'whitelist_count': len(self.whitelist_addresses),
                'blacklist_count': len(self.blacklist_addresses),
                'supported_threat_types': [tt.value for tt in ThreatType],
                'supported_threat_levels': [tl.value for tl in ThreatLevel],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_firewall',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }