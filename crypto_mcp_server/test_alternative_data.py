#!/usr/bin/env python3
"""
Test script för alternativa datakällor i crypto-hanteringssystemet.
Testar DexScreener, CoinMarketCap och andra fallback-datakällor.
"""
import asyncio
import logging
from alternative_data_providers import (
    DexScreenerProvider,
    CoinMarketCapProvider,
    NewsProvider,
    AlternativeDataManager
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dexscreener():
    """Testa DexScreener provider"""
    print("🧪 Testar DexScreener Provider...")
    provider = DexScreenerProvider()

    # Testa Bitcoin
    result = await provider.get_token_price("bitcoin")
    print(f"Bitcoin pris från DexScreener: {result}")

    # Testa Ethereum
    result = await provider.get_token_price("ethereum")
    print(f"Ethereum pris från DexScreener: {result}")

    # Testa trending
    trending = await provider.get_trending_tokens(3)
    print(f"Trending tokens från DexScreener: {trending}")

async def test_coinmarketcap():
    """Testa CoinMarketCap provider"""
    print("\n🧪 Testar CoinMarketCap Provider...")
    provider = CoinMarketCapProvider()

    # Testa Bitcoin
    result = await provider.get_token_price("bitcoin")
    print(f"Bitcoin pris från CMC: {result}")

    # Testa Ethereum
    result = await provider.get_token_price("ethereum")
    print(f"Ethereum pris från CMC: {result}")

async def test_news_providers():
    """Testa nyhets-providers"""
    print("\n🧪 Testar News Providers...")
    provider = NewsProvider()

    # Testa allmänna crypto-nyheter
    news = await provider.get_crypto_news("cryptocurrency", 3)
    print(f"Crypto-nyheter: {len(news.get('news', []))} artiklar hittade")
    if news.get('news'):
        print(f"Första nyheten: {news['news'][0]['title'][:50]}...")

async def test_alternative_data_manager():
    """Testa den kompletta AlternativeDataManager"""
    print("\n🧪 Testar AlternativeDataManager...")

    manager = AlternativeDataManager()

    # Testa pris-fallback för Bitcoin
    print("Testar pris-fallback för Bitcoin...")
    result = await manager.get_token_price_fallback("bitcoin")
    print(f"Bitcoin fallback-resultat: {result}")

    # Testa pris-fallback för Ethereum
    print("Testar pris-fallback för Ethereum...")
    result = await manager.get_token_price_fallback("ethereum")
    print(f"Ethereum fallback-resultat: {result}")

    # Testa pris-fallback för okänd token
    print("Testar pris-fallback för okänd token...")
    result = await manager.get_token_price_fallback("nonexistenttoken123")
    print(f"Okänd token fallback-resultat: {result}")

    # Testa trending-fallback
    print("Testar trending-fallback...")
    trending = await manager.get_trending_fallback(3)
    print(f"Trending fallback-resultat: {trending}")

async def main():
    """Huvudfunktion för att köra alla tester"""
    print("🚀 Startar test av alternativa datakällor för crypto-systemet\n")

    try:
        await test_dexscreener()
    except Exception as e:
        print(f"❌ DexScreener test misslyckades: {e}")

    try:
        await test_coinmarketcap()
    except Exception as e:
        print(f"❌ CoinMarketCap test misslyckades: {e}")

    try:
        await test_news_providers()
    except Exception as e:
        print(f"❌ News provider test misslyckades: {e}")

    try:
        await test_alternative_data_manager()
    except Exception as e:
        print(f"❌ AlternativeDataManager test misslyckades: {e}")

    print("\n✅ Alla tester slutförda!")

if __name__ == "__main__":
    asyncio.run(main())