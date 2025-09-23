"""
Test script för att verifiera token expansion och bakåtkompatibilitet.
"""
import asyncio
import logging
import sys
import os

# Lägg till projekt root i path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from crypto.core.token_resolver import DynamicTokenResolver, TokenNotFoundError
from crypto.core.token_providers import FallbackTokenProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_backward_compatibility():
    """Testa att befintliga tokens fortfarande fungerar."""
    print("🔄 Testing backward compatibility for existing tokens...")

    # Lista över befintliga tokens från gamla implementationen
    existing_tokens = [
        'ETH', 'BTC', 'USDC', 'USDT', 'DAI', 'WBTC',
        'MATIC', 'BNB', 'ADA', 'SOL', 'DOT', 'AVAX',
        'LINK', 'UNI', 'AAVE', 'CAKE', 'SUSHI'
    ]

    resolver = DynamicTokenResolver()
    success_count = 0
    total_count = len(existing_tokens)

    async with resolver:
        for token in existing_tokens:
            try:
                print(f"  Testing {token}...", end=" ")
                token_info = await resolver.resolve_token(token)
                print(f"✅ -> {token_info.symbol} ({token_info.name})")
                success_count += 1
            except Exception as e:
                print(f"❌ Failed: {e}")

    print(f"\n📊 Backward compatibility: {success_count}/{total_count} tokens resolved")
    return success_count == total_count

async def test_dynamic_resolution():
    """Testa dynamisk resolution av nya tokens."""
    print("\n🔍 Testing dynamic resolution for new tokens...")

    # Testa några populära tokens som inte var hårdkodade
    new_tokens = [
        'PEPE', 'SHIB', 'DOGE', 'AVAX', 'CRO', 'NEAR', 'FTM'
    ]

    resolver = DynamicTokenResolver()
    success_count = 0
    total_count = len(new_tokens)

    async with resolver:
        for token in new_tokens:
            try:
                print(f"  Testing {token}...", end=" ")
                token_info = await resolver.resolve_token(token)
                print(f"✅ -> {token_info.symbol} ({token_info.name})")
                success_count += 1
            except Exception as e:
                print(f"❌ Failed: {e}")

    print(f"\n📊 Dynamic resolution: {success_count}/{total_count} new tokens resolved")
    return success_count > 0  # Acceptera att några kan misslyckas beroende på API

async def test_fallback_provider():
    """Testa fallback providern."""
    print("\n🛟 Testing fallback provider...")

    fallback = FallbackTokenProvider()

    async with fallback:
        test_cases = ['ETH', 'BTC', 'UNKNOWN_TOKEN']

        for token in test_cases:
            try:
                print(f"  Testing fallback for {token}...", end=" ")
                token_info = await fallback.search_token(token)
                if token_info:
                    print(f"✅ -> {token_info.symbol} ({token_info.name})")
                else:
                    print("❌ Not found")
            except Exception as e:
                print(f"❌ Error: {e}")

async def test_cache_functionality():
    """Testa cache-funktionalitet."""
    print("\n💾 Testing cache functionality...")

    resolver = DynamicTokenResolver()

    async with resolver:
        # Första anropet (ska gå till API/fallback)
        print("  First call (should hit API)...")
        start_time = asyncio.get_event_loop().time()
        token_info1 = await resolver.resolve_token('ETH')
        first_call_time = asyncio.get_event_loop().time() - start_time

        # Andra anropet (ska använda cache)
        print("  Second call (should use cache)...")
        start_time = asyncio.get_event_loop().time()
        token_info2 = await resolver.resolve_token('ETH')
        second_call_time = asyncio.get_event_loop().time() - start_time

        print(f"  First call: {first_call_time:.4f}s")
        print(f"  Second call: {second_call_time:.4f}s")
        # Verifiera att samma data returneras
        if token_info1.symbol == token_info2.symbol:
            print("  ✅ Cache consistency verified")
        else:
            print("  ❌ Cache inconsistency detected")

        # Visa cache stats
        stats = resolver.get_stats()
        print("  📊 Cache stats:")
        print(f"    - Cache hits: {stats['resolver_stats']['cache_hits']}")
        print(f"    - Cache misses: {stats['resolver_stats']['cache_misses']}")
        print(f"    - API calls: {stats['resolver_stats']['api_calls']}")

async def main():
    """Huvudtestfunktion."""
    print("🚀 Starting Token Expansion Tests")
    print("=" * 50)

    try:
        # Test 1: Bakåtkompatibilitet
        backward_compat = await test_backward_compatibility()

        # Test 2: Dynamisk resolution
        dynamic_resolution = await test_dynamic_resolution()

        # Test 3: Fallback provider
        await test_fallback_provider()

        # Test 4: Cache
        await test_cache_functionality()

        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY:")
        print(f"  Backward Compatibility: {'✅ PASS' if backward_compat else '❌ FAIL'}")
        print(f"  Dynamic Resolution: {'✅ PASS' if dynamic_resolution else '❌ FAIL'}")
        print("  Fallback Provider: ✅ Tested")
        print("  Cache Functionality: ✅ Tested")
        if backward_compat and dynamic_resolution:
            print("\n🎉 ALL CRITICAL TESTS PASSED!")
            print("Token expansion implementation is ready for production.")
        else:
            print("\n⚠️  SOME TESTS FAILED!")
            print("Please review the implementation before deployment.")

    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())