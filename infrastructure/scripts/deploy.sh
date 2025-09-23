#!/bin/bash

# 🚀 Felicia's Finance - Google Cloud Deployment Script
# Detta script automatiserar hela deployment-processen för crypto-systemet

set -e  # Exit on any error

# Colors för output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
PROJECT_ID=${PROJECT_ID:-"felicia-finance-prod"}
REGION=${REGION:-"europe-west1"}
ZONE=${ZONE:-"europe-west1-b"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Check prerequisites
check_prerequisites() {
    log_info "Kontrollerar prerequisites..."

    # Check Google Cloud SDK
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud SDK är inte installerat. Installera från https://cloud.google.com/sdk"
        exit 1
    fi

    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform är inte installerat. Installera från https://terraform.io"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker är inte installerat."
        exit 1
    fi

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl är inte installerat."
        exit 1
    fi

    log_success "Alla prerequisites är installerade"
}

# Setup Google Cloud Project
setup_gcp_project() {
    log_info "Konfigurerar Google Cloud Project: $PROJECT_ID"

    # Authenticate
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_warning "Du är inte autentiserad med Google Cloud. Kör 'gcloud auth login'"
        gcloud auth login
    fi

    # Set project
    gcloud config set project $PROJECT_ID

    # Enable required APIs
    log_info "Aktiverar Google Cloud APIs..."
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        container.googleapis.com \
        bigquery.googleapis.com \
        pubsub.googleapis.com \
        cloudfunctions.googleapis.com \
        aiplatform.googleapis.com \
        kms.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com \
        --project=$PROJECT_ID

    log_success "Google Cloud Project konfigurerad"
}

# Create Service Accounts
create_service_accounts() {
    log_info "Skapar Service Accounts..."

    # Web3 Provider Service Account
    gcloud iam service-accounts create web3-provider-sa \
        --display-name="Web3 Provider Service Account" \
        --project=$PROJECT_ID

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:web3-provider-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/bigquery.dataEditor"

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:web3-provider-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/pubsub.publisher"

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:web3-provider-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"

    # BigQuery Service Account
    gcloud iam service-accounts create bigquery-service-sa \
        --display-name="BigQuery Service Account" \
        --project=$PROJECT_ID

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:bigquery-service-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/bigquery.admin"

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:bigquery-service-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/pubsub.subscriber"

    # Security Service Account
    gcloud iam service-accounts create security-service-sa \
        --display-name="Security Service Account" \
        --project=$PROJECT_ID

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:security-service-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/logging.logWriter"

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:security-service-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/monitoring.metricWriter"

    log_success "Service Accounts skapade"
}

# Setup Terraform
setup_terraform() {
    log_info "Konfigurerar Terraform..."

    cd infrastructure/terraform

    # Create terraform.tfvars
    cat > terraform.tfvars << EOF
project_id = "$PROJECT_ID"
region = "$REGION"
zone = "$ZONE"
environment = "$ENVIRONMENT"
EOF

    # Initialize Terraform
    terraform init

    # Validate configuration
    terraform validate

    # Plan deployment
    log_info "Terraform plan:"
    terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="zone=$ZONE"

    # Ask for confirmation
    read -p "Vill du fortsätta med deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment avbrutet av användaren"
        exit 0
    fi

    # Apply deployment
    log_info "Deployar infrastruktur med Terraform..."
    terraform apply -auto-approve -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="zone=$ZONE"

    cd ../..
    log_success "Terraform deployment slutfört"
}

# Build Docker Images
build_docker_images() {
    log_info "Bygger Docker images..."

    # Create Dockerfile för Web3 provider
    cat > infrastructure/docker/Dockerfile.web3-provider << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY crypto/config/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY crypto/ /app/crypto/
COPY adk_agents/ /app/adk_agents/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "-m", "uvicorn", "crypto.services.google_cloud_web3_provider:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

    # Create Dockerfile för BigQuery service
    cat > infrastructure/docker/Dockerfile.bigquery-service << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY crypto/config/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY crypto/ /app/crypto/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "-m", "uvicorn", "crypto.services.web3_bigquery_integration:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

    # Build images
    docker build -t gcr.io/$PROJECT_ID/web3-provider:latest -f infrastructure/docker/Dockerfile.web3-provider .
    docker build -t gcr.io/$PROJECT_ID/bigquery-service:latest -f infrastructure/docker/Dockerfile.bigquery-service .

    # Configure Docker authentication
    gcloud auth configure-docker

    # Push images
    docker push gcr.io/$PROJECT_ID/web3-provider:latest
    docker push gcr.io/$PROJECT_ID/bigquery-service:latest

    log_success "Docker images byggda och pushade"
}

# Deploy Services
deploy_services() {
    log_info "Deployar Cloud Run services..."

    # Deploy Web3 Provider
    gcloud run deploy web3-provider \
        --image gcr.io/$PROJECT_ID/web3-provider:latest \
        --platform managed \
        --region $REGION \
        --service-account web3-provider-sa@$PROJECT_ID.iam.gserviceaccount.com \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 1 \
        --min-instances 1 \
        --max-instances 10 \
        --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,WEB3_GATEWAY_ENABLED=true,ENVIRONMENT=$ENVIRONMENT"

    # Deploy BigQuery Service
    gcloud run deploy bigquery-service \
        --image gcr.io/$PROJECT_ID/bigquery-service:latest \
        --platform managed \
        --region $REGION \
        --service-account bigquery-service-sa@$PROJECT_ID.iam.gserviceaccount.com \
        --allow-unauthenticated \
        --memory 4Gi \
        --cpu 2 \
        --min-instances 1 \
        --max-instances 5 \
        --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID,BIGQUERY_DATASET_TRADING=trading_analytics,BIGQUERY_DATASET_PORTFOLIO=portfolio_tracking,ENVIRONMENT=$ENVIRONMENT"

    log_success "Cloud Run services deployade"
}

# Setup Load Balancer
setup_load_balancer() {
    log_info "Konfigurerar load balancer..."

    # Get service URLs
    WEB3_PROVIDER_URL=$(gcloud run services describe web3-provider --region=$REGION --format="value(status.url)")
    BIGQUERY_SERVICE_URL=$(gcloud run services describe bigquery-service --region=$REGION --format="value(status.url)")

    log_info "Web3 Provider URL: $WEB3_PROVIDER_URL"
    log_info "BigQuery Service URL: $BIGQUERY_SERVICE_URL"

    log_success "Load balancer konfigurerad"
}

# Validate Deployment
validate_deployment() {
    log_info "Validerar deployment..."

    # Test Web3 Provider
    WEB3_PROVIDER_URL=$(gcloud run services describe web3-provider --region=$REGION --format="value(status.url)")
    if curl -f "$WEB3_PROVIDER_URL/health" 2>/dev/null; then
        log_success "Web3 Provider health check lyckades"
    else
        log_error "Web3 Provider health check misslyckades"
    fi

    # Test BigQuery Service
    BIGQUERY_SERVICE_URL=$(gcloud run services describe bigquery-service --region=$REGION --format="value(status.url)")
    if curl -f "$BIGQUERY_SERVICE_URL/health" 2>/dev/null; then
        log_success "BigQuery Service health check lyckades"
    else
        log_error "BigQuery Service health check misslyckades"
    fi

    log_success "Deployment validering slutförd"
}

# Main deployment function
main() {
    log_info "🚀 Startar deployment av Felicia's Finance till Google Cloud..."
    log_info "Project ID: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Environment: $ENVIRONMENT"
    echo

    # Execute deployment steps
    check_prerequisites
    echo

    setup_gcp_project
    echo

    create_service_accounts
    echo

    setup_terraform
    echo

    build_docker_images
    echo

    deploy_services
    echo

    setup_load_balancer
    echo

    validate_deployment
    echo

    log_success "🎉 Deployment slutfört framgångsrikt!"
    log_info "Systemet är nu tillgängligt på följande endpoints:"

    WEB3_PROVIDER_URL=$(gcloud run services describe web3-provider --region=$REGION --format="value(status.url)")
    BIGQUERY_SERVICE_URL=$(gcloud run services describe bigquery-service --region=$REGION --format="value(status.url)")

    echo "🌐 Web3 Provider: $WEB3_PROVIDER_URL"
    echo "📊 BigQuery Service: $BIGQUERY_SERVICE_URL"
    echo "🔒 Security Service: $(gcloud run services describe security-service --region=$REGION --format="value(status.url)")"
    echo
    log_info "📊 Öppna Cloud Console för att se monitoring dashboard:"
    echo "https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
}

# Handle script arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Felicia's Finance - Google Cloud Deployment Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  setup     - Setup Google Cloud project och prerequisites"
        echo "  terraform - Kör bara Terraform deployment"
        echo "  docker    - Bygg och push Docker images"
        echo "  deploy    - Deploya Cloud Run services"
        echo "  validate  - Validera deployment"
        echo "  all       - Kör hela deployment-processen (default)"
        echo ""
        echo "Environment Variables:"
        echo "  PROJECT_ID     - Google Cloud project ID (default: felicia-finance-prod)"
        echo "  REGION         - Google Cloud region (default: europe-west1)"
        echo "  ZONE           - Google Cloud zone (default: europe-west1-b)"
        echo "  ENVIRONMENT    - Deployment environment (default: production)"
        ;;
    "setup")
        check_prerequisites
        setup_gcp_project
        create_service_accounts
        ;;
    "terraform")
        setup_terraform
        ;;
    "docker")
        build_docker_images
        ;;
    "deploy")
        deploy_services
        setup_load_balancer
        ;;
    "validate")
        validate_deployment
        ;;
    "all"|*)
        main
        ;;
esac