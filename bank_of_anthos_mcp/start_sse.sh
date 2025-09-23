#!/bin/bash

# Bank of Anthos MCP Server Startup Script
# This script starts the Bank of Anthos MCP server in SSE mode

echo "🚀 Starting Bank of Anthos MCP Server (SSE Mode)"

# Set default environment variables if not set
export BANKOFANTHOS_MCP_TRANSPORT=${BANKOFANTHOS_MCP_TRANSPORT:-"sse"}
export BANKOFANTHOS_MCP_HOST=${BANKOFANTHOS_MCP_HOST:-"localhost"}
export BANKOFANTHOS_MCP_PORT=${BANKOFANTHOS_MCP_PORT:-"8001"}

# Bank of Anthos service endpoints (adjust as needed)
export TRANSACTIONS_API_ADDR=${TRANSACTIONS_API_ADDR:-"http://localhost:8080"}
export USERSERVICE_API_ADDR=${USERSERVICE_API_ADDR:-"http://localhost:8081"}
export BALANCES_API_ADDR=${BALANCES_API_ADDR:-"http://localhost:8082"}
export HISTORY_API_ADDR=${HISTORY_API_ADDR:-"http://localhost:8083"}
export CONTACTS_API_ADDR=${CONTACTS_API_ADDR:-"http://localhost:8084"}

# Bank configuration
export LOCAL_ROUTING_NUM=${LOCAL_ROUTING_NUM:-"123456789"}
export BACKEND_TIMEOUT=${BACKEND_TIMEOUT:-"30"}

echo "📋 Configuration:"
echo "  🌐 Host: $BANKOFANTHOS_MCP_HOST"
echo "  🔌 Port: $BANKOFANTHOS_MCP_PORT"
echo "  🏦 Transactions: $TRANSACTIONS_API_ADDR"
echo "  👤 User Service: $USERSERVICE_API_ADDR"
echo "  💰 Balances: $BALANCES_API_ADDR"
echo "  📋 History: $HISTORY_API_ADDR"
echo "  📞 Contacts: $CONTACTS_API_ADDR"
echo "  🏛️  Local Routing: $LOCAL_ROUTING_NUM"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
echo "📥 Installing requirements..."
pip install -q -r requirements.txt

# Generate API key if not set
if [ -z "$BANKOFANTHOS_MCP_API_KEY" ]; then
    export BANKOFANTHOS_MCP_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "🔑 Generated API Key: ${BANKOFANTHOS_MCP_API_KEY:0:20}..."
    echo "💡 Set BANKOFANTHOS_MCP_API_KEY environment variable to persist this key"
fi

echo ""
echo "🎯 Starting SSE server..."
echo "📡 Endpoint: http://$BANKOFANTHOS_MCP_HOST:$BANKOFANTHOS_MCP_PORT/sse"
echo "🔐 API Key: ${BANKOFANTHOS_MCP_API_KEY:0:16}..."
echo ""
echo "Press Ctrl+C to stop the server"
echo "═══════════════════════════════════════════════════════════════"

# Start the server
python bankofanthos_mcp_server.py --sse