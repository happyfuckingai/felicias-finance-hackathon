# =============================================================================
# ECS TASK DEFINITIONS
# =============================================================================

# Frontend Task Definition
resource "aws_ecs_task_definition" "frontend_task" {
  family                   = "felicia-finance-frontend-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "frontend"
      image = var.frontend_image

      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "NODE_ENV"
          value = "production"
        },
        {
          name  = "NEXT_PUBLIC_API_URL"
          value = aws_api_gateway_deployment.felicia_finance_deployment.invoke_url
        },
        {
          name  = "NEXT_PUBLIC_COGNITO_USER_POOL_ID"
          value = aws_cognito_user_pool.felicia_finance_pool.id
        },
        {
          name  = "NEXT_PUBLIC_COGNITO_CLIENT_ID"
          value = aws_cognito_user_pool_client.felicia_finance_client.id
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "frontend"
        }
      }

      essential = true
    }
  ])

  tags = merge(var.tags, {
    Name = "felicia-finance-frontend-task-${var.environment}"
  })
}

# MCP Server Task Definition
resource "aws_ecs_task_definition" "mcp_server_task" {
  family                   = "felicia-finance-mcp-server-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.mcp_server_cpu
  memory                   = var.mcp_server_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "mcp-server"
      image = var.mcp_server_image

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "DATABASE_URL"
          value = "postgresql://${aws_db_instance.postgres.username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
        },
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}"
        },
        {
          name  = "WEB3_RPC_URL"
          value = var.web3_rpc_url
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "BEDROCK_AGENT_ID"
          value = aws_bedrock_agent.felicia_finance_agent.id
        }
      ]

      secrets = [
        {
          name      = "JWT_SECRET"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "mcp-server"
        }
      }

      essential = true
    }
  ])

  tags = merge(var.tags, {
    Name = "felicia-finance-mcp-server-task-${var.environment}"
  })
}

# =============================================================================
# LOAD BALANCER CONFIGURATION
# =============================================================================

# Application Load Balancer
resource "aws_lb" "felicia_finance_lb" {
  name               = "felicia-finance-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = aws_subnet.public_subnets[*].id

  enable_deletion_protection = var.environment == "prod"

  tags = merge(var.tags, {
    Name = "felicia-finance-alb-${var.environment}"
  })
}

# Target Group for Frontend
resource "aws_lb_target_group" "frontend_tg" {
  name        = "felicia-finance-frontend-${var.environment}"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.felicia_finance_vpc.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/api/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-frontend-tg-${var.environment}"
  })
}

# ALB Listener
resource "aws_lb_listener" "frontend_listener" {
  load_balancer_arn = aws_lb.felicia_finance_lb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_tg.arn
  }
}

# HTTPS Listener (if SSL certificate is available)
resource "aws_lb_listener" "frontend_https_listener" {
  count             = var.environment == "prod" ? 1 : 0
  load_balancer_arn = aws_lb.felicia_finance_lb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate.felicia_finance_cert[0].arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_tg.arn
  }
}