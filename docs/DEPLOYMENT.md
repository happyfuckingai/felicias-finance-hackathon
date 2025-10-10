# Deployment Guide: Felicia's Finance Multi-Agent Platform

## Overview

This guide provides comprehensive instructions for deploying the Felicia's Finance multi-agent orchestration platform in production environments. The platform is designed for cloud-native deployment with enterprise-grade security, scalability, and reliability.

## Prerequisites

### Infrastructure Requirements

#### Minimum System Requirements
- **Kubernetes Cluster**: Version 1.24 or higher
- **CPU**: 8 cores minimum (16 cores recommended)
- **Memory**: 16GB minimum (32GB recommended)
- **Storage**: 100GB SSD minimum (500GB recommended)
- **Network**: 1Gbps bandwidth minimum

#### Cloud Platform Support
- **Google Cloud Platform** (Primary)
- **Amazon Web Services** (Supported)
- **Microsoft Azure** (Supported)
- **On-premises Kubernetes** (Supported)

### Required Tools
```bash
# Install required tools
kubectl version --client  # v1.24+
helm version              # v3.8+
terraform version         # v1.0+
docker version           # v20.10+
```

### Access Requirements
- **Kubernetes cluster admin access**
- **Cloud provider credentials**
- **Container registry access**
- **DNS management capabilities**

## Quick Start Deployment

### 1. Clone Repository
```bash
git clone https://github.com/happyfuckingai/felicias-finance-hackathon.git
cd felicias-finance-hackathon
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
vim .env
```

**Required Environment Variables:**
```bash
# Cluster Configuration
CLUSTER_NAME=felicias-finance
CLUSTER_REGION=us-central1
PROJECT_ID=your-gcp-project

# Security Configuration
CERT_MANAGER_EMAIL=admin@yourdomain.com
DOMAIN_NAME=felicias-finance.yourdomain.com

# Database Configuration
DB_PASSWORD=your-secure-password
REDIS_PASSWORD=your-redis-password

# Agent Configuration
AGENT_REGISTRY_URL=https://registry.yourdomain.com
DEFAULT_AGENT_IMAGE=felicias-finance/agent:latest
```

### 3. Deploy Infrastructure
```bash
# Initialize Terraform
cd infrastructure/terraform
terraform init

# Plan deployment
terraform plan -var-file="production.tfvars"

# Apply infrastructure
terraform apply -var-file="production.tfvars"
```

### 4. Deploy Platform
```bash
# Return to root directory
cd ../..

# Deploy using Helm
helm install felicias-finance ./infrastructure/helm/felicias-finance \
  --namespace felicias-finance \
  --create-namespace \
  --values ./infrastructure/helm/values/production.yaml
```

### 5. Verify Deployment
```bash
# Check pod status
kubectl get pods -n felicias-finance

# Check services
kubectl get services -n felicias-finance

# Check ingress
kubectl get ingress -n felicias-finance
```

## Detailed Deployment Steps

### Infrastructure Deployment with Terraform

#### 1. Google Cloud Platform Setup
```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable dns.googleapis.com
gcloud services enable certificatemanager.googleapis.com
```

#### 2. Terraform Configuration
```hcl
# infrastructure/terraform/production.tfvars
project_id = "your-gcp-project"
region     = "us-central1"
zone       = "us-central1-a"

# Cluster configuration
cluster_name               = "felicias-finance"
kubernetes_version         = "1.27"
node_count                = 3
machine_type              = "e2-standard-4"
disk_size_gb              = 100

# Network configuration
network_name    = "felicias-finance-network"
subnet_name     = "felicias-finance-subnet"
subnet_cidr     = "10.0.0.0/16"

# Security configuration
enable_network_policy      = true
enable_pod_security_policy = true
enable_workload_identity   = true

# Monitoring
enable_monitoring = true
enable_logging    = true
```

#### 3. Execute Terraform Deployment
```bash
cd infrastructure/terraform

# Initialize
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan -var-file="production.tfvars" -out=tfplan

# Apply infrastructure
terraform apply tfplan
```

### Kubernetes Platform Deployment

#### 1. Namespace Setup
```yaml
# infrastructure/k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: felicias-finance
  labels:
    name: felicias-finance
    istio-injection: enabled
---
apiVersion: v1
kind: Namespace
metadata:
  name: felicias-finance-system
  labels:
    name: felicias-finance-system
```

#### 2. Security Configuration
```yaml
# infrastructure/k8s/security/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: felicias-finance-agent
rules:
- apiGroups: [""]
  resources: ["services", "endpoints", "pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: felicias-finance-agent
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: felicias-finance-agent
subjects:
- kind: ServiceAccount
  name: felicias-finance-agent
  namespace: felicias-finance
```

#### 3. Certificate Management
```yaml
# infrastructure/k8s/security/cert-manager.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Application Deployment with Helm

#### 1. Helm Chart Structure
```
infrastructure/helm/felicias-finance/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   └── hpa.yaml
└── charts/
    ├── postgresql/
    ├── redis/
    └── monitoring/
