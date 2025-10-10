# =============================================================================
# AWS SECRETS MANAGER
# =============================================================================

# JWT Secret
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "felicia-finance/jwt-secret-${var.environment}"
  description             = "JWT signing secret for Felicia Finance"
  recovery_window_in_days = 0

  tags = merge(var.tags, {
    Name = "felicia-finance-jwt-secret-${var.environment}"
  })
}

resource "aws_secretsmanager_secret_version" "jwt_secret_version" {
  secret_id = aws_secretsmanager_secret.jwt_secret.id
  secret_string = jsonencode({
    jwt_secret = var.jwt_secret
  })
}

# Database Password
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "felicia-finance/db-password-${var.environment}"
  description             = "Database password for Felicia Finance"
  recovery_window_in_days = 0

  tags = merge(var.tags, {
    Name = "felicia-finance-db-password-${var.environment}"
  })
}

resource "aws_secretsmanager_secret_version" "db_password_version" {
  secret_id = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    password = var.db_password
  })
}

# Web3 RPC URL
resource "aws_secretsmanager_secret" "web3_rpc_url" {
  name                    = "felicia-finance/web3-rpc-url-${var.environment}"
  description             = "Web3 RPC URL for blockchain interactions"
  recovery_window_in_days = 0

  tags = merge(var.tags, {
    Name = "felicia-finance-web3-rpc-url-${var.environment}"
  })
}

resource "aws_secretsmanager_secret_version" "web3_rpc_url_version" {
  secret_id = aws_secretsmanager_secret.web3_rpc_url.id
  secret_string = jsonencode({
    rpc_url = var.web3_rpc_url
  })
}

# =============================================================================
# PARAMETER STORE (for non-sensitive config)
# =============================================================================

resource "aws_ssm_parameter" "environment_config" {
  name  = "/felicia-finance/${var.environment}/config"
  type  = "String"
  value = jsonencode({
    environment     = var.environment
    aws_region      = var.aws_region
    domain_name     = var.domain_name
    api_gateway_url = aws_api_gateway_deployment.felicia_finance_deployment.invoke_url
    cloudfront_url  = aws_cloudfront_distribution.felicia_finance_distribution.domain_name
  })

  tags = merge(var.tags, {
    Name = "felicia-finance-environment-config-${var.environment}"
  })
}

resource "aws_ssm_parameter" "bedrock_config" {
  name  = "/felicia-finance/${var.environment}/bedrock"
  type  = "String"
  value = jsonencode({
    agent_id     = aws_bedrock_agent.felicia_finance_agent.id
    agent_arn    = aws_bedrock_agent.felicia_finance_agent.arn
    model_id     = "anthropic.claude-3-sonnet-20240229-v1:0"
    region       = var.aws_region
  })

  tags = merge(var.tags, {
    Name = "felicia-finance-bedrock-config-${var.environment}"
  })
}