# App secrets stored in AWS Secrets Manager
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${local.prefix}/app-secrets"
  recovery_window_in_days = 7
  tags                    = local.tags
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    SECRET_KEY       = var.secret_key
    GROQ_API_KEY     = var.groq_api_key
    MERGE_API_KEY    = var.merge_api_key
    MERGE_SECRET_KEY = var.merge_secret_key
  })
}
