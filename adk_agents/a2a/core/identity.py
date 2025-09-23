"""
Agent Identity Management for A2A Protocol

Handles cryptographic identity, keys, certificates, and DID (Decentralized Identifiers)
for secure agent authentication and authorization.
"""

import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID


@dataclass
class AgentIdentity:
    """Represents an agent's cryptographic identity."""

    agent_id: str
    did: str  # Decentralized Identifier
    public_key: str  # PEM-encoded public key
    capabilities: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.agent_id:
            self.agent_id = str(uuid.uuid4())
        if not self.did:
            self.did = f"did:a2a:{self.agent_id}"

    @classmethod
    def create(cls, capabilities: List[str], metadata: Dict[str, Any] = None,
               validity_days: int = 365) -> 'AgentIdentity':
        """Create a new agent identity with cryptographic keys."""

        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Extract public key
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        # Create self-signed certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Felicia's Finance"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"agent-{str(uuid.uuid4())[:8]}"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("agent.felicia.finance"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())

        # Create identity
        identity = cls(
            agent_id="",
            did="",
            public_key=public_key_pem,
            capabilities=capabilities,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=validity_days)
        )

        return identity, private_key, cert

    def to_dict(self) -> Dict[str, Any]:
        """Convert identity to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentIdentity':
        """Create identity from dictionary."""
        # Convert ISO strings back to datetime
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)

    def is_valid(self) -> bool:
        """Check if the identity is still valid (not expired)."""
        if not self.expires_at:
            return True
        return datetime.utcnow() < self.expires_at

    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities

    def sign_data(self, private_key: rsa.RSAPrivateKey, data: bytes) -> str:
        """Sign data with the agent's private key."""
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature.hex()

    def verify_signature(self, data: bytes, signature: str) -> bool:
        """Verify data signature against the agent's public key."""
        try:
            public_key = serialization.load_pem_public_key(
                self.public_key.encode('utf-8'),
                backend=default_backend()
            )

            public_key.verify(
                bytes.fromhex(signature),
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


class IdentityManager:
    """Manages agent identities and cryptographic operations."""

    def __init__(self, storage_path: str = "./identities"):
        self.storage_path = storage_path
        self.identities: Dict[str, AgentIdentity] = {}
        self.private_keys: Dict[str, rsa.RSAPrivateKey] = {}
        self.certificates: Dict[str, x509.Certificate] = {}

        # Create storage directory if it doesn't exist
        import os
        os.makedirs(storage_path, exist_ok=True)

    def create_identity(self, capabilities: List[str], metadata: Dict[str, Any] = None,
                       validity_days: int = 365) -> AgentIdentity:
        """Create and store a new agent identity."""

        identity, private_key, cert = AgentIdentity.create(
            capabilities=capabilities,
            metadata=metadata,
            validity_days=validity_days
        )

        # Store identity and keys
        self.identities[identity.agent_id] = identity
        self.private_keys[identity.agent_id] = private_key
        self.certificates[identity.agent_id] = cert

        # Save to disk
        self._save_identity(identity, private_key, cert)

        return identity

    def load_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        """Load an identity from storage."""
        identity_file = f"{self.storage_path}/{agent_id}_identity.json"
        key_file = f"{self.storage_path}/{agent_id}_private.pem"
        cert_file = f"{self.storage_path}/{agent_id}_cert.pem"

        try:
            # Load identity
            with open(identity_file, 'r') as f:
                identity_data = json.load(f)
            identity = AgentIdentity.from_dict(identity_data)

            # Load private key
            with open(key_file, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )

            # Load certificate
            with open(cert_file, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read(), default_backend())

            # Store in memory
            self.identities[agent_id] = identity
            self.private_keys[agent_id] = private_key
            self.certificates[agent_id] = cert

            return identity

        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading identity {agent_id}: {e}")
            return None

    def get_identity(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get an identity from memory or load from storage."""
        if agent_id in self.identities:
            return self.identities[agent_id]
        return self.load_identity(agent_id)

    def get_private_key(self, agent_id: str) -> Optional[rsa.RSAPrivateKey]:
        """Get the private key for an agent."""
        if agent_id not in self.private_keys:
            self.load_identity(agent_id)
        return self.private_keys.get(agent_id)

    def get_certificate(self, agent_id: str) -> Optional[x509.Certificate]:
        """Get the certificate for an agent."""
        if agent_id not in self.certificates:
            self.load_identity(agent_id)
        return self.certificates.get(agent_id)

    def sign_data(self, agent_id: str, data: bytes) -> Optional[str]:
        """Sign data using the agent's private key."""
        private_key = self.get_private_key(agent_id)
        identity = self.get_identity(agent_id)

        if not private_key or not identity:
            return None

        return identity.sign_data(private_key, data)

    def verify_signature(self, agent_id: str, data: bytes, signature: str) -> bool:
        """Verify data signature for an agent."""
        identity = self.get_identity(agent_id)
        if not identity:
            return False

        return identity.verify_signature(data, signature)

    def _save_identity(self, identity: AgentIdentity, private_key: rsa.RSAPrivateKey,
                      cert: x509.Certificate):
        """Save identity, private key, and certificate to disk."""
        agent_id = identity.agent_id

        # Save identity
        identity_file = f"{self.storage_path}/{agent_id}_identity.json"
        with open(identity_file, 'w') as f:
            json.dump(identity.to_dict(), f, indent=2)

        # Save private key
        key_file = f"{self.storage_path}/{agent_id}_private.pem"
        with open(key_file, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Save certificate
        cert_file = f"{self.storage_path}/{agent_id}_cert.pem"
        with open(cert_file, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))