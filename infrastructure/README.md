# 🚀 Google Cloud Deployment för Felicia's Finance

## 📋 Deployment Översikt

Detta dokument beskriver deployment-strategin för Felicia's Finance crypto-system till Google Cloud Platform.

## 🏗️ System Arkitektur

### **Core Services som ska deployas:**

1. **Google Cloud Web3 Provider Service**
   - Multi-chain Web3 gateway
   - Token resolution och balance queries
   - Smart contract interactions

2. **Web3 BigQuery Integration Service**
   - Real-tids portfolio analytics
   - Risk management och monitoring
   - Cross-chain data aggregation

3. **Security & Monitoring Services**
   - Web3 security manager
   - Access control system
   - Cost analyzer och monitoring

4. **Cache Management System**
   - Redis cache för Web3 data
   - BigQuery data caching
   - Performance optimization

## 🛠️ Deployment Strategi

### **Fas 1: Foundation Setup**
1. Google Cloud Project konfiguration
2. Service Accounts och IAM setup
3. Network och security configuration
4. Database och storage setup

### **Fas 2: Core Services Deployment**
1. Web3 Provider Service
2. BigQuery Integration Service
3. Cache Management System
4. Security Services

### **Fas 3: Integration & Testing**
1. Service-to-service integration
2. End-to-end testing
3. Performance optimization
4. Monitoring setup

### **Fas 4: Production Deployment**
1. Load balancer configuration
2. Auto-scaling setup
3. CI/CD pipeline
4. Production validation

## 📁 Deployment Filer

```
infrastructure/
├── README.md                           # Detta dokument
├── deployment-config.yaml              # Deployment konfiguration
├── terraform/
│   ├── main.tf                        # Huvud Terraform config
│   ├── variables.tf                   # Input variables
│   ├── outputs.tf                     # Output values
│   └── modules/
│       ├── web3-provider/             # Web3 provider module
│       ├── bigquery-integration/      # BigQuery integration module
│       ├── security/                  # Security module
│       └── monitoring/                # Monitoring module
├── docker/
│   ├── Dockerfile.web3-provider       # Web3 provider container
│   ├── Dockerfile.bigquery-service    # BigQuery service container
│   ├── Dockerfile.security-service   # Security service container
│   └── Dockerfile.monitoring         # Monitoring container
├── k8s/
│   ├── web3-provider-deployment.yaml  # K8s deployment för Web3
│   ├── bigquery-service-deployment.yaml # K8s deployment för BigQuery
│   ├── security-service-deployment.yaml # K8s deployment för security
│   ├── monitoring-deployment.yaml     # K8s deployment för monitoring
│   ├── ingress.yaml                   # Ingress configuration
│   └── service.yaml                   # Service configuration
└── scripts/
    ├── deploy.sh                      # Deployment script
    ├── validate.sh                    # Validation script
    └── cleanup.sh                     # Cleanup script
```

## 🚀 Quick Start Deployment

### **Förutsättningar:**
- Google Cloud SDK installerad
- Terraform installerad
- Docker installerad
- kubectl installerad

### **1. Google Cloud Project Setup:**
```bash
# Sätt ditt project ID
export PROJECT_ID="felicia-finance-prod"

# Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    container.googleapis.com \
    bigquery.googleapis.com \
    pubsub.googleapis.com \
    cloudfunctions.googleapis.com \
    aiplatform.googleapis.com \
    kms.googleapis.com \
    --project=$PROJECT_ID

# Skapa service accounts
gcloud iam service-accounts create web3-provider-sa \
    --display-name="Web3 Provider Service Account" \
    --project=$PROJECT_ID

gcloud iam service-accounts create bigquery-service-sa \
    --display-name="BigQuery Service Account" \
    --project=$PROJECT_ID

gcloud iam service-accounts create security-service-sa \
    --display-name="Security Service Account" \
    --project=$PROJECT_ID
```

### **2. Deploy Infrastructure:**
```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="project_id=$PROJECT_ID"

# Deploy infrastructure
terraform apply -var="project_id=$PROJECT_ID"
```

### **3. Build och Deploy Services:**
```bash
# Build Docker images
cd ../docker
docker build -t gcr.io/$PROJECT_ID/web3-provider:latest -f Dockerfile.web3-provider .
docker build -t gcr.io/$PROJECT_ID/bigquery-service:latest -f Dockerfile.bigquery-service .
docker build -t gcr.io/$PROJECT_ID/security-service:latest -f Dockerfile.security-service .

# Push images till GCR
gcloud auth configure-docker
docker push gcr.io/$PROJECT_ID/web3-provider:latest
docker push gcr.io/$PROJECT_ID/bigquery-service:latest
docker push gcr.io/$PROJECT_ID/security-service:latest
```

### **4. Deploy till Kubernetes:**
```bash
cd ../k8s

# Deploy services
kubectl apply -f web3-provider-deployment.yaml
kubectl apply -f bigquery-service-deployment.yaml
kubectl apply -f security-service-deployment.yaml
kubectl apply -f monitoring-deployment.yaml

# Deploy ingress
kubectl apply -f ingress.yaml
```

## 🔧 Service Konfigurationer

