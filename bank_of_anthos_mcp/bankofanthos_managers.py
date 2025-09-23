#!/usr/bin/env python3
"""
Bank of Anthos Manager Classes for MCP Server

This module provides manager classes that handle communication with all
Bank of Anthos backend services, extracted and adapted from the original
frontend.py and contacts.py implementations.
"""

import os
import json
import logging
import requests
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from requests.exceptions import HTTPError, RequestException, Timeout

logger = logging.getLogger(__name__)


class BankOfAnthosManager:
    """
    Manager class for all Bank of Anthos backend services.

    Handles authentication, balances, transactions, contacts, and user management
    by communicating with the respective microservices.
    """

    def __init__(self):
        """Initialize the Bank of Anthos manager with service endpoints."""
        # Service endpoints - these should match the Bank of Anthos deployment
        self.transactions_uri = os.getenv('TRANSACTIONS_API_ADDR', 'http://localhost:8080')
        self.userservice_uri = os.getenv('USERSERVICE_API_ADDR', 'http://localhost:8081')
        self.balances_uri = os.getenv('BALANCES_API_ADDR', 'http://localhost:8082')
        self.history_uri = os.getenv('HISTORY_API_ADDR', 'http://localhost:8083')
        self.contacts_uri = os.getenv('CONTACTS_API_ADDR', 'http://localhost:8084')

        # Configuration
        self.backend_timeout = int(os.getenv('BACKEND_TIMEOUT', '30'))
        self.local_routing = os.getenv('LOCAL_ROUTING_NUM', '123456789')
        self.public_key_path = os.getenv('PUB_KEY_PATH', '/tmp/pubkey.pem')

        # Load public key for token verification if available
        self.public_key = None
        try:
            if os.path.exists(self.public_key_path):
                with open(self.public_key_path, 'r') as f:
                    self.public_key = f.read()
                logger.info("Loaded public key for token verification")
        except Exception as e:
            logger.warning(f"Could not load public key: {e}")

        logger.info("BankOfAnthosManager initialized with service endpoints")

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional requests parameters

        Returns:
            Response object

        Raises:
            RequestException: For request failures
        """
        try:
            # Set default timeout if not provided
            kwargs.setdefault('timeout', self.backend_timeout)

            logger.debug(f"Making {method} request to {url}")
            response = requests.request(method, url, **kwargs)

            # Raise for HTTP errors
            response.raise_for_status()

            return response

        except Timeout:
            logger.error(f"Request timeout for {url}")
            raise RequestException(f"Request timeout for {url}")
        except HTTPError as e:
            logger.error(f"HTTP error for {url}: {e.response.status_code} - {e.response.text}")
            raise
        except RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            raise

    def _get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    # USER SERVICE METHODS

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate user with username and password.

        Args:
            username: User's username
            password: User's password

        Returns:
            Tuple of (success: bool, result: str)
            On success: (True, jwt_token)
            On failure: (False, error_message)
        """
        try:
            login_url = f"{self.userservice_uri}/login"
            params = {'username': username, 'password': password}

            logger.info(f"Authenticating user: {username}")
            response = self._make_request('GET', login_url, params=params)

            token_data = response.json()
            token = token_data.get('token')

            if token:
                logger.info(f"User {username} authenticated successfully")
                return True, token
            else:
                return False, "No token received from authentication service"

        except HTTPError as e:
            if e.response.status_code == 401:
                return False, "Invalid username or password"
            else:
                return False, f"Authentication failed: {e.response.text}"
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, f"Authentication error: {str(e)}"

    def signup_user(self, username: str, password: str, **user_data) -> Tuple[bool, str]:
        """
        Create a new user account.

        Args:
            username: Desired username
            password: Desired password
            **user_data: Additional user data (firstname, lastname, etc.)

        Returns:
            Tuple of (success: bool, result: str)
        """
        try:
            signup_url = f"{self.userservice_uri}/users"
            data = {
                'username': username,
                'password': password,
                **user_data
            }

            logger.info(f"Creating new user: {username}")
            response = self._make_request('POST', signup_url, json=data)

            if response.status_code == 201:
                logger.info(f"User {username} created successfully")
                return True, "User account created successfully"
            else:
                return False, f"Unexpected response: {response.status_code}"

        except HTTPError as e:
            if e.response.status_code == 409:
                return False, "Username already exists"
            else:
                return False, f"Signup failed: {e.response.text}"
        except Exception as e:
            logger.error(f"Signup error: {e}")
            return False, f"Signup error: {str(e)}"

    # BALANCE SERVICE METHODS

    def get_account_balance(self, account_id: str, token: str) -> Tuple[bool, str]:
        """
        Get account balance for a specific account.

        Args:
            account_id: Account ID to get balance for
            token: JWT authentication token

        Returns:
            Tuple of (success: bool, result: str)
            On success: (True, balance_data_json)
            On failure: (False, error_message)
        """
        try:
            balance_url = f"{self.balances_uri}/balances/{account_id}"
            headers = self._get_auth_headers(token)

            logger.info(f"Getting balance for account: {account_id}")
            response = self._make_request('GET', balance_url, headers=headers)

            balance_data = response.json()
            logger.info(f"Balance retrieved for account {account_id}")
            return True, json.dumps(balance_data)

        except HTTPError as e:
            if e.response.status_code == 401:
                return False, "Authentication failed"
            elif e.response.status_code == 404:
                return False, "Account not found"
            else:
                return False, f"Balance retrieval failed: {e.response.text}"
        except Exception as e:
            logger.error(f"Balance retrieval error: {e}")
            return False, f"Balance retrieval error: {str(e)}"

    # TRANSACTION SERVICE METHODS

    def get_transaction_history(self, account_id: str, token: str) -> Tuple[bool, str]:
        """
        Get transaction history for an account.

        Args:
            account_id: Account ID to get history for
            token: JWT authentication token

        Returns:
            Tuple of (success: bool, result: str)
            On success: (True, transactions_json)
            On failure: (False, error_message)
        """
        try:
            history_url = f"{self.history_uri}/transactions/{account_id}"
            headers = self._get_auth_headers(token)

            logger.info(f"Getting transaction history for account: {account_id}")
            response = self._make_request('GET', history_url, headers=headers)

            transactions = response.json()
            logger.info(f"Retrieved {len(transactions)} transactions for account {account_id}")
            return True, json.dumps(transactions)

        except HTTPError as e:
            if e.response.status_code == 401:
                return False, "Authentication failed"
            elif e.response.status_code == 404:
                return False, "Account not found"
            else:
                return False, f"History retrieval failed: {e.response.text}"
        except Exception as e:
            logger.error(f"History retrieval error: {e}")
            return False, f"History retrieval error: {str(e)}"

    def execute_fiat_transfer(self, transfer_data: Dict[str, Any], token: str) -> Tuple[bool, str]:
        """
        Execute a fiat transfer (payment).

        Args:
            transfer_data: Transfer details including:
                - fromAccountNum: Source account
                - fromRoutingNum: Source routing number
                - toAccountNum: Destination account
                - toRoutingNum: Destination routing number
                - amount: Amount in cents
                - uuid: Unique transaction ID
            token: JWT authentication token

        Returns:
            Tuple of (success: bool, result: str)
        """
        try:
            # Validate required fields
            required_fields = ['fromAccountNum', 'fromRoutingNum', 'toAccountNum',
                             'toRoutingNum', 'amount', 'uuid']
            for field in required_fields:
                if field not in transfer_data:
                    return False, f"Missing required field: {field}"

            # Convert amount to cents if it's a decimal
            if isinstance(transfer_data['amount'], (int, float)):
                transfer_data['amount'] = int(Decimal(str(transfer_data['amount'])) * 100)

            transactions_url = f"{self.transactions_uri}/transactions"
            headers = self._get_auth_headers(token)

            logger.info(f"Executing transfer from {transfer_data['fromAccountNum']} to {transfer_data['toAccountNum']}")
            response = self._make_request('POST', transactions_url, headers=headers, json=transfer_data)

            logger.info("Transfer executed successfully")
            return True, "Transfer executed successfully"

        except HTTPError as e:
            if e.response.status_code == 401:
                return False, "Authentication failed"
            elif e.response.status_code == 400:
                return False, f"Transfer validation failed: {e.response.text}"
            else:
                return False, f"Transfer failed: {e.response.text}"
        except Exception as e:
            logger.error(f"Transfer error: {e}")
            return False, f"Transfer error: {str(e)}"

    def execute_deposit(self, deposit_data: Dict[str, Any], token: str) -> Tuple[bool, str]:
        """
        Execute a deposit from external account.

        Args:
            deposit_data: Deposit details including:
                - fromAccountNum: External account
                - fromRoutingNum: External routing number
                - toAccountNum: Bank of Anthos account
                - amount: Amount in cents
                - uuid: Unique transaction ID
            token: JWT authentication token

        Returns:
            Tuple of (success: bool, result: str)
        """
        try:
            # Set destination routing to local routing
            deposit_data['toRoutingNum'] = self.local_routing

            # Validate routing numbers
            if deposit_data.get('fromRoutingNum') == self.local_routing:
                return False, "Cannot deposit from internal account"

            # Convert amount to cents if needed
            if isinstance(deposit_data['amount'], (int, float)):
                deposit_data['amount'] = int(Decimal(str(deposit_data['amount'])) * 100)

            return self.execute_fiat_transfer(deposit_data, token)

        except Exception as e:
            logger.error(f"Deposit error: {e}")
            return False, f"Deposit error: {str(e)}"

    # CONTACTS SERVICE METHODS

    def get_contacts(self, username: str, token: str) -> Tuple[bool, str]:
        """
        Get contacts list for a user.

        Args:
            username: Username to get contacts for
            token: JWT authentication token

        Returns:
            Tuple of (success: bool, result: str)
            On success: (True, contacts_json)
            On failure: (False, error_message)
        """
        try:
            contacts_url = f"{self.contacts_uri}/contacts/{username}"
            headers = self._get_auth_headers(token)

            logger.info(f"Getting contacts for user: {username}")
            response = self._make_request('GET', contacts_url, headers=headers)

            contacts = response.json()
            logger.info(f"Retrieved {len(contacts)} contacts for user {username}")
            return True, json.dumps(contacts)

        except HTTPError as e:
            if e.response.status_code == 401:
                return False, "Authentication failed"
            elif e.response.status_code == 404:
                return False, "User not found"
            else:
                return False, f"Contacts retrieval failed: {e.response.text}"
        except Exception as e:
            logger.error(f"Contacts retrieval error: {e}")
            return False, f"Contacts retrieval error: {str(e)}"

    def add_contact(self, username: str, contact_data: Dict[str, Any], token: str) -> Tuple[bool, str]:
        """
        Add a new contact for a user.

        Args:
            username: Username to add contact for
            contact_data: Contact details including:
                - label: Contact label
                - account_num: Account number (10 digits)
                - routing_num: Routing number (9 digits)
                - is_external: Whether this is an external account
            token: JWT authentication token

        Returns:
            Tuple of (success: bool, result: str)
        """
        try:
            # Validate required fields
            required_fields = ['label', 'account_num', 'routing_num', 'is_external']
            for field in required_fields:
                if field not in contact_data:
                    return False, f"Missing required field: {field}"

            # Validate account number (10 digits)
            account_num = contact_data['account_num']
            if not isinstance(account_num, str) or not account_num.isdigit() or len(account_num) != 10:
                return False, "Account number must be exactly 10 digits"

            # Validate routing number (9 digits)
            routing_num = contact_data['routing_num']
            if not isinstance(routing_num, str) or not routing_num.isdigit() or len(routing_num) != 9:
                return False, "Routing number must be exactly 9 digits"

            # Don't allow external accounts with local routing
            if contact_data['is_external'] and routing_num == self.local_routing:
                return False, "External accounts cannot use local routing number"

            # Validate label
            label = contact_data['label']
            if not isinstance(label, str) or len(label) < 1 or len(label) > 30:
                return False, "Label must be 1-30 characters"
            if not label[0].isalnum() or not all(c.isalnum() or c == ' ' for c in label):
                return False, "Label must start with letter/number and contain only letters, numbers, and spaces"

            contact_payload = {
                'label': label,
                'account_num': account_num,
                'routing_num': routing_num,
                'is_external': contact_data['is_external']
            }

            contacts_url = f"{self.contacts_uri}/contacts/{username}"
            headers = self._get_auth_headers(token)

            logger.info(f"Adding contact '{label}' for user: {username}")
            response = self._make_request('POST', contacts_url, headers=headers, json=contact_payload)

            if response.status_code == 201:
                logger.info(f"Contact '{label}' added successfully for user {username}")
                return True, "Contact added successfully"
            else:
                return False, f"Unexpected response: {response.status_code}"

        except HTTPError as e:
            if e.response.status_code == 401:
                return False, "Authentication failed"
            elif e.response.status_code == 400:
                return False, f"Validation failed: {e.response.text}"
            elif e.response.status_code == 409:
                return False, f"Contact already exists: {e.response.text}"
            else:
                return False, f"Add contact failed: {e.response.text}"
        except Exception as e:
            logger.error(f"Add contact error: {e}")
            return False, f"Add contact error: {str(e)}"

    def validate_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate JWT token and extract claims.

        Args:
            token: JWT token to validate

        Returns:
            Tuple of (is_valid: bool, claims: dict or None)
        """
        if not self.public_key:
            logger.warning("No public key available for token validation")
            return False, None

        try:
            import jwt
            claims = jwt.decode(token, key=self.public_key, algorithms=['RS256'])
            return True, claims
        except jwt.exceptions.InvalidTokenError as e:
            logger.warning(f"Token validation failed: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None


# Global manager instance
bankofanthos_manager = BankOfAnthosManager()