"""
Enkelt test för token expansion - testar endast fallback och grundläggande funktionalitet.
"""
import asyncio
import sys
import os

# Lägg till projekt root i path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def test_fallback_only():
    """Testa endast fallback providern utan externa dependencies."""
    print("🧪 Testing Token Expansion (Fallback Only)")
    print("=" * 50)

    try:
        # Importera endast det som behövs för fallback
        from crypto.core.token_providers import FallbackTokenProvider

        fallback = FallbackTokenProvider()

        # Testa kända tokens från fallback
        test_tokens = [
            'ETH', 'BTC', 'USDC', 'USDT', 'DAI', 'WBTC',
            'MATIC', 'BNB', 'ADA', 'SOL', 'LINK', 'UNI',
            'HAPPY'  # Vårt custom token
        ]

        success_count = 0
        total_count = len(test_tokens)

        async with fallback:
            print("Testing fallback resolution:")
            for token in test_tokens:
                try:
                    print(f"  {token}...", end=" ")
                    token_info = await fallback.search_token(token)
                    if token_info:
                        print(f"✅ -> {token_info.symbol} ({token_info.name})")
                        success_count += 1
                    else:
                        print("❌ Not found")
                except Exception as e:
                    print(f"❌ Error: {e}")

        print(f"\n📊 Fallback Test Results: {success_count}/{total_count} tokens resolved")

        # Testa okänd token
        print("\nTesting unknown token:")
        try:
            print("  UNKNOWN_TOKEN...", end=" ")
            result = await fallback.search_token('UNKNOWN_TOKEN')
            if result:
                print(f"✅ -> {result.symbol} ({result.name})")
            else:
                print("❌ Not found (expected)")
        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "=" * 50)
        if success_count >= 12:  # Majoriteten av våra test-tokens
            print("✅ FALLBACK TEST PASSED")
            print("Token expansion foundation is working!")
            return True
        else:
            print("❌ FALLBACK TEST FAILED")
            print("Too many tokens failed to resolve")
            return False

    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_basic_imports():
    """Testa att våra nya moduler kan importeras."""
    print("\n🔧 Testing Basic Imports:")
    print("-" * 30)

    try:
        # Testa cache-systemet
        from crypto.core.token_cache import TokenCache
        cache = TokenCache()
        print("✅ TokenCache imported successfully")

        # Testa providers
        from crypto.core.token_providers import TokenInfo, FallbackTokenProvider
        print("✅ Token providers imported successfully")

        # Testa resolver (utan att initiera externa providers)
        try:
            from crypto.core.token_resolver import DynamicTokenResolver, TokenNotFoundError
            print("✅ Token resolver imported successfully")
        except ImportError as e:
            print(f"⚠️  Token resolver import failed (expected due to missing aiohttp): {e}")

        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

async def main():
    """Huvudtestfunktion."""
    print("🚀 Simple Token Expansion Test")
    print("=" * 50)

    # Test 1: Importer
    import_success = await test_basic_imports()

    # Test 2: Fallback
    fallback_success = await test_fallback_only()

    print("\n" + "=" * 50)
    print("📋 SIMPLE TEST SUMMARY:")
    print(f"  Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"  Fallback: {'✅ PASS' if fallback_success else '❌ FAIL'}")

    if import_success and fallback_success:
        print("\n🎉 SIMPLE TESTS PASSED!")
        print("Token expansion implementation has solid foundation.")
        print("Full integration test can be performed after installing dependencies.")
    else:
        print("\n⚠️  SOME SIMPLE TESTS FAILED!")
        print("Please review the implementation.")

if __name__ == "__main__":
    asyncio.run(main())