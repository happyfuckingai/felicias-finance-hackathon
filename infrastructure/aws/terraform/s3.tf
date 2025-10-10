# =============================================================================
# S3 BUCKETS
# =============================================================================

# Frontend Bucket
resource "aws_s3_bucket" "frontend_bucket" {
  bucket = "felicia-finance-frontend-${var.environment}-${random_string.bucket_suffix.result}"

  tags = merge(var.tags, {
    Name = "felicia-finance-frontend-${var.environment}"
  })
}

resource "aws_s3_bucket_public_access_block" "frontend_bucket_pab" {
  bucket = aws_s3_bucket.frontend_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "frontend_bucket_versioning" {
  bucket = aws_s3_bucket.frontend_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Logs Bucket
resource "aws_s3_bucket" "logs_bucket" {
  bucket = "felicia-finance-logs-${var.environment}-${random_string.bucket_suffix.result}"

  tags = merge(var.tags, {
    Name = "felicia-finance-logs-${var.environment}"
  })
}

resource "aws_s3_bucket_public_access_block" "logs_bucket_pab" {
  bucket = aws_s3_bucket.logs_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "logs_bucket_versioning" {
  bucket = aws_s3_bucket.logs_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Bedrock Logs Bucket
resource "aws_s3_bucket" "bedrock_logs_bucket" {
  bucket = "felicia-finance-bedrock-logs-${var.environment}-${random_string.bucket_suffix.result}"

  tags = merge(var.tags, {
    Name = "felicia-finance-bedrock-logs-${var.environment}"
  })
}

resource "aws_s3_bucket_public_access_block" "bedrock_logs_bucket_pab" {
  bucket = aws_s3_bucket.bedrock_logs_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "bedrock_logs_bucket_versioning" {
  bucket = aws_s3_bucket.bedrock_logs_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# =============================================================================
# CLOUDFRONT DISTRIBUTION
# =============================================================================

# Origin Access Identity for S3
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for Felicia Finance frontend"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "felicia_finance_distribution" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  origin {
    domain_name = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
    origin_id   = "felicia-finance-frontend-origin"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "felicia-finance-frontend-origin"

    forwarded_values {
      query_string = true
      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400

    # SPA routing support
    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_routing.arn
    }
  }

  # API Gateway origin for API calls
  origin {
    domain_name = replace(aws_api_gateway_deployment.felicia_finance_deployment.invoke_url, "https://", "")
    origin_id   = "felicia-finance-api-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "felicia-finance-api-origin"

    forwarded_values {
      query_string = true
      headers      = ["Authorization"]
      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # Custom error pages for SPA
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.logs_bucket.bucket_domain_name
    prefix          = "cloudfront/"
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-distribution-${var.environment}"
  })
}

# CloudFront Function for SPA routing
resource "aws_cloudfront_function" "spa_routing" {
  name    = "felicia-finance-spa-routing-${var.environment}"
  runtime = "cloudfront-js-1.0"
  comment = "SPA routing function for Felicia Finance"
  publish = true
  code    = <<-EOF
function handler(event) {
    var request = event.request;
    var uri = request.uri;
    
    // Check whether the URI is missing a file name.
    if (uri.endsWith('/')) {
        request.uri += 'index.html';
    }
    // Check whether the URI is missing a file extension.
    else if (!uri.includes('.')) {
        request.uri += '/index.html';
    }

    return request;
}
EOF
}

# =============================================================================
# S3 BUCKET POLICIES
# =============================================================================

resource "aws_s3_bucket_policy" "frontend_bucket_policy" {
  bucket = aws_s3_bucket.frontend_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontAccess"
        Effect    = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.oai.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend_bucket.arn}/*"
      }
    ]
  })
}

# =============================================================================
# RANDOM SUFFIX FOR BUCKETS
# =============================================================================

resource "random_string" "bucket_suffix" {
  length  = 8
  lower   = true
  upper   = false
  numeric = true
  special = false
}