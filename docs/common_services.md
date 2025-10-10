# Gemensamma Tjänster för HappyOS Platform

## Översikt

HappyOS kräver flera gemensamma tjänster som alla domänspecifika MCP-servrar kan använda. Dessa tjänster hanterar kors-domän funktioner som service discovery, autentisering, routing och övervakning.

## 1. Service Registry & Discovery

### Funktion
- Registrerar alla MCP-servrar vid startup
- Tillhandahåller service discovery för inter-MCP kommunikation
- Hälsokontroll och service status
- Metadata om tillgängliga verktyg per tjänst

### Implementation
```python
# service_registry.py - Enkel registry tjänst
from fastapi import FastAPI
from typing import Dict, List
import httpx
import asyncio

app = FastAPI()

services = {}

@app.post("/register")
async def register_service(service_data: dict):
    """Registrera en ny tjänst"""
    service_id = service_data["id"]
    services[service_id] = {
        "url": service_data["url"],
        "tools": service_data["tools"],
        "health_url": service_data["health_url"],
        "last_seen": datetime.now(),
        "status": "healthy"
    }
    return {"status": "registered"}

@app.get("/services")
async def get_services():
    """Hämta alla registrerade tjänster"""
    return services

@app.get("/service/{service_id}/tools")
async def get_service_tools(service_id: str):
    """Hämta verktyg för specifik tjänst"""
    return services.get(service_id, {}).get("tools", [])
```

### Användning i MCP-servrar
```python
# I varje MCP-server vid startup
async def register_with_registry():
    async with httpx.AsyncClient() as client:
        await client.post("http://registry:8080/register", json={
            "id": "crypto-mcp",
            "url": "http://crypto-mcp:8000",
            "tools": ["create_wallet", "deploy_token"],
            "health_url": "/health"
        })
```

## 2. API Gateway & Router

### Funktion
- Enhetlig entry point för externa förfrågningar
- Routar förfrågningar till rätt MCP-server
- Load balancing mellan instanser
- Rate limiting och säkerhet

### Implementation
```python
# api_gateway.py
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_request(request: Request, path: str):
    """Routa förfrågningar till rätt tjänst"""

    # Bestäm mål-tjänst baserat på path
    if path.startswith("crypto/"):
        target_service = "crypto-mcp"
        target_path = path.replace("crypto/", "")
    elif path.startswith("banking/"):
        target_service = "banking-mcp"
        target_path = path.replace("banking/", "")
    else:
        return {"error": "Unknown service"}

    # Hämta service URL från registry
    service_url = await get_service_url(target_service)

    # Vidarebefordra förfrågan
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=f"{service_url}/{target_path}",
            headers=dict(request.headers),
            content=await request.body()
        )
        return response.json()
```

## 3. Autentisering & Auktorisering (Auth Service)

### Funktion
- Centraliserad användarautentisering
- JWT-token hantering
- Roll-baserad åtkomstkontroll (RBAC)
- API-nyckel hantering för tjänster

### Implementation
```python
# auth_service.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

app = FastAPI()
security = HTTPBearer()

VALID_ROLES = ["user", "admin", "service"]

@app.post("/authenticate")
async def authenticate(credentials: dict):
    """Autentisera användare och returnera JWT"""
    # Validera credentials
    # Generera JWT med roller och behörigheter
    pass

@app.get("/validate")
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validera JWT-token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "user": payload["sub"], "roles": payload["roles"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_role: str):
    """Dependency för roll-baserad auktorisering"""
    def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        if required_role not in payload.get("roles", []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return payload
    return role_checker
```

### Användning i MCP-servrar
```python
# I banking-mcp för att skydda verktyg
@tool()
async def execute_payment(
    amount: float,
    token: str = Depends(require_role("user"))
):
    """Utför betalning - kräver användarroll"""
    # Implementering...
    pass
```

## 4. Konfigurationshantering (Config Service)

### Funktion
- Centraliserad konfiguration för alla tjänster
- Miljöspecifika inställningar (dev/staging/prod)
- Dynamisk konfigurationsuppdatering
- Sekret hantering