### **Web3 Provider Service**
```yaml
# k8s/web3-provider-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web3-provider
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web3-provider
  template:
    metadata:
      labels:
        app: web3-provider
    spec:
      serviceAccountName: web3-provider-sa
      containers:
      - name: web3-provider
        image: gcr.io/felicia-finance-prod/web3-provider:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_CLOUD_PROJECT_ID
          value: "felicia-finance-prod"
        - name: WEB3_GATEWAY_ENABLED
          value: "true"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### **BigQuery Integration Service**
```yaml
# k8s/bigquery-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bigquery-integration
spec:
  replicas: 2
  selector:
    matchLabels:
      app: bigquery-integration
  template:
    metadata:
      labels:
        app: bigquery-integration
    spec:
      serviceAccountName: bigquery-service-sa
      containers:
      - name: bigquery-integration
        image: gcr.io/felicia-finance-prod/bigquery-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_CLOUD_PROJECT_ID
          value: "felicia-finance-prod"
        - name: BIGQUERY_DATASET_TRADING
          value: "trading_analytics"
        - name: BIGQUERY_DATASET_PORTFOLIO
          value: "portfolio_tracking"
        - name: PUBSUB_TOPIC_TRADES
          value: "crypto-trades"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

## 🔐 Security Configuration

### **Service Account Permissions:**
```bash
# Web3 Provider Service Account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:web3-provider-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:web3-provider-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

# BigQuery Service Account
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:bigquery-service-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:bigquery-service-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"
```

## 📊 Monitoring & Alerting

### **Cloud Monitoring Setup:**
```bash
# Skapa uptime check
gcloud monitoring uptime-check-configs create web3-provider-uptime \
    --display-name="Web3 Provider Uptime" \
    --http-check-path="/" \
    --http-check-port=8080

# Skapa alert policy för hög error rate
gcloud monitoring policies create \
    --display-name="High Error Rate Alert" \
    --condition-filter="metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" AND metric.label.state=\"error\"" \
    --condition-threshold-value=10 \
    --condition-threshold-duration=300s \
    --notification-channels="email-channel"
```

## 🔄 CI/CD Pipeline

### **Cloud Build Configuration:**
```yaml
# cloudbuild.yaml
steps:
  # Build Web3 provider
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/web3-provider:$COMMIT_SHA', './docker/web3-provider']

  # Build BigQuery service
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/bigquery-service:$COMMIT_SHA', './docker/bigquery-service']

  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/web3-provider:$COMMIT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/bigquery-service:$COMMIT_SHA']

  # Deploy till Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'web3-provider'
      - '--image'
      - 'gcr.io/$PROJECT_ID/web3-provider:$COMMIT_SHA'
      - '--region'
      - 'europe-west1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'bigquery-service'
      - '--image'
      - 'gcr.io/$PROJECT_ID/bigquery-service:$COMMIT_SHA'
      - '--region'
      - 'europe-west1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
```

## 🧪 Testing & Validation

### **Health Checks:**
```bash
# Testa Web3 provider health
curl -X GET "https://web3-provider-<hash>-ew.a.run.app/health" -H "Content-Type: application/json"

# Testa BigQuery service health
curl -X GET "https://bigquery-service-<hash>-ew.a.run.app/health" -H "Content-Type: application/json"

# Testa wallet analysis
curl -X POST "https://bigquery-service-<hash>-ew.a.run.app/analyze-wallet" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x123...", "include_live_data": true}'
```

### **Performance Testing:**
```bash
# Load test Web3 provider
hey -n 1000 -c 10 https://web3-provider-<hash>-ew.a.run.app/balance/0x123...

# Load test BigQuery service
hey -n 1000 -c 10 https://bigquery-service-<hash>-ew.a.run.app/portfolio-analysis
```

## 🚨 Troubleshooting

### **Vanliga Problem:**

1. **Authentication Errors:**
   - Verifiera service account keys
   - Kontrollera IAM permissions
   - Validera Google Cloud credentials

2. **Network Issues:**
   - Kontrollera VPC firewall rules
   - Verifiera service-to-service connectivity
   - Kontrollera Cloud Load Balancer configuration

3. **Performance Issues:**
   - Öka CPU/memory limits
   - Aktivera Cloud CDN
   - Optimera BigQuery queries

### **Log Analysis:**
```bash
# Visa Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Visa BigQuery job logs
gcloud logging read "resource.type=bigquery_resource" --limit 50

# Visa Pub/Sub message logs
gcloud logging read "resource.type=pubsub_topic" --limit 50
```

## 📞 Support & Maintenance

### **Production Support:**
- **Monitoring Dashboard**: https://console.cloud.google.com/monitoring
- **Alerting**: Konfigurerade för critical errors och performance issues
- **Logs**: Centralized logging med Stackdriver
- **Metrics**: Real-tids metrics för alla services

### **Maintenance Windows:**
- **Scheduled Maintenance**: Söndagar 02:00-04:00 CET
- **Emergency Maintenance**: As needed med 1-hour notice
- **Database Maintenance**: Automatic with zero-downtime

---

**🚀 Happy Deploying!**

För frågor eller support, kontakta DevOps teamet eller skapa ett issue i GitHub.