#!/bin/bash

# Crypto MCP Server - SSE Startup Script
echo "🚀 Starting Crypto MCP Server (SSE Mode)"
echo "========================================"

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source devenv/bin/activate

# Optional: Set custom host/port
# export MCP_HOST="0.0.0.0"
# export MCP_PORT="8000"

echo "🌐 Starting SSE server on http://localhost:8000/sse"
echo "Press Ctrl+C to stop"
echo ""

# Start the server with SSE mode
python crypto_mcp_server.py --sse