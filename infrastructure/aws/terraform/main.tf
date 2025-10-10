terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "felicia-finance-aws-terraform-state"
    key    = "terraform/state"
    region = "us-east-1"
  }
}

# AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "FeliciaFinance"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# =============================================================================
# AWS COGNITO USER POOL (Authentication)
# =============================================================================

resource "aws_cognito_user_pool" "felicia_finance_pool" {
  name = "felicia-finance-${var.environment}"

  # Password policy
  password_policy {
    minimum_length    = 8
    require_uppercase = true
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
  }

  # Auto-verified attributes
  auto_verified_attributes = ["email"]

  # User attributes
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }

  schema {
    name                = "given_name"
    attribute_data_type = "String"
    required            = false
    mutable             = true
  }

  schema {
    name                = "family_name"
    attribute_data_type = "String"
    required            = false
    mutable             = true
  }
}

resource "aws_cognito_user_pool_client" "felicia_finance_client" {
  name         = "felicia-finance-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.felicia_finance_pool.id

  # OAuth settings
  supported_identity_providers = ["COGNITO"]
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # Token validity
  access_token_validity  = 1   # 1 hour
  id_token_validity     = 1   # 1 hour
  refresh_token_validity = 30  # 30 days

  # Prevent client secret (for public clients)
  generate_secret = false
}

# =============================================================================
# AWS API GATEWAY
# =============================================================================

