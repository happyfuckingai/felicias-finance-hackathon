#!/bin/bash

# Health Check Script for Felicia's Finance AWS Deployment
# Usage: ./health-check.sh [environment]

set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Felicia's Finance Health Check - ${ENVIRONMENT} Environment${NC}"
echo "=================================================="

# Load environment variables
if [ -f "${PROJECT_ROOT}/infrastructure/aws/terraform/${ENVIRONMENT}.tfvars" ]; then
    echo -e "${BLUE}Loading Terraform variables...${NC}"
    # Extract key variables from tfvars (simplified parsing)
    AWS_REGION=$(grep '^aws_region' "${PROJECT_ROOT}/infrastructure/aws/terraform/${ENVIRONMENT}.tfvars" | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
    PROJECT_NAME=$(grep '^project_name' "${PROJECT_ROOT}/infrastructure/aws/terraform/${ENVIRONMENT}.tfvars" | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
else
    echo -e "${YELLOW}Warning: Could not find tfvars file, using defaults${NC}"
    AWS_REGION="us-east-1"
    PROJECT_NAME="felicia-finance"
fi

echo "Environment: $ENVIRONMENT"
echo "AWS Region: $AWS_REGION"
echo "Project Name: $PROJECT_NAME"
echo ""

# Function to check command success
check_command() {
    local cmd="$1"
    local description="$2"

    echo -e "${BLUE}Checking: ${description}${NC}"
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

# Function to check URL
check_url() {
    local url="$1"
    local description="$2"
    local expected_code="${3:-200}"

    echo -e "${BLUE}Checking: ${description}${NC}"
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "^$expected_code$"; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        return 1
    fi
}

FAILED_CHECKS=0

# AWS CLI and credentials
echo -e "${YELLOW}AWS Configuration Checks${NC}"
echo "-------------------------"

check_command "aws sts get-caller-identity" "AWS CLI authentication" || ((FAILED_CHECKS++))
check_command "aws ec2 describe-regions --region $AWS_REGION" "AWS region access" || ((FAILED_CHECKS++))

# Terraform state
echo ""
echo -e "${YELLOW}Terraform Checks${NC}"
echo "------------------"

check_command "cd ${PROJECT_ROOT}/infrastructure/aws/terraform && terraform validate" "Terraform configuration validation" || ((FAILED_CHECKS++))
check_command "cd ${PROJECT_ROOT}/infrastructure/aws/terraform && terraform state list" "Terraform state exists" || ((FAILED_CHECKS++))

# Docker images
echo ""
echo -e "${YELLOW}Docker Checks${NC}"
echo "---------------"

check_command "docker images | grep -q feliciafinance/frontend" "Frontend Docker image exists" || ((FAILED_CHECKS++))
check_command "docker images | grep -q feliciafinance/mcp-server" "MCP server Docker image exists" || ((FAILED_CHECKS++))
check_command "docker images | grep -q feliciafinance/crypto-service" "Crypto service Docker image exists" || ((FAILED_CHECKS++))
check_command "docker images | grep -q feliciafinance/banking-service" "Banking service Docker image exists" || ((FAILED_CHECKS++))

# AWS Resources
echo ""
echo -e "${YELLOW}AWS Resources Checks${NC}"
echo "-----------------------"

# VPC
check_command "aws ec2 describe-vpcs --filters Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-vpc --region $AWS_REGION | jq -r '.Vpcs[0].VpcId'" "VPC exists" || ((FAILED_CHECKS++))

# ECS Cluster
check_command "aws ecs describe-clusters --cluster ${PROJECT_NAME}-${ENVIRONMENT} --region $AWS_REGION | jq -r '.clusters[0].status'" "ECS cluster exists and is ACTIVE" || ((FAILED_CHECKS++))

# API Gateway
API_ID=$(aws apigateway get-rest-apis --region $AWS_REGION --query "items[?name=='${PROJECT_NAME}-api-${ENVIRONMENT}'].id" --output text)
if [ -n "$API_ID" ] && [ "$API_ID" != "None" ]; then
    echo -e "${GREEN}✓ PASS${NC} - API Gateway exists"
else
    echo -e "${RED}✗ FAIL${NC} - API Gateway not found"
    ((FAILED_CHECKS++))
fi

# CloudFront Distribution
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='${PROJECT_NAME}-frontend-${ENVIRONMENT}'].Id" --output text)
if [ -n "$DISTRIBUTION_ID" ] && [ "$DISTRIBUTION_ID" != "None" ]; then
    echo -e "${GREEN}✓ PASS${NC} - CloudFront distribution exists"
    CLOUDFRONT_URL="https://$(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query 'Distribution.DomainName' --output text)"
else
    echo -e "${RED}✗ FAIL${NC} - CloudFront distribution not found"
    ((FAILED_CHECKS++))
fi

# RDS Database
check_command "aws rds describe-db-instances --db-instance-identifier ${PROJECT_NAME}-${ENVIRONMENT} --region $AWS_REGION | jq -r '.DBInstances[0].DBInstanceStatus'" "RDS instance exists and is available" || ((FAILED_CHECKS++))

# ElastiCache Redis
check_command "aws elasticache describe-cache-clusters --cache-cluster-id ${PROJECT_NAME}-${ENVIRONMENT} --region $AWS_REGION | jq -r '.CacheClusters[0].CacheClusterStatus'" "ElastiCache cluster exists and is available" || ((FAILED_CHECKS++))

# Application Load Balancer
ALB_ARN=$(aws elbv2 describe-load-balancers --names ${PROJECT_NAME}-${ENVIRONMENT}-alb --region $AWS_REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || echo "")
if [ -n "$ALB_ARN" ] && [ "$ALB_ARN" != "None" ]; then
    echo -e "${GREEN}✓ PASS${NC} - ALB exists"
    ALB_DNS=$(aws elbv2 describe-load-balancers --names ${PROJECT_NAME}-${ENVIRONMENT}-alb --region $AWS_REGION --query 'LoadBalancers[0].DNSName' --output text)
else
    echo -e "${RED}✗ FAIL${NC} - ALB not found"
    ((FAILED_CHECKS++))
fi

# Service Endpoints
echo ""
echo -e "${YELLOW}Service Endpoint Checks${NC}"
echo "--------------------------"

# Frontend via CloudFront
if [ -n "$CLOUDFRONT_URL" ]; then
    check_url "$CLOUDFRONT_URL" "Frontend via CloudFront" || ((FAILED_CHECKS++))
fi

# API Gateway
if [ -n "$API_ID" ]; then
    API_URL="https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/$ENVIRONMENT"
    check_url "$API_URL/health" "API Gateway health endpoint" || ((FAILED_CHECKS++))
fi

# ALB
if [ -n "$ALB_DNS" ]; then
    check_url "http://$ALB_DNS/health" "ALB health endpoint" || ((FAILED_CHECKS++))
fi

# ECS Services
echo ""
echo -e "${YELLOW}ECS Services Checks${NC}"
echo "----------------------"

SERVICES=("frontend" "mcp-server" "crypto-service" "banking-service")
for service in "${SERVICES[@]}"; do
    SERVICE_STATUS=$(aws ecs describe-services --cluster ${PROJECT_NAME}-${ENVIRONMENT} --services ${PROJECT_NAME}-${ENVIRONMENT}-$service --region $AWS_REGION --query 'services[0].status' --output text 2>/dev/null || echo "MISSING")
    if [ "$SERVICE_STATUS" = "ACTIVE" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $service service is ACTIVE"

        # Check running tasks
        RUNNING_COUNT=$(aws ecs describe-services --cluster ${PROJECT_NAME}-${ENVIRONMENT} --services ${PROJECT_NAME}-${ENVIRONMENT}-$service --region $AWS_REGION --query 'services[0].runningCount' --output text)
        DESIRED_COUNT=$(aws ecs describe-services --cluster ${PROJECT_NAME}-${ENVIRONMENT} --services ${PROJECT_NAME}-${ENVIRONMENT}-$service --region $AWS_REGION --query 'services[0].desiredCount' --output text)

        if [ "$RUNNING_COUNT" -eq "$DESIRED_COUNT" ] && [ "$DESIRED_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✓ PASS${NC} - $service tasks: $RUNNING_COUNT/$DESIRED_COUNT running"
        else
            echo -e "${RED}✗ FAIL${NC} - $service tasks: $RUNNING_COUNT/$DESIRED_COUNT running"
            ((FAILED_CHECKS++))
        fi
    else
        echo -e "${RED}✗ FAIL${NC} - $service service status: $SERVICE_STATUS"
        ((FAILED_CHECKS++))
    fi
done

# Lambda Functions
echo ""
echo -e "${YELLOW}Lambda Functions Checks${NC}"
echo "---------------------------"

LAMBDAS=("auth-login" "auth-register" "crypto-prices" "banking-transactions")
for lambda in "${LAMBDAS[@]}"; do
    LAMBDA_ARN=$(aws lambda get-function --function-name ${PROJECT_NAME}-${ENVIRONMENT}-$lambda --region $AWS_REGION --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "")
    if [ -n "$LAMBDA_ARN" ] && [ "$LAMBDA_ARN" != "None" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $lambda Lambda function exists"
    else
        echo -e "${RED}✗ FAIL${NC} - $lambda Lambda function not found"
        ((FAILED_CHECKS++))
    fi
done

# Cognito User Pool
echo ""
echo -e "${YELLOW}Cognito Checks${NC}"
echo "-----------------"

USER_POOL_ID=$(aws cognito-idp list-user-pools --max-results 10 --region $AWS_REGION --query "UserPools[?Name=='${PROJECT_NAME}-${ENVIRONMENT}'].Id" --output text)
if [ -n "$USER_POOL_ID" ] && [ "$USER_POOL_ID" != "None" ]; then
    echo -e "${GREEN}✓ PASS${NC} - Cognito User Pool exists"
else
    echo -e "${RED}✗ FAIL${NC} - Cognito User Pool not found"
    ((FAILED_CHECKS++))
fi

# Summary
echo ""
echo "=================================================="
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL HEALTH CHECKS PASSED!${NC}"
    echo "Your Felicia's Finance deployment is healthy and ready for use."
    exit 0
else
    echo -e "${RED}❌ $FAILED_CHECKS health checks failed!${NC}"
    echo "Please review the failed checks above and fix any issues."
    exit 1
fi