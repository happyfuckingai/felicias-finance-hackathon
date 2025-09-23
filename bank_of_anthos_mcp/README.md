# Bank of Anthos MCP Server

En MCP-kompatibel server som ger tillgång till Bank of Anthos finansiella tjänster genom AI-agenter. Servern bygger på den officiella Bank of Anthos-implementationen och erbjuder verktyg för autentisering, kontohantering, transaktioner och kontakter.

## 🚀 Funktioner

### Autentisering & Användarhantering
- **authenticate_user**: Logga in användare och få JWT-token
- **signup_user**: Skapa nya användarkonton
- **validate_token**: Verifiera JWT-tokens

### Kontohantering
- **get_account_balance**: Visa kontosaldo
- **get_transaction_history**: Visa transaktionshistorik

### Transaktioner
- **execute_fiat_transfer**: Överför pengar mellan konton
- **execute_deposit**: Sätt in pengar från externa konton
- **execute_payment**: Betala till kontakter (användarvänligt)

### Kontakthantering
- **get_contacts**: Visa användarens kontaktlista
- **add_contact**: Lägg till nya kontakter
- **add_external_contact**: Lägg till externa kontakter
- **add_internal_contact**: Lägg till interna kontakter

## 🛠️ Installation

### Förutsättningar
- Python 3.8+
- Tillgång till Bank of Anthos backend-tjänster
- Tillgång till kryptosystemet (för integration)

### Setup
```bash
# Gå till server-katalogen
cd bankofanthos_mcp_server

# Aktivera virtuell miljö (skapa om nödvändigt)
python3 -m venv venv
source venv/bin/activate

# Installera beroenden
pip install -r requirements.txt
```

## 🔧 Konfiguration

### Miljövariabler
Konfigurera följande miljövariabler för att ansluta till Bank of Anthos tjänster:

```bash
# Bank of Anthos tjänster
export TRANSACTIONS_API_ADDR="http://localhost:8080"
export USERSERVICE_API_ADDR="http://localhost:8081"
export BALANCES_API_ADDR="http://localhost:8082"
export HISTORY_API_ADDR="http://localhost:8083"
export CONTACTS_API_ADDR="http://localhost:8084"

# Bank konfiguration
export LOCAL_ROUTING_NUM="123456789"
export BACKEND_TIMEOUT="30"

# Säkerhet (valfritt för token-validering)
export PUB_KEY_PATH="/path/to/public/key.pem"

# MCP server konfiguration
export BANKOFANTHOS_MCP_API_KEY="din-api-nyckel-här"
export BANKOFANTHOS_MCP_HOST="localhost"
export BANKOFANTHOS_MCP_PORT="8001"
```

### Roo Code Integration

Servern är konfigurerad för Roo Code som en SSE-server:

```json
{
  "mcpServers": {
    "bankofanthos-server": {
      "url": "http://localhost:8001/sse",
      "headers": {
        "Authorization": "Bearer [din-genererade-api-nyckel]"
      }
    }
  }
}
```

## 🧪 Testning

### Lokal testning (SSE)

#### Enkelt sätt - Använd startup script
```bash
# Från projektroten
./bankofanthos_mcp_server/start_sse.sh
```

#### Manuellt
```bash
# Aktivera miljö och starta servern
cd bankofanthos_mcp_server
source venv/bin/activate

# Starta SSE servern
python bankofanthos_mcp_server.py --sse
# Servern startar på http://localhost:8001/sse
```

### MCP Inspector för SSE
```bash
# Installera MCP inspector globalt
npm install -g @modelcontextprotocol/inspector

# Kör inspector med SSE URL
mcp-inspector --sse http://localhost:8001/sse
```

## 📋 Tillgängliga Verktyg

### authenticate_user(username: str, password: str)
Loggar in användare och returnerar JWT-token.
```python
# Returnerar:
✅ Inloggning lyckades med token eller
❌ Felmeddelande
```

