"""
Proof of Concept för HappyOS Crypto - Konkreta exempel.
"""
import asyncio
import os
import sys
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
except ImportError:
    print("python-dotenv not available, using system environment variables")
except Exception as e:
    print(f"Failed to load .env file: {e}")

from ..crypto.core.contracts import ContractDeployer, BASE_TESTNET_CONFIG
from ..crypto.core.analytics import MarketAnalyzer

async def deploy_token_example():
    """
    Exempel: Deploya ERC20 token på Base testnet.
    
    Kräver:
    - CRYPTO_PRIVATE_KEY i environment
    - Testnet ETH för gas
    """
    print("🚀 PROOF OF CONCEPT: Token Deployment på Base Testnet")
    print("=" * 60)
    
    # Kontrollera private key
    private_key = os.getenv('CRYPTO_PRIVATE_KEY')
    if not private_key:
        print("❌ CRYPTO_PRIVATE_KEY saknas i environment")
        print("💡 Skapa wallet först: python -c \"from eth_account import Account; acc = Account.create(); print(f'Address: {acc.address}\\nPrivate Key: {acc.key.hex()}')\"")
        return
    
    try:
        # Skapa deployer
        deployer = ContractDeployer(BASE_TESTNET_CONFIG['rpc_url'], private_key)
        
        print(f"📍 Deployer address: {deployer.account.address}")
        print(f"🔗 Chain: {BASE_TESTNET_CONFIG['name']}")
        print(f"🌐 RPC: {BASE_TESTNET_CONFIG['rpc_url']}")
        print()
        
        # Token parametrar
        token_name = "HappyToken"
        token_symbol = "HAPPY"
        total_supply = 1000000  # 1M tokens
        
        print(f"🪙 Deploying token:")
        print(f"   Name: {token_name}")
        print(f"   Symbol: {token_symbol}")
        print(f"   Supply: {total_supply:,}")
        print()
        
        # Deploya token
        print("⏳ Deploying contract...")
        result = await deployer.deploy_erc20_token(
            name=token_name,
            symbol=token_symbol,
            total_supply=total_supply
        )
        
        if result['success']:
            print("✅ TOKEN DEPLOYMENT LYCKADES!")
            print(f"📍 Contract Address: {result['contract_address']}")
            print(f"🔗 Transaction Hash: {result['transaction_hash']}")
            print(f"⛽ Gas Used: {result['gas_used']:,}")
            print(f"🔍 Explorer: {BASE_TESTNET_CONFIG['explorer']}/address/{result['contract_address']}")
            
            # Testa första transaktion
            print("\n" + "=" * 60)
            print("💸 PROOF OF CONCEPT: Första On-Chain Transaktion")
            print("=" * 60)
            
            # Skicka 0.001 ETH till sig själv (test)
            amount_wei = deployer.w3.to_wei(0.001, 'ether')
            tx_result = await deployer.send_transaction(
                to_address=deployer.account.address,
                amount_wei=amount_wei
            )
            
            if tx_result['success']:
                print("✅ TRANSAKTION LYCKADES!")
                print(f"📤 Till: {tx_result['to_address']}")
                print(f"💰 Belopp: 0.001 ETH")
                print(f"🔗 TX Hash: {tx_result['transaction_hash']}")
                print(f"⛽ Gas Used: {tx_result['gas_used']:,}")
                print(f"🔍 Explorer: {BASE_TESTNET_CONFIG['explorer']}/tx/{tx_result['transaction_hash']}")
            else:
                print(f"❌ Transaktion misslyckades: {tx_result['error']}")
        else:
            print(f"❌ Token deployment misslyckades: {result['error']}")
            
    except Exception as e:
        print(f"❌ Fel: {e}")

