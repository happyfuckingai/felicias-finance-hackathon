# Felicia's Finance - Multi-Agent Orchestration Platform
# Makefile for development, testing, and deployment

.PHONY: help install-dev deploy-local clean-local test test-all test-coverage build docker-build docker-push deploy-prod lint format security-scan

# Default target
.DEFAULT_GOAL := help

# Variables
PROJECT_NAME := felicias-finance
NAMESPACE_DEV := felicias-finance-dev
NAMESPACE_PROD := felicias-finance
DOCKER_REGISTRY := gcr.io/your-project-id
VERSION := $(shell git describe --tags --always --dirty)
PYTHON := python3
PIP := pip3
KUBECTL := kubectl
HELM := helm
TERRAFORM := terraform

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

##@ Help
help: ## Display this help
	@echo "$(BLUE)Felicia's Finance - Multi-Agent Orchestration Platform$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development Setup
install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(RESET)"
	@if command -v python3 >/dev/null 2>&1; then \
		$(PIP) install --upgrade pip; \
		$(PIP) install -r requirements-dev.txt || echo "$(YELLOW)requirements-dev.txt not found, skipping Python deps$(RESET)"; \
	else \
		echo "$(RED)Python3 not found, skipping Python dependencies$(RESET)"; \
	fi
	@if command -v npm >/dev/null 2>&1; then \
		npm install || echo "$(YELLOW)package.json not found, skipping Node.js deps$(RESET)"; \
	else \
		echo "$(YELLOW)npm not found, skipping Node.js dependencies$(RESET)"; \
	fi
	@if command -v go >/dev/null 2>&1; then \
		go mod download || echo "$(YELLOW)go.mod not found, skipping Go deps$(RESET)"; \
	else \
		echo "$(YELLOW)Go not found, skipping Go dependencies$(RESET)"; \
	fi
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
	else \
		echo "$(YELLOW)pre-commit not found, install with: pip install pre-commit$(RESET)"; \
	fi
	@echo "$(GREEN)Development environment setup complete!$(RESET)"

setup-local-cluster: ## Set up local Kubernetes cluster
	@echo "$(GREEN)Setting up local Kubernetes cluster...$(RESET)"
	@if command -v minikube >/dev/null 2>&1; then \
		minikube start --driver=docker --memory=8192 --cpus=4; \
		minikube addons enable ingress; \
		minikube addons enable metrics-server; \
	elif command -v kind >/dev/null 2>&1; then \
		kind create cluster --name $(PROJECT_NAME) --config=infrastructure/kind/cluster-config.yaml || \
		kind create cluster --name $(PROJECT_NAME); \
	else \
		echo "$(RED)Neither minikube nor kind found. Please install one of them.$(RESET)"; \
		exit 1; \
	fi

##@ Building
build: ## Build all components
	@echo "$(GREEN)Building all components...$(RESET)"
	@$(MAKE) build-orchestrator
	@$(MAKE) build-banking-agent
	@$(MAKE) build-crypto-agent

build-orchestrator: ## Build orchestrator component
	@echo "$(GREEN)Building orchestrator...$(RESET)"
	@if [ -f "orchestrator/Dockerfile" ]; then \
		docker build -t $(PROJECT_NAME)/orchestrator:$(VERSION) orchestrator/; \
	elif [ -f "Dockerfile.orchestrator" ]; then \
		docker build -f Dockerfile.orchestrator -t $(PROJECT_NAME)/orchestrator:$(VERSION) .; \
	else \
		echo "$(YELLOW)No orchestrator Dockerfile found, skipping...$(RESET)"; \
	fi

build-banking-agent: ## Build banking agent
	@echo "$(GREEN)Building banking agent...$(RESET)"
	@if [ -f "adk_agents/banking/Dockerfile" ]; then \
		docker build -t $(PROJECT_NAME)/banking-agent:$(VERSION) adk_agents/banking/; \
	elif [ -f "Dockerfile.banking" ]; then \
		docker build -f Dockerfile.banking -t $(PROJECT_NAME)/banking-agent:$(VERSION) .; \
	else \
		echo "$(YELLOW)No banking agent Dockerfile found, skipping...$(RESET)"; \
	fi

build-crypto-agent: ## Build crypto agent
	@echo "$(GREEN)Building crypto agent...$(RESET)"
	@if [ -f "adk_agents/crypto/Dockerfile" ]; then \
		docker build -t $(PROJECT_NAME)/crypto-agent:$(VERSION) adk_agents/crypto/; \
	elif [ -f "Dockerfile.crypto" ]; then \
		docker build -f Dockerfile.crypto -t $(PROJECT_NAME)/crypto-agent:$(VERSION) .; \
	else \
		echo "$(YELLOW)No crypto agent Dockerfile found, skipping...$(RESET)"; \
	fi

docker-build: build ## Alias for build

docker-push: ## Push Docker images to registry
	@echo "$(GREEN)Pushing Docker images to registry...$(RESET)"
	@docker tag $(PROJECT_NAME)/orchestrator:$(VERSION) $(DOCKER_REGISTRY)/$(PROJECT_NAME)/orchestrator:$(VERSION)
	@docker tag $(PROJECT_NAME)/banking-agent:$(VERSION) $(DOCKER_REGISTRY)/$(PROJECT_NAME)/banking-agent:$(VERSION)
	@docker tag $(PROJECT_NAME)/crypto-agent:$(VERSION) $(DOCKER_REGISTRY)/$(PROJECT_NAME)/crypto-agent:$(VERSION)
	@docker push $(DOCKER_REGISTRY)/$(PROJECT_NAME)/orchestrator:$(VERSION)
	@docker push $(DOCKER_REGISTRY)/$(PROJECT_NAME)/banking-agent:$(VERSION)
	@docker push $(DOCKER_REGISTRY)/$(PROJECT_NAME)/crypto-agent:$(VERSION)

##@ Testing
test: ## Run unit tests
	@echo "$(GREEN)Running unit tests...$(RESET)"
	@if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ] || [ -d "tests" ]; then \
		$(PYTHON) -m pytest tests/unit/ -v || echo "$(YELLOW)No unit tests found$(RESET)"; \
	fi
	@if [ -f "package.json" ]; then \
		npm test || echo "$(YELLOW)No npm tests configured$(RESET)"; \
	fi
	@if [ -f "go.mod" ]; then \
		go test ./... || echo "$(YELLOW)No Go tests found$(RESET)"; \
	fi

test-integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(RESET)"
	@if [ -d "tests/integration" ]; then \
		$(PYTHON) -m pytest tests/integration/ -v; \
	else \
		echo "$(YELLOW)No integration tests found$(RESET)"; \
	fi

test-e2e: ## Run end-to-end tests
	@echo "$(GREEN)Running end-to-end tests...$(RESET)"
	@if [ -d "tests/e2e" ]; then \
		$(PYTHON) -m pytest tests/e2e/ -v; \
	else \
		echo "$(YELLOW)No e2e tests found$(RESET)"; \
	fi

test-all: test test-integration test-e2e ## Run all tests

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	@if command -v pytest >/dev/null 2>&1; then \
		$(PYTHON) -m pytest --cov=. --cov-report=html --cov-report=term tests/ || echo "$(YELLOW)Coverage tests failed$(RESET)"; \
		echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"; \
	else \
		echo "$(YELLOW)pytest-cov not installed, run: pip install pytest-cov$(RESET)"; \
	fi

##@ Code Quality
lint: ## Run linting
	@echo "$(GREEN)Running linting...$(RESET)"
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; \
	else \
		echo "$(YELLOW)flake8 not found, install with: pip install flake8$(RESET)"; \
	fi
	@if command -v pylint >/dev/null 2>&1; then \
		find . -name "*.py" -exec pylint {} \; || true; \
	else \
		echo "$(YELLOW)pylint not found, install with: pip install pylint$(RESET)"; \
	fi
	@if command -v golangci-lint >/dev/null 2>&1; then \
		golangci-lint run || echo "$(YELLOW)No Go files to lint$(RESET)"; \
	fi

format: ## Format code
	@echo "$(GREEN)Formatting code...$(RESET)"
	@if command -v black >/dev/null 2>&1; then \
		black . --line-length 88; \
	else \
		echo "$(YELLOW)black not found, install with: pip install black$(RESET)"; \
	fi
	@if command -v isort >/dev/null 2>&1; then \
		isort .; \
	else \
		echo "$(YELLOW)isort not found, install with: pip install isort$(RESET)"; \
	fi
	@if command -v gofmt >/dev/null 2>&1; then \
		find . -name "*.go" -exec gofmt -w {} \; || echo "$(YELLOW)No Go files to format$(RESET)"; \
	fi
	@if command -v prettier >/dev/null 2>&1; then \
		prettier --write "**/*.{js,ts,json,yaml,yml,md}" || echo "$(YELLOW)Prettier formatting failed$(RESET)"; \
	fi

security-scan: ## Run security scans
	@echo "$(GREEN)Running security scans...$(RESET)"
	@if command -v bandit >/dev/null 2>&1; then \
		bandit -r . -f json -o security-report.json || echo "$(YELLOW)Bandit scan completed with warnings$(RESET)"; \
	else \
		echo "$(YELLOW)bandit not found, install with: pip install bandit$(RESET)"; \
	fi
	@if command -v safety >/dev/null 2>&1; then \
		safety check || echo "$(YELLOW)Safety check completed$(RESET)"; \
	else \
		echo "$(YELLOW)safety not found, install with: pip install safety$(RESET)"; \
	fi
	@if command -v trivy >/dev/null 2>&1; then \
		trivy fs . || echo "$(YELLOW)Trivy scan completed$(RESET)"; \
	else \
		echo "$(YELLOW)trivy not found, install from: https://github.com/aquasecurity/trivy$(RESET)"; \
	fi

##@ Local Deployment
deploy-local: ## Deploy to local Kubernetes cluster
	@echo "$(GREEN)Deploying to local cluster...$(RESET)"
	@$(MAKE) setup-local-cluster || true
	@$(KUBECTL) create namespace $(NAMESPACE_DEV) --dry-run=client -o yaml | $(KUBECTL) apply -f -
	@if [ -d "infrastructure/helm/$(PROJECT_NAME)" ]; then \
		$(HELM) upgrade --install $(PROJECT_NAME)-dev infrastructure/helm/$(PROJECT_NAME) \
			--namespace $(NAMESPACE_DEV) \
			--values infrastructure/helm/values/development.yaml \
			--set image.tag=$(VERSION) \
			--wait; \
	elif [ -d "infrastructure/k8s" ]; then \
		$(KUBECTL) apply -f infrastructure/k8s/ -n $(NAMESPACE_DEV); \
	else \
		echo "$(YELLOW)No Kubernetes manifests found$(RESET)"; \
	fi
	@echo "$(GREEN)Local deployment complete!$(RESET)"
	@echo "$(BLUE)Access services with:$(RESET)"
	@echo "  kubectl port-forward svc/orchestrator 8080:8080 -n $(NAMESPACE_DEV)"

clean-local: ## Clean up local deployment
	@echo "$(GREEN)Cleaning up local deployment...$(RESET)"
	@$(HELM) uninstall $(PROJECT_NAME)-dev -n $(NAMESPACE_DEV) || true
	@$(KUBECTL) delete namespace $(NAMESPACE_DEV) || true
	@if command -v minikube >/dev/null 2>&1; then \
		minikube delete || true; \
	elif command -v kind >/dev/null 2>&1; then \
		kind delete cluster --name $(PROJECT_NAME) || true; \
	fi

##@ Production Deployment
deploy-infrastructure: ## Deploy infrastructure with Terraform
	@echo "$(GREEN)Deploying infrastructure...$(RESET)"
	@if [ -d "infrastructure/terraform" ]; then \
		cd infrastructure/terraform && \
		$(TERRAFORM) init && \
		$(TERRAFORM) plan -var-file="production.tfvars" && \
		$(TERRAFORM) apply -var-file="production.tfvars"; \
	else \
		echo "$(RED)No Terraform configuration found$(RESET)"; \
		exit 1; \
	fi

deploy-prod: ## Deploy to production
	@echo "$(GREEN)Deploying to production...$(RESET)"
	@$(KUBECTL) create namespace $(NAMESPACE_PROD) --dry-run=client -o yaml | $(KUBECTL) apply -f -
	@if [ -d "infrastructure/helm/$(PROJECT_NAME)" ]; then \
		$(HELM) upgrade --install $(PROJECT_NAME) infrastructure/helm/$(PROJECT_NAME) \
			--namespace $(NAMESPACE_PROD) \
			--values infrastructure/helm/values/production.yaml \
			--set image.tag=$(VERSION) \
			--wait; \
	else \
		echo "$(RED)No Helm chart found$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Production deployment complete!$(RESET)"

##@ Monitoring
logs: ## View application logs
	@echo "$(GREEN)Viewing application logs...$(RESET)"
	@$(KUBECTL) logs -f deployment/$(PROJECT_NAME)-orchestrator -n $(NAMESPACE_DEV) || \
	$(KUBECTL) logs -f deployment/orchestrator -n $(NAMESPACE_DEV) || \
	echo "$(YELLOW)No orchestrator deployment found$(RESET)"

status: ## Check deployment status
	@echo "$(GREEN)Checking deployment status...$(RESET)"
	@echo "$(BLUE)Pods:$(RESET)"
	@$(KUBECTL) get pods -n $(NAMESPACE_DEV) || echo "$(YELLOW)No pods in dev namespace$(RESET)"
	@echo "$(BLUE)Services:$(RESET)"
	@$(KUBECTL) get services -n $(NAMESPACE_DEV) || echo "$(YELLOW)No services in dev namespace$(RESET)"
	@echo "$(BLUE)Ingress:$(RESET)"
	@$(KUBECTL) get ingress -n $(NAMESPACE_DEV) || echo "$(YELLOW)No ingress in dev namespace$(RESET)"

port-forward: ## Set up port forwarding for local access
	@echo "$(GREEN)Setting up port forwarding...$(RESET)"
	@echo "$(BLUE)Orchestrator: http://localhost:8080$(RESET)"
	@$(KUBECTL) port-forward svc/orchestrator 8080:8080 -n $(NAMESPACE_DEV) &
	@echo "$(BLUE)Banking Agent: http://localhost:8081$(RESET)"
	@$(KUBECTL) port-forward svc/banking-agent 8081:8080 -n $(NAMESPACE_DEV) &
	@echo "$(BLUE)Crypto Agent: http://localhost:8082$(RESET)"
	@$(KUBECTL) port-forward svc/crypto-agent 8082:8080 -n $(NAMESPACE_DEV) &
	@echo "$(GREEN)Port forwarding active. Press Ctrl+C to stop.$(RESET)"

##@ Database
db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(RESET)"
	@if [ -f "alembic.ini" ]; then \
		alembic upgrade head; \
	elif [ -f "migrate.py" ]; then \
		$(PYTHON) migrate.py; \
	else \
		echo "$(YELLOW)No migration system found$(RESET)"; \
	fi

db-seed: ## Seed database with test data
	@echo "$(GREEN)Seeding database...$(RESET)"
	@if [ -f "seed.py" ]; then \
		$(PYTHON) seed.py; \
	elif [ -f "scripts/seed.py" ]; then \
		$(PYTHON) scripts/seed.py; \
	else \
		echo "$(YELLOW)No seed script found$(RESET)"; \
	fi

##@ Utilities
clean: ## Clean up build artifacts
	@echo "$(GREEN)Cleaning up build artifacts...$(RESET)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	@rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/
	@docker system prune -f || true

docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(RESET)"
	@if command -v sphinx-build >/dev/null 2>&1; then \
		sphinx-build -b html docs/ docs/_build/html/; \
	else \
		echo "$(YELLOW)Sphinx not found, install with: pip install sphinx$(RESET)"; \
	fi

version: ## Show version information
	@echo "$(BLUE)Version: $(VERSION)$(RESET)"
	@echo "$(BLUE)Git Commit: $(shell git rev-parse HEAD)$(RESET)"
	@echo "$(BLUE)Build Date: $(shell date)$(RESET)"

env-check: ## Check environment prerequisites
	@echo "$(GREEN)Checking environment prerequisites...$(RESET)"
	@echo -n "Docker: "; command -v docker >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"
	@echo -n "Kubernetes: "; command -v kubectl >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"
	@echo -n "Helm: "; command -v helm >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"
	@echo -n "Terraform: "; command -v terraform >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"
	@echo -n "Python3: "; command -v python3 >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"
	@echo -n "Node.js: "; command -v node >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"
	@echo -n "Go: "; command -v go >/dev/null 2>&1 && echo "$(GREEN)✓$(RESET)" || echo "$(RED)✗$(RESET)"

##@ Development Workflow
dev: ## Start development environment
	@echo "$(GREEN)Starting development environment...$(RESET)"
	@$(MAKE) install-dev
	@$(MAKE) deploy-local
	@$(MAKE) port-forward

dev-stop: ## Stop development environment
	@echo "$(GREEN)Stopping development environment...$(RESET)"
	@pkill -f "kubectl port-forward" || true
	@$(MAKE) clean-local

dev-restart: ## Restart development environment
	@$(MAKE) dev-stop
	@$(MAKE) dev

##@ CI/CD
ci: ## Run CI pipeline locally
	@echo "$(GREEN)Running CI pipeline...$(RESET)"
	@$(MAKE) env-check
	@$(MAKE) lint
	@$(MAKE) security-scan
	@$(MAKE) test-all
	@$(MAKE) build
	@echo "$(GREEN)CI pipeline completed successfully!$(RESET)"

release: ## Create a new release
	@echo "$(GREEN)Creating new release...$(RESET)"
	@$(MAKE) ci
	@$(MAKE) docker-push
	@echo "$(GREEN)Release $(VERSION) created successfully!$(RESET)"