```

#### 2. Core Application Deployment
```yaml
# infrastructure/helm/felicias-finance/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "felicias-finance.fullname" . }}-orchestrator
  labels:
    {{- include "felicias-finance.labels" . | nindent 4 }}
    component: orchestrator
spec:
  replicas: {{ .Values.orchestrator.replicaCount }}
  selector:
    matchLabels:
      {{- include "felicias-finance.selectorLabels" . | nindent 6 }}
      component: orchestrator
  template:
    metadata:
      labels:
        {{- include "felicias-finance.selectorLabels" . | nindent 8 }}
        component: orchestrator
    spec:
      serviceAccountName: {{ include "felicias-finance.serviceAccountName" . }}
      containers:
      - name: orchestrator
        image: "{{ .Values.orchestrator.image.repository }}:{{ .Values.orchestrator.image.tag }}"
        imagePullPolicy: {{ .Values.orchestrator.image.pullPolicy }}
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        - name: grpc
          containerPort: 9090
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {{ include "felicias-finance.fullname" . }}-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: {{ include "felicias-finance.fullname" . }}-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.orchestrator.resources | nindent 10 }}
```

#### 3. Agent Deployment
```yaml
# infrastructure/helm/felicias-finance/templates/agents/banking-agent.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "felicias-finance.fullname" . }}-banking-agent
  labels:
    {{- include "felicias-finance.labels" . | nindent 4 }}
    component: banking-agent
spec:
  replicas: {{ .Values.agents.banking.replicaCount }}
  selector:
    matchLabels:
      {{- include "felicias-finance.selectorLabels" . | nindent 6 }}
      component: banking-agent
  template:
    metadata:
      labels:
        {{- include "felicias-finance.selectorLabels" . | nindent 8 }}
        component: banking-agent
    spec:
      containers:
      - name: banking-agent
        image: "{{ .Values.agents.banking.image.repository }}:{{ .Values.agents.banking.image.tag }}"
        env:
        - name: AGENT_ID
          value: "banking-agent-001"
        - name: CAPABILITIES
          value: "banking:transactions,banking:accounts,banking:transfers"
        - name: ORCHESTRATOR_URL
          value: "http://{{ include "felicias-finance.fullname" . }}-orchestrator:8080"
        ports:
        - name: http
          containerPort: 8080
        - name: a2a
          containerPort: 9090
        volumeMounts:
        - name: agent-certs
          mountPath: /etc/certs
          readOnly: true
      volumes:
      - name: agent-certs
        secret:
          secretName: {{ include "felicias-finance.fullname" . }}-agent-certs
```

### Database Setup

#### 1. PostgreSQL Configuration
```yaml
# infrastructure/helm/values/production.yaml
postgresql:
  enabled: true
  auth:
    postgresPassword: "your-secure-password"
    database: "felicias_finance"
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: "ssd"
    resources:
      requests:
        memory: "2Gi"
        cpu: "1000m"
      limits:
        memory: "4Gi"
        cpu: "2000m"
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
```

#### 2. Redis Configuration
```yaml
redis:
  enabled: true
  auth:
    enabled: true
    password: "your-redis-password"
  master:
    persistence:
      enabled: true
      size: 50Gi
      storageClass: "ssd"
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1000m"
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
```

### Monitoring and Observability

#### 1. Prometheus Configuration
```yaml
# infrastructure/k8s/monitoring/prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: felicias-finance
  namespace: felicias-finance-system
spec:
  serviceAccountName: prometheus
  serviceMonitorSelector:
    matchLabels:
      app: felicias-finance
  ruleSelector:
    matchLabels:
      app: felicias-finance
  resources:
    requests:
      memory: 2Gi
      cpu: 1000m
    limits:
      memory: 4Gi
      cpu: 2000m
  retention: 30d
  storage:
    volumeClaimTemplate:
      spec:
        storageClassName: ssd
        resources:
          requests:
            storage: 100Gi
```

#### 2. Grafana Dashboard
```yaml
# infrastructure/k8s/monitoring/grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: felicias-finance-dashboard
  namespace: felicias-finance-system
  labels:
    grafana_dashboard: "1"
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "Felicia's Finance - Agent Metrics",
        "panels": [
          {
            "title": "Agent Response Time",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(agent_request_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              }
            ]
          }
        ]
      }
    }
```

### Security Hardening

#### 1. Network Policies
```yaml
# infrastructure/k8s/security/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: felicias-finance-network-policy
  namespace: felicias-finance
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: felicias-finance
    - namespaceSelector:
        matchLabels:
          name: istio-system
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: felicias-finance
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

#### 2. Pod Security Standards
```yaml
# infrastructure/k8s/security/pod-security.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: felicias-finance
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Backup and Disaster Recovery

#### 1. Database Backup
```yaml
# infrastructure/k8s/backup/postgres-backup.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: felicias-finance
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h postgresql -U postgres felicias_finance | \
              gzip > /backup/felicias_finance_$(date +%Y%m%d_%H%M%S).sql.gz
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgresql-secret
                  key: password
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

