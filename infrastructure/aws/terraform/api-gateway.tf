# =============================================================================
# API GATEWAY INTEGRATIONS
# =============================================================================

# Auth API Resources
resource "aws_api_gateway_resource" "auth_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_rest_api.felicia_finance_api.root_resource_id
  path_part   = "auth"
}

resource "aws_api_gateway_resource" "auth_login_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_resource.auth_resource.id
  path_part   = "login"
}

resource "aws_api_gateway_resource" "auth_register_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_resource.auth_resource.id
  path_part   = "register"
}

resource "aws_api_gateway_resource" "auth_me_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_resource.auth_resource.id
  path_part   = "me"
}

resource "aws_api_gateway_resource" "auth_logout_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_resource.auth_resource.id
  path_part   = "logout"
}

# Crypto API Resources
resource "aws_api_gateway_resource" "crypto_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_rest_api.felicia_finance_api.root_resource_id
  path_part   = "crypto"
}

resource "aws_api_gateway_resource" "crypto_portfolio_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_resource.crypto_resource.id
  path_part   = "portfolio"
}

resource "aws_api_gateway_resource" "crypto_trading_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_resource.crypto_resource.id
  path_part   = "trading"
}

# Banking API Resources
resource "aws_api_gateway_resource" "banking_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_rest_api.felicia_finance_api.root_resource_id
  path_part   = "banking"
}

resource "aws_api_gateway_resource" "banking_accounts_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_resource.banking_resource.id
  path_part   = "accounts"
}

resource "aws_api_gateway_resource" "banking_transactions_resource" {
  rest_api_id = aws_api_gateway_rest_api.felicia_finance_api.id
  parent_id   = aws_api_gateway_resource.banking_resource.id
  path_part   = "transactions"
}

# =============================================================================
# API GATEWAY METHODS AND INTEGRATIONS
# =============================================================================

# Auth Login
resource "aws_api_gateway_method" "auth_login_method" {
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id   = aws_api_gateway_resource.auth_login_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_login_integration" {
  rest_api_id             = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id             = aws_api_gateway_resource.auth_login_resource.id
  http_method             = aws_api_gateway_method.auth_login_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.auth_lambda.invoke_arn
}

# Auth Register
resource "aws_api_gateway_method" "auth_register_method" {
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id   = aws_api_gateway_resource.auth_register_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_register_integration" {
  rest_api_id             = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id             = aws_api_gateway_resource.auth_register_resource.id
  http_method             = aws_api_gateway_method.auth_register_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.auth_lambda.invoke_arn
}

# Auth Me (Protected)
resource "aws_api_gateway_method" "auth_me_method" {
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id   = aws_api_gateway_resource.auth_me_resource.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "auth_me_integration" {
  rest_api_id             = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id             = aws_api_gateway_resource.auth_me_resource.id
  http_method             = aws_api_gateway_method.auth_me_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.auth_lambda.invoke_arn
}

# Auth Logout
resource "aws_api_gateway_method" "auth_logout_method" {
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id   = aws_api_gateway_resource.auth_logout_resource.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "auth_logout_integration" {
  rest_api_id             = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id             = aws_api_gateway_resource.auth_logout_resource.id
  http_method             = aws_api_gateway_method.auth_logout_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.auth_lambda.invoke_arn
}

# Crypto Portfolio
resource "aws_api_gateway_method" "crypto_portfolio_method" {
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id   = aws_api_gateway_resource.crypto_portfolio_resource.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "crypto_portfolio_integration" {
  rest_api_id             = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id             = aws_api_gateway_resource.crypto_portfolio_resource.id
  http_method             = aws_api_gateway_method.crypto_portfolio_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crypto_lambda.invoke_arn
}

# Crypto Trading
resource "aws_api_gateway_method" "crypto_trading_method" {
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id   = aws_api_gateway_resource.crypto_trading_resource.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "crypto_trading_integration" {
  rest_api_id             = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id             = aws_api_gateway_resource.crypto_trading_resource.id
  http_method             = aws_api_gateway_method.crypto_trading_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crypto_lambda.invoke_arn
}

# Banking Accounts
resource "aws_api_gateway_method" "banking_accounts_method" {
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id   = aws_api_gateway_resource.banking_accounts_resource.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "banking_accounts_integration" {
  rest_api_id             = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id             = aws_api_gateway_resource.banking_accounts_resource.id
  http_method             = aws_api_gateway_method.banking_accounts_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.banking_lambda.invoke_arn
}

# Banking Transactions
resource "aws_api_gateway_method" "banking_transactions_method" {
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id   = aws_api_gateway_resource.banking_transactions_resource.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito_authorizer.id
}

resource "aws_api_gateway_integration" "banking_transactions_integration" {
  rest_api_id             = aws_api_gateway_rest_api.felicia_finance_api.id
  resource_id             = aws_api_gateway_resource.banking_transactions_resource.id
  http_method             = aws_api_gateway_method.banking_transactions_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.banking_lambda.invoke_arn
}

# =============================================================================
# COGNITO AUTHORIZER
# =============================================================================

resource "aws_api_gateway_authorizer" "cognito_authorizer" {
  name          = "felicia-finance-cognito-authorizer-${var.environment}"
  rest_api_id   = aws_api_gateway_rest_api.felicia_finance_api.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [aws_cognito_user_pool.felicia_finance_pool.arn]
}

# =============================================================================
# LAMBDA PERMISSIONS
# =============================================================================

resource "aws_lambda_permission" "auth_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvokeAuth"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.felicia_finance_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "crypto_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvokeCrypto"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.crypto_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.felicia_finance_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "banking_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvokeBanking"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.banking_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.felicia_finance_api.execution_arn}/*/*"
}