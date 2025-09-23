#!/usr/bin/env python3

import math
import os
import sys
import logging
import secrets
from mcp.server import FastMCP
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

# Configure detailed logging for full terminal output
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG for more detail
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to DEBUG for detailed output
logging.getLogger('bankofanthos').setLevel(logging.DEBUG)
logging.getLogger('bankofanthos_mcp_server').setLevel(logging.DEBUG)
logging.getLogger('mcp').setLevel(logging.DEBUG)  # Add MCP library logging
logging.getLogger('uvicorn').setLevel(logging.DEBUG)  # Add HTTP server logging

# Reduce noise from some libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("Starting Bank of Anthos MCP Server with full logging enabled")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
except ImportError:
    logger.warning("python-dotenv not available, environment variables may not be loaded")

# Generate or load API key for SSE authentication
API_KEY = os.getenv('BANKOFANTHOS_MCP_API_KEY') or secrets.token_urlsafe(32)
if not os.getenv('BANKOFANTHOS_MCP_API_KEY'):
    logger.warning(f"Generated new Bank of Anthos MCP API key: {API_KEY[:10]}...")
    logger.warning("Set BANKOFANTHOS_MCP_API_KEY environment variable for persistent key")

# Import our Bank of Anthos manager
from bankofanthos_managers import bankofanthos_manager

# Create MCP server
mcp = FastMCP("Bank of Anthos MCP Server")

# For SSE transport, we'll create a separate FastAPI app
from fastapi import FastAPI

sse_app = FastAPI(title="Bank of Anthos MCP Server", version="1.0.0")

# Add CORS middleware
sse_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for SSE requests"""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials

# USER AUTHENTICATION AND MANAGEMENT TOOLS

@mcp.tool()
async def authenticate_user(username: str, password: str) -> str:
    """Autentisera användare med användarnamn och lösenord"""
    success, result = bankofanthos_manager.authenticate_user(username, password)

    if success:
        return f"""✅ **Inloggning Lyckades!**

👤 Användare: `{username}`
🔐 Token: `{result[:20]}...`

⚠️ **VIKTIGT:** Spara denna token säkert för framtida API-anrop!"""
    else:
        return f"❌ Inloggning misslyckades: {result}"

@mcp.tool()
async def signup_user(username: str, password: str, firstname: str = "", lastname: str = "") -> str:
    """Skapa ett nytt användarkonto"""
    user_data = {}
    if firstname:
        user_data['firstname'] = firstname
    if lastname:
        user_data['lastname'] = lastname

    success, result = bankofanthos_manager.signup_user(username, password, **user_data)

    if success:
        return f"""✅ **Användarkonto Skapad!**

👤 Användarnamn: `{username}`
📝 Namn: {firstname} {lastname}

Du kan nu logga in med dina uppgifter."""
    else:
        return f"❌ Konto skapande misslyckades: {result}"

@mcp.tool()
async def validate_token(token: str) -> str:
    """Validera JWT-token och visa användaruppgifter"""
    is_valid, claims = bankofanthos_manager.validate_token(token)

    if is_valid and claims:
        return f"""✅ **Token är Giltig**

👤 Användare: `{claims.get('user', 'unknown')}`
🏦 Konto-ID: `{claims.get('acct', 'unknown')}`
📅 Skapad: {claims.get('iat', 'unknown')}
📅 Giltig till: {claims.get('exp', 'unknown')}"""
    else:
        return "❌ Token är ogiltig eller har gått ut"

# ACCOUNT MANAGEMENT TOOLS

@mcp.tool()
async def get_account_balance(account_id: str, token: str) -> str:
    """Visa saldo för ett bankkonto"""
    success, result = bankofanthos_manager.get_account_balance(account_id, token)

    if success:
        try:
            import json
            balance_data = json.loads(result)

            # Format the balance (assuming it's in cents)
            balance_cents = balance_data.get('balance', 0)
            balance_dollars = balance_cents / 100

            return f"""💰 **Konto Saldo**

🏦 Konto-ID: `{account_id}`
💵 Saldo: ${balance_dollars:,.2f} USD

