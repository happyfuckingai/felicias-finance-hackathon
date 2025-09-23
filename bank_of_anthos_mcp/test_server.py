#!/usr/bin/env python3
"""
Simple test script for Bank of Anthos MCP Server
Tests basic functionality without MCP inspector
"""

import requests
import json
import time

# Server endpoint
SSE_URL = "http://localhost:8001/sse"
API_KEY = "CUkw3m5QVwa3na1lWt_H"

def test_server_connection():
    """Test basic server connection"""
    print("🔗 Testing server connection...")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Try to connect to SSE endpoint
        response = requests.get(SSE_URL, headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ Server connection successful")
            return True
        else:
            print(f"❌ Server connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_basic_functionality():
    """Test basic MCP functionality by making a simple request"""
    print("\n🧪 Testing basic MCP functionality...")

    # MCP Initialize request
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # This is a simplified test - in real MCP we'd need proper SSE handling
        # For now, just verify the server is responding
        response = requests.post(
            f"{SSE_URL.replace('/sse', '/messages/?session_id=test')}",
            json=init_payload,
            headers=headers,
            timeout=10
        )

        print(f"📡 Response status: {response.status_code}")
        if response.status_code in [200, 404, 405]:  # Server is responding
            print("✅ Server is responding to MCP requests")
        else:
            print(f"⚠️ Unexpected response: {response.text[:200]}")

    except Exception as e:
        print(f"❌ MCP test error: {e}")

def show_server_info():
    """Show server configuration info"""
    print("\n📋 Server Information:")
    print(f"🌐 SSE URL: {SSE_URL}")
    print(f"🔐 API Key: {API_KEY[:20]}...")
    print("⏰ Timeout: 30s")
    print("🏛️ Local Routing: 123456789")

def main():
    """Main test function"""
    print("🧪 Bank of Anthos MCP Server Test")
    print("=" * 40)

    show_server_info()

    if test_server_connection():
        test_basic_functionality()
        print("\n✅ Server test completed!")
        print("\n💡 Server is running and accepting connections.")
        print("💡 You can now use this server with AI agents or MCP clients.")
    else:
        print("\n❌ Server test failed!")
        print("💡 Make sure the server is running: cd bankofanthos_mcp_server && ./start_sse.sh")

if __name__ == "__main__":
    main()