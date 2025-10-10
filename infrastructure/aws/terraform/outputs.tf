# API Gateway
output "api_gateway_url" {
  description = "API Gateway URL"
  value       = aws_api_gateway_deployment.felicia_finance_deployment.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_api_gateway_rest_api.felicia_finance_api.id
}

# Cognito
output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.felicia_finance_pool.id
}

output "cognito_client_id" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.felicia_finance_client.id
}

output "cognito_domain" {
  description = "Cognito Domain"
  value       = aws_cognito_user_pool_domain.felicia_finance_domain.domain
}

# ECS
output "ecs_cluster_name" {
  description = "ECS Cluster Name"
  value       = aws_ecs_cluster.felicia_finance_cluster.name
}

output "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  value       = aws_ecs_cluster.felicia_finance_cluster.arn
}

# Load Balancer
output "load_balancer_dns" {
  description = "Load Balancer DNS Name"
  value       = aws_lb.felicia_finance_lb.dns_name
}

# Database
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

# Redis
output "redis_endpoint" {
  description = "Redis ElastiCache endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis ElastiCache port"
  value       = aws_elasticache_cluster.redis.port
}

# Bedrock
output "bedrock_agent_id" {
  description = "Bedrock Agent ID"
  value       = aws_bedrock_agent.felicia_finance_agent.id
}

output "bedrock_agent_arn" {
  description = "Bedrock Agent ARN"
  value       = aws_bedrock_agent.felicia_finance_agent.arn
}

# S3 Buckets
output "frontend_bucket" {
  description = "Frontend S3 bucket name"
  value       = aws_s3_bucket.frontend_bucket.bucket
}

output "logs_bucket" {
  description = "Logs S3 bucket name"
  value       = aws_s3_bucket.logs_bucket.bucket
}

output "bedrock_logs_bucket" {
  description = "Bedrock logs S3 bucket name"
  value       = aws_s3_bucket.bedrock_logs.bucket
}

# CloudFront
output "cloudfront_distribution_id" {
  description = "CloudFront Distribution ID"
  value       = aws_cloudfront_distribution.felicia_finance_distribution.id
}

output "cloudfront_domain" {
  description = "CloudFront Distribution Domain"
  value       = aws_cloudfront_distribution.felicia_finance_distribution.domain_name
}

# VPC
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.felicia_finance_vpc.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public_subnets[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private_subnets[*].id
}

# Security Groups
output "alb_security_group" {
  description = "ALB Security Group ID"
  value       = aws_security_group.alb_sg.id
}

output "ecs_security_group" {
  description = "ECS Security Group ID"
  value       = aws_security_group.ecs_sg.id
}

output "rds_security_group" {
  description = "RDS Security Group ID"
  value       = aws_security_group.rds_sg.id
}

output "redis_security_group" {
  description = "Redis Security Group ID"
  value       = aws_security_group.redis_sg.id
}

# IAM Roles
output "ecs_task_execution_role_arn" {
  description = "ECS Task Execution Role ARN"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "bedrock_agent_role_arn" {
  description = "Bedrock Agent Role ARN"
  value       = aws_iam_role.bedrock_agent_role.arn
}

# Lambda Functions
output "auth_lambda_arn" {
  description = "Auth Lambda Function ARN"
  value       = aws_lambda_function.auth_lambda.arn
}

output "crypto_lambda_arn" {
  description = "Crypto Lambda Function ARN"
  value       = aws_lambda_function.crypto_lambda.arn
}

output "banking_lambda_arn" {
  description = "Banking Lambda Function ARN"
  value       = aws_lambda_function.banking_lambda.arn
}