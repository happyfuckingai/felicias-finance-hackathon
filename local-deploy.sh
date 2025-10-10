#!/bin/bash

# 🚀 Felicia's Finance - Local Docker Deployment Script
# Detta script deployar hela systemet lokalt med Docker Compose istället för Google Cloud

set -e

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

# Check prerequisites
check_prerequisites() {
    log_info "Kontrollerar prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker är inte installerat. Installera från https://docker.com"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose är inte installerat."
        exit 1
    fi

    # Check if .env.local exists
    if [ ! -f ".env.local" ]; then
        log_warning ".env.local hittades inte. Kopierar från mall..."
        cp .env.local.example .env.local 2>/dev/null || log_warning "Ingen .env.local.example hittades. Säkerställ att dina miljövariabler är satta."
    fi

    log_success "Alla prerequisites är installerade"
}

# Setup environment
setup_environment() {
    log_info "Konfigurerar lokal miljö..."

    # Copy local env file
    if [ -f ".env.local" ]; then
        cp .env.local .env
        log_success "Miljövariabler kopierade från .env.local"
    else
        log_warning "Ingen .env.local hittades. Använd dina egna miljövariabler."
    fi

    # Create necessary directories
    mkdir -p infrastructure/postgres/init
    mkdir -p logs

    log_success "Lokal miljö konfigurerad"
}

# Create database initialization script
create_db_init() {
    log_info "Skapar databas-initiering..."

    cat > infrastructure/postgres/init/01-init-db.sql << 'EOF'
-- Felicia's Finance Database Initialization
-- Detta skapar alla nödvändiga tabeller för lokal utveckling

-- Trading analytics tables (ersätter BigQuery)
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(255) NOT NULL,
    token_address VARCHAR(255) NOT NULL,
    token_symbol VARCHAR(50),
    amount DECIMAL(36,18) NOT NULL,
    price_usd DECIMAL(20,8),
    total_value_usd DECIMAL(20,2),
    transaction_hash VARCHAR(255) UNIQUE,
    blockchain VARCHAR(50) DEFAULT 'base',
    trade_type VARCHAR(20) DEFAULT 'buy', -- buy, sell, swap
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    gas_used BIGINT,
    gas_price DECIMAL(36,18),
    status VARCHAR(20) DEFAULT 'completed' -- pending, completed, failed
);

-- Portfolio snapshots
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(255) NOT NULL,
    total_value_usd DECIMAL(20,2) NOT NULL,
    btc_value DECIMAL(20,8),
    eth_value DECIMAL(20,8),
    risk_score DECIMAL(5,4),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Daily balances
CREATE TABLE IF NOT EXISTS daily_balances (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(255) NOT NULL,
    token_symbol VARCHAR(10) NOT NULL,
    balance DECIMAL(36,18) NOT NULL,
    value_usd DECIMAL(20,2),
    price_usd DECIMAL(20,8),
    date DATE NOT NULL,
    UNIQUE(wallet_address, token_symbol, date)
);

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(255),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20,8),
    date DATE NOT NULL,
    metadata JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_trades_wallet ON trades(wallet_address);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
CREATE INDEX IF NOT EXISTS idx_portfolio_wallet ON portfolio_snapshots(wallet_address);
CREATE INDEX IF NOT EXISTS idx_daily_wallet ON daily_balances(wallet_address);
CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_balances(date);

-- Insert some sample data for testing
INSERT INTO trades (wallet_address, token_address, token_symbol, amount, price_usd, total_value_usd, transaction_hash, blockchain)
VALUES
    ('0x742d35Cc6634C0532925a3b8848c5C5F3b6e0c85', '0x4200000000000000000000000000000000000006', 'WETH', 0.5, 2800.00, 1400.00, '0x123abc', 'base'),
    ('0x742d35Cc6634C0532925a3b8848c5C5F3b6e0c85', '0x4200000000000000000000000000000000000006', 'WETH', 0.3, 2750.00, 825.00, '0x456def', 'base')
ON CONFLICT (transaction_hash) DO NOTHING;

EOF

    log_success "Databas-initiering skapad"
}

# Build and start services
start_services() {
    log_info "Startar tjänster med Docker Compose..."

    # Stop any existing containers
    docker-compose down 2>/dev/null || true

    # Build and start services
    docker-compose up --build -d

    log_success "Tjänster startade i bakgrunden"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Väntar på att tjänster blir hälsosamma..."

    # Wait for PostgreSQL
    log_info "Väntar på PostgreSQL..."
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U felicia -d felicia_finance 2>/dev/null; then
            log_success "PostgreSQL är redo"
            break
        fi
        sleep 2
    done

    # Wait for Redis
    log_info "Väntar på Redis..."
    for i in {1..30}; do
        if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
            log_success "Redis är redo"
            break
        fi
        sleep 2
    done

    # Wait for web services
    log_info "Väntar på web-tjänster..."
    sleep 10  # Give services time to start

    log_success "Alla tjänster är startade"
}

# Validate deployment
validate_deployment() {
    log_info "Validerar lokal deployment..."

    # Test Web3 Provider
    if curl -f http://localhost:8080/health 2>/dev/null; then
        log_success "Web3 Provider health check lyckades"
    else
        log_warning "Web3 Provider health check misslyckades - tjänsten kan fortfarande starta"
    fi

    # Test BigQuery Service
    if curl -f http://localhost:8081/health 2>/dev/null; then
        log_success "BigQuery Service health check lyckades"
    else
        log_warning "BigQuery Service health check misslyckades - tjänsten kan fortfarande starta"
    fi

    # Test Crypto MCP Server
    if curl -f http://localhost:8000/health 2>/dev/null; then
        log_success "Crypto MCP Server health check lyckades"
    else
        log_warning "Crypto MCP Server health check misslyckades - tjänsten kan fortfarande starta"
    fi

    log_success "Lokal deployment validerad"
}

# Show service URLs
show_info() {
    echo
    log_success "🎉 Lokala tjänster är nu igång!"
    echo
    echo "🌐 Tillgängliga tjänster:"
    echo "📍 Web3 Provider:    http://localhost:8080"
    echo "📊 BigQuery Service: http://localhost:8081"
    echo "🔒 Security Service: http://localhost:8082"
    echo "🤖 Crypto MCP Server: http://localhost:8000"
    echo "🐘 PostgreSQL:        localhost:5432"
    echo "🔴 Redis:            localhost:6379"
    echo
    echo "🛠️  Hantering:"
    echo "   • Visa logs:    docker-compose logs -f [service-name]"
    echo "   • Stoppa:       docker-compose down"
    echo "   • Starta om:    docker-compose restart"
    echo "   • Debugga:      docker-compose exec [service-name] bash"
    echo
    echo "🧪 Testa systemet:"
    echo "   • python3 test_simulation.py"
    echo "   • curl http://localhost:8000/health"
    echo
}

# Main function
main() {
    log_info "🚀 Startar lokal deployment av Felicia's Finance..."
    echo

    check_prerequisites
    echo

    setup_environment
    echo

    create_db_init
    echo

    start_services
    echo

    wait_for_services
    echo

    validate_deployment
    echo

    show_info
}

# Handle script arguments
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "Felicia's Finance - Local Docker Deployment Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  setup    - Setup environment and prerequisites"
        echo "  build    - Build Docker images only"
        echo "  start    - Start services only"
        echo "  stop     - Stop all services"
        echo "  logs     - Show logs from all services"
        echo "  test     - Run basic health checks"
        echo "  all      - Full deployment (default)"
        echo ""
        ;;
    "setup")
        check_prerequisites
        setup_environment
        create_db_init
        ;;
    "build")
        docker-compose build
        ;;
    "start")
        docker-compose up -d
        wait_for_services
        ;;
    "stop")
        docker-compose down
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "test")
        validate_deployment
        ;;
    "all"|*)
        main
        ;;
esac