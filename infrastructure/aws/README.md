# 🚀 AWS Deployment för Felicia's Finance

Detta dokument beskriver AWS-deployment strategin för Felicia's Finance baserat på AWS Agent Hackathon.

## 🏗️ AWS Arkitektur Översikt

### **Core AWS Services:**

1. **AWS Bedrock (AI/ML)**
   - Claude 3 Sonnet för AI-agenten Felicia
   - Custom Bedrock Agent för finansiell analys
   - Model access och logging

2. **AWS Cognito (Authentication)**
   - User Pool för användarautentisering
   - OAuth2/OIDC integration
   - JWT token management

3. **AWS Lambda (Serverless Functions)**
   - Auth Lambda: Hantering av login/registrering
   - Crypto Lambda: Kryptovaluta operationer
   - Banking Lambda: Bankoperationer

4. **Amazon ECS (Container Services)**
   - Frontend service (Next.js)
   - MCP server service
   - Auto-scaling och load balancing

5. **AWS API Gateway**
   - REST API för alla tjänster
   - Cognito Authorizer för skyddade endpoints
   - Rate limiting och CORS

6. **Amazon RDS PostgreSQL**
   - Huvuddatabas för applikationsdata
   - Multi-AZ deployment för hög tillgänglighet

7. **Amazon ElastiCache Redis**
   - Caching för Web3 data och sessioner
   - Performance optimization

8. **Amazon S3 & CloudFront**
   - Static asset hosting
   - CDN för global distribution
   - SPA routing support

## 🛠️ Deployment Strategi

### **Fas 1: Infrastructure Setup**
1. AWS konto och IAM konfiguration
2. Terraform backend setup (S3 + DynamoDB)
3. VPC, subnets och security groups
4. Secrets Manager setup

### **Fas 2: Core Services Deployment**
1. Cognito User Pool setup
2. RDS och Redis provisioning
3. Lambda functions deployment
4. ECS cluster och services
5. API Gateway configuration

### **Fas 3: AI/ML Integration**
1. Bedrock model access
2. Custom agent creation
3. MCP server integration
4. Testing och validation

### **Fas 4: Frontend & CDN**
1. S3 bucket setup
2. CloudFront distribution
3. SSL certificate (ACM)
4. SPA routing configuration

## 📋 Förutsättningar

- AWS CLI konfigurerad
- Terraform 1.5+
- Docker för container builds
- Node.js 18+ för frontend
- Python 3.11+ för Lambda functions

## 🚀 Snabba Kommandon

### **Initial Setup**
```bash
# Klona repository
git clone <repository-url>
cd felicia-finance

# Installera dependencies
npm install
pip install -r requirements.txt

# Konfigurera AWS
aws configure

# Initiera Terraform
cd infrastructure/aws/terraform
terraform init
```

### **Deployment**
```bash
# Plan deployment
terraform plan -var-file=dev.tfvars

# Deploy infrastructure
terraform apply -var-file=dev.tfvars

# Build och push containers
cd ../../../..
docker build -t feliciafinance/frontend ./react_frontend
docker build -t feliciafinance/mcp-server ./crypto_mcp_server
docker build -t feliciafinance/crypto-service ./crypto
docker build -t feliciafinance/banking-service ./bank_of_anthos

# Deploy till ECS
aws ecs update-service --cluster felicia-finance-dev --service felicia-finance-frontend-dev --force-new-deployment
```

### **Environment Variables**
Skapa `.env` filer för olika miljöer:

```bash
# dev.tfvars
environment = "dev"
aws_region = "us-east-1"
db_password = "your-secure-db-password"
jwt_secret = "your-jwt-secret"
web3_rpc_url = "https://your-web3-rpc-endpoint"
```

## 🔧 Konfiguration

### **Bedrock Agent Setup**
Agenten är konfigurerad för finansiella operationer:
- Portfolio analys
- Trading rekommendationer
- Risk assessment
- Marknadsdata hämtning

### **Cognito User Pool**
- Email-baserad autentisering
- Självregistrering aktiverad
- JWT tokens med 1h giltighetstid
- Refresh tokens med 30 dagar

### **API Gateway**
Skyddade endpoints kräver Cognito authentication:
- `/api/auth/me` - User profile
- `/api/crypto/*` - Crypto operations
- `/api/banking/*` - Banking operations

## 📊 Monitoring & Logging

### **CloudWatch**
- ECS container metrics
- Lambda function logs
- API Gateway access logs
- Custom alarms för CPU/memory

### **Bedrock Logging**
- Model invocation logs
- Agent interaction logs
- S3-baserad lagring

## 🔒 Säkerhet

### **IAM Roles & Policies**
- Least privilege principle
- Service-specific IAM roles
- Secrets Manager för känsliga data

### **Network Security**
- Private subnets för databaser
- Security groups med minimal exposure
- VPC endpoints för AWS services

### **Data Protection**
- Encryption at rest (RDS, S3, Redis)
- TLS 1.2+ för all kommunikation
- JWT tokens för API authentication

## 🧪 Testing

### **Local Development**
```bash
# Start local stack
docker-compose up -d

# Run tests
npm test
pytest

# Check health endpoints
curl http://localhost:3000/api/health
```

### **Integration Testing**
```bash
# API tests
npm run test:integration

# Load testing
npm run test:load

# E2E tests
npm run test:e2e
```

## 📈 Skalering

### **Auto Scaling**
- ECS services skalar baserat på CPU/memory
- Lambda concurrency limits
- RDS read replicas för read-heavy workloads

### **Performance Optimization**
- CloudFront CDN
- Redis caching
- Database query optimization
- Lambda provisioned concurrency

## 🚨 Troubleshooting

### **Vanliga Problem**

**ECS Service inte startar:**
```bash
# Check service events
aws ecs describe-services --cluster felicia-finance-dev --services felicia-finance-frontend-dev

# Check CloudWatch logs
aws logs tail /ecs/felicia-finance-dev --follow
```

**Lambda timeout:**
- Öka timeout i terraform
- Optimera function code
- Använd provisioned concurrency

**Bedrock API errors:**
- Kontrollera model access permissions
- Verify region availability
- Check rate limits

## 📚 Resurser

- [AWS Agent Hackathon](https://aws-agent-hackathon.devpost.com/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest)

## 🤝 Bidrag

1. Fork repository
2. Skapa feature branch
3. Commit changes
4. Push till branch
5. Skapa Pull Request

## 📄 Licens

Detta projekt är licensierat under MIT License.