#### 2. Configuration Backup
```bash
#!/bin/bash
# scripts/backup-config.sh

# Backup Kubernetes configurations
kubectl get all -n felicias-finance -o yaml > backup/k8s-config-$(date +%Y%m%d).yaml

# Backup secrets (encrypted)
kubectl get secrets -n felicias-finance -o yaml | \
  gpg --encrypt --recipient admin@yourdomain.com > backup/secrets-$(date +%Y%m%d).yaml.gpg

# Backup persistent volumes
kubectl get pv -o yaml > backup/persistent-volumes-$(date +%Y%m%d).yaml
```

## Production Considerations

### Scaling Configuration

#### 1. Horizontal Pod Autoscaler
```yaml
# infrastructure/k8s/scaling/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: felicias-finance-orchestrator-hpa
  namespace: felicias-finance
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: felicias-finance-orchestrator
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### 2. Vertical Pod Autoscaler
```yaml
# infrastructure/k8s/scaling/vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: felicias-finance-orchestrator-vpa
  namespace: felicias-finance
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: felicias-finance-orchestrator
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: orchestrator
      maxAllowed:
        cpu: 4
        memory: 8Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
```

### Performance Optimization

#### 1. Resource Limits
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

#### 2. JVM Tuning (for Java agents)
```yaml
env:
- name: JAVA_OPTS
  value: "-Xms1g -Xmx2g -XX:+UseG1GC -XX:MaxGCPauseMillis=200"
```

### Health Checks and Monitoring

#### 1. Comprehensive Health Checks
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 5
  failureThreshold: 3

startupProbe:
  httpGet:
    path: /health/startup
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 30
```

#### 2. Custom Metrics
```python
# Example custom metrics in agent code
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
agent_requests_total = Counter('agent_requests_total', 'Total agent requests', ['agent_id', 'action'])
agent_request_duration = Histogram('agent_request_duration_seconds', 'Agent request duration')
active_connections = Gauge('agent_active_connections', 'Active agent connections')

# Use in code
@agent_request_duration.time()
def handle_request(request):
    agent_requests_total.labels(agent_id=self.agent_id, action=request.action).inc()
    # Handle request
```

## Troubleshooting

### Common Issues

#### 1. Pod Startup Issues
```bash
# Check pod status
kubectl get pods -n felicias-finance

# Check pod logs
kubectl logs -n felicias-finance deployment/felicias-finance-orchestrator

# Describe pod for events
kubectl describe pod -n felicias-finance <pod-name>
```

#### 2. Network Connectivity Issues
```bash
# Test service connectivity
kubectl exec -n felicias-finance <pod-name> -- curl http://service-name:port/health

# Check network policies
kubectl get networkpolicies -n felicias-finance

# Test DNS resolution
kubectl exec -n felicias-finance <pod-name> -- nslookup service-name
```

#### 3. Certificate Issues
```bash
# Check certificate status
kubectl get certificates -n felicias-finance

# Check certificate details
kubectl describe certificate -n felicias-finance <cert-name>

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

### Performance Troubleshooting

#### 1. Resource Usage Analysis
```bash
# Check resource usage
kubectl top pods -n felicias-finance
kubectl top nodes

# Check resource limits
kubectl describe pod -n felicias-finance <pod-name> | grep -A 10 "Limits:"
```

#### 2. Database Performance
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check connection count
SELECT count(*) FROM pg_stat_activity;
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### 1. Security Updates
```bash
# Update base images
docker pull felicias-finance/agent:latest
docker pull felicias-finance/orchestrator:latest

# Update Kubernetes
kubectl version
# Follow cluster upgrade procedures
```

#### 2. Certificate Renewal
```bash
# Check certificate expiration
kubectl get certificates -n felicias-finance -o custom-columns=NAME:.metadata.name,READY:.status.conditions[0].status,EXPIRY:.status.notAfter

# Force certificate renewal if needed
kubectl delete certificate -n felicias-finance <cert-name>
```

#### 3. Database Maintenance
```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Reindex if needed
REINDEX DATABASE felicias_finance;

-- Check database size
SELECT pg_size_pretty(pg_database_size('felicias_finance'));
```

### Upgrade Procedures

#### 1. Rolling Updates
```bash
# Update deployment image
kubectl set image deployment/felicias-finance-orchestrator \
  orchestrator=felicias-finance/orchestrator:v2.0.0 \
  -n felicias-finance

# Monitor rollout
kubectl rollout status deployment/felicias-finance-orchestrator -n felicias-finance

# Rollback if needed
kubectl rollout undo deployment/felicias-finance-orchestrator -n felicias-finance
```

#### 2. Blue-Green Deployment
```bash
# Deploy new version to staging namespace
helm install felicias-finance-staging ./infrastructure/helm/felicias-finance \
  --namespace felicias-finance-staging \
  --create-namespace \
  --values ./infrastructure/helm/values/staging.yaml

# Test new version
# Switch traffic
# Remove old version
```

## Conclusion

This deployment guide provides comprehensive instructions for deploying the Felicia's Finance multi-agent platform in production environments. The platform is designed for enterprise-scale deployment with robust security, monitoring, and maintenance procedures.

For additional support or questions, please refer to the project documentation or contact the development team.
