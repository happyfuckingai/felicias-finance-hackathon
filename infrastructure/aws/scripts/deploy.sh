#!/bin/bash

# AWS Deployment Script for Felicia's Finance
# This script handles the complete deployment pipeline for AWS

set -e

# Configuration
ENVIRONMENT=${1:-dev}
AWS_REGION=${AWS_REGION:-us-east-1}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INFRA_ROOT="$PROJECT_ROOT/infrastructure/aws"

# Colors for output
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi

    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials are not configured. Please run 'aws configure'."
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Setup Terraform backend
setup_terraform_backend() {
    log_info "Setting up Terraform backend..."

    cd "$INFRA_ROOT/terraform"

    # Create S3 bucket for Terraform state if it doesn't exist
    STATE_BUCKET="felicia-finance-tf-state-$ENVIRONMENT"
    if ! aws s3 ls "s3://$STATE_BUCKET" &> /dev/null; then
        log_info "Creating Terraform state bucket: $STATE_BUCKET"
        aws s3 mb "s3://$STATE_BUCKET" --region "$AWS_REGION"
        aws s3api put-bucket-versioning \
            --bucket "$STATE_BUCKET" \
            --versioning-configuration Status=Enabled
    fi

    # Create DynamoDB table for state locking if it doesn't exist
    TABLE_NAME="felicia-finance-tf-locks-$ENVIRONMENT"
    if ! aws dynamodb describe-table --table-name "$TABLE_NAME" &> /dev/null; then
        log_info "Creating DynamoDB table for state locking: $TABLE_NAME"
        aws dynamodb create-table \
            --table-name "$TABLE_NAME" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST
    fi

    log_success "Terraform backend setup complete"
}

# Initialize Terraform
terraform_init() {
    log_info "Initializing Terraform..."

    cd "$INFRA_ROOT/terraform"

    terraform init \
        -backend-config="bucket=$STATE_BUCKET" \
        -backend-config="key=terraform/state" \
        -backend-config="region=$AWS_REGION" \
        -backend-config="dynamodb_table=$TABLE_NAME"

    log_success "Terraform initialized"
}

# Plan Terraform changes
terraform_plan() {
    log_info "Planning Terraform changes..."

    cd "$INFRA_ROOT/terraform"

    terraform plan \
        -var-file="$ENVIRONMENT.tfvars" \
        -out=tfplan \
        -input=false

    log_success "Terraform plan created"
}

# Apply Terraform changes
terraform_apply() {
    log_info "Applying Terraform changes..."

    cd "$INFRA_ROOT/terraform"

    terraform apply \
        -auto-approve \
        tfplan

    log_success "Terraform apply complete"
}

# Build and push Docker images
build_and_push_images() {
    log_info "Building and pushing Docker images..."

    cd "$PROJECT_ROOT"

    # Get ECR repository URLs from Terraform output
    ECR_FRONTEND_REPO=$(cd "$INFRA_ROOT/terraform" && terraform output -raw frontend_repository_url)
    ECR_MCP_REPO=$(cd "$INFRA_ROOT/terraform" && terraform output -raw mcp_repository_url)
    ECR_CRYPTO_REPO=$(cd "$INFRA_ROOT/terraform" && terraform output -raw crypto_repository_url)
    ECR_BANKING_REPO=$(cd "$INFRA_ROOT/terraform" && terraform output -raw banking_repository_url)

    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com"

    # Build and push frontend
    log_info "Building frontend image..."
    docker build -t "$ECR_FRONTEND_REPO:latest" ./react_frontend
    docker push "$ECR_FRONTEND_REPO:latest"

    # Build and push MCP server
    log_info "Building MCP server image..."
    docker build -t "$ECR_MCP_REPO:latest" ./crypto_mcp_server
    docker push "$ECR_MCP_REPO:latest"

    # Build and push crypto service
    log_info "Building crypto service image..."
    docker build -t "$ECR_CRYPTO_REPO:latest" ./crypto
    docker push "$ECR_CRYPTO_REPO:latest"

    # Build and push banking service
    log_info "Building banking service image..."
    docker build -t "$ECR_BANKING_REPO:latest" ./bank_of_anthos
    docker push "$ECR_BANKING_REPO:latest"

    log_success "All Docker images built and pushed"
}

