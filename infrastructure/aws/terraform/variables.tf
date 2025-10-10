# AWS Region
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

# Environment
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnets" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# Database
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# JWT Secret
variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

# Web3 Configuration
variable "web3_rpc_url" {
  description = "Web3 RPC URL for blockchain interactions"
  type        = string
  sensitive   = true
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "feliciafinance.com"
}

# Container Images
variable "frontend_image" {
  description = "Docker image for frontend service"
  type        = string
  default     = "feliciafinance/frontend:latest"
}

variable "mcp_server_image" {
  description = "Docker image for MCP server service"
  type        = string
  default     = "feliciafinance/mcp-server:latest"
}

variable "crypto_service_image" {
  description = "Docker image for crypto service"
  type        = string
  default     = "feliciafinance/crypto-service:latest"
}

variable "banking_service_image" {
  description = "Docker image for banking service"
  type        = string
  default     = "feliciafinance/banking-service:latest"
}

# ECS Configuration
variable "frontend_cpu" {
  description = "CPU units for frontend service"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory for frontend service"
  type        = number
  default     = 512
}

variable "mcp_server_cpu" {
  description = "CPU units for MCP server service"
  type        = number
  default     = 512
}

variable "mcp_server_memory" {
  description = "Memory for MCP server service"
  type        = number
  default     = 1024
}

# Lambda Configuration
variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 256
}

# Monitoring
variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alerts"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "FeliciaFinance"
    ManagedBy   = "Terraform"
    Owner       = "FeliciaFinanceTeam"
  }
}