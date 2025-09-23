#!/usr/bin/env python3
"""
Enkel test av Crypto MCP Server
"""
import asyncio
import sys
import os

# Lägg till parent directory för import av crypto-modulen
sys.path.append('../..')

from crypto_managers import WalletManager, TokenManager, MarketAnalyzer

async def test_wallet_manager():
    """Testa wallet manager"""
    print("🧪 Testar WalletManager...")

    manager = WalletManager()

    # Testa skapa wallet
    result = await manager.create_wallet()
    print(f"✅ Wallet skapad: {result['success']}")
    print(f"   Adress: {result['address'][:20]}...")

    if result['success']:
        private_key = result['private_key']

        # Testa show_balance (kan misslyckas utan riktig nätverksanslutning)
        balance_result = await manager.show_balance(private_key)
        print(f"✅ Balance check: {balance_result['success']}")

    print()

async def test_market_analyzer():
    """Testa market analyzer"""
    print("🧪 Testar MarketAnalyzer...")

    analyzer = MarketAnalyzer()

    # Testa prischeck
    price_result = await analyzer.check_price("bitcoin")
    print(f"✅ Bitcoin pris: {price_result['success']}")

    if price_result['success']:
        print(f"   Pris: ${price_result['price']:,.2f}")

    # Testa trending
    trending_result = await analyzer.get_trending(3)
    print(f"✅ Trending tokens: {trending_result['success']}")

    if trending_result['success']:
        print(f"   Hittade {len(trending_result['trending_tokens'])} tokens")

    print()

async def main():
    """Huvudtestfunktion"""
    print("🚀 Testar Crypto MCP Server Komponenter\n")

    try:
        await test_wallet_manager()
        await test_market_analyzer()

        print("✅ Alla tester slutförda!")
        print("\n💡 Tips: För full funktionalitet, lägg till CRYPTO_PRIVATE_KEY i .env")

    except Exception as e:
        print(f"❌ Testfel: {e}")
        return 1

    return 0

async def test_sse_server():
    """Testa SSE server startup"""
    print("🧪 Testar SSE Server Startup...")
    print("För att testa SSE-servern:")
    print("1. Öppna en terminal och kör: cd crypto_mcp_server && source devenv/bin/activate && python crypto_mcp_server.py")
    print("2. Servern ska starta på http://localhost:8080/sse")
    print("3. Använd MCP inspector: mcp-inspector --sse http://localhost:8080/sse")
    print("4. Verifiera att verktyg listas korrekt")
    print("\n⚠️  Notera: SSE-servern kräver att den körs i bakgrunden")
    return True

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "sse":
        # Test SSE server
        asyncio.run(test_sse_server())
    else:
        # Test regular components
        exit_code = asyncio.run(main())
        sys.exit(exit_code)