# Deploy ECS services
deploy_ecs_services() {
    log_info "Deploying ECS services..."

    cd "$INFRA_ROOT/terraform"

    ECS_CLUSTER=$(terraform output -raw ecs_cluster_name)
    FRONTEND_SERVICE=$(terraform output -raw frontend_service_name)
    MCP_SERVICE=$(terraform output -raw mcp_service_name)

    # Force new deployment for frontend
    aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$FRONTEND_SERVICE" \
        --force-new-deployment

    # Force new deployment for MCP server
    aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$MCP_SERVICE" \
        --force-new-deployment

    log_success "ECS services deployment triggered"
}

# Deploy Lambda functions
deploy_lambda_functions() {
    log_info "Deploying Lambda functions..."

    cd "$PROJECT_ROOT"

    # Package and deploy auth lambda
    cd crypto
    zip -r ../lambda_packages/auth_lambda.zip . -x "*.git*" "*__pycache__*" "*tests*"
    cd ..

    # Package and deploy crypto lambda
    cd crypto
    zip -r ../lambda_packages/crypto_lambda.zip . -x "*.git*" "*__pycache__*" "*tests*"
    cd ..

    # Package and deploy banking lambda
    cd bank_of_anthos
    zip -r ../lambda_packages/banking_lambda.zip . -x "*.git*" "*__pycache__*" "*tests*"
    cd ..

    # Update Lambda functions
    cd "$INFRA_ROOT/terraform"
    AUTH_LAMBDA=$(terraform output -raw auth_lambda_arn)
    CRYPTO_LAMBDA=$(terraform output -raw crypto_lambda_arn)
    BANKING_LAMBDA=$(terraform output -raw banking_lambda_arn)

    aws lambda update-function-code \
        --function-name "$AUTH_LAMBDA" \
        --zip-file fileb://../lambda_packages/auth_lambda.zip

    aws lambda update-function-code \
        --function-name "$CRYPTO_LAMBDA" \
        --zip-file fileb://../lambda_packages/crypto_lambda.zip

    aws lambda update-function-code \
        --function-name "$BANKING_LAMBDA" \
        --zip-file fileb://../lambda_packages/banking_lambda.zip

    log_success "Lambda functions deployed"
}

# Deploy frontend to S3
deploy_frontend_to_s3() {
    log_info "Deploying frontend to S3..."

    cd "$PROJECT_ROOT/react_frontend"

    # Build frontend
    npm run build

    # Get S3 bucket name from Terraform
    cd "$INFRA_ROOT/terraform"
    S3_BUCKET=$(terraform output -raw frontend_bucket)

    # Sync build files to S3
    aws s3 sync "$PROJECT_ROOT/react_frontend/out" "s3://$S3_BUCKET" --delete

    # Invalidate CloudFront cache
    DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)
    aws cloudfront create-invalidation \
        --distribution-id "$DISTRIBUTION_ID" \
        --paths "/*"

    log_success "Frontend deployed to S3 and CloudFront cache invalidated"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."

    cd "$INFRA_ROOT/terraform"

    API_URL=$(terraform output -raw api_gateway_url)
    CLOUDFRONT_URL=$(terraform output -raw cloudfront_domain)

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 60

    # Check API health
    if curl -f "$API_URL/health" &> /dev/null; then
        log_success "API health check passed"
    else
        log_warning "API health check failed"
    fi

    # Check frontend health
    if curl -f "https://$CLOUDFRONT_URL" &> /dev/null; then
        log_success "Frontend health check passed"
    else
        log_warning "Frontend health check failed"
    fi
}

# Main deployment function
main() {
    log_info "Starting AWS deployment for Felicia's Finance (Environment: $ENVIRONMENT)"

    check_prerequisites
    setup_terraform_backend
    terraform_init
    terraform_plan

    echo "Terraform plan created. Review the changes above."
    read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled by user"
        exit 0
    fi

    terraform_apply
    build_and_push_images
    deploy_ecs_services
    deploy_lambda_functions
    deploy_frontend_to_s3
    run_health_checks

    log_success "AWS deployment completed successfully!"
    log_info "Application URLs:"
    cd "$INFRA_ROOT/terraform"
    echo "Frontend: https://$(terraform output -raw cloudfront_domain)"
    echo "API: $(terraform output -raw api_gateway_url)"
}

# Run main function
main "$@"