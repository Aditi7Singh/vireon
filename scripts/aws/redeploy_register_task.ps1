# Registers the backend ECS task definition with all correct env vars
$ErrorActionPreference = "Stop"

$groqKey = (Get-Content "$PSScriptRoot\config.bat" | Where-Object { $_ -match "^set GROQ_API_KEY=" } | ForEach-Object { ($_ -split "=", 2)[1].Trim() })

$taskJson = @"
{
  "family": "vireon-prod-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::732772501496:role/ecsTaskExecutionRole",
  "containerDefinitions": [{
    "name": "backend",
    "image": "732772501496.dkr.ecr.ap-south-1.amazonaws.com/vireon-backend:latest",
    "essential": true,
    "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
    "command": ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"],
    "environment": [
      {"name": "DATABASE_URL",    "value": "postgresql+psycopg2://vireon:vireon_yagna_project@vireon-postgres.cd686gs48rds.ap-south-1.rds.amazonaws.com:5432/vireon"},
      {"name": "REDIS_URL",       "value": "redis://vireon-redis.r1atz6.0001.aps1.cache.amazonaws.com:6379/0"},
      {"name": "GROQ_API_KEY",    "value": "$groqKey"},
      {"name": "SECRET_KEY",      "value": "vireon-prod-secret-key-2026-seedlinglabs-ap-south-1"},
      {"name": "COMPANY_NAME",    "value": "SeedlingLabs"},
      {"name": "S3_BUCKET",       "value": "vireon-documents-732772501496"},
      {"name": "AWS_REGION",      "value": "ap-south-1"},
      {"name": "ALLOWED_ORIGINS", "value": "http://vireon-frontend-732772501496.s3-website.ap-south-1.amazonaws.com,https://d10nqxcoyrzhqf.cloudfront.net"},
      {"name": "MERGE_API_KEY",   "value": "sNtk4aFWUGxqtiuLivhhP8F59OtpLZT-ZzjSN-IA9lozfcjKD-DYx"},
      {"name": "ENV",             "value": "production"},
      {"name": "SANDBOX_MODE",    "value": "false"},
      {"name": "USE_LOCAL_LLM",   "value": "false"},
      {"name": "USE_OPENROUTER",  "value": "false"},
      {"name": "STRICT_STARTUP_CHECKS",       "value": "false"},
      {"name": "REQUIRE_REDIS_FOR_READINESS", "value": "false"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group":         "/ecs/vireon-prod/backend",
        "awslogs-region":        "ap-south-1",
        "awslogs-stream-prefix": "backend"
      }
    }
  }]
}
"@

$f = "$env:TEMP\vireon_redeploy_td.json"
[System.IO.File]::WriteAllText($f, $taskJson, [System.Text.Encoding]::ASCII)
$arn = (aws ecs register-task-definition --cli-input-json "file://$f" --region ap-south-1 --query "taskDefinition.taskDefinitionArn" --output text 2>&1)
Write-Host $arn
$arn | Out-File -FilePath "$env:TEMP\vireon_task_arn.txt" -Encoding ASCII -NoNewline
