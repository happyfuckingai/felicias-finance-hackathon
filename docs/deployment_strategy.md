# Deployment Strategy för HappyOS Multi-MCP Platform

## Översikt

HappyOS deployeras som en containeriserad, orkestrerad plattform där varje domän (Crypto, Banking, etc.) körs som en separat MCP-server. Detta möjliggör skalbarhet, isolering och enkel expansion med nya domäner.

## Container Strategi

### Varje MCP-server containeriseras
```dockerfile
# Exempel: crypto_mcp_server/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Kopiera beroenden
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiera applikation
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Exponera port
EXPOSE 8000

# Startkommando
CMD ["python", "crypto_mcp_server.py", "--sse"]
```

### Docker Compose för lokal utveckling
```yaml
# docker-compose.yml
version: '3.8'

services:
  crypto-mcp:
    build: ./crypto_mcp_server
    ports:
      - "8000:8000"
    environment:
      - CRYPTO_PRIVATE_KEY=${CRYPTO_PRIVATE_KEY}
    networks:
      - happyos-network
    depends_on:
      - registry

  banking-mcp:
    build: ./bankofanthos_mcp_server
    ports:
      - "8001:8001"
    environment:
      - TRANSACTIONS_API_ADDR=http://banking-backend:8080
      - USERSERVICE_API_ADDR=http://banking-backend:8081
      # ... andra env vars
    networks:
      - happyos-network
    depends_on:
      - registry
      - banking-backend

  banking-backend:
    # Bank of Anthos backend tjänster
    image: gcr.io/bank-of-anthos/banking-backend
    # ... konfiguration

  registry:
    build: ./service-registry
    ports:
      - "8080:8080"
    networks:
      - happyos-network

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    networks:
      - happyos-network

networks:
  happyos-network:
    driver: bridge

volumes:
  crypto-data:
  banking-data:
```

## Kubernetes Deployment för Produktion

### Namespace-struktur
```
happyos-system/
├── crypto-mcp/          # Crypto domän
├── banking-mcp/         # Banking domän
├── registry/            # Service discovery
├── ingress/             # API Gateway
└── monitoring/          # Observability
```

### Deployment Manifest
```yaml
# crypto-mcp-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crypto-mcp
  namespace: happyos-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crypto-mcp
  template:
    metadata:
      labels:
        app: crypto-mcp
    spec:
      containers:
      - name: crypto-mcp
        image: happyos/crypto-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: CRYPTO_PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: crypto-secrets
              key: private-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: crypto-mcp
  namespace: happyos-system
spec:
  selector:
    app: crypto-mcp
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Ingress för Extern Åtkomst
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: happyos-ingress
  namespace: happyos-system
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.happyos.com
    http:
      paths:
      - path: /crypto
        pathType: Prefix
        backend:
          service:
            name: crypto-mcp
            port:
              number: 8000
      - path: /banking
        pathType: Prefix
        backend:
          service:
            name: banking-mcp
            port:
              number: 8001
      - path: /registry
        pathType: Prefix
        backend:
          service:
            name: service-registry
            port:
              number: 8080
```

## Terraform för Infrastruktur

### Grundläggande Cloud Setup
```hcl
# main.tf
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# GKE Cluster
resource "google_container_cluster" "happyos_cluster" {
  name     = "happyos-cluster"
  location = var.region

  initial_node_count = 3

  node_config {
    machine_type = "e2-medium"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# Cloud SQL för persistens
resource "google_sql_database_instance" "happyos_db" {
  name             = "happyos-db"
  database_version = "POSTGRES_14"
  region           = var.region

  settings {
    tier = "db-f1-micro"
  }
}

# Storage buckets
resource "google_storage_bucket" "crypto_data" {
  name     = "${var.project_id}-crypto-data"
  location = var.region
}
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy HappyOS

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Login to Google Artifact Registry
      uses: docker/login-action@v2
      with:
        registry: europe-north1-docker.pkg.dev
        username: _json_key
        password: ${{ secrets.GAR_JSON_KEY }}

    - name: Build and push crypto MCP
      uses: docker/build-push-action@v4
      with:
        context: ./crypto_mcp_server
        push: true
        tags: europe-north1-docker.pkg.dev/${{ secrets.PROJECT_ID }}/happyos/crypto-mcp:latest

    - name: Deploy to GKE
      uses: google-github-actions/deploy-cloudrun@v1
      with:
        service: happyos-cluster
        image: europe-north1-docker.pkg.dev/${{ secrets.PROJECT_ID }}/happyos/crypto-mcp:latest
```

## Skalbarhet & Resilience

### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: crypto-mcp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: crypto-mcp
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Service Mesh (Istio)
- Traffic management mellan tjänster
- Load balancing
- Circuit breakers
- Observability

## Säkerhet i Deployment

- **Image scanning**: Sök efter säkerhetshål i containers
- **Secrets management**: Kubernetes secrets eller external vault
- **Network policies**: Isolera trafik mellan namespaces
- **RBAC**: Roll-baserad åtkomstkontroll för Kubernetes
- **TLS**: Automatisk certifikathantering med cert-manager

## Miljöer

- **Development**: Docker Compose på lokal maskin
- **Staging**: Minikube eller liten GKE-cluster
- **Production**: Fullständig GKE-setup med multi-zone deployment

## Kostnadsoptimering

- **Spot instances**: För icke-kritiska workloads
- **Auto-scaling**: Skala ner när belastning är låg
- **Storage classes**: Välj rätt storage baserat på behov
- **Resource limits**: Förhindra överkonsumtion

Denna strategi möjliggör enkel skalning från lokal utveckling till global produktion, med varje domän isolerad men kapabel att kommunicera med andra genom det definierade MCP-protokollet.