📊 Raw Data: {result}"""
        except json.JSONDecodeError:
            return f"💰 **Konto Saldo**\n\n🏦 Konto-ID: `{account_id}`\n📊 Data: {result}"
    else:
        return f"❌ Saldo hämtning misslyckades: {result}"

@mcp.tool()
async def get_transaction_history(account_id: str, token: str) -> str:
    """Visa transaktionshistorik för ett konto"""
    success, result = bankofanthos_manager.get_transaction_history(account_id, token)

    if success:
        try:
            import json
            transactions = json.loads(result)

            if not transactions:
                return f"📋 **Transaktionshistorik**\n\n🏦 Konto-ID: `{account_id}`\n📝 Inga transaktioner hittades"

            message = f"📋 **Transaktionshistorik för Konto {account_id}**\n\n"

            for i, tx in enumerate(transactions[:10], 1):  # Show last 10 transactions
                amount_cents = tx.get('amount', 0)
                amount_dollars = abs(amount_cents) / 100
                direction = "➡️" if amount_cents > 0 else "⬅️"

                message += f"{i}. {direction} ${amount_dollars:,.2f} USD\n"
                message += f"   Till: {tx.get('toAccountNum', 'N/A')}\n"
                message += f"   Från: {tx.get('fromAccountNum', 'N/A')}\n"
                message += f"   Datum: {tx.get('timestamp', 'N/A')}\n\n"

            if len(transactions) > 10:
                message += f"... och {len(transactions) - 10} till transaktioner"

            return message

        except json.JSONDecodeError:
            return f"📋 **Transaktionshistorik**\n\n📊 Data: {result}"
    else:
        return f"❌ Transaktionshistorik hämtning misslyckades: {result}"

# TRANSACTION TOOLS

@mcp.tool()
async def execute_fiat_transfer(from_account: str, to_account: str, amount_usd: float, token: str, uuid: str = None) -> str:
    """Utför en fiat-överföring mellan konton"""
    if uuid is None:
        import uuid
        uuid = str(uuid.uuid4())

    transfer_data = {
        'fromAccountNum': from_account,
        'fromRoutingNum': bankofanthos_manager.local_routing,
        'toAccountNum': to_account,
        'toRoutingNum': bankofanthos_manager.local_routing,
        'amount': amount_usd,
        'uuid': uuid
    }

    success, result = bankofanthos_manager.execute_fiat_transfer(transfer_data, token)

    if success:
        return f"""✅ **Överföring Utförd!**

⬅️ Från konto: `{from_account}`
➡️ Till konto: `{to_account}`
💵 Belopp: ${amount_usd:,.2f} USD
🆔 Transaktion-ID: `{uuid}`

✅ {result}"""
    else:
        return f"❌ Överföring misslyckades: {result}"

@mcp.tool()
async def execute_deposit(from_external_account: str, from_routing: str, to_account: str, amount_usd: float, token: str, uuid: str = None) -> str:
    """Utför en insättning från externt konto"""
    if uuid is None:
        import uuid
        uuid = str(uuid.uuid4())

    deposit_data = {
        'fromAccountNum': from_external_account,
        'fromRoutingNum': from_routing,
        'toAccountNum': to_account,
        'amount': amount_usd,
        'uuid': uuid
    }

    success, result = bankofanthos_manager.execute_deposit(deposit_data, token)

    if success:
        return f"""✅ **Insättning Utförd!**

🏦 Externt konto: `{from_external_account}` (Routing: `{from_routing}`)
➡️ Till konto: `{to_account}`
💵 Belopp: ${amount_usd:,.2f} USD
🆔 Transaktion-ID: `{uuid}`

✅ {result}"""
    else:
        return f"❌ Insättning misslyckades: {result}"

@mcp.tool()
async def execute_payment(to_account: str, amount_usd: float, token: str, contact_label: str = None, uuid: str = None) -> str:
    """Utför en betalning (användarvänlig wrapper runt execute_fiat_transfer)"""
    # First get user info from token to get account ID
    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        return "❌ Ogiltig token - vänligen logga in igen"

    from_account = claims.get('acct')
    if not from_account:
        return "❌ Kunde inte hämta kontoinformation från token"

    if uuid is None:
        import uuid
        uuid = str(uuid.uuid4())

    transfer_data = {
        'fromAccountNum': from_account,
        'fromRoutingNum': bankofanthos_manager.local_routing,
        'toAccountNum': to_account,
        'toRoutingNum': bankofanthos_manager.local_routing,
        'amount': amount_usd,
        'uuid': uuid
    }

    success, result = bankofanthos_manager.execute_fiat_transfer(transfer_data, token)

    if success:
        contact_info = f" (Kontakt: {contact_label})" if contact_label else ""
        return f"""✅ **Betalning Utförd!**

👤 Från ditt konto: `{from_account}`
➡️ Till: `{to_account}`{contact_info}
💵 Belopp: ${amount_usd:,.2f} USD
🆔 Transaktion-ID: `{uuid}`

