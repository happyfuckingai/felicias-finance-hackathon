"""
Web3 Security - Google Cloud KMS för key management och säkerhet.
Transaction data encryption/decryption, secure nonce generation och signature validation.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import secrets
import hashlib
import base64
import json
from dataclasses import dataclass, field
from enum import Enum

from ..core.errors.error_handling import handle_errors, CryptoError, ValidationError, SecurityError

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Säkerhetsnivåer för olika operationer."""
    LOW = "låg"
    MEDIUM = "medium"
    HIGH = "hög"
    CRITICAL = "kritisk"

class KeyType(Enum):
    """Typer av kryptografiska keys."""
    ENCRYPTION = "encryption"
    SIGNING = "signing"
    AUTHENTICATION = "authentication"

@dataclass
class SecurityAuditEvent:
    """Säkerhetsaudit event."""
    timestamp: datetime
    event_type: str
    severity: str
    user_id: str
    resource: str
    action: str
    details: Dict[str, Any]
    ip_address: str = ""
    user_agent: str = ""

@dataclass
class SecureTransaction:
    """Säker transaction med kryptering."""
    transaction_data: Dict[str, Any]
    encrypted_payload: str
    nonce: str
    signature: str
    security_level: SecurityLevel
    timestamp: datetime
    checksum: str = ""

