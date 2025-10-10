# =============================================================================
# VPC CONFIGURATION
# =============================================================================

resource "aws_vpc" "felicia_finance_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = "felicia-finance-vpc-${var.environment}"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.felicia_finance_vpc.id

  tags = merge(var.tags, {
    Name = "felicia-finance-igw-${var.environment}"
  })
}

# NAT Gateway for private subnets
resource "aws_eip" "nat_eip" {
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "felicia-finance-nat-eip-${var.environment}"
  })
}

resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_subnets[0].id

  tags = merge(var.tags, {
    Name = "felicia-finance-nat-gw-${var.environment}"
  })

  depends_on = [aws_internet_gateway.igw]
}

# Public Subnets
resource "aws_subnet" "public_subnets" {
  count             = length(var.public_subnets)
  vpc_id            = aws_vpc.felicia_finance_vpc.id
  cidr_block        = var.public_subnets[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "felicia-finance-public-${count.index + 1}-${var.environment}"
    Type = "Public"
  })
}

# Private Subnets
resource "aws_subnet" "private_subnets" {
  count             = length(var.private_subnets)
  vpc_id            = aws_vpc.felicia_finance_vpc.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(var.tags, {
    Name = "felicia-finance-private-${count.index + 1}-${var.environment}"
    Type = "Private"
  })
}

# Route Tables
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.felicia_finance_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-public-rt-${var.environment}"
  })
}

resource "aws_route_table" "private_rt" {
  vpc_id = aws_vpc.felicia_finance_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gw.id
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-private-rt-${var.environment}"
  })
}

# Route Table Associations
resource "aws_route_table_association" "public_rta" {
  count          = length(var.public_subnets)
  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "private_rta" {
  count          = length(var.private_subnets)
  subnet_id      = aws_subnet.private_subnets[count.index].id
  route_table_id = aws_route_table.private_rt.id
}

# =============================================================================
# SECURITY GROUPS
# =============================================================================

# ALB Security Group
resource "aws_security_group" "alb_sg" {
  name_prefix = "felicia-finance-alb-${var.environment}"
  vpc_id      = aws_vpc.felicia_finance_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-alb-sg-${var.environment}"
  })
}

# ECS Security Group
resource "aws_security_group" "ecs_sg" {
  name_prefix = "felicia-finance-ecs-${var.environment}"
  vpc_id      = aws_vpc.felicia_finance_vpc.id

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-ecs-sg-${var.environment}"
  })
}

# RDS Security Group
resource "aws_security_group" "rds_sg" {
  name_prefix = "felicia-finance-rds-${var.environment}"
  vpc_id      = aws_vpc.felicia_finance_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id, aws_security_group.lambda_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-rds-sg-${var.environment}"
  })
}

# Redis Security Group
resource "aws_security_group" "redis_sg" {
  name_prefix = "felicia-finance-redis-${var.environment}"
  vpc_id      = aws_vpc.felicia_finance_vpc.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id, aws_security_group.lambda_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-redis-sg-${var.environment}"
  })
}

# Lambda Security Group
resource "aws_security_group" "lambda_sg" {
  name_prefix = "felicia-finance-lambda-${var.environment}"
  vpc_id      = aws_vpc.felicia_finance_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "felicia-finance-lambda-sg-${var.environment}"
  })
}

# =============================================================================
# SUBNET GROUPS
# =============================================================================

# RDS Subnet Group
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "felicia-finance-rds-${var.environment}"
  subnet_ids = aws_subnet.private_subnets[*].id

  tags = merge(var.tags, {
    Name = "felicia-finance-rds-subnet-group-${var.environment}"
  })
}

# Redis Subnet Group
resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "felicia-finance-redis-${var.environment}"
  subnet_ids = aws_subnet.private_subnets[*].id

  tags = merge(var.tags, {
    Name = "felicia-finance-redis-subnet-group-${var.environment}"
  })
}

# =============================================================================
# DATA SOURCES
# =============================================================================

data "aws_availability_zones" "available" {
  state = "available"
}