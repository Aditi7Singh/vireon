output "alb_dns_name" {
  description = "ALB DNS name - use this as your app URL if no custom domain"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecr_backend_url" {
  description = "ECR repository URL for backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  description = "ECR repository URL for frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.address
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "db_secret_arn" {
  description = "Secrets Manager ARN for DB password"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "database_url_secret_arn" {
  description = "Secrets Manager ARN for full DATABASE_URL"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "app_secrets_arn" {
  description = "Secrets Manager ARN for app secrets"
  value       = aws_secretsmanager_secret.app_secrets.arn
}
