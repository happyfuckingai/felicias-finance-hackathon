"""
Authentication and Authorization for A2A Protocol

Implements secure authentication mechanisms including OAuth2, JWT, and mutual TLS
for agent-to-agent communication.
"""

import jwt
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple, List
from dataclasses import dataclass
from cryptography import x509
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

from .identity import AgentIdentity, IdentityManager


@dataclass
class AuthToken:
    """Represents an authentication token."""

    token: str
    token_type: str  # "Bearer", "JWT", etc.
    expires_at: datetime
    agent_id: str
    permissions: List[str]
    metadata: Dict[str, Any]

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.utcnow() > self.expires_at

    def has_permission(self, permission: str) -> bool:
        """Check if token has a specific permission."""
        return permission in self.permissions


class JWTAuthenticator:
    """Handles JWT-based authentication for agents."""

    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.algorithm = algorithm

    def create_token(self, agent_id: str, permissions: List[str],
                    expires_in: int = 3600, metadata: Dict[str, Any] = None) -> AuthToken:
        """Create a JWT token for an agent."""

        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=expires_in)

        payload = {
            "iss": "felicia-a2a-auth",
            "sub": agent_id,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "permissions": permissions,
            "metadata": metadata or {}
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        return AuthToken(
            token=token,
            token_type="JWT",
            expires_at=expires_at,
            agent_id=agent_id,
            permissions=permissions,
            metadata=metadata or {}
        )

    def validate_token(self, token: str) -> Optional[AuthToken]:
        """Validate a JWT token and return AuthToken if valid."""

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            expires_at = datetime.fromtimestamp(payload["exp"])

            return AuthToken(
                token=token,
                token_type="JWT",
                expires_at=expires_at,
                agent_id=payload["sub"],
                permissions=payload.get("permissions", []),
                metadata=payload.get("metadata", {})
            )

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def refresh_token(self, token: AuthToken, expires_in: int = 3600) -> AuthToken:
        """Refresh an existing token."""
        if token.is_expired():
            raise ValueError("Cannot refresh expired token")

        return self.create_token(
            agent_id=token.agent_id,
            permissions=token.permissions,
            expires_in=expires_in,
            metadata=token.metadata
        )


class MutualTLSAuthenticator:
    """Handles mutual TLS authentication for agents."""

    def __init__(self, identity_manager: IdentityManager):
        self.identity_manager = identity_manager

    def authenticate_client_cert(self, client_cert: x509.Certificate) -> Optional[str]:
        """Authenticate an agent using its client certificate."""

        # Extract agent ID from certificate subject
        subject = client_cert.subject
        common_name = subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)

        if not common_name:
            return None

        agent_id = common_name[0].value
        if not agent_id.startswith("agent-"):
            return None

        agent_id = agent_id.replace("agent-", "")

        # Verify certificate is not expired
        now = datetime.utcnow()
        if now < client_cert.not_valid_before or now > client_cert.not_valid_after:
            return None

        # Check if agent identity exists
        identity = self.identity_manager.get_identity(agent_id)
        if not identity:
            return None

        # Verify certificate matches stored certificate
        stored_cert = self.identity_manager.get_certificate(agent_id)
        if not stored_cert:
            return None

        # Compare certificate details (simplified check)
        if (client_cert.subject == stored_cert.subject and
            client_cert.public_key().public_numbers() == stored_cert.public_key().public_numbers()):
            return agent_id

        return None


class OAuth2Authenticator:
    """Handles OAuth2-based authentication for agents."""

    def __init__(self, client_id: str, client_secret: str, token_endpoint: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.tokens: Dict[str, AuthToken] = {}

    def request_token(self, agent_id: str, scope: str = "a2a:messaging") -> Optional[AuthToken]:
        """Request an OAuth2 token for an agent."""

        # This is a simplified implementation
        # In a real scenario, you'd make HTTP requests to the OAuth2 server

        import requests

        try:
            response = requests.post(self.token_endpoint, data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": scope
            })

            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)

                return AuthToken(
                    token=access_token,
                    token_type="Bearer",
                    expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                    agent_id=agent_id,
                    permissions=scope.split(),
                    metadata={"token_type": "oauth2"}
                )

        except Exception as e:
            print(f"OAuth2 token request failed: {e}")

        return None

    def validate_token(self, token: str) -> Optional[AuthToken]:
        """Validate an OAuth2 token."""
        # In a real implementation, you'd validate against the OAuth2 server
        # For now, we'll do a simple check
        return self.tokens.get(token)