### get_account_balance(account_id: str, token: str)
Hämtar saldo för ett konto.
```python
# Kräver: account_id, JWT token
# Returnerar: Formaterat saldo i USD
```

### execute_payment(to_account: str, amount_usd: float, token: str)
Utför en betalning (hämtar användarens konto från token).
```python
# Kräver: mottagarkonto, belopp i USD, JWT token
# Returnerar: Bekräftelse eller fel
```

### get_contacts(token: str)
Visar användarens kontaktlista.
```python
# Kräver: JWT token
# Returnerar: Formaterad lista med kontakter
```

### add_contact(label: str, account_num: str, routing_num: str, is_external: bool, token: str)
Lägger till en ny kontakt.
```python
# Kräver: etikett, kontonummer, routing-nummer, extern-flagga, JWT token
# Returnerar: Bekräftelse eller valideringsfel
```

## 🔒 Säkerhet

### VIKTIGT - Säkerhetsrekommendationer:

1. **Använd giltiga JWT-tokens**: Alla verktyg kräver autentisering
2. **Validera alla transaktioner**: Kontrollera konto och belopp före överföring
3. **Skydda API-nycklar**: Dela inte SSE API-nycklar
4. **Använd HTTPS**: I produktion, använd HTTPS för alla anslutningar
5. **Logga aktiviteter**: Alla transaktioner loggas för granskning

### Risker:
- **Ogiltiga tokens**: Kan leda till åtkomst nekad
- **Felaktiga överföringar**: Kan orsaka oavsiktliga transaktioner
- **Exponerade nycklar**: Kan ge obehörig åtkomst

## 🏗️ Arkitektur

```
bankofanthos_mcp_server/
├── bankofanthos_managers.py      # Core manager för Bank of Anthos API:er
├── bankofanthos_mcp_server.py   # MCP server med alla verktyg
├── requirements.txt              # Python beroenden
├── start_sse.sh                  # Startup script
└── README.md                    # Denna dokumentation

Bank of Anthos Backend/
├── userservice                   # Autentisering & användarhantering
├── balances                      # Saldo tjänst
├── transactions                  # Transaktions tjänst
├── history                       # Transaktionshistorik
└── contacts                      # Kontakthantering
```

## 🤖 Användning med AI-agenter

Servern är designad för att användas av AI-agenter för automatiserade bankuppgifter:

### Exempel på användning:
- **Automatiska betalningar**: Schemalagda räkningar och överföringar
- **Saldoövervakning**: Kontinuerlig övervakning av konton
- **Kontaktshantering**: Automatisk hantering av betalningsmottagare
- **Transaktionsanalys**: AI-driven analys av utgiftsmönster

### Integration:
```python
# AI-agent kan nu använda verktyg som:
await authenticate_user("username", "password")
await get_account_balance("1234567890", token)
await execute_payment("0987654321", 100.00, token)
```

## 🐛 Felsökning

### Vanliga problem:

1. **"Connection refused"**
   - Kontrollera att alla Bank of Anthos tjänster körs
   - Verifiera miljövariablerna för tjänste-URL:er

2. **"Authentication failed"**
   - Kontrollera JWT-token giltighet
   - Verifiera användaruppgifter

3. **"Invalid account/routing number"**
   - Kontonummer måste vara exakt 10 siffror
   - Routing-nummer måste vara exakt 9 siffror

4. **MCP-anslutningsfel**
   - Kontrollera `.roo/mcp.json` konfiguration
   - Starta Roo Code om efter konfigurationsändringar

## 📞 Support

För frågor eller problem:
1. Kontrollera denna README
2. Verifiera Bank of Anthos tjänsters status
3. Testa enskilda verktyg separat
4. Kontrollera loggfiler för felmeddelanden

## 🔄 Uppdateringar

Servern använder Bank of Anthos tjänster direkt, så uppdateringar där återspeglas automatiskt. För MCP-specifika ändringar:

```bash
cd bankofanthos_mcp_server
source venv/bin/activate
pip install --upgrade mcp fastapi
```

## 📜 Licens

Samma licens som huvudprojektet.