async def dex_integration_example():
    """
    Exempel: DEX integration med verkliga priser och quotes.
    """
    print("\n" + "=" * 60)
    print("🔄 PROOF OF CONCEPT: DEX Integration")
    print("=" * 60)

    try:
        from ..crypto.core.dex_integration import RealDexIntegration

        # Försök skapa DEX integration
        web3_provider = None
        private_key = os.getenv('TRADING_PRIVATE_KEY') or os.getenv('CRYPTO_PRIVATE_KEY')

        # Använd Infura som standard för mainnet data (utan trading)
        try:
            from web3 import Web3
            web3_provider = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_PROJECT_ID'))
        except:
            pass

        dex = RealDexIntegration(web3_provider, private_key)

        # Testa DEX data hämtning
        print("⏳ Hämtar DEX data för WETH...")
        dex_data = await dex.get_dex_data("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "ethereum")

        if dex_data['success']:
            print("✅ DEX DATA HÄMTAD!")
            print(f"💰 WETH Pris: ${dex_data['best_price']:.2f}")
            print(f"💧 Total Likviditet: ${dex_data['total_liquidity']/1000000:.1f}M")
            print(f"📊 Total Volym 24h: ${dex_data['total_volume_24h']/1000000:.1f}M")
            print(f"📡 Källa: {dex_data['source']}")

            if 'uniswap_v3' in dex_data['dex_data']:
                uni = dex_data['dex_data']['uniswap_v3']
                if uni.get('available'):
                    print(f"🦄 Uniswap V3: ${uni['price_usd']:.4f} | 💧 ${uni['liquidity_usd']/1000000:.1f}M")
        else:
            print("⚠️ DEX data inte tillgänglig (kontrollera internetanslutning)")

        # Testa swap quote
        print("\n⏳ Hämtar swap quote (100 USDC -> WETH)...")
        quote = await dex.get_swap_quote("usdc", "weth", 100)

        if quote['success']:
            print("✅ SWAP QUOTE HÄMTAD!")
            print(f"💱 100 USDC -> {quote['expected_out']:.4f} WETH")
            print(f"💵 Fee Tier: {quote['fee_tier']}")
            print(f"📊 Price Impact: {quote['price_impact']:.4f}")
            print(f"🏪 DEX: {quote['dex']}")
        else:
            print(f"⚠️ Swap quote inte tillgänglig: {quote.get('error', 'Okänt fel')}")

        # Info om verklig trading
        if dex.uniswap_trader:
            print("\n🟢 VERKLIG TRADING AKTIVERAD!")
            print("⚠️ Du kan nu utföra riktiga swaps på Ethereum mainnet")
            print("💡 För testnet trading, använd TRADING_PRIVATE_KEY med testnet funds")
        else:
            print("\n🟡 SIMULERAD TRADING")
            print("💡 För verklig trading, sätt TRADING_PRIVATE_KEY och WEB3_RPC_URL")

    except Exception as e:
        print(f"❌ Fel vid DEX integration: {e}")

async def market_data_example():
    """
    Exempel: Hämta prisdata från CoinGecko.
    """
    print("\n" + "=" * 60)
    print("📊 PROOF OF CONCEPT: Marknadsdata från CoinGecko")
    print("=" * 60)
    
    try:
        async with MarketAnalyzer() as analyzer:
            # Hämta Bitcoin pris
            print("⏳ Hämtar Bitcoin prisdata...")
            btc_price = await analyzer.get_token_price('bitcoin')
            
            if btc_price['success']:
                print("✅ PRISDATA HÄMTAD!")
                print(f"💰 Bitcoin Pris: ${btc_price['price']:,.2f}")
                print(f"📈 24h Förändring: {btc_price['price_change_24h']:+.2f}%")
                print(f"📊 24h Volym: ${btc_price['volume_24h']:,.0f}")
                print(f"🏦 Market Cap: ${btc_price['market_cap']:,.0f}")
                print(f"🕐 Timestamp: {btc_price['timestamp']}")
            else:
                print(f"❌ Kunde inte hämta prisdata: {btc_price['error']}")
            
            # Hämta trending tokens
            print("\n⏳ Hämtar trending tokens...")
            trending = await analyzer.get_trending_tokens(5)
            
            if trending['success']:
                print("✅ TRENDING TOKENS:")
                for i, token in enumerate(trending['trending_tokens'], 1):
                    print(f"{i}. {token['name']} ({token['symbol']}) - Rank #{token['market_cap_rank']}")
            else:
                print(f"❌ Kunde inte hämta trending: {trending['error']}")
                
            # Analysera Ethereum prestanda
            print("\n⏳ Analyserar Ethereum prestanda (7 dagar)...")
            eth_analysis = await analyzer.analyze_token_performance('ethereum', 7)
            
            if eth_analysis['success']:
                print("✅ ETHEREUM ANALYS:")
                print(f"📊 Trend: {eth_analysis['trend'].title()}")
                print(f"📈 Prisförändring: {eth_analysis['price_change_percent']:+.2f}%")
                print(f"⚡ Volatilitet: {eth_analysis['volatility_percent']:.1f}%")
                print(f"💰 Högsta: ${eth_analysis['max_price']:,.2f}")
                print(f"💸 Lägsta: ${eth_analysis['min_price']:,.2f}")
            else:
                print(f"❌ Kunde inte analysera Ethereum: {eth_analysis['error']}")
                
    except Exception as e:
        print(f"❌ Fel vid marknadsdata: {e}")

async def main():
    """Kör alla proof of concept exempel."""
    print("🎯 HappyOS Crypto - Proof of Concept")
    print("=" * 60)
    print("Detta script demonstrerar:")
    print("1. ERC20 token deployment på Base testnet")
    print("2. Första on-chain transaktion")
    print("3. DEX integration med realtid priser")
    print("4. Marknadsdata från CoinGecko API")
    print("=" * 60)

    # Kör token deployment exempel
    await deploy_token_example()

    # Kör DEX integration exempel
    await dex_integration_example()

    # Kör marknadsdata exempel
    await market_data_example()
    
    print("\n" + "=" * 60)
    print("🎉 PROOF OF CONCEPT KOMPLETT!")
    print("=" * 60)
    print("✅ IMPLEMENTERADE FUNKTIONER:")
    print("1. ERC20 token deployment ✓")
    print("2. On-chain transaktioner ✓")
    print("3. DEX integration med Uniswap V3 ✓")
    print("4. Realtidsprisdata från DexScreener ✓")
    print("5. Marknadsanalys från CoinGecko ✓")
    print("=" * 60)
    print("Nästa steg:")
    print("1. Installera beroenden: pip install -r requirements.txt")
    print("2. Sätt TRADING_PRIVATE_KEY för verklig trading")
    print("3. Konfigurera WEB3_RPC_URL (Infura/Alchemy)")
    print("4. Testa verkliga swaps på testnet först")
    print("5. Integrera med HappyOS skill-systemet")
    print("6. Implementera arbitrage och yield farming")
    print("7. Bygg AI/ML trading-strategier")

if __name__ == "__main__":
    asyncio.run(main())
