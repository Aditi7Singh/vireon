# ─── ECS Cluster ─────────────────────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "${local.prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.tags
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# ─── CloudWatch Log Groups ────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${local.prefix}/backend"
  retention_in_days = 30
  tags              = local.tags
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.prefix}/frontend"
  retention_in_days = 30
  tags              = local.tags
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${local.prefix}/worker"
  retention_in_days = 30
  tags              = local.tags
}

resource "aws_cloudwatch_log_group" "beat" {
  name              = "/ecs/${local.prefix}/beat"
  retention_in_days = 30
  tags              = local.tags
}

# ─── Store DATABASE_URL in Secrets Manager (keeps it out of task def plaintext) ─
resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${local.prefix}/database-url"
  recovery_window_in_days = 7
  tags                    = local.tags
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql+psycopg2://${var.db_username}:${random_password.db_password.result}@${aws_db_instance.postgres.address}:5432/${var.db_name}"
}

# Allow execution role to also read the database_url secret
resource "aws_iam_role_policy" "ecs_execution_db_secret" {
  name = "${local.prefix}-ecs-db-secret-policy"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
      Resource = aws_secretsmanager_secret.database_url.arn
    }]
  })
}

# ─── Backend Task Definition ──────────────────────────────────────────────────
resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.prefix}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
    essential = true

    portMappings = [{ containerPort = 8000, protocol = "tcp" }]

    environment = [
      { name = "REDIS_URL",                   value = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0" },
      { name = "BACKEND_URL",                 value = "http://localhost:8000" },
      { name = "USE_LOCAL_LLM",               value = "false" },
      { name = "STRICT_STARTUP_CHECKS",       value = "true" },
      { name = "REQUIRE_REDIS_FOR_READINESS", value = "true" },
      { name = "STARTUP_MAX_RETRIES",         value = "30" },
      { name = "STARTUP_RETRY_DELAY_SECONDS", value = "2" },
      { name = "ENV",                         value = var.environment },
      { name = "ALLOWED_ORIGINS",             value = var.acm_certificate_arn != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}" },
    ]

    secrets = [
      { name = "DATABASE_URL",  valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "SECRET_KEY",    valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:SECRET_KEY::" },
      { name = "GROQ_API_KEY",  valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:GROQ_API_KEY::" },
      { name = "MERGE_API_KEY", valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:MERGE_API_KEY::" },
      { name = "MERGE_SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:MERGE_SECRET_KEY::" },
    ]

    command = ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

    healthCheck = {
      command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready', timeout=3)\""]
      interval    = 30
      timeout     = 10
      retries     = 3
      startPeriod = 60
    }

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${local.prefix}/backend"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
      }
    }
  }])

  tags = local.tags
}

# ─── Backend ECS Service ──────────────────────────────────────────────────────
resource "aws_ecs_service" "backend" {
  name            = "${local.prefix}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = local.tags
}

# ─── Frontend Task Definition ─────────────────────────────────────────────────
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "frontend"
    image     = "${aws_ecr_repository.frontend.repository_url}:${var.frontend_image_tag}"
    essential = true

    portMappings = [{ containerPort = 3000, protocol = "tcp" }]

    environment = [
      { name = "NEXT_PUBLIC_API_URL", value = var.acm_certificate_arn != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}" },
      { name = "PORT",                value = "3000" },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${local.prefix}/frontend"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "frontend"
      }
    }
  }])

  tags = local.tags
}

# ─── Frontend ECS Service ─────────────────────────────────────────────────────
resource "aws_ecs_service" "frontend" {
  name            = "${local.prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.http]

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = local.tags
}

# ─── Celery Worker Task Definition ───────────────────────────────────────────
resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
    essential = true

    environment = [
      { name = "REDIS_URL",   value = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0" },
      { name = "BACKEND_URL", value = "http://${aws_lb.main.dns_name}" },
      { name = "ENV",         value = var.environment },
    ]

    secrets = [
      { name = "DATABASE_URL",     valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "SECRET_KEY",       valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:SECRET_KEY::" },
      { name = "GROQ_API_KEY",     valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:GROQ_API_KEY::" },
      { name = "MERGE_API_KEY",    valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:MERGE_API_KEY::" },
      { name = "MERGE_SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:MERGE_SECRET_KEY::" },
    ]

    command = ["celery", "-A", "anomaly.celery_app", "worker", "-l", "info", "--concurrency=2"]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${local.prefix}/worker"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "worker"
      }
    }
  }])

  tags = local.tags
}

resource "aws_ecs_service" "worker" {
  name            = "${local.prefix}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.worker.id]
    assign_public_ip = false
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = local.tags
}

# ─── Celery Beat Task Definition ─────────────────────────────────────────────
resource "aws_ecs_task_definition" "beat" {
  family                   = "${local.prefix}-beat"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "beat"
    image     = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
    essential = true

    environment = [
      { name = "REDIS_URL",   value = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0" },
      { name = "BACKEND_URL", value = "http://${aws_lb.main.dns_name}" },
      { name = "ENV",         value = var.environment },
    ]

    secrets = [
      { name = "DATABASE_URL",     valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "SECRET_KEY",       valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:SECRET_KEY::" },
      { name = "GROQ_API_KEY",     valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:GROQ_API_KEY::" },
      { name = "MERGE_API_KEY",    valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:MERGE_API_KEY::" },
      { name = "MERGE_SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:MERGE_SECRET_KEY::" },
    ]

    command = ["celery", "-A", "anomaly.celery_app", "beat", "-l", "info"]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${local.prefix}/beat"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "beat"
      }
    }
  }])

  tags = local.tags
}

resource "aws_ecs_service" "beat" {
  name            = "${local.prefix}-beat"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.beat.arn
  # IMPORTANT: always keep beat at 1 to avoid duplicate scheduled jobs
  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.worker.id]
    assign_public_ip = false
  }

  lifecycle {
    ignore_changes = [task_definition]
  }

  tags = local.tags
}