resource "aws_api_gateway_rest_api" "felicia_finance_api" {
  name        = "felicia-finance-api-${var.environment}"
  description = "Felicia's Finance API Gateway"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_deployment" "felicia_finance_deployment" {
  depends_on = [
    aws_api_gateway_integration.auth_login_integration,
    aws_api_gateway_integration.auth_register_integration,
    aws_api_gateway_integration.crypto_integration,
    aws_api_gateway_integration.banking_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  stage_name  = var.environment
}

# =============================================================================
# AWS LAMBDA FUNCTIONS
# =============================================================================

# Auth Lambda
resource "aws_lambda_function" "auth_lambda" {
  function_name = "felicia-finance-auth-${var.environment}"
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"
  timeout       = 30

  # Use container image for complex dependencies
  package_type = "Zip"
  filename     = data.archive_file.auth_lambda_zip.output_path
  source_code_hash = data.archive_file.auth_lambda_zip.output_base64sha256

  environment {
    variables = {
      COGNITO_USER_POOL_ID = aws_cognito_user_pool.felicia_finance_pool.id
      JWT_SECRET          = var.jwt_secret
    }
  }

  role = aws_iam_role.lambda_execution_role.arn
}

# Crypto Lambda
resource "aws_lambda_function" "crypto_lambda" {
  function_name = "felicia-finance-crypto-${var.environment}"
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"
  timeout       = 60

  package_type = "Zip"
  filename     = data.archive_file.crypto_lambda_zip.output_path
  source_code_hash = data.archive_file.crypto_lambda_zip.output_base64sha256

  environment {
    variables = {
      WEB3_RPC_URL        = var.web3_rpc_url
      REDIS_URL          = aws_elasticache_cluster.redis.cache_nodes[0].address
      DATABASE_URL       = "postgresql://${aws_db_instance.postgres.username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
    }
  }

  role = aws_iam_role.lambda_execution_role.arn
}

# Banking Lambda
resource "aws_lambda_function" "banking_lambda" {
  function_name = "felicia-finance-banking-${var.environment}"
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"
  timeout       = 60

  package_type = "Zip"
  filename     = data.archive_file.banking_lambda_zip.output_path
  source_code_hash = data.archive_file.banking_lambda_zip.output_base64sha256

  environment {
    variables = {
      DATABASE_URL = "postgresql://${aws_db_instance.postgres.username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
      REDIS_URL    = aws_elasticache_cluster.redis.cache_nodes[0].address
    }
  }

  role = aws_iam_role.lambda_execution_role.arn
}

# =============================================================================
# AWS ECS CLUSTER (For complex services)
# =============================================================================

resource "aws_ecs_cluster" "felicia_finance_cluster" {
  name = "felicia-finance-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Frontend Service
resource "aws_ecs_service" "frontend_service" {
  name            = "felicia-finance-frontend-${var.environment}"
  cluster         = aws_ecs_cluster.felicia_finance_cluster.id
  task_definition = aws_ecs_task_definition.frontend_task.arn
  desired_count   = 2

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend_tg.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.frontend_listener]
}

# MCP Server Service
resource "aws_ecs_service" "mcp_server_service" {
  name            = "felicia-finance-mcp-${var.environment}"
  cluster         = aws_ecs_cluster.felicia_finance_cluster.id
  task_definition = aws_ecs_task_definition.mcp_server_task.arn
  desired_count   = 1
}

# =============================================================================
# AWS BEDROCK (AI/ML Services)
# =============================================================================

# Bedrock Model Access
resource "aws_bedrock_model_invocation_logging_configuration" "felicia_finance_logging" {
  logging_config {
    embedding_data_delivery_enabled = true
    image_data_delivery_enabled     = true
    text_data_delivery_enabled      = true

    s3_config {
      bucket_name = aws_s3_bucket.bedrock_logs.bucket
      key_prefix  = "bedrock-logs"
    }
  }
}

# Custom Bedrock Agent for Felicia's Finance
resource "aws_bedrock_agent" "felicia_finance_agent" {
  name                = "felicia-finance-agent-${var.environment}"
  description         = "AI Agent for Felicia's Finance financial analysis and recommendations"
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn
  foundation_model     = "anthropic.claude-3-sonnet-20240229-v1:0"

  instruction = "You are Felicia, an AI financial assistant. Help users with crypto trading, banking, portfolio management, and financial planning. Always prioritize user security and provide accurate financial advice."

  # Enable action groups for different financial operations
  action_group {
    action_group_name = "CryptoOperations"
    description       = "Handle cryptocurrency trading and analysis"

    function_schema {
      functions = [
        {
          name        = "analyze_portfolio"
          description = "Analyze user's crypto portfolio"
          parameters = {
            portfolio = {
              type        = "object"
              description = "User's crypto holdings"
            }
          }
        },
        {
          name        = "get_market_data"
          description = "Get current market data for cryptocurrencies"
          parameters = {
            symbols = {
              type        = "array"
              description = "Crypto symbols to fetch"
              items = {
                type = "string"
              }
            }
          }
        }
      ]
    }
  }

  action_group {
    action_group_name = "BankingOperations"
    description       = "Handle banking and account operations"

    function_schema {
      functions = [
        {
          name        = "check_balance"
          description = "Check account balance"
          parameters = {
            account_id = {
              type        = "string"
              description = "Account ID to check"
            }
          }
        },
        {
          name        = "transfer_funds"
          description = "Transfer funds between accounts"
          parameters = {
            from_account = {
              type        = "string"
              description = "Source account"
            }
            to_account = {
              type        = "string"
              description = "Destination account"
            }
            amount = {
              type        = "number"
              description = "Amount to transfer"
            }
          }
        }
      ]
    }
  }
}

# =============================================================================
# DATABASES
# =============================================================================

# PostgreSQL RDS
resource "aws_db_instance" "postgres" {
  identifier             = "felicia-finance-db-${var.environment}"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  max_allocated_storage  = 100
  storage_type           = "gp2"
  db_name                = "feliciafinance"
  username               = "feliciaadmin"
  password               = var.db_password
  parameter_group_name   = "default.postgres15"
  skip_final_snapshot    = true
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
}

# Redis ElastiCache
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "felicia-finance-cache-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  security_group_ids   = [aws_security_group.redis_sg.id]
  subnet_group_name    = aws_elasticache_subnet_group.redis_subnet_group.name
}

# =============================================================================
# MONITORING & LOGGING
# =============================================================================

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/felicia-finance-${var.environment}"
  retention_in_days = 30
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_cpu_alarm" {
  alarm_name          = "felicia-finance-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.felicia_finance_cluster.name
    ServiceName = aws_ecs_service.frontend_service.name
  }
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "felicia-finance-alerts-${var.environment}"
}

# =============================================================================
# DATA SOURCES (for Lambda packages)
# =============================================================================

data "archive_file" "auth_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../crypto/"
  output_path = "${path.module}/lambda_packages/auth_lambda.zip"
  excludes    = ["__pycache__", "*.pyc", ".git", "tests/"]
}

data "archive_file" "crypto_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../crypto/"
  output_path = "${path.module}/lambda_packages/crypto_lambda.zip"
  excludes    = ["__pycache__", "*.pyc", ".git", "tests/"]
}

data "archive_file" "banking_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../bank_of_anthos/"
  output_path = "${path.module}/lambda_packages/banking_lambda.zip"
  excludes    = ["__pycache__", "*.pyc", ".git", "tests/"]
}