class AuthenticationManager:
    """Central authentication manager for A2A protocol."""

    def __init__(self, identity_manager: IdentityManager):
        self.identity_manager = identity_manager
        self.jwt_auth = JWTAuthenticator()
        self.mtls_auth = MutualTLSAuthenticator(identity_manager)
        self.active_tokens: Dict[str, AuthToken] = {}

    def authenticate_agent(self, agent_id: str, auth_method: str = "jwt",
                          **kwargs) -> Optional[AuthToken]:
        """Authenticate an agent using the specified method."""

        identity = self.identity_manager.get_identity(agent_id)
        if not identity or not identity.is_valid():
            return None

        if auth_method == "jwt":
            permissions = kwargs.get("permissions", ["a2a:messaging"])
            expires_in = kwargs.get("expires_in", 3600)
            return self.jwt_auth.create_token(agent_id, permissions, expires_in)

        elif auth_method == "oauth2":
            # Would need OAuth2 config
            return None

        elif auth_method == "mtls":
            client_cert = kwargs.get("client_cert")
            if client_cert:
                authenticated_agent = self.mtls_auth.authenticate_client_cert(client_cert)
                if authenticated_agent == agent_id:
                    permissions = kwargs.get("permissions", ["a2a:messaging"])
                    expires_in = kwargs.get("expires_in", 3600)
                    return self.jwt_auth.create_token(agent_id, permissions, expires_in)

        return None

    def validate_authentication(self, token: str, required_permissions: List[str] = None) -> Tuple[bool, Optional[str]]:
        """Validate authentication token and check permissions."""

        # Try JWT validation first
        auth_token = self.jwt_auth.validate_token(token)
        if auth_token and not auth_token.is_expired():
            if required_permissions:
                for perm in required_permissions:
                    if not auth_token.has_permission(perm):
                        return False, f"Missing permission: {perm}"
            return True, auth_token.agent_id

        # Try OAuth2 validation
        auth_token = self.mtls_auth  # This is wrong - need to fix
        # Simplified - in real implementation, would check OAuth2 server

        return False, None

    def authorize_action(self, agent_id: str, action: str, resource: str = None) -> bool:
        """Authorize an agent to perform a specific action."""

        identity = self.identity_manager.get_identity(agent_id)
        if not identity:
            return False

        # Check capabilities based on action
        capability_map = {
            "send_message": "a2a:messaging",
            "receive_message": "a2a:messaging",
            "discover_agents": "a2a:discovery",
            "manage_identity": "a2a:admin"
        }

        required_capability = capability_map.get(action)
        if required_capability:
            return identity.has_capability(required_capability)

        return False

    def create_session_key(self, agent_a: str, agent_b: str) -> str:
        """Create a shared session key for two agents."""

        # Generate a shared secret using agent IDs and timestamp
        combined = f"{agent_a}:{agent_b}:{int(time.time())}"
        session_key = hashlib.sha256(combined.encode()).hexdigest()

        return session_key

    def sign_challenge(self, agent_id: str, challenge: str) -> Optional[str]:
        """Sign a challenge for agent authentication."""

        challenge_bytes = challenge.encode('utf-8')
        return self.identity_manager.sign_data(agent_id, challenge_bytes)

    def verify_challenge_response(self, agent_id: str, challenge: str, signature: str) -> bool:
        """Verify a challenge response signature."""

        challenge_bytes = challenge.encode('utf-8')
        return self.identity_manager.verify_signature(agent_id, challenge_bytes, signature)