### Implementation
```yaml
# config.yaml
services:
  crypto-mcp:
    database_url: "postgresql://crypto-db:5432/crypto"
    api_keys:
      coinbase: "${COINBASE_API_KEY}"
      infura: "${INFURA_API_KEY}"
    features:
      enable_trading: true
      enable_deployments: true

  banking-mcp:
    database_url: "postgresql://banking-db:5432/banking"
    jwt_secret: "${JWT_SECRET}"
    features:
      enable_transfers: true
      enable_contacts: true
```

### Miljö-variabler
```bash
# .env
COINBASE_API_KEY=sk-...
INFURA_API_KEY=...
JWT_SECRET=super-secret-key
DATABASE_URL=postgresql://localhost:5432/happyos
```

## 5. Övervakning & Loggning (Observability Service)

### Funktion
- Centraliserad loggning från alla tjänster
- Metrik-insamling (CPU, minne, svarstider)
- Hälsokontroller och alert-system
- Trace-spårning för förfrågningar

### Implementation
```python
# monitoring_service.py
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest
import logging

app = FastAPI()

# Metrik-definieringar
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Konfigurera loggning
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def add_metrics(request, call_next):
    """Middleware för att samla metrik"""
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    return response

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrik-endpoint"""
    return generate_latest()

@app.post("/logs")
async def ingest_logs(log_data: dict):
    """Ta emot och lagra loggar från andra tjänster"""
    logger.info(f"Received log: {log_data}")
    # Lagra i databas eller vidarebefordra till ELK-stack
    return {"status": "logged"}
```

### Loggning i MCP-servrar
```python
# I varje MCP-server
import logging
from monitoring_service import MonitoringClient

logger = logging.getLogger(__name__)
monitor = MonitoringClient("http://monitoring:8080")

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    await monitor.log_event({
        "service": "crypto-mcp",
        "method": request.method,
        "path": request.url.path,
        "duration": duration,
        "status_code": response.status_code
    })

    return response
```

## 6. Meddelandesystem (Message Bus)

### Funktion
- Asynkron kommunikation mellan tjänster
- Event-driven arkitektur
- Kö-system för långvariga operationer
- Pub/Sub-mönster för loose coupling

### Implementation
```python
# message_bus.py
from fastapi import FastAPI
from typing import Dict, List, Callable
import asyncio

app = FastAPI()

# Enkel in-memory meddelandebuss
subscribers: Dict[str, List[Callable]] = {}

@app.post("/publish/{topic}")
async def publish_message(topic: str, message: dict):
    """Publicera meddelande till topic"""
    if topic in subscribers:
        for callback in subscribers[topic]:
            await callback(message)
    return {"status": "published"}

@app.post("/subscribe/{topic}")
async def subscribe_to_topic(topic: str, callback_url: str):
    """Prenumerera på topic"""
    # I praktiken skulle detta lagra callback-URL:er
    # och använda webhooks för att leverera meddelanden
    pass

# Exempel på användning
async def handle_crypto_transaction(message):
    """Hantera crypto-transaktion event"""
    print(f"Processing crypto transaction: {message}")

# Registrera hanterare
subscribers["crypto.transaction.completed"] = [handle_crypto_transaction]
```

## Arkitekturöversikt

```
┌─────────────────────────────────────────────────────────────┐
│                    HappyOS Common Services                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Service     │  │ Auth        │  │ Config      │         │
│  │ Registry    │  │ Service     │  │ Service     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ API Gateway │  │ Monitoring  │  │ Message    │         │
│  │ & Router    │  │ & Logging   │  │ Bus        │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐     │
│  │                   MCP Servers                        │     │
│  │  Crypto • Banking • Svea • Future Services          │     │
│  └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Implementeringsordning

1. **Service Registry** - Grundläggande discovery
2. **Auth Service** - Säkerhet först
3. **API Gateway** - Routing och åtkomst
4. **Config Service** - Konfigurationshantering
5. **Monitoring** - Observability
6. **Message Bus** - Avancerad kommunikation

Dessa gemensamma tjänster skapar en robust plattform där varje ny domän automatiskt får tillgång till alla nödvändiga funktioner för att fungera inom HappyOS-ekosystemet.