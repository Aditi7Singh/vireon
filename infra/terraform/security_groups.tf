# ─── ALB ─────────────────────────────────────────────────────────────────────
resource "aws_security_group" "alb" {
  name        = "${local.prefix}-alb-sg"
  description = "Allow HTTP/HTTPS from internet"
  vpc_id      = aws_vpc.main.id

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

  tags = merge(local.tags, { Name = "${local.prefix}-alb-sg" })
}

# ─── Backend ECS tasks ───────────────────────────────────────────────────────
resource "aws_security_group" "backend" {
  name        = "${local.prefix}-backend-sg"
  description = "Backend ECS tasks - allow from ALB only"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-backend-sg" })
}

# ─── Frontend ECS tasks ──────────────────────────────────────────────────────
resource "aws_security_group" "frontend" {
  name        = "${local.prefix}-frontend-sg"
  description = "Frontend ECS tasks - allow from ALB only"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-frontend-sg" })
}

# ─── Worker ECS tasks (no inbound needed) ────────────────────────────────────
resource "aws_security_group" "worker" {
  name        = "${local.prefix}-worker-sg"
  description = "Celery worker/beat - outbound only"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-worker-sg" })
}

# ─── RDS ─────────────────────────────────────────────────────────────────────
resource "aws_security_group" "rds" {
  name        = "${local.prefix}-rds-sg"
  description = "PostgreSQL - allow from backend and workers"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id, aws_security_group.worker.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-rds-sg" })
}

# ─── ElastiCache ─────────────────────────────────────────────────────────────
resource "aws_security_group" "redis" {
  name        = "${local.prefix}-redis-sg"
  description = "Redis - allow from backend and workers"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id, aws_security_group.worker.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-redis-sg" })
}
