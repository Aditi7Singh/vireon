resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.prefix}-redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  tags       = local.tags
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "${local.prefix}-redis"
  description          = "Redis for Vireon (Celery broker + cache)"

  node_type            = var.redis_node_type
  num_cache_clusters   = 1
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false  # set true if you add auth token

  automatic_failover_enabled = false  # set true with num_cache_clusters >= 2

  tags = merge(local.tags, { Name = "${local.prefix}-redis" })
}