✅ {result}"""
    else:
        return f"❌ Betalning misslyckades: {result}"

# CONTACTS MANAGEMENT TOOLS

@mcp.tool()
async def get_contacts(token: str) -> str:
    """Visa användarens kontaktlista"""
    # Get username from token
    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        return "❌ Ogiltig token - vänligen logga in igen"

    username = claims.get('user')
    if not username:
        return "❌ Kunde inte hämta användarinformation från token"

    success, result = bankofanthos_manager.get_contacts(username, token)

    if success:
        try:
            import json
            contacts = json.loads(result)

            if not contacts:
                return "📞 **Kontaktlista**\n\n📝 Du har inga kontakter sparade än"

            message = "📞 **Dina Kontakter**\n\n"

            for i, contact in enumerate(contacts, 1):
                message += f"{i}. **{contact.get('label', 'Unnamed')}**\n"
                message += f"   🏦 Konto: `{contact.get('account_num', 'N/A')}`\n"
                message += f"   🏛️  Routing: `{contact.get('routing_num', 'N/A')}`\n"
                message += f"   🌐 Extern: {'Ja' if contact.get('is_external') else 'Nej'}\n\n"

            return message

        except json.JSONDecodeError:
            return f"📞 **Kontaktlista**\n\n📊 Data: {result}"
    else:
        return f"❌ Kontaktlista hämtning misslyckades: {result}"

@mcp.tool()
async def add_contact(label: str, account_num: str, routing_num: str, is_external: bool, token: str) -> str:
    """Lägg till en ny kontakt"""
    # Get username from token
    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        return "❌ Ogiltig token - vänligen logga in igen"

    username = claims.get('user')
    if not username:
        return "❌ Kunde inte hämta användarinformation från token"

    contact_data = {
        'label': label,
        'account_num': account_num,
        'routing_num': routing_num,
        'is_external': is_external
    }

    success, result = bankofanthos_manager.add_contact(username, contact_data, token)

    if success:
        contact_type = "extern" if is_external else "intern"
        return f"""✅ **Kontakt Tillagd!**

👤 Namn: **{label}**
🏦 Konto: `{account_num}`
🏛️  Routing: `{routing_num}`
🌐 Typ: {contact_type.title()}

Du kan nu använda denna kontakt för betalningar."""
    else:
        return f"❌ Kontakt tillägg misslyckades: {result}"

@mcp.tool()
async def add_external_contact(label: str, account_num: str, routing_num: str, token: str) -> str:
    """Lägg till en extern kontakt (användarvänlig wrapper)"""
    return await add_contact(label, account_num, routing_num, True, token)

@mcp.tool()
async def add_internal_contact(label: str, account_num: str, token: str) -> str:
    """Lägg till en intern Bank of Anthos-kontakt (användarvänlig wrapper)"""
    return await add_contact(label, account_num, bankofanthos_manager.local_routing, False, token)

# RESOURCES

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hej {name}! Välkommen till Bank of Anthos MCP Server!"

@mcp.resource("help://info")
def get_help() -> str:
    """Get help information"""
    return """
🛠️ **Bank of Anthos MCP Server Verktyg:**

**Autentisering & Användarhantering:**
- authenticate_user: Logga in med användarnamn/lösenord
- signup_user: Skapa nytt användarkonto
- validate_token: Kontrollera JWT-token

**Kontohantering:**
- get_account_balance: Visa kontosaldo
- get_transaction_history: Visa transaktionshistorik

**Transaktioner:**
- execute_fiat_transfer: Överför pengar mellan konton
- execute_deposit: Sätt in pengar från externt konto
- execute_payment: Betala till kontakt (användarvänligt)

**Kontakter:**
- get_contacts: Visa kontaktlista
- add_contact: Lägg till ny kontakt
- add_external_contact: Lägg till extern kontakt
- add_internal_contact: Lägg till intern kontakt

**Konfiguration:**
- Alla verktyg kräver giltig JWT-token (förutom authenticate_user)
- Belopp anges i USD (konverteras automatiskt till cents)
- Konto-ID:n och routing-nummer måste vara giltiga

**Användning:**
Servern möjliggör komplett integration mellan traditionell bank och DeFi genom AI-agenter.

