#!/bin/bash

# 🧪 Felicia's Finance - Deployment Validation Script
# Detta script validerar deployment och testar alla services

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

# Test functions
test_service_health() {
    local service_name=$1
    local service_url=$2

    log_info "Testing $service_name health endpoint..."

    if curl -f -s "$service_url/health" > /dev/null 2>&1; then
        log_success "$service_name health check passed"
        return 0
    else
        log_error "$service_name health check failed"
        return 1
    fi
}

test_web3_provider() {
    local service_url=$1

    log_info "Testing Web3 Provider functionality..."

    # Test basic Web3 functionality
    local test_payload='{
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }'

    if curl -f -s -X POST "$service_url/api/v1/web3" \
        -H "Content-Type: application/json" \
        -d "$test_payload" > /dev/null 2>&1; then
        log_success "Web3 Provider API test passed"
        return 0
    else
        log_error "Web3 Provider API test failed"
        return 1
    fi
}

test_bigquery_service() {
    local service_url=$1

    log_info "Testing BigQuery Service functionality..."

    # Test wallet analysis
    local test_payload='{
        "wallet_address": "0x742d35Cc6A3d2f6c6E6E6D6E6E6E6E6E6E6E6E6E6E6E6E6E",
        "include_live_data": false,
        "include_risk_analysis": true
    }'

    if curl -f -s -X POST "$service_url/api/v1/portfolio/analyze" \
        -H "Content-Type: application/json" \
        -d "$test_payload" > /dev/null 2>&1; then
        log_success "BigQuery Service portfolio analysis test passed"
        return 0
    else
        log_error "BigQuery Service portfolio analysis test failed"
        return 1
    fi
}

test_cross_chain_balance() {
    local service_url=$1

    log_info "Testing cross-chain balance functionality..."

    # Test cross-chain balance query
    local test_payload='{
        "wallet_address": "0x742d35Cc6A3d2f6c6E6E6D6E6E6E6E6E6E6E6E6E6E6E6E6E",
        "tokens": ["0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5"]
    }'

    if curl -f -s -X POST "$service_url/api/v1/balance/cross-chain" \
        -H "Content-Type: application/json" \
        -d "$test_payload" > /dev/null 2>&1; then
        log_success "Cross-chain balance test passed"
        return 0
    else
        log_error "Cross-chain balance test failed"
        return 1
    fi
}

test_security_service() {
    local service_url=$1

    log_info "Testing Security Service functionality..."

    # Test security scoring
    local test_payload='{
        "token_address": "0xA0b86a33E6441e88C5F2712C3E9b74F5b8F1b8E5",
        "chain": "ethereum"
    }'

    if curl -f -s -X POST "$service_url/api/v1/security/score" \
        -H "Content-Type: application/json" \
        -d "$test_payload" > /dev/null 2>&1; then
        log_success "Security Service scoring test passed"
        return 0
    else
        log_error "Security Service scoring test failed"
        return 1
    fi
}

test_load_balancer() {
    local lb_url=$1

    log_info "Testing Load Balancer functionality..."

    # Test load balancer health
    if curl -f -s "$lb_url/health" > /dev/null 2>&1; then
        log_success "Load Balancer health check passed"
        return 0
    else
        log_error "Load Balancer health check failed"
        return 1
    fi
}

test_gcp_services() {
    log_info "Testing Google Cloud services..."

    # Test BigQuery
    if gcloud bigquery datasets list --project=$PROJECT_ID --format="value(datasetId)" | grep -q "trading_analytics"; then
        log_success "BigQuery datasets created successfully"
    else
        log_error "BigQuery datasets not found"
        return 1
    fi

    # Test Pub/Sub topics
    if gcloud pubsub topics list --project=$PROJECT_ID --format="value(name)" | grep -q "crypto-trades"; then
        log_success "Pub/Sub topics created successfully"
    else
        log_error "Pub/Sub topics not found"
        return 1
    fi

    # Test KMS
    if gcloud kms keyrings list --project=$PROJECT_ID --location=$REGION --format="value(name)" | grep -q "felicia-keyring"; then
        log_success "KMS keyring created successfully"
    else
        log_error "KMS keyring not found"
        return 1
    fi
}

test_monitoring() {
    log_info "Testing monitoring och alerting..."

    # Check if uptime checks exist
    if gcloud monitoring uptime-check-configs list --project=$PROJECT_ID --format="value(displayName)" | grep -q "web3-provider-uptime"; then
        log_success "Uptime checks configured successfully"
    else
        log_warning "Uptime checks not found"
    fi

    # Check if alert policies exist
    if gcloud monitoring policies list --project=$PROJECT_ID --format="value(displayName)" | grep -q "High Error Rate Alert"; then
        log_success "Alert policies configured successfully"
    else
        log_warning "Alert policies not found"
    fi
}

