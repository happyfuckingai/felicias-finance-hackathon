# Production Environment Configuration
environment = "prod"
aws_region  = "us-east-1"

# Database
db_password = "CHANGE_THIS_TO_A_SECURE_PASSWORD"

# JWT Secret
jwt_secret = "CHANGE_THIS_TO_A_SECURE_JWT_SECRET"

# Web3 Configuration
web3_rpc_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"

# Domain
domain_name = "feliciafinance.com"

# Container Configuration (Higher resources for prod)
frontend_cpu    = 512
frontend_memory = 1024
mcp_server_cpu = 1024
mcp_server_memory = 2048

# Lambda Configuration
lambda_timeout     = 60
lambda_memory_size = 512

# Monitoring
enable_monitoring  = true
log_retention_days = 90

# Tags
tags = {
  Project     = "FeliciaFinance"
  Environment = "prod"
  Owner       = "FeliciaFinanceTeam"
  ManagedBy   = "Terraform"
  Backup      = "Daily"
}