class Web3Security:
    """
    Web3 säkerhetsservice med Google Cloud KMS integration.

    Features:
    - Google Cloud KMS för key management
    - Transaction data encryption/decryption
    - Secure nonce generation och signature validation
    - Integration med befintliga security patterns
    - Audit logging och security monitoring
    - Key rotation och lifecycle management
    """

    def __init__(self, project_id: str, key_ring_id: str, location_id: str = "global"):
        """
        Initiera Web3 Security service.

        Args:
            project_id: Google Cloud project ID
            key_ring_id: KMS key ring ID
            location_id: KMS location
        """
        self.project_id = project_id
        self.key_ring_id = key_ring_id
        self.location_id = location_id

        # Lokal key cache för performance
        self.local_keys = {}
        self.key_cache_ttl = 300  # 5 minuter

        # Security audit log
        self.audit_events = []

        # Rate limiting för security operations
        self.rate_limit_cache = {}
        self.rate_limit_window = 60  # 1 minut
        self.max_operations_per_window = 100

        # Initialize Fernet för lokal kryptering
        self._fernet_keys = {}

        logger.info(f"Web3 Security service initierad för project: {project_id}")

    @handle_errors(service_name="web3_security")
    async def encrypt_transaction_data(self, transaction_data: Dict[str, Any],
                                     security_level: SecurityLevel = SecurityLevel.HIGH) -> SecureTransaction:
        """
        Kryptera transaction data med lämplig säkerhetsnivå.

        Args:
            transaction_data: Transaction data att kryptera
            security_level: Säkerhetsnivå för kryptering

        Returns:
            SecureTransaction med krypterad data
        """
        try:
            # Generera säker nonce
            nonce = await self._generate_secure_nonce()

            # Serialisera transaction data
            serialized_data = json.dumps(transaction_data, sort_keys=True)

            # Beräkna checksum för integritetskontroll
            checksum = self._calculate_checksum(serialized_data + nonce)

            # Välj krypteringsmetod baserat på säkerhetsnivå
            if security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                # Använd Google Cloud KMS för hög säkerhet
                encrypted_payload = await self._encrypt_with_kms(serialized_data, security_level)
            else:
                # Använd lokal kryptering för lägre säkerhetsnivåer
                encrypted_payload = self._encrypt_with_fernet(serialized_data, security_level)

            # Generera digital signatur
            signature = await self._generate_digital_signature(serialized_data, security_level)

            # Skapa secure transaction
            secure_tx = SecureTransaction(
                transaction_data=transaction_data,
                encrypted_payload=encrypted_payload,
                nonce=nonce,
                signature=signature,
                security_level=security_level,
                timestamp=datetime.now(),
                checksum=checksum
            )

            # Logga security event
            await self._log_security_event(
                'transaction_encryption',
                'info',
                'system',  # user_id kommer från context
                'transaction_data',
                'encrypt',
                {
                    'security_level': security_level.value,
                    'data_size': len(serialized_data),
                    'nonce_length': len(nonce),
                    'checksum': checksum[:16] + '...'  # Logga bara början
                }
            )

            logger.info(f"Transaction data krypterad med säkerhetsnivå: {security_level.value}")
            return secure_tx

        except Exception as e:
            logger.error(f"Transaction kryptering misslyckades: {e}")
            raise SecurityError(f"Transaction kryptering misslyckades: {str(e)}", "ENCRYPTION_FAILED")

    @handle_errors(service_name="web3_security")
    async def decrypt_transaction_data(self, secure_transaction: SecureTransaction,
                                     expected_security_level: SecurityLevel = None) -> Dict[str, Any]:
        """
        Dekryptera transaction data och validera integritet.

        Args:
            secure_transaction: SecureTransaction att dekryptera
            expected_security_level: Förväntad säkerhetsnivå

        Returns:
            Dekrypterad transaction data
        """
        try:
            # Validera säkerhetsnivå om specificerad
            if expected_security_level and secure_transaction.security_level != expected_security_level:
                raise ValidationError(
                    f"Säkerhetsnivå mismatch: förväntade {expected_security_level.value}, fick {secure_transaction.security_level.value}",
                    "SECURITY_LEVEL_MISMATCH"
                )

            # Verifiera checksum för integritetskontroll
            expected_checksum = self._calculate_checksum(
                secure_transaction.encrypted_payload + secure_transaction.nonce
            )

            if secure_transaction.checksum != expected_checksum:
                raise ValidationError("Checksum validering misslyckades - data kan vara korrupt",
                                    "CHECKSUM_VALIDATION_FAILED")

            # Välj dekrypteringsmetod baserat på säkerhetsnivå
            if secure_transaction.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                decrypted_data = await self._decrypt_with_kms(secure_transaction.encrypted_payload)
            else:
                decrypted_data = self._decrypt_with_fernet(secure_transaction.encrypted_payload,
                                                         secure_transaction.security_level)

            # Validera digital signatur
            signature_valid = await self._validate_digital_signature(
                decrypted_data, secure_transaction.signature, secure_transaction.security_level
            )

            if not signature_valid:
                raise ValidationError("Digital signatur validering misslyckades",
                                    "SIGNATURE_VALIDATION_FAILED")

            # Parse JSON data
            transaction_data = json.loads(decrypted_data)

            # Logga security event
            await self._log_security_event(
                'transaction_decryption',
                'info',
                'system',
                'transaction_data',
                'decrypt',
                {
                    'security_level': secure_transaction.security_level.value,
                    'data_size': len(decrypted_data),
                    'signature_valid': signature_valid
                }
            )

            logger.info(f"Transaction data dekrypterad och validerad: {secure_transaction.security_level.value}")
            return transaction_data

        except Exception as e:
            logger.error(f"Transaction dekryptering misslyckades: {e}")
            raise SecurityError(f"Transaction dekryptering misslyckades: {str(e)}", "DECRYPTION_FAILED")

    @handle_errors(service_name="web3_security")
    async def generate_secure_nonce(self, length: int = 32) -> str:
        """
        Generera säker nonce för blockchain operationer.

        Args:
            length: Längd på nonce i bytes

        Returns:
            Hex-kodad säker nonce
        """
        try:
            # Kontrollera rate limiting
            await self._check_rate_limit('nonce_generation')

            # Generera kryptografiskt säker nonce
            nonce_bytes = secrets.token_bytes(length)
            nonce_hex = nonce_bytes.hex()

            # Logga security event
            await self._log_security_event(
                'nonce_generation',
                'info',
                'system',
                'nonce',
                'generate',
                {
                    'length': length,
                    'nonce_prefix': nonce_hex[:8] + '...'
                }
            )

            logger.debug(f"Säker nonce genererad: {nonce_hex[:16]}...")
            return nonce_hex

        except Exception as e:
            logger.error(f"Nonce generation misslyckades: {e}")
            raise SecurityError(f"Nonce generation misslyckades: {str(e)}", "NONCE_GENERATION_FAILED")

    @handle_errors(service_name="web3_security")
    async def validate_transaction_signature(self, transaction_data: Dict[str, Any],
                                          signature: str, public_key: str) -> bool:
        """
        Validera digital signatur för transaction.

        Args:
            transaction_data: Transaction data som signerades
            signature: Digital signatur att validera
            public_key: Public key för validering

        Returns:
            True om signatur är giltig
        """
        try:
            # Serialisera transaction data för signing
            serialized_data = json.dumps(transaction_data, sort_keys=True)

            # Validera signatur
            is_valid = await self._validate_signature_with_key(serialized_data, signature, public_key)

            # Logga security event
            await self._log_security_event(
                'signature_validation',
                'info' if is_valid else 'warning',
                'system',
                'transaction_signature',
                'validate',
                {
                    'signature_valid': is_valid,
                    'public_key_hash': hashlib.sha256(public_key.encode()).hexdigest()[:16]
                }
            )

            logger.info(f"Transaction signatur validerad: {'giltig' if is_valid else 'ogiltig'}")
            return is_valid

        except Exception as e:
            logger.error(f"Signature validering misslyckades: {e}")
            return False

    @handle_errors(service_name="web3_security")
    async def create_secure_key_pair(self, key_type: KeyType,
                                   key_name: str) -> Dict[str, Any]:
        """
        Skapa säker key pair via Google Cloud KMS.

        Args:
            key_type: Typ av key att skapa
            key_name: Namn på key

        Returns:
            Key information
        """
        try:
            # Skapa key via Google Cloud KMS
            key_info = await self._create_kms_key(key_type, key_name)

            # Cache key information
            cache_key = f"{key_type.value}_{key_name}"
            self.local_keys[cache_key] = {
                'key_info': key_info,
                'cached_at': datetime.now()
            }

            # Logga security event
            await self._log_security_event(
                'key_creation',
                'info',
                'system',
                f'kms_key_{key_name}',
                'create',
                {
                    'key_type': key_type.value,
                    'key_name': key_name,
                    'key_version': key_info.get('version', 'unknown')
                }
            )

            logger.info(f"Säker key pair skapad: {key_type.value}_{key_name}")
            return key_info

        except Exception as e:
            logger.error(f"Key pair creation misslyckades: {e}")
            raise SecurityError(f"Key pair creation misslyckades: {str(e)}", "KEY_CREATION_FAILED")

    @handle_errors(service_name="web3_security")
    async def rotate_encryption_key(self, key_name: str) -> Dict[str, Any]:
        """
        Rotera krypteringsnyckel för säkerhet.

        Args:
            key_name: Namn på key att rotera

        Returns:
            Rotation information
        """
        try:
            # Skapa ny key version
            rotation_info = await self._rotate_kms_key(key_name)

            # Invalidera cache för gammal key
            cache_keys_to_remove = [k for k in self.local_keys.keys() if key_name in k]
            for cache_key in cache_keys_to_remove:
                del self.local_keys[cache_key]

            # Logga security event
            await self._log_security_event(
                'key_rotation',
                'info',
                'system',
                f'kms_key_{key_name}',
                'rotate',
                {
                    'old_version': rotation_info.get('old_version', 'unknown'),
                    'new_version': rotation_info.get('new_version', 'unknown'),
                    'rotation_reason': 'scheduled'
                }
            )

            logger.info(f"Krypteringsnyckel roterad: {key_name}")
            return rotation_info

        except Exception as e:
            logger.error(f"Key rotation misslyckades: {e}")
            raise SecurityError(f"Key rotation misslyckades: {str(e)}", "KEY_ROTATION_FAILED")

    async def _encrypt_with_kms(self, data: str, security_level: SecurityLevel) -> str:
        """Kryptera data med Google Cloud KMS."""
        try:
            # Simulerad KMS kryptering
            # I produktion skulle detta anropa Google Cloud KMS API

            key_name = f"{security_level.value}_encryption_key"

            # Generera symmetric key för denna session
            if key_name not in self._fernet_keys:
                self._fernet_keys[key_name] = Fernet.generate_key()

            fernet = Fernet(self._fernet_keys[key_name])
            encrypted_data = fernet.encrypt(data.encode()).decode()

            # Lägg till KMS metadata
            kms_metadata = {
                'kms_key': key_name,
                'kms_version': '1',
                'encrypted_at': datetime.now().isoformat(),
                'security_level': security_level.value
            }

            encrypted_payload = json.dumps({
                'data': encrypted_data,
                'kms_metadata': kms_metadata
            })

            return base64.b64encode(encrypted_payload.encode()).decode()

        except Exception as e:
            logger.error(f"KMS kryptering misslyckades: {e}")
            raise

    async def _decrypt_with_kms(self, encrypted_payload: str) -> str:
        """Dekryptera data med Google Cloud KMS."""
        try:
            # Dekoda base64
            decoded_payload = base64.b64decode(encrypted_payload).decode()
            payload_data = json.loads(decoded_payload)

            data = payload_data['data']
            kms_metadata = payload_data['kms_metadata']

            key_name = kms_metadata['kms_key']

            # Hämta rätt key
            if key_name not in self._fernet_keys:
                # I produktion skulle detta hämta från KMS
                # Simulerad key för demo
                self._fernet_keys[key_name] = Fernet.generate_key()

            fernet = Fernet(self._fernet_keys[key_name])
            decrypted_data = fernet.decrypt(data.encode()).decode()

            return decrypted_data

        except Exception as e:
            logger.error(f"KMS dekryptering misslyckades: {e}")
            raise

    def _encrypt_with_fernet(self, data: str, security_level: SecurityLevel) -> str:
        """Kryptera data med lokal Fernet key."""
        try:
            key_name = f"{security_level.value}_local_key"

            if key_name not in self._fernet_keys:
                self._fernet_keys[key_name] = Fernet.generate_key()

            fernet = Fernet(self._fernet_keys[key_name])
            encrypted_data = fernet.encrypt(data.encode())

            return base64.b64encode(encrypted_data).decode()

        except Exception as e:
            logger.error(f"Fernet kryptering misslyckades: {e}")
            raise

    def _decrypt_with_fernet(self, encrypted_data: str, security_level: SecurityLevel) -> str:
        """Dekryptera data med lokal Fernet key."""
        try:
            key_name = f"{security_level.value}_local_key"

            if key_name not in self._fernet_keys:
                raise CryptoError("Krypteringsnyckel hittades inte", "KEY_NOT_FOUND")

            fernet = Fernet(self._fernet_keys[key_name])
            decrypted_data = fernet.decrypt(base64.b64decode(encrypted_data))

            return decrypted_data.decode()

        except Exception as e:
            logger.error(f"Fernet dekryptering misslyckades: {e}")
            raise

    async def _generate_digital_signature(self, data: str, security_level: SecurityLevel) -> str:
        """Generera digital signatur för data."""
        try:
            # Simulerad digital signatur
            # I produktion skulle detta använda Google Cloud KMS för signing

            if security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                # Använd RSA för hög säkerhet
                private_key = await self._get_or_create_signing_key(security_level)
                signature = self._sign_with_rsa(data.encode(), private_key)
            else:
                # Använd HMAC för lägre säkerhet
                signature = self._sign_with_hmac(data, security_level)

            return base64.b64encode(signature).decode()

        except Exception as e:
            logger.error(f"Digital signatur generation misslyckades: {e}")
            raise

    async def _validate_digital_signature(self, data: str, signature: str,
                                        security_level: SecurityLevel) -> bool:
        """Validera digital signatur."""
        try:
            signature_bytes = base64.b64decode(signature)

            if security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                # Validera RSA signatur
                public_key = await self._get_signing_public_key(security_level)
                return self._validate_rsa_signature(data.encode(), signature_bytes, public_key)
            else:
                # Validera HMAC signatur
                return self._validate_hmac_signature(data, signature_bytes, security_level)

        except Exception as e:
            logger.error(f"Digital signatur validering misslyckades: {e}")
            return False

    async def _generate_secure_nonce(self) -> str:
        """Generera säker nonce."""
        try:
            # Använd kryptografiskt säker random
            nonce_bytes = secrets.token_bytes(32)
            return nonce_bytes.hex()

        except Exception as e:
            logger.error(f"Säker nonce generation misslyckades: {e}")
            raise

    def _calculate_checksum(self, data: str) -> str:
        """Beräkna SHA256 checksum för data."""
        try:
            return hashlib.sha256(data.encode()).hexdigest()

        except Exception as e:
            logger.error(f"Checksum beräkning misslyckades: {e}")
            return ""

    async def _check_rate_limit(self, operation: str) -> None:
        """Kontrollera rate limiting för security operations."""
        try:
            current_time = datetime.now()
            window_start = current_time - timedelta(seconds=self.rate_limit_window)

            # Rensa gamla entries
            self.rate_limit_cache = {
                k: v for k, v in self.rate_limit_cache.items()
                if v['timestamp'] > window_start
            }

            # Kontrollera rate limit
            operation_key = f"{operation}_{current_time.strftime('%Y%m%d%H%M')}"

            if operation_key not in self.rate_limit_cache:
                self.rate_limit_cache[operation_key] = {
                    'count': 0,
                    'timestamp': current_time
                }

            self.rate_limit_cache[operation_key]['count'] += 1

            if self.rate_limit_cache[operation_key]['count'] > self.max_operations_per_window:
                raise ValidationError(
                    f"Rate limit överskreds för operation: {operation}",
                    "RATE_LIMIT_EXCEEDED"
                )

        except Exception as e:
            logger.error(f"Rate limit kontroll misslyckades: {e}")
            raise

    async def _log_security_event(self, event_type: str, severity: str, user_id: str,
                                resource: str, action: str, details: Dict[str, Any],
                                ip_address: str = "", user_agent: str = "") -> None:
        """Logga security event."""
        try:
            event = SecurityAuditEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                resource=resource,
                action=action,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )

            self.audit_events.append(event)

            # Logga till security log
            if severity in ['warning', 'critical']:
                logger.warning(f"SECURITY EVENT [{severity.upper()}]: {event_type} - {action} på {resource}")
            else:
                logger.info(f"Security event: {event_type} - {action}")

            # Behåll bara senaste 1000 events
            if len(self.audit_events) > 1000:
                self.audit_events = self.audit_events[-1000:]

        except Exception as e:
            logger.error(f"Security event logging misslyckades: {e}")

    async def _create_kms_key(self, key_type: KeyType, key_name: str) -> Dict[str, Any]:
        """Skapa KMS key."""
        # Simulerad KMS key creation
        return {
            'key_name': f"{key_type.value}_{key_name}",
            'key_type': key_type.value,
            'version': '1',
            'created_at': datetime.now().isoformat(),
            'kms_key_id': f"projects/{self.project_id}/locations/{self.location_id}/keyRings/{self.key_ring_id}/cryptoKeys/{key_name}"
        }

    async def _rotate_kms_key(self, key_name: str) -> Dict[str, Any]:
        """Rotera KMS key."""
        # Simulerad key rotation
        return {
            'key_name': key_name,
            'old_version': '1',
            'new_version': '2',
            'rotated_at': datetime.now().isoformat(),
            'status': 'success'
        }

    async def _get_or_create_signing_key(self, security_level: SecurityLevel):
        """Hämta eller skapa signing key."""
        # Simulerad RSA key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        return private_key

    async def _get_signing_public_key(self, security_level: SecurityLevel):
        """Hämta signing public key."""
        # Simulerad public key
        private_key = await self._get_or_create_signing_key(security_level)
        return private_key.public_key()

    def _sign_with_rsa(self, data: bytes, private_key) -> bytes:
        """Signera data med RSA."""
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    def _validate_rsa_signature(self, data: bytes, signature: bytes, public_key) -> bool:
        """Validera RSA signatur."""
        try:
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def _sign_with_hmac(self, data: str, security_level: SecurityLevel) -> bytes:
        """Signera data med HMAC."""
        import hmac
        key_name = f"{security_level.value}_hmac_key"

        if key_name not in self._fernet_keys:
            self._fernet_keys[key_name] = Fernet.generate_key()

        key = base64.urlsafe_b64decode(self._fernet_keys[key_name])
        return hmac.new(key, data.encode(), hashlib.sha256).digest()

    def _validate_hmac_signature(self, data: str, signature: bytes, security_level: SecurityLevel) -> bool:
        """Validera HMAC signatur."""
        try:
            expected_signature = self._sign_with_hmac(data, security_level)
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False

    async def _validate_signature_with_key(self, data: str, signature: str, public_key: str) -> bool:
        """Validera signatur med given public key."""
        # Simulerad validering
        # I produktion skulle detta validera mot den givna public key
        return True

    async def get_security_audit_log(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Hämta security audit log."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [event for event in self.audit_events if event.timestamp > cutoff_time]

        return [event.__dict__ for event in recent_events]

    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Hämta security dashboard."""
        try:
            # Beräkna security metrics
            total_events = len(self.audit_events)
            critical_events = len([e for e in self.audit_events if e.severity == 'critical'])
            warning_events = len([e for e in self.audit_events if e.severity == 'warning'])

            # Rate limit status
            rate_limit_status = {
                'max_operations_per_window': self.max_operations_per_window,
                'current_window_operations': len(self.rate_limit_cache),
                'rate_limit_exceeded': len([k for k, v in self.rate_limit_cache.items() if v['count'] > self.max_operations_per_window])
            }

            # Key rotation status
            key_rotation_status = await self._get_key_rotation_status()

            # Security recommendations
            recommendations = await self._generate_security_recommendations()

            dashboard_data = {
                'total_audit_events': total_events,
                'critical_events': critical_events,
                'warning_events': warning_events,
                'events_by_type': self._group_events_by_type(),
                'rate_limit_status': rate_limit_status,
                'key_rotation_status': key_rotation_status,
                'security_score': self._calculate_security_score(critical_events, warning_events, total_events),
                'recommendations': recommendations,
                'supported_security_levels': [level.value for level in SecurityLevel],
                'supported_key_types': [key_type.value for key_type in KeyType],
                'timestamp': datetime.now().isoformat()
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Security dashboard misslyckades: {e}")
            return {'error': str(e)}

    def _group_events_by_type(self) -> Dict[str, int]:
        """Gruppera events efter typ."""
        event_types = {}
        for event in self.audit_events:
            event_type = event.event_type
            event_types[event_type] = event_types.get(event_type, 0) + 1
        return event_types

    async def _get_key_rotation_status(self) -> Dict[str, Any]:
        """Hämta key rotation status."""
        # Simulerad key rotation status
        return {
            'last_rotation': datetime.now() - timedelta(days=30),
            'next_rotation_due': datetime.now() + timedelta(days=60),
            'rotation_interval_days': 90,
            'keys_needing_rotation': 2
        }

    async def _generate_security_recommendations(self) -> List[str]:
        """Generera security recommendations."""
        recommendations = []

        # Kontrollera rate limiting
        if len(self.rate_limit_cache) > self.max_operations_per_window * 0.8:
            recommendations.append("Överväg att justera rate limits för hög operation volym")

        # Kontrollera audit log
        if len(self.audit_events) > 800:
            recommendations.append("Granska och arkivera gamla audit events")

        # Generiska säkerhetsrekommendationer
        recommendations.extend([
            "Implementera multi-factor authentication för alla security operations",
            "Regelbundet rotera krypteringsnycklar enligt policy",
            "Övervaka security events för ovanliga mönster",
            "Håll security dependencies uppdaterade"
        ])

        return recommendations

    def _calculate_security_score(self, critical_events: int, warning_events: int, total_events: int) -> float:
        """Beräkna security score."""
        if total_events == 0:
            return 1.0

        # Score baserat på event severity
        critical_penalty = critical_events * 0.3
        warning_penalty = warning_events * 0.1

        score = max(0.0, 1.0 - critical_penalty - warning_penalty)

        return round(score, 2)

    async def clear_audit_log(self, older_than_days: int = 90) -> int:
        """Rensa gamla audit events."""
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
        original_count = len(self.audit_events)

        self.audit_events = [event for event in self.audit_events if event.timestamp > cutoff_time]

        cleared_count = original_count - len(self.audit_events)
        logger.info(f"Rensade {cleared_count} gamla audit events")
        return cleared_count

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på security service."""
        try:
            return {
                'service': 'web3_security',
                'status': 'healthy',
                'audit_events_count': len(self.audit_events),
                'local_keys_count': len(self.local_keys),
                'fernet_keys_count': len(self._fernet_keys),
                'rate_limit_active_operations': len(self.rate_limit_cache),
                'supported_security_levels': [level.value for level in SecurityLevel],
                'supported_key_types': [key_type.value for key_type in KeyType],
                'project_id': self.project_id,
                'key_ring_id': self.key_ring_id,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_security',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }