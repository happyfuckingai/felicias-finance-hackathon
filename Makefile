# Makefile for Felicia's Finance AWS Deployment

.PHONY: help init plan apply deploy destroy clean

# Default environment
ENV ?= dev

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

help: ## Show this help message
	@echo "$(BLUE)Felicia's Finance AWS Deployment$(NC)"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

init: ## Initialize Terraform
	@echo "$(BLUE)Initializing Terraform for $(ENV) environment...$(NC)"
	cd infrastructure/aws/terraform && terraform init

plan: ## Plan Terraform changes
	@echo "$(BLUE)Planning Terraform changes for $(ENV) environment...$(NC)"
	cd infrastructure/aws/terraform && terraform plan -var-file=$(ENV).tfvars

apply: ## Apply Terraform changes
	@echo "$(BLUE)Applying Terraform changes for $(ENV) environment...$(NC)"
	cd infrastructure/aws/terraform && terraform apply -var-file=$(ENV).tfvars

deploy: ## Full deployment (Terraform + Docker + Services)
	@echo "$(BLUE)Starting full deployment for $(ENV) environment...$(NC)"
	./infrastructure/aws/scripts/deploy.sh $(ENV)

destroy: ## Destroy all AWS resources (USE WITH CAUTION!)
	@echo "$(RED)WARNING: This will destroy all AWS resources for $(ENV) environment!$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "$(YELLOW)Destroying AWS resources...$(NC)"; \
		cd infrastructure/aws/terraform && terraform destroy -var-file=$(ENV).tfvars; \
	else \
		echo "$(BLUE)Destroy cancelled.$(NC)"; \
	fi

clean: ## Clean up temporary files
	@echo "$(BLUE)Cleaning up temporary files...$(NC)"
	find . -name "*.tfstate*" -type f -delete
	find . -name "*.tfplan" -type f -delete
	find . -name ".terraform" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf lambda_packages/

outputs: ## Show Terraform outputs
	@echo "$(BLUE)Terraform outputs for $(ENV) environment:$(NC)"
	cd infrastructure/aws/terraform && terraform output

validate: ## Validate Terraform configuration
	@echo "$(BLUE)Validating Terraform configuration...$(NC)"
	cd infrastructure/aws/terraform && terraform validate

fmt: ## Format Terraform files
	@echo "$(BLUE)Formatting Terraform files...$(NC)"
	cd infrastructure/aws/terraform && terraform fmt -recursive

check: ## Run pre-deployment checks
	@echo "$(BLUE)Running pre-deployment checks...$(NC)"
	@command -v aws >/dev/null 2>&1 || { echo "$(RED)AWS CLI is not installed$(NC)"; exit 1; }
	@command -v terraform >/dev/null 2>&1 || { echo "$(RED)Terraform is not installed$(NC)"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Docker is not installed$(NC)"; exit 1; }
	@aws sts get-caller-identity >/dev/null 2>&1 || { echo "$(RED)AWS credentials not configured$(NC)"; exit 1; }
	@echo "$(GREEN)All checks passed!$(NC)"

# Environment-specific targets
dev-init: ## Initialize for dev environment
	$(MAKE) ENV=dev init

dev-plan: ## Plan for dev environment
	$(MAKE) ENV=dev plan

dev-apply: ## Apply for dev environment
	$(MAKE) ENV=dev apply

dev-deploy: ## Deploy to dev environment
	$(MAKE) ENV=dev deploy

prod-init: ## Initialize for prod environment
	$(MAKE) ENV=prod init

prod-plan: ## Plan for prod environment
	$(MAKE) ENV=prod plan

prod-apply: ## Apply for prod environment
	$(MAKE) ENV=prod apply

prod-deploy: ## Deploy to prod environment
	$(MAKE) ENV=prod deploy

# Development helpers
build-frontend: ## Build frontend Docker image
	@echo "$(BLUE)Building frontend Docker image...$(NC)"
	docker build -t feliciafinance/frontend:latest ./react_frontend

build-mcp: ## Build MCP server Docker image
	@echo "$(BLUE)Building MCP server Docker image...$(NC)"
	docker build -t feliciafinance/mcp-server:latest ./crypto_mcp_server

build-crypto: ## Build crypto service Docker image
	@echo "$(BLUE)Building crypto service Docker image...$(NC)"
	docker build -t feliciafinance/crypto-service:latest ./crypto

build-banking: ## Build banking service Docker image
	@echo "$(BLUE)Building banking service Docker image...$(NC)"
	docker build -t feliciafinance/banking-service:latest ./bank_of_anthos

build-all: build-frontend build-mcp build-crypto build-banking ## Build all Docker images

# Testing
test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd react_frontend && npm test

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd crypto && python -m pytest
	cd bank_of_anthos && python -m pytest

test-all: test-frontend test-backend ## Run all tests

# Logs and monitoring
logs-frontend: ## Show frontend ECS service logs
	@echo "$(BLUE)Showing frontend logs...$(NC)"
	aws logs tail /ecs/felicia-finance-$(ENV) --filter-pattern "frontend" --follow

logs-mcp: ## Show MCP server ECS service logs
	@echo "$(BLUE)Showing MCP server logs...$(NC)"
	aws logs tail /ecs/felicia-finance-$(ENV) --filter-pattern "mcp-server" --follow

logs-api: ## Show API Gateway logs
	@echo "$(BLUE)Showing API Gateway logs...$(NC)"
	aws logs tail /aws/api-gateway/felicia-finance-api-$(ENV) --follow

# Health checks
health-check: ## Run health checks
	@echo "$(BLUE)Running health checks...$(NC)"
	./infrastructure/aws/scripts/health-check.sh $(ENV)