test_performance() {
    log_info "Testing performance metrics..."

    local service_url=$1
    local start_time=$(date +%s)

    # Simple performance test
    for i in {1..10}; do
        curl -s -o /dev/null -w "%{http_code}" "$service_url/health" > /dev/null 2>&1
    done

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ $duration -lt 30 ]; then
        log_success "Performance test passed (completed in ${duration}s)"
        return 0
    else
        log_warning "Performance test took longer than expected (${duration}s)"
        return 1
    fi
}

run_comprehensive_validation() {
    log_info "🧪 Kör comprehensive validation av Felicia's Finance deployment..."
    log_info "Project ID: $PROJECT_ID"
    log_info "Region: $REGION"
    echo

    # Get service URLs
    WEB3_PROVIDER_URL=$(gcloud run services describe web3-provider --region=$REGION --format="value(status.url)")
    BIGQUERY_SERVICE_URL=$(gcloud run services describe bigquery-service --region=$REGION --format="value(status.url)")
    SECURITY_SERVICE_URL=$(gcloud run services describe security-service --region=$REGION --format="value(status.url)")
    LOAD_BALANCER_IP=$(gcloud compute forwarding-rules describe felicia-finance-forwarding-rule --global --format="value(IPAddress)")
    LOAD_BALANCER_URL="http://$LOAD_BALANCER_IP"

    log_info "Service URLs:"
    echo "  🌐 Web3 Provider: $WEB3_PROVIDER_URL"
    echo "  📊 BigQuery Service: $BIGQUERY_SERVICE_URL"
    echo "  🔒 Security Service: $SECURITY_SERVICE_URL"
    echo "  ⚖️ Load Balancer: $LOAD_BALANCER_URL"
    echo

    local tests_passed=0
    local tests_total=0

    # Test Google Cloud services
    ((tests_total++))
    if test_gcp_services; then
        ((tests_passed++))
    fi
    echo

    # Test Load Balancer
    ((tests_total++))
    if test_load_balancer "$LOAD_BALANCER_URL"; then
        ((tests_passed++))
    fi
    echo

    # Test Web3 Provider
    ((tests_total++))
    if test_service_health "Web3 Provider" "$WEB3_PROVIDER_URL"; then
        ((tests_passed++))
    fi

    ((tests_total++))
    if test_web3_provider "$WEB3_PROVIDER_URL"; then
        ((tests_passed++))
    fi
    echo

    # Test BigQuery Service
    ((tests_total++))
    if test_service_health "BigQuery Service" "$BIGQUERY_SERVICE_URL"; then
        ((tests_passed++))
    fi

    ((tests_total++))
    if test_bigquery_service "$BIGQUERY_SERVICE_URL"; then
        ((tests_passed++))
    fi

    ((tests_total++))
    if test_cross_chain_balance "$WEB3_PROVIDER_URL"; then
        ((tests_passed++))
    fi
    echo

    # Test Security Service
    ((tests_total++))
    if test_service_health "Security Service" "$SECURITY_SERVICE_URL"; then
        ((tests_passed++))
    fi

    ((tests_total++))
    if test_security_service "$SECURITY_SERVICE_URL"; then
        ((tests_passed++))
    fi
    echo

    # Test Monitoring
    ((tests_total++))
    if test_monitoring; then
        ((tests_passed++))
    fi
    echo

    # Test Performance
    ((tests_total++))
    if test_performance "$WEB3_PROVIDER_URL"; then
        ((tests_passed++))
    fi
    echo

    # Summary
    log_info "📊 Validation Summary:"
    echo "  ✅ Tests passed: $tests_passed/$tests_total"
    echo "  📈 Success rate: $((tests_passed * 100 / tests_total))%"

    if [ $tests_passed -eq $tests_total ]; then
        log_success "🎉 All tests passed! Deployment is healthy and ready for production."
        return 0
    else
        log_warning "⚠️  Some tests failed. Check the output above for details."
        return 1
    fi
}

# Main validation function
main() {
    case "${1:-}" in
        "quick")
            log_info "Kör quick validation..."
            # Just test basic health
            WEB3_PROVIDER_URL=$(gcloud run services describe web3-provider --region=$REGION --format="value(status.url)")
            test_service_health "Web3 Provider" "$WEB3_PROVIDER_URL"
            test_service_health "BigQuery Service" "$(gcloud run services describe bigquery-service --region=$REGION --format="value(status.url)")"
            ;;
        "full"|*)
            run_comprehensive_validation
            ;;
    esac
}

# Handle script arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Felicia's Finance - Deployment Validation Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  quick  - Kör basic health checks"
        echo "  full   - Kör comprehensive validation (default)"
        echo ""
        echo "Environment Variables:"
        echo "  PROJECT_ID - Google Cloud project ID"
        echo "  REGION     - Google Cloud region"
        ;;
    *)
        main "$@"
        ;;
esac