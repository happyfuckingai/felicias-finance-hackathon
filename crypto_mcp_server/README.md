# Crypto MCP Server

En MCP-kompatibel server som ger tillgång till kryptovaluta-funktionalitet genom AI-agenter. Servern bygger på din befintliga crypto-modul och erbjuder verktyg för wallet-hantering, token-deployment och marknadsanalys.

## 🚀 Funktioner

### Wallet Management
- **create_wallet**: Skapa nya Ethereum wallets
- **show_balance**: Visa wallet-saldon på Base testnet
- **send_transaction**: Skicka ETH-transaktioner

### Token Operations
- **deploy_token**: Deploya ERC20 tokens på Base/Polygon testnet

### Market Analysis
- **check_price**: Kolla aktuella token-priser via CoinGecko
- **analyze_token**: Analysera token-prestanda över tid
- **get_trending**: Visa trending tokens
- **generate_signal**: Generera BUY/SELL/HOLD trading-signaler

## 🛠️ Installation

### Förutsättningar
- Python 3.8+
- Tillgång till befintlig crypto-modul i `../crypto/`

### Setup
```bash
# Gå till server-katalogen
cd crypto_mcp_server

# Aktivera virtuell miljö
source devenv/bin/activate

# Alla beroenden är redan installerade
```

## 🔧 Konfiguration

### Roo Code Integration

Servern är konfigurerad för Roo Code som en SSE (Server-Sent Events) server:

```json
{
  "mcpServers": {
    "crypto-server": {
      "url": "http://localhost:8000/sse",
      "headers": {
        "Authorization": "Bearer [din-genererade-api-nyckel]"
      },
      "env": {
        "CRYPTO_PRIVATE_KEY": ""
      }
    }
  }
}
```

### Miljövariabler

För att använda wallet-funktioner, lägg till din private key:

```bash
export CRYPTO_PRIVATE_KEY="din-private-key-här"
```

## 🧪 Testning

### Lokal testning (SSE)

#### Enkelt sätt - Använd startup script
```bash
# Från projektroten
./crypto_mcp_server/start_sse.sh
```

#### Manuellt
```bash
# Aktivera miljö och starta servern
cd crypto_mcp_server
source devenv/bin/activate

# Starta SSE servern
python crypto_mcp_server.py --sse
# Servern startar på http://localhost:8000/sse
```

### Miljövariabler för SSE
```bash
# Ange port och host för SSE-servern (valfritt, standard localhost:8000)
export MCP_HOST="localhost"
export MCP_PORT="8000"
```

### MCP Inspector för SSE
```bash
# Installera MCP inspector globalt
npm install -g @modelcontextprotocol/inspector

# Kör inspector med SSE URL
mcp-inspector --sse http://localhost:8000/sse
```

## 📋 Tillgängliga Verktyg

### create_wallet()
Skapar en ny Ethereum wallet.
```python
# Returnerar:
{
  "address": "0x...",
  "private_key": "0x...",
  "warning": "Spara private key säkert!"
}
```

### show_balance(private_key: str)
Visar saldo för en wallet.
```python
# Kräver: private_key
# Returnerar: ETH-saldo och adress
```

### send_transaction(private_key: str, to_address: str, amount_eth: float)
Skickar ETH från wallet.
```python
# Kräver: private_key, mottagaradress, ETH-belopp
# Returnerar: transaktionshash och gas-användning
```

### deploy_token(private_key: str, name: str, symbol: str, total_supply: int, chain: str = "base")
Deployar ERC20 token.
```python
# Kräver: private_key, token-info, kedja
# Returnerar: contract-adress och deployment-info
```

### check_price(token_id: str)
Hämtar aktuellt pris från CoinGecko.
```python
# Kräver: token_id (t.ex. "bitcoin", "ethereum")
# Returnerar: pris, förändring, volym
```

### analyze_token(token_id: str, days: int = 7)
Analyserar token-prestanda.
```python
# Kräver: token_id, dagar att analysera
# Returnerar: trend, prisändring, volatilitet
```

### get_trending(limit: int = 5)
Visar trending tokens.
```python
# Returnerar: lista med populära tokens
```

### generate_signal(token_id: str)
Genererar trading-signal.
```python
# Kräver: token_id
# Returnerar: BUY/SELL/HOLD med konfidens och analys
```

## 🔒 Säkerhet

### VIKTIGT - Säkerhetsrekommendationer:

1. **Aldrig använd mainnet för testning** - Använd endast testnets
2. **Spara private keys säkert** - Använd aldrig produktions-keys
3. **Verifiera alla transaktioner** - Kontrollera adress och belopp före sändning
4. **Använd minimala behörigheter** - Ge endast nödvändig åtkomst
5. **Logga aktiviteter** - Håll koll på alla transaktioner
6. **Backup av wallets** - Spara seed phrases och private keys säkert

### Risker:
- **Förlorade medel**: Fel adress eller nätverk kan orsaka permanenta förluster
- **Hackade konton**: Exponerade private keys kan leda till stöld
- **Smarta kontraktsfel**: Deployment-fel kan göra tokens obrukbara

## 🏗️ Arkitektur

```
crypto_mcp_server/
├── crypto_managers.py      # Adapter-klasser för MCP
├── crypto_mcp_server.py   # Huvud-MCP server med FastMCP
├── devenv/                 # Virtuell Python-miljö
└── README.md              # Denna fil

../crypto/                  # Befintlig crypto-modul
├── core/
│   ├── contracts.py       # ERC20 deployment
│   ├── analytics.py       # CoinGecko integration
│   └── ...
├── handlers/
│   ├── wallet.py         # Wallet-logik
│   ├── market.py         # Market handlers
│   └── ...
└── ...
```

## 🤖 Användning med AI-agenter

Servern är designad för att användas av AI-agenter för automatiserade uppgifter:

### Exempel på användning:
- **Trading Bots**: Automatisk prisövervakning och signalgenerering
- **Wallet Management**: Automatisk balansering och rebalancing
- **Token Launch**: Automatisk token-deployment och distribution
- **Market Analysis**: Realtidsanalys och rapportering

### Integration:
```python
# AI-agent kan nu använda verktyg som:
await create_wallet()
await check_price("ethereum")
await generate_signal("bitcoin")
```

## 🐛 Felsökning

### Vanliga problem:

1. **"ImportError: cannot import name"**
   - Kontrollera att crypto-modulen finns i `../crypto/`
   - Verifiera Python path

2. **"Connection refused"**
   - Kontrollera RPC URLs i contract-konfigurationen
   - Verifiera nätverksanslutning

3. **"Insufficient funds"**
   - Få testnet ETH från faucets
   - Base: https://goerlifaucet.com/
   - Polygon: https://faucet.polygon.technology/

4. **MCP-anslutningsfel**
   - Kontrollera `.roo/mcp.json` konfiguration
   - Starta Roo Code om efter konfigurationsändringar

## 📞 Support

För frågor eller problem:
1. Kontrollera denna README
2. Verifiera logs från servern
3. Testa enskilda komponenter separat
4. Kontrollera nätverksanslutningar

## 🔄 Uppdateringar

Servern använder din befintliga crypto-modul, så uppdateringar där återspeglas automatiskt här. För MCP-specifika uppdateringar:

```bash
cd crypto_mcp_server
source devenv/bin/activate
pip install --upgrade mcp
```

## 📜 Licens

Samma licens som huvudprojektet.