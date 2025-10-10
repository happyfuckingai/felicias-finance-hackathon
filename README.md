# Felicia's Finance - AWS Agent Hackathon

Ett minimalt projekt för AWS Agent Hackathon med fokus på AI-agent integration och Bank of Anthos.

## 📁 Projektstruktur

```
felicias-finance/
├── infrastructure/          # AWS Terraform-konfigurationer
│   └── aws/
│       └── terraform/
├── bank_of_anthos/          # Bank of Anthos integration
├── bank_of_anthos_mcp/      # MCP server för Bank of Anthos
├── aws/                     # AWS-specifik kod
├── adk_agents/              # Agent Development Kit (ADK)
├── agent_core/              # Kärnlogik för AI-agenter
├── docs/                    # Dokumentation
├── crypto_mcp_server/      # Crypto MCP server
└── react_frontend/          # React frontend-applikation
```

## 🚀 Komponenter

### **Infrastructure (AWS)**
- Terraform-konfigurationer för AWS deployment
- ECS, Lambda, API Gateway, RDS setup
- Säkerhetsgrupper och IAM-roller

### **Bank of Anthos Integration**
- Integration med Google Cloud Bank of Anthos
- MCP (Model Context Protocol) implementation
- Transaction processing och account management

### **AI Agents**
- Agent Development Kit (ADK) framework
- Core agent logic och orkestrering
- Multi-agent kommunikation

### **Frontend**
- React-baserad användargränssnitt
- Dashboard för agent monitoring
- Transaction visualization

## 🛠️ Teknologier

- **Backend**: Python, FastAPI
- **AI/ML**: OpenAI, AWS Bedrock
- **Cloud**: AWS (ECS, Lambda, RDS, API Gateway)
- **Frontend**: React, TypeScript
- **Infrastructure**: Terraform, Docker
- **Communication**: MCP, WebSocket

## 🚀 Deployment

### AWS Deployment
```bash
cd infrastructure/aws/terraform
terraform init
terraform plan
terraform apply
```

### Lokal Development
```bash
# Installera dependencies
pip install -r requirements.txt

# Starta tjänster
docker-compose up
```

## 📚 Dokumentation

Se `docs/` mappen för detaljerad dokumentation om:
- API-referenser
- Deployment-guider
- Arkitektur-översikt
- Agent-konfiguration

## 🤝 Bidrag

Detta är ett hackathon-projekt. För frågor eller förbättringsförslag, skapa en issue eller pull request.

## 📄 Licens

MIT License