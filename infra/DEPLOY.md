# AWS Deployment Guide

## Architecture

```
Internet → ALB (port 80/443)
              ├── /api/* /health/*  → Backend ECS (Fargate, port 8000)
              └── /*                → Frontend ECS (Fargate, port 3000)

Backend → RDS PostgreSQL (private subnet)
Backend → ElastiCache Redis (private subnet)
Worker  → Redis (Celery tasks)
Beat    → Redis (Celery scheduler)
```

All ECS tasks run in private subnets. Only the ALB is public-facing.

---

## Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform >= 1.5 installed
- Docker installed
- An AWS account with sufficient permissions (EC2, ECS, RDS, ElastiCache, ECR, IAM, Secrets Manager)

---

## Step 1 — Bootstrap Terraform

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

Generate a strong JWT secret:
```bash
openssl rand -hex 32
```

---

## Step 2 — Provision Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

This creates:
- VPC with public/private subnets across 2 AZs
- RDS PostgreSQL 15 (encrypted, automated backups)
- ElastiCache Redis 7
- ECR repositories for backend and frontend
- ECS Fargate cluster
- ALB with routing rules
- Secrets Manager entries
- CloudWatch log groups
- IAM roles

Save the outputs — you'll need the ECR URLs:
```bash
terraform output ecr_backend_url
terraform output ecr_frontend_url
```

---

## Step 3 — Push Initial Docker Images

```bash
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND=$(terraform output -raw ecr_backend_url)
ECR_FRONTEND=$(terraform output -raw ecr_frontend_url)

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend
docker build -t $ECR_BACKEND:latest ./backend
docker push $ECR_BACKEND:latest

# Build and push frontend
docker build -f frontend/Dockerfile.prod -t $ECR_FRONTEND:latest ./frontend
docker push $ECR_FRONTEND:latest
```

---

## Step 4 — Run Database Migrations

```bash
CLUSTER=$(terraform output -raw ecs_cluster_name)
TASK_DEF=vireon-prod-backend

# Get network config from the backend service
NETWORK=$(aws ecs describe-services \
  --cluster $CLUSTER \
  --services vireon-prod-backend \
  --query 'services[0].networkConfiguration' \
  --output json)

# Run one-off migration task
aws ecs run-task \
  --cluster $CLUSTER \
  --task-definition $TASK_DEF \
  --launch-type FARGATE \
  --network-configuration "$NETWORK" \
  --overrides '{"containerOverrides":[{"name":"backend","command":["alembic","upgrade","head"]}]}'
```

---

## Step 5 — Set Up CI/CD (GitHub Actions)

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |

The workflow in `.github/workflows/deploy.yml` will automatically:
1. Build and push Docker images to ECR on every push to `main`
2. Run Alembic migrations
3. Deploy all ECS services

---

## Step 6 — Custom Domain (Optional)

1. Request a certificate in ACM (must be in `us-east-1` for ALB):
   ```
   AWS Console → Certificate Manager → Request → DNS validation
   ```

2. Add to `terraform.tfvars`:
   ```hcl
   domain_name         = "app.yourdomain.com"
   acm_certificate_arn = "arn:aws:acm:us-east-1:..."
   ```

3. `terraform apply` — this adds the HTTPS listener and HTTP→HTTPS redirect

4. Point your DNS CNAME to the ALB DNS name:
   ```bash
   terraform output alb_dns_name
   ```

---

## Accessing Your App

```bash
terraform output alb_dns_name
# → http://vireon-prod-alb-123456.us-east-1.elb.amazonaws.com
```

API docs: `http://<alb-dns>/api/v1/docs`

---

## Monitoring

Logs are in CloudWatch under:
- `/ecs/vireon-prod/backend`
- `/ecs/vireon-prod/frontend`
- `/ecs/vireon-prod/worker`
- `/ecs/vireon-prod/beat`

---

## Scaling

```bash
# Scale backend to 2 tasks
aws ecs update-service --cluster vireon-prod-cluster \
  --service vireon-prod-backend --desired-count 2

# NOTE: Keep beat at desired-count=1 always (duplicate schedulers = duplicate jobs)
```

---

## Teardown

```bash
# Scale all services to 0 first (RDS deletion protection must be disabled manually)
terraform destroy
```
