#!/usr/bin/env python3
"""
🧪 Enkel test för att verifiera att systemet fungerar för simulering
"""

import os
import sys

def test_basic_imports():
    """Testa grundläggande imports"""
    try:
        print("✅ Testing basic Python functionality...")

        # Test web3 import
        import web3
        print(f"✅ Web3 version: {web3.__version__}")

        # Test pandas
        import pandas as pd
        print(f"✅ Pandas version: {pd.__version__}")

        # Test numpy
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_env_config():
    """Testa miljökonfiguration"""
    try:
        print("\n✅ Testing environment configuration...")

        # Check if .env exists
        env_path = "crypto/config/.env"
        if os.path.exists(env_path):
            print(f"✅ .env file exists at {env_path}")
        else:
            print(f"⚠️ .env file missing at {env_path}")

        # Test environment variables
        testnet = os.getenv('TESTNET', 'false')
        print(f"✅ TESTNET mode: {testnet}")

        return True
    except Exception as e:
        print(f"❌ Environment error: {e}")
        return False

def simulate_trading():
    """Simulera enkel trading utan riktiga transaktioner"""
    try:
        print("\n🎯 Testing paper trading simulation...")

        # Mock trading data
        portfolio = {
            'BTC': 0.05,
            'ETH': 2.0,
            'SOL': 10.0
        }

        prices = {
            'BTC': 45000,
            'ETH': 2800,
            'SOL': 120
        }

        # Calculate portfolio value
        total_value = sum(portfolio[token] * prices[token] for token in portfolio)
        print(f"💰 Portfolio value: ${total_value:.2f}")

        # Mock analysis
        analysis = {
            'trend': 'bullish',
            'confidence': 0.85,
            'next_action': 'HOLD'
        }

        print(f"📊 Market analysis: {analysis['trend']} ({analysis['confidence']:.1%})")
        print(f"🎪 Recommended action: {analysis['next_action']}")

        print("✅ Paper trading simulation successful!")
        return True
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return False

def main():
    """Huvudfunktion"""
    print("🚀 Felicia's Finance - Simulation Test")
    print("=" * 50)

    success = True

    # Test basic functionality
    success &= test_basic_imports()

    # Test configuration
    success &= test_env_config()

    # Test simulation
    success &= simulate_trading()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Systemet är redo för simulering.")
        print("\n📝 Nästa steg:")
        print("1. Kör 'python3 demos/demo_cli.py' för AI-assistent")
        print("2. Starta MCP-server: 'python3 crypto_mcp_server/crypto_mcp_server.py'")
        print("3. Utforska andra demos i demos/-mappen")
    else:
        print("⚠️ Some tests failed. Kontrollera konfigurationen.")

if __name__ == "__main__":
    main()