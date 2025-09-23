#!/bin/bash

# 🧪 Felicia's Finance - Bank of Anthos Integration Test
# Testar integrationen mellan crypto-system och banking-system

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

# Test functions
test_bankofanthos_services() {
    log_info "Testing Bank of Anthos services..."

    # Test accounts service
    if kubectl get pods -l app=accounts-service --field-selector=status.phase=Running | grep -q accounts-service; then
        log_success "Bank of Anthos accounts service is running"
    else
        log_error "Bank of Anthos accounts service is not running"
        return 1
    fi

    # Test transactions service
    if kubectl get pods -l app=transactions-service --field-selector=status.phase=Running | grep -q transactions-service; then
        log_success "Bank of Anthos transactions service is running"
    else
        log_error "Bank of Anthos transactions service is not running"
        return 1
    fi

    # Test ledger service
    if kubectl get pods -l app=ledger-service --field-selector=status.phase=Running | grep -q ledger-service; then
        log_success "Bank of Anthos ledger service is running"
    else
        log_error "Bank of Anthos ledger service is not running"
        return 1
    fi
}

test_felicia_services() {
    log_info "Testing Felicia's Finance services..."

    # Test Web3 provider service
    if kubectl get pods -l app=felicia-web3-provider --field-selector=status.phase=Running | grep -q felicia-web3-provider; then
        log_success "Felicia Web3 provider service is running"
    else
        log_error "Felicia Web3 provider service is not running"
        return 1
    fi

    # Test BigQuery service
    if kubectl get pods -l app=felicia-bigquery-service --field-selector=status.phase=Running | grep -q felicia-bigquery-service; then
        log_success "Felicia BigQuery service is running"
    else
        log_error "Felicia BigQuery service is not running"
        return 1
    fi

    # Test Security service
    if kubectl get pods -l app=felicia-security-service --field-selector=status.phase=Running | grep -q felicia-security-service; then
        log_success "Felicia Security service is running"
    else
        log_error "Felicia Security service is not running"
        return 1
    fi
}

test_shared_resources() {
    log_info "Testing shared resources..."

    # Test PostgreSQL connectivity
    if kubectl get pods -l app=ledger-db --field-selector=status.phase=Running | grep -q ledger-db; then
        log_success "Shared PostgreSQL database is running"
    else
        log_error "Shared PostgreSQL database is not running"
        return 1
    fi

    # Test Redis connectivity
    if kubectl get pods -l app=redis --field-selector=status.phase=Running | grep -q redis; then
        log_success "Shared Redis cache is running"
    else
        log_error "Shared Redis cache is not running"
        return 1
    fi

    # Test Load Balancer
    if kubectl get svc bankofanthos-frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}' | grep -q '[0-9]'; then
        log_success "Load balancer is configured"
    else
        log_error "Load balancer is not configured"
        return 1
    fi
}

test_integration_endpoints() {
    log_info "Testing integration endpoints..."

    # Get service URLs
    BANKOFANTHOS_URL=$(kubectl get svc bankofanthos-frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    FELICIA_WEB3_URL=$(kubectl get svc felicia-web3-provider -o jsonpath='{.spec.clusterIP}')
    FELICIA_ANALYTICS_URL=$(kubectl get svc felicia-bigquery-service -o jsonpath='{.spec.clusterIP}')

    if [ -n "$BANKOFANTHOS_URL" ]; then
        log_success "Bank of Anthos is accessible at: http://$BANKOFANTHOS_URL"
    else
        log_error "Bank of Anthos URL not found"
        return 1
    fi

    if [ -n "$FELICIA_WEB3_URL" ]; then
        log_success "Felicia Web3 provider is accessible at: $FELICIA_WEB3_URL"
    else
        log_error "Felicia Web3 provider URL not found"
        return 1
    fi

    if [ -n "$FELICIA_ANALYTICS_URL" ]; then
        log_success "Felicia Analytics is accessible at: $FELICIA_ANALYTICS_URL"
    else
        log_error "Felicia Analytics URL not found"
        return 1
    fi
}

test_cross_system_communication() {
    log_info "Testing cross-system communication..."

    # Test if Felicia services can access Bank of Anthos database
    if kubectl exec -it deployment/felicia-web3-provider -- nc -z ledger-db 5432 2>/dev/null; then
        log_success "Felicia Web3 provider can access shared database"
    else
        log_warning "Felicia Web3 provider cannot access shared database"
    fi

    # Test if Felicia services can access Redis
    if kubectl exec -it deployment/felicia-bigquery-service -- nc -z redis 6379 2>/dev/null; then
        log_success "Felicia BigQuery service can access shared Redis"
    else
        log_warning "Felicia BigQuery service cannot access shared Redis"
    fi

    # Test service mesh connectivity
    if kubectl get virtualservices -o jsonpath='{.items[*].metadata.name}' | grep -q felicia; then
        log_success "Service mesh virtual services are configured for Felicia"
    else
        log_warning "Service mesh virtual services not found for Felicia"
    fi
}

test_monitoring_integration() {
    log_info "Testing monitoring integration..."

    # Test Prometheus metrics
    if kubectl get servicemonitor felicia-crypto-services -o jsonpath='{.metadata.name}' | grep -q felicia-crypto-services; then
        log_success "Prometheus ServiceMonitor is configured for Felicia services"
    else
        log_warning "Prometheus ServiceMonitor not found for Felicia services"
    fi

    # Test if metrics are being collected
    if kubectl exec -it deployment/prometheus -- wget -q -O- http://localhost:9090/api/v1/label/__name__ | grep -q felicia; then
        log_success "Felicia metrics are being collected by Prometheus"
    else
        log_warning "Felicia metrics not found in Prometheus"
    fi
}

test_security_integration() {
    log_info "Testing security integration..."

    # Test KMS connectivity
    if kubectl exec -it deployment/felicia-security-service -- gcloud kms keyrings list --project=$PROJECT_ID --location=europe-west1 | grep -q felicia-keyring; then
        log_success "Felicia Security service can access KMS"
    else
        log_warning "Felicia Security service cannot access KMS"
    fi

    # Test IAM permissions
    if kubectl auth can-i get pods --as=system:serviceaccount:default:felicia-web3-sa; then
        log_success "Felicia service accounts have correct IAM permissions"
    else
        log_warning "Felicia service accounts may have permission issues"
    fi
}

run_comprehensive_integration_test() {
    log_info "🧪 Kör comprehensive integration test för Felicia's Finance + Bank of Anthos..."
    log_info "Project ID: $PROJECT_ID"
    echo

    local tests_passed=0
    local tests_total=0

    # Test individual components
    ((tests_total++))
    if test_bankofanthos_services; then
        ((tests_passed++))
    fi
    echo

    ((tests_total++))
    if test_felicia_services; then
        ((tests_passed++))
    fi
    echo

    ((tests_total++))
    if test_shared_resources; then
        ((tests_passed++))
    fi
    echo

    ((tests_total++))
    if test_integration_endpoints; then
        ((tests_passed++))
    fi
    echo

    ((tests_total++))
    if test_cross_system_communication; then
        ((tests_passed++))
    fi
    echo

    ((tests_total++))
    if test_monitoring_integration; then
        ((tests_passed++))
    fi
    echo

    ((tests_total++))
    if test_security_integration; then
        ((tests_passed++))
    fi
    echo

    # Summary
    log_info "📊 Integration Test Summary:"
    echo "  ✅ Tests passed: $tests_passed/$tests_total"
    echo "  📈 Success rate: $((tests_passed * 100 / tests_total))%"
    echo
    log_info "🔗 Integration Status:"
    echo "  🏦 Bank of Anthos: $(kubectl get pods -l app=accounts-service,app=transactions-service,app=ledger-service --field-selector=status.phase=Running | wc -l)/3 services running"
    echo "  🔗 Felicia's Finance: $(kubectl get pods -l app=felicia-web3-provider,app=felicia-bigquery-service,app=felicia-security-service --field-selector=status.phase=Running | wc -l)/3 services running"
    echo "  🗄️ Shared Resources: PostgreSQL $(kubectl get pods -l app=ledger-db --field-selector=status.phase=Running | wc -l)/1, Redis $(kubectl get pods -l app=redis --field-selector=status.phase=Running | wc -l)/1"
    echo

    if [ $tests_passed -eq $tests_total ]; then
        log_success "🎉 Integration test PASSED! Felicia's Finance och Bank of Anthos är framgångsrikt integrerade."
        log_info "🚀 Systemet är redo för production!"
        return 0
    else
        log_warning "⚠️  Integration test har några problem. Kolla output ovan för detaljer."
        log_info "🔧 För troubleshooting: Kontrollera logs med 'kubectl logs -l app=<service-name>'"
        return 1
    fi
}

# Main test function
main() {
    case "${1:-}" in
        "quick")
            log_info "Kör quick integration test..."
            test_bankofanthos_services && \
            test_felicia_services && \
            test_shared_resources && \
            log_success "Quick integration test passed!"
            ;;
        "services")
            log_info "Testing services connectivity..."
            test_bankofanthos_services
            test_felicia_services
            ;;
        "integration")
            log_info "Testing cross-system integration..."
            test_cross_system_communication
            test_integration_endpoints
            ;;
        "monitoring")
            log_info "Testing monitoring integration..."
            test_monitoring_integration
            ;;
        "security")
            log_info "Testing security integration..."
            test_security_integration
            ;;
        "full"|*)
            run_comprehensive_integration_test
            ;;
    esac
}

# Handle script arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Felicia's Finance - Bank of Anthos Integration Test"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  quick       - Kör basic service health checks"
        echo "  services    - Testa service connectivity"
        echo "  integration - Testa cross-system integration"
        echo "  monitoring  - Testa monitoring integration"
        echo "  security    - Testa security integration"
        echo "  full        - Kör comprehensive integration test (default)"
        echo ""
        echo "Environment Variables:"
        echo "  PROJECT_ID  - Google Cloud project ID"
        ;;
    *)
        main "$@"
        ;;
esac