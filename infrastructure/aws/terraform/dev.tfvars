# Development Environment Configuration
environment = "dev"
aws_region  = "us-east-1"

# Database
db_password = "CHANGE_THIS_TO_A_SECURE_PASSWORD"

# JWT Secret
jwt_secret = "CHANGE_THIS_TO_A_SECURE_JWT_SECRET"

# Web3 Configuration
web3_rpc_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"

# Domain (optional for dev)
domain_name = "dev.feliciafinance.com"

# Container Configuration
frontend_cpu    = 256
frontend_memory = 512
mcp_server_cpu = 512
mcp_server_memory = 1024

# Lambda Configuration
lambda_timeout     = 30
lambda_memory_size = 256

# Monitoring
enable_monitoring  = true
log_retention_days = 30

# Tags
tags = {
  Project     = "FeliciaFinance"
  Environment = "dev"
  Owner       = "FeliciaFinanceTeam"
  ManagedBy   = "Terraform"
}