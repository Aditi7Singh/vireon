# Vireon AWS Deployment Guide

## Architecture

```
Amplify (Frontend) — https://main.d1tzlh2fec7rai.amplifyapp.com
    │
    ▼
ALB (vireon-prod-alb) — http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com
    │
    ▼
ECS Fargate (vireon-prod-backend)  ──►  RDS PostgreSQL (default VPC, publicly accessible)
    │                               ──►  ElastiCache Redis (default VPC)
    ▼                               ──►  S3 (vireon-documents-732772501496)
ECS Fargate Workers (vireon-prod-cluster)
  ├── Celery Worker (vireon-prod-worker)
  └── Celery Beat   (vireon-prod-beat)
```

### VPC Notes
- **RDS and Redis** are in the **default VPC** (`vpc-047a5218129c4114b`)
- **ECS + ALB** are in a **new VPC** (`vpc-08d98ac34e0e5bed7`, CIDR 10.0.0.0/16)
- RDS is publicly accessible with port 5432 open to `0.0.0.0/0` to allow cross-VPC access
- Redis is accessible within its default VPC

---

## Prerequisites

- AWS CLI installed and configured (`aws configure`)
- Docker Desktop running
- AWS account: `732772501496`, region: `ap-south-1`

Run the check first:
```
scripts\aws\00_prerequisites_check.bat
```

---

## Deployment Order

Run these scripts **in order**:

| Step | Script | What it does |
|------|--------|--------------|
| 0 | `00_prerequisites_check.bat` | Validates tools and AWS credentials |
| 1 | `01_setup_ecr.bat` | Creates ECR image repositories |
| 2 | `02_build_and_push.bat` | Builds Docker images and pushes to ECR |
| 3 | `03_setup_infrastructure.bat` | Creates RDS, ElastiCache, S3, SSM secrets |
| 4 | `04_deploy_backend.bat` | Deploys FastAPI to ECS Fargate + ALB |
| 5 | `06_run_db_migrations.bat` | Runs Alembic migrations on RDS |
| 6 | `05_deploy_workers.bat` | Deploys Celery worker/beat on ECS Fargate |
| 7 | `07_verify_deployment.bat` | Checks all resources and hits health endpoints |
| 8 | `08_deploy_frontend.bat` | Deploys Next.js frontend to Amplify |

### Before running

Edit `scripts\aws\config.bat` — all values are already set:

| Variable | Value |
|---|---|
| `AWS_REGION` | `ap-south-1` |
| `DB_PASSWORD` | `vireon_yagna_project` |
| `S3_BUCKET` | `vireon-documents-732772501496` |
| `GROQ_API_KEY` | Your key from https://console.groq.com |
| `APP_SECRET_KEY` | `vireon-prod-secret-key-2026-seedlinglabs-ap-south-1` |
| `MERGE_API_KEY` | Production key from Merge.dev |
| `ALLOWED_ORIGINS` | `https://main.d1tzlh2fec7rai.amplifyapp.com` |

### Important wait step after Step 3

RDS and ElastiCache take 5-10 minutes to become available. Before running Step 4:

```bat
aws rds describe-db-instances --db-instance-identifier vireon-postgres --query "DBInstances[0].DBInstanceStatus" --output text --region ap-south-1

aws elasticache describe-cache-clusters --cache-cluster-id vireon-redis --query "CacheClusters[0].CacheClusterStatus" --output text --region ap-south-1
```

Both should return `available` before proceeding.

---

## Deployed Resources

| Resource | ID / Name | VPC |
|---|---|---|
| RDS PostgreSQL | `vireon-postgres` | default (`vpc-047a5218129c4114b`) |
| ElastiCache Redis | `vireon-redis` | default (`vpc-047a5218129c4114b`) |
| S3 Bucket | `vireon-documents-732772501496` | global |
| ECS Cluster | `vireon-prod-cluster` | new (`vpc-08d98ac34e0e5bed7`) |
| ALB | `vireon-prod-alb` | new (`vpc-08d98ac34e0e5bed7`) |
| ECR Backend | `vireon-backend` | — |
| ECR Worker | `vireon-worker` | — |
| Amplify App | `vireon-frontend` (d1tzlh2fec7rai) | — |

---

## API Endpoints

| Endpoint | URL |
|---|---|
| Health (live) | `http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com/health/live` |
| Health (ready) | `http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com/health/ready` |
| API Docs | `http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com/api/v1/docs` |
| Frontend | `https://main.d1tzlh2fec7rai.amplifyapp.com` |

---

## Viewing Logs

### Backend logs (ECS)
```bat
aws logs tail /ecs/vireon-prod/backend --follow --region ap-south-1
```

### Worker logs
```bat
aws logs tail /ecs/vireon-prod/worker --follow --region ap-south-1
```

### Beat logs
```bat
aws logs tail /ecs/vireon-prod/beat --follow --region ap-south-1
```

---

## Updating Secrets

To update any secret and trigger an ECS redeploy:
```bat
scripts\aws\update_secret.bat GROQ_API_KEY your_new_key
scripts\aws\update_secret.bat MERGE_API_KEY your_new_key
```

---

## Force Redeploy Backend

If you push a new Docker image or change config:
```bat
aws ecs update-service --cluster vireon-prod-cluster --service vireon-prod-backend --force-new-deployment --region ap-south-1
```

---

## Troubleshooting

### Bad Gateway / Health check failing
The ECS task can't reach RDS or Redis. Check:
1. RDS security group (`sg-0ccad704bdb2ee9b4`) has port 5432 open to `0.0.0.0/0`
2. Redis is reachable from the ECS task's VPC
3. Check logs: `aws logs tail /ecs/vireon-prod/backend --region ap-south-1`

### Task keeps restarting
Check the ECS task logs in CloudWatch → `/ecs/vireon-prod/backend` for the error.

### Migrations failed
Run `scripts\aws\06_run_db_migrations.bat` again — it's idempotent.

---

## Cleanup

```bat
scripts\aws\cleanup_vireon.bat
```

> Irreversible. Deletes RDS, Redis, S3, Secrets, IAM roles, VPC, security groups, log groups.