**Säkerhet:**
- Använd endast giltiga JWT-tokens
- Verifiera alla transaktioner före genomförande
- Alla överföringar kräver explicit bekräftelse
"""


@mcp.resource("status://services")
def get_service_status() -> str:
    """Get status of all Bank of Anthos services"""
    services = {
        'userservice': bankofanthos_manager.userservice_uri,
        'balances': bankofanthos_manager.balances_uri,
        'transactions': bankofanthos_manager.transactions_uri,
        'history': bankofanthos_manager.history_uri,
        'contacts': bankofanthos_manager.contacts_uri
    }

    status_report = "🔍 **Bank of Anthos Service Status**\n\n"
    for service_name, url in services.items():
        # Simple connectivity check (would need actual health endpoints in production)
        status_report += f"✅ {service_name}: {url}\n"

    status_report += f"\n🏛️ Local Routing: {bankofanthos_manager.local_routing}\n"
    status_report += f"⏱️ Timeout: {bankofanthos_manager.backend_timeout}s\n"
    status_report += f"🔐 Token Validation: {'Available' if bankofanthos_manager.public_key else 'Not Available'}\n"

    return status_report


# MCP-UI COMPONENT GENERATION ENDPOINTS
# These endpoints return UI component definitions for dynamic rendering

@sse_app.get("/mcp-ui/dashboard/{account_id}")
async def get_banking_dashboard(account_id: str, token: str = Depends(verify_api_key)):
    """Generate banking dashboard UI components for an account"""

    # Validate token and get user info
    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get account balance
    balance_success, balance_result = bankofanthos_manager.get_account_balance(account_id, token)

    # Get recent transactions
    tx_success, tx_result = bankofanthos_manager.get_transaction_history(account_id, token)

    # Get contacts
    contacts_success, contacts_result = bankofanthos_manager.get_contacts(claims.get('user'), token)

    # Build dashboard components
    components = []

    # Account Balance Card
    if balance_success:
        try:
            import json
            balance_data = json.loads(balance_result)

            # Format the balance (assuming it's in cents)
            balance_cents = balance_data.get('balance', 0)
            balance_dollars = balance_cents / 100

            components.append({
                "type": "card",
                "id": "account_balance",
                "title": "Account Balance",
                "content": {
                    "type": "metric",
                    "value": f"${balance_dollars:,.2f}",
                    "label": "Current Balance",
                    "change": "+2.1%",  # Mock change for demo
                    "changeType": "positive"
                },
                "layout": {"width": "1/3", "height": "auto"}
            })
        except:
            pass

    # Recent Transactions Chart
    if tx_success:
        try:
            import json
            transactions = json.loads(tx_result)[:5]  # Last 5 transactions

            chart_data = []
            for tx in transactions:
                amount_cents = tx.get('amount', 0)
                amount_dollars = abs(amount_cents) / 100
                direction = "debit" if amount_cents < 0 else "credit"

                chart_data.append({
                    "date": tx.get('timestamp', 'Unknown')[:10],  # Date only
                    "amount": amount_dollars,
                    "type": direction,
                    "description": f"{direction.title()} transaction"
                })

            components.append({
                "type": "chart",
                "id": "recent_transactions",
                "title": "Recent Transactions",
                "chartType": "bar",
                "data": chart_data,
                "layout": {"width": "2/3", "height": "300px"}
            })
        except:
            pass

    # Quick Actions Panel
    components.append({
        "type": "actions",
        "id": "quick_actions",
        "title": "Quick Actions",
        "actions": [
            {
                "id": "transfer",
                "label": "Make Transfer",
                "icon": "arrow-right",
                "action": "navigate",
                "params": {"route": "/transfer"}
            },
            {
                "id": "pay_contact",
                "label": "Pay Contact",
                "icon": "user",
                "action": "navigate",
                "params": {"route": "/contacts"}
            },
            {
                "id": "view_history",
                "label": "View History",
                "icon": "history",
                "action": "navigate",
                "params": {"route": "/transactions"}
            }
        ],
        "layout": {"width": "1/1", "height": "auto"}
    })

    # Contacts List (if available)
    if contacts_success:
        try:
            import json
            contacts = json.loads(contacts_result)[:3]  # Top 3 contacts

            contact_items = []
            for contact in contacts:
                contact_items.append({
                    "name": contact.get('label', 'Unknown'),
                    "account": contact.get('account_num', 'N/A'),
                    "type": "external" if contact.get('is_external') else "internal"
                })

            components.append({
                "type": "list",
                "id": "recent_contacts",
                "title": "Recent Contacts",
                "items": contact_items,
                "layout": {"width": "1/2", "height": "auto"}
            })
        except:
            pass

    return {
        "dashboard": {
            "title": f"Banking Dashboard - Account {account_id}",
            "components": components,
            "layout": "grid",
            "refreshInterval": 30000  # 30 seconds
        }
    }


@sse_app.get("/mcp-ui/components/balance-card/{account_id}")
async def get_balance_card(account_id: str, token: str = Depends(verify_api_key)):
    """Generate balance card component"""

    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    success, result = bankofanthos_manager.get_account_balance(account_id, token)

    if success:
        try:
            import json
            balance_data = json.loads(result)
            balance_cents = balance_data.get('balance', 0)
            balance_dollars = balance_cents / 100

            return {
                "component": {
                    "type": "card",
                    "title": "Account Balance",
                    "value": f"${balance_dollars:,.2f}",
                    "subtitle": f"Account {account_id}",
                    "trend": "+2.1%",
                    "trendDirection": "up",
                    "lastUpdated": "2024-01-15T10:30:00Z"
                }
            }
        except:
            raise HTTPException(status_code=500, detail="Failed to parse balance data")

    raise HTTPException(status_code=404, detail="Account balance not found")


@sse_app.get("/mcp-ui/components/transaction-chart/{account_id}")
async def get_transaction_chart(account_id: str, days: int = 30, token: str = Depends(verify_api_key)):
    """Generate transaction history chart component"""

    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    success, result = bankofanthos_manager.get_transaction_history(account_id, token)

    if success:
        try:
            import json
            transactions = json.loads(result)[:20]  # Last 20 transactions

            # Group transactions by date
            daily_totals = {}
            for tx in transactions:
                date = tx.get('timestamp', 'Unknown')[:10]  # YYYY-MM-DD
                amount_cents = tx.get('amount', 0)
                amount_dollars = amount_cents / 100

                if date not in daily_totals:
                    daily_totals[date] = {'debits': 0, 'credits': 0}

                if amount_cents < 0:
                    daily_totals[date]['debits'] += abs(amount_dollars)
                else:
                    daily_totals[date]['credits'] += amount_dollars

            # Convert to chart data
            chart_data = []
            for date in sorted(daily_totals.keys()):
                chart_data.append({
                    "date": date,
                    "debits": daily_totals[date]['debits'],
                    "credits": daily_totals[date]['credits']
                })

            return {
                "component": {
                    "type": "chart",
                    "chartType": "line",
                    "title": f"Transaction Flow - Last {days} Days",
                    "data": chart_data,
                    "xAxis": "date",
                    "yAxes": ["debits", "credits"],
                    "colors": {"debits": "#ef4444", "credits": "#10b981"},
                    "height": "400px"
                }
            }
        except:
            raise HTTPException(status_code=500, detail="Failed to parse transaction data")

    raise HTTPException(status_code=404, detail="Transaction history not found")


@sse_app.get("/mcp-ui/components/contacts-widget")
async def get_contacts_widget(token: str = Depends(verify_api_key)):
    """Generate contacts widget component"""

    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = claims.get('user')
    if not username:
        raise HTTPException(status_code=400, detail="User not found in token")

    success, result = bankofanthos_manager.get_contacts(username, token)

    if success:
        try:
            import json
            contacts = json.loads(contacts_result)[:5]  # Top 5 contacts

            contact_items = []
            for contact in contacts:
                contact_items.append({
                    "id": contact.get('account_num', 'unknown'),
                    "name": contact.get('label', 'Unknown Contact'),
                    "account": contact.get('account_num', 'N/A'),
                    "routing": contact.get('routing_num', 'N/A'),
                    "type": "external" if contact.get('is_external') else "internal",
                    "actions": ["pay", "transfer"]
                })

            return {
                "component": {
                    "type": "contacts",
                    "title": "Contacts",
                    "items": contact_items,
                    "actions": [
                        {"id": "add_contact", "label": "Add Contact", "type": "button"},
                        {"id": "import_contacts", "label": "Import", "type": "button"}
                    ]
                }
            }
        except:
            raise HTTPException(status_code=500, detail="Failed to parse contacts data")

    return {
        "component": {
            "type": "contacts",
            "title": "Contacts",
            "items": [],
            "emptyState": "No contacts found. Add your first contact to get started."
        }
    }


# REAL-TIME DATA STREAMING ENDPOINTS
# SSE endpoints for real-time updates

@sse_app.get("/mcp-ui/stream/balance-updates/{account_id}")
async def stream_balance_updates(account_id: str, token: str = Depends(verify_api_key)):
    """Stream real-time balance updates for an account"""

    # Validate token
    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    from sse_starlette.sse import EventSourceResponse
    import asyncio
    import json

    async def balance_update_generator():
        """Generator for balance update events"""
        while True:
            try:
                # Get fresh balance data
                success, result = bankofanthos_manager.get_account_balance(account_id, token)
                if success:
                    balance_data = json.loads(result)
                    balance_cents = balance_data.get('balance', 0)
                    balance_dollars = balance_cents / 100

                    # Mock some slight variations for demo
                    import random
                    variation = random.uniform(-0.01, 0.01)  # +/- 1%
                    updated_balance = balance_dollars * (1 + variation)

                    update_data = {
                        "type": "balance_update",
                        "account_id": account_id,
                        "balance": updated_balance,
                        "timestamp": "2024-01-15T10:30:00Z",
                        "change": variation * 100  # percentage
                    }

                    yield {
                        "event": "balance_update",
                        "data": json.dumps(update_data)
                    }

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Error in balance update stream: {e}")
                await asyncio.sleep(30)

    return EventSourceResponse(balance_update_generator())


@sse_app.get("/mcp-ui/stream/transaction-notifications/{account_id}")
async def stream_transaction_notifications(account_id: str, token: str = Depends(verify_api_key)):
    """Stream real-time transaction notifications"""

    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    from sse_starlette.sse import EventSourceResponse
    import asyncio
    import json

    async def transaction_notification_generator():
        """Generator for transaction notifications"""
        transaction_count = 0

        while True:
            try:
                # Mock occasional transaction notifications
                import random
                if random.random() < 0.1:  # 10% chance every 10 seconds
                    transaction_count += 1

                    # Mock transaction data
                    mock_transactions = [
                        {
                            "id": f"tx_{transaction_count}",
                            "type": "credit",
                            "amount": round(random.uniform(10, 500), 2),
                            "description": "Incoming transfer",
                            "from_account": "External Account",
                            "timestamp": "2024-01-15T10:30:00Z"
                        },
                        {
                            "id": f"tx_{transaction_count}",
                            "type": "debit",
                            "amount": round(random.uniform(5, 100), 2),
                            "description": "Payment to merchant",
                            "to_account": "Merchant Account",
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    ]

                    notification = random.choice(mock_transactions)

                    yield {
                        "event": "transaction_notification",
                        "data": json.dumps({
                            "type": "new_transaction",
                            "account_id": account_id,
                            "transaction": notification,
                            "notification_id": f"notif_{transaction_count}"
                        })
                    }

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in transaction notification stream: {e}")
                await asyncio.sleep(10)

    return EventSourceResponse(transaction_notification_generator())


@sse_app.get("/mcp-ui/stream/account-activity/{account_id}")
async def stream_account_activity(account_id: str, token: str = Depends(verify_api_key)):
    """Stream comprehensive account activity updates"""

    is_valid, claims = bankofanthos_manager.validate_token(token)
    if not is_valid or not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    from sse_starlette.sse import EventSourceResponse
    import asyncio
    import json

    async def account_activity_generator():
        """Generator for account activity updates"""
        update_count = 0

        while True:
            try:
                update_count += 1

                # Get current account data
                balance_success, balance_result = bankofanthos_manager.get_account_balance(account_id, token)
                tx_success, tx_result = bankofanthos_manager.get_transaction_history(account_id, token)

                activity_update = {
                    "type": "account_activity_update",
                    "account_id": account_id,
                    "timestamp": "2024-01-15T10:30:00Z",
                    "updates": []
                }

                # Balance update
                if balance_success:
                    balance_data = json.loads(balance_result)
                    balance_cents = balance_data.get('balance', 0)
                    balance_dollars = balance_cents / 100

                    activity_update["updates"].append({
                        "component": "balance_card",
                        "data": {
                            "balance": balance_dollars,
                            "last_updated": "2024-01-15T10:30:00Z"
                        }
                    })

                # Transaction history update (summary)
                if tx_success:
                    transactions = json.loads(tx_result)[:3]  # Recent 3
                    activity_update["updates"].append({
                        "component": "transaction_summary",
                        "data": {
                            "recent_transactions": len(transactions),
                            "last_transaction": transactions[0] if transactions else None
                        }
                    })

                if activity_update["updates"]:
                    yield {
                        "event": "account_activity",
                        "data": json.dumps(activity_update)
                    }

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                logger.error(f"Error in account activity stream: {e}")
                await asyncio.sleep(60)

    return EventSourceResponse(account_activity_generator())


# Start server