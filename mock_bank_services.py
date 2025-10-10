#!/usr/bin/env python3
"""
Mock Bank of Anthos Services for Development
Provides minimal API responses to support MCP server integration
"""

import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.serving import make_server
import threading
import time

# Mock data
MOCK_USERS = {
    "testuser": {
        "username": "testuser",
        "password": "password",
        "accounts": ["1234567890"],
        "firstname": "Test",
        "lastname": "User"
    }
}

MOCK_ACCOUNTS = {
    "1234567890": {
        "account_id": "1234567890",
        "balance": 1542067,  # 15420.67 in cents
        "currency": "USD"
    }
}

MOCK_TRANSACTIONS = [
    {
        "timestamp": "2024-01-15T10:30:00Z",
        "fromAccountNum": "1234567890",
        "toAccountNum": "0987654321",
        "amount": -2500,  # -25.00 in cents
        "uuid": str(uuid.uuid4())
    },
    {
        "timestamp": "2024-01-14T15:45:00Z",
        "fromAccountNum": "0987654321",
        "toAccountNum": "1234567890",
        "amount": 50000,  # 500.00 in cents
        "uuid": str(uuid.uuid4())
    }
]

MOCK_CONTACTS = [
    {
        "label": "John Smith",
        "account_num": "0987654321",
        "routing_num": "123456789",
        "is_external": True
    }
]

class MockService:
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.app = Flask(name)
        self.server = None
        self.thread = None
        self.setup_routes()

    def setup_routes(self):
        pass

    def start(self):
        def run_server():
            self.server = make_server('localhost', self.port, self.app, threaded=True)
            print(f"🚀 {self.name} mock service running on port {self.port}")
            self.server.serve_forever()

        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()

# User Service (Port 8081)
class UserService(MockService):
    def setup_routes(self):
        @self.app.route('/login', methods=['GET'])
        def login():
            username = request.args.get('username')
            password = request.args.get('password')

            if username in MOCK_USERS and MOCK_USERS[username]['password'] == password:
                # Generate mock JWT token
                token = f"mock_jwt_token_{username}_{int(time.time())}"
                return jsonify({"token": token})
            else:
                return jsonify({"error": "Invalid credentials"}), 401

        @self.app.route('/users', methods=['POST'])
        def create_user():
            data = request.get_json()
            username = data.get('username')
            if username in MOCK_USERS:
                return jsonify({"error": "User already exists"}), 409

            MOCK_USERS[username] = {
                "username": username,
                "password": data.get('password'),
                "accounts": [str(uuid.uuid4().hex)[:10]],
                "firstname": data.get('firstname', ''),
                "lastname": data.get('lastname', '')
            }
            return jsonify({"message": "User created"}), 201

# Balances Service (Port 8082)
class BalancesService(MockService):
    def setup_routes(self):
        @self.app.route('/balances/<account_id>', methods=['GET'])
        def get_balance(account_id):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')

            # Mock token validation
            if not token.startswith('mock_jwt_token_'):
                return jsonify({"error": "Invalid token"}), 401

            if account_id in MOCK_ACCOUNTS:
                return jsonify(MOCK_ACCOUNTS[account_id])
            else:
                return jsonify({"error": "Account not found"}), 404

# Transactions Service (Port 8080)
class TransactionsService(MockService):
    def setup_routes(self):
        @self.app.route('/transactions', methods=['POST'])
        def create_transaction():
            token = request.headers.get('Authorization', '').replace('Bearer ', '')

            if not token.startswith('mock_jwt_token_'):
                return jsonify({"error": "Invalid token"}), 401

            data = request.get_json()
            # Validate required fields
            required_fields = ['fromAccountNum', 'fromRoutingNum', 'toAccountNum', 'toRoutingNum', 'amount', 'uuid']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400

            # Mock successful transaction
            transaction = {
                "timestamp": datetime.now().isoformat(),
                "fromAccountNum": data['fromAccountNum'],
                "toAccountNum": data['toAccountNum'],
                "amount": data['amount'],
                "uuid": data['uuid']
            }

            MOCK_TRANSACTIONS.insert(0, transaction)

            # Update mock balance
            if data['amount'] < 0 and data['fromAccountNum'] in MOCK_ACCOUNTS:
                MOCK_ACCOUNTS[data['fromAccountNum']]['balance'] += data['amount']
            elif data['amount'] > 0 and data['toAccountNum'] in MOCK_ACCOUNTS:
                MOCK_ACCOUNTS[data['toAccountNum']]['balance'] += data['amount']

            return jsonify({"message": "Transaction processed successfully"})

# History Service (Port 8083)
class HistoryService(MockService):
    def setup_routes(self):
        @self.app.route('/transactions/<account_id>', methods=['GET'])
        def get_transaction_history(account_id):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')

            if not token.startswith('mock_jwt_token_'):
                return jsonify({"error": "Invalid token"}), 401

            # Filter transactions for this account
            account_transactions = [
                tx for tx in MOCK_TRANSACTIONS
                if tx['fromAccountNum'] == account_id or tx['toAccountNum'] == account_id
            ]

            return jsonify(account_transactions)

# Contacts Service (Port 8084)
class ContactsService(MockService):
    def setup_routes(self):
        @self.app.route('/contacts/<username>', methods=['GET'])
        def get_contacts(username):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')

            if not token.startswith('mock_jwt_token_'):
                return jsonify({"error": "Invalid token"}), 401

            return jsonify(MOCK_CONTACTS)

        @self.app.route('/contacts/<username>', methods=['POST'])
        def add_contact(username):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')

            if not token.startswith('mock_jwt_token_'):
                return jsonify({"error": "Invalid token"}), 401

            data = request.get_json()

            # Validate contact data
            required_fields = ['label', 'account_num', 'routing_num', 'is_external']
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400

            MOCK_CONTACTS.append(data)
            return jsonify({"message": "Contact added"}), 201

def start_mock_services():
    """Start all mock Bank of Anthos services"""
    services = [
        TransactionsService("Transactions", 8080),
        UserService("User Service", 8081),
        BalancesService("Balances", 8082),
        HistoryService("History", 8083),
        ContactsService("Contacts", 8084)
    ]

    print("🏦 Starting Mock Bank of Anthos Services...")
    print("These services provide minimal API responses for MCP server integration")

    for service in services:
        service.start()
        time.sleep(0.1)  # Brief delay between startups

    print("\n✅ All mock services started!")
    print("📋 Services running on ports 8080-8084")
    print("🔑 Test credentials: username='testuser', password='password'")
    print("💰 Test account: 1234567890")
    print("\nPress Ctrl+C to stop all services")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping mock services...")
        for service in services:
            service.stop()
        print("✅ All services stopped")

if __name__ == "__main__":
    start_mock_services()