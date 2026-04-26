# Vireon AWS Deployment — Console Verification Guide

After running each script, use this guide to confirm it worked in the AWS Console.
All links are for region **ap-south-1 (Mumbai)**.

---

## Current Deployment State

| Resource | Status | Details |
|---|---|---|
| RDS | ✅ Available | `vireon-postgres.cd686gs48rds.ap-south-1.rds.amazonaws.com` |
| ElastiCache | ✅ Available | `vireon-redis.r1atz6.0001.aps1.cache.amazonaws.com` |
| S3 | ✅ Exists | `vireon-documents-732772501496` |
| ECS Cluster | ✅ Active | `vireon-prod-cluster` |
| ALB | ✅ Active | `vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com` |
| ECR | ✅ Images pushed | `vireon-backend:latest`, `vireon-worker:latest` |
| Amplify | ✅ Deployed | `https://main.d1tzlh2fec7rai.amplifyapp.com` |

### VPC Architecture
- RDS + Redis → **default VPC** `vpc-047a5218129c4114b`
- ECS + ALB → **new VPC** `vpc-08d98ac34e0e5bed7` (10.0.0.0/16)
- RDS port 5432 is open to `0.0.0.0/0` to allow cross-VPC access

---

## config.bat values

| Variable | Value |
|---|---|
| `AWS_REGION` | `ap-south-1` |
| `GROQ_API_KEY` | Your key from https://console.groq.com |
| `DB_PASSWORD` | `vireon_yagna_project` |
| `S3_BUCKET` | `vireon-documents-732772501496` |
| `APP_SECRET_KEY` | `vireon-prod-secret-key-2026-seedlinglabs-ap-south-1` |
| `MERGE_API_KEY` | `sNtk4aFWUGxqtiuLivhhP8F59OtpLZT-ZzjSN-IA9lozfcjKD-DYx` |
| `ALLOWED_ORIGINS` | `https://main.d1tzlh2fec7rai.amplifyapp.com` |

---

## Step 0 — Prerequisites Check
**Run:** `scripts\aws\00_prerequisites_check.bat`

**Verify in console:**
- Go to https://console.aws.amazon.com/iam/home?region=ap-south-1
- Top right shows account `732772501496`

**Expected output:**
```
[OK]  AWS CLI: aws-cli/2.x.x
[OK]  Docker: Docker version xx.x.x
[OK]  AWS Account: 732772501496
[OK]  AWS Region: ap-south-1
All prerequisites met.
```

---

## Step 1 — Create ECR Repositories
**Run:** `scripts\aws\01_setup_ecr.bat`

**Verify:**
- Go to https://ap-south-1.console.aws.amazon.com/ecr/repositories?region=ap-south-1
- Should see `vireon-backend` and `vireon-worker`

---

## Step 2 — Build and Push Docker Images
**Run:** `scripts\aws\02_build_and_push.bat`

> Docker Desktop must be running. Takes 5–15 minutes.

**Verify:**
- Go to https://ap-south-1.console.aws.amazon.com/ecr/repositories?region=ap-south-1
- Click `vireon-backend` → image tagged **latest** with today's date

---

## Step 3 — Setup Infrastructure
**Run:** `scripts\aws\03_setup_infrastructure.bat`

> Wait for RDS to show **Available** before running step 4.

**S3:**
- https://s3.console.aws.amazon.com/s3/buckets
- `vireon-documents-732772501496` → Versioning = **Enabled**

**RDS:**
- https://ap-south-1.console.aws.amazon.com/rds/home?region=ap-south-1#databases:
- `vireon-postgres` → Status = **Available**
- VPC = **default** (`vpc-047a5218129c4114b`)
- Publicly accessible = **Yes**
- Security group `sg-0ccad704bdb2ee9b4` must have port 5432 open to `0.0.0.0/0`

**ElastiCache:**
- https://ap-south-1.console.aws.amazon.com/elasticache/home?region=ap-south-1#/redis
- `vireon-redis` → Status = **Available**
- VPC = **default** (`vpc-047a5218129c4114b`)

**SSM Parameters:**
- https://ap-south-1.console.aws.amazon.com/systems-manager/parameters?region=ap-south-1
- Should see `/vireon/GROQ_API_KEY`, `/vireon/DB_PASSWORD`, `/vireon/SECRET_KEY`, `/vireon/S3_BUCKET`, `/vireon/AWS_REGION`, `/vireon/COMPANY_NAME`

---

## Step 4 — Deploy Backend (ECS Fargate + ALB)
**Run:** `scripts\aws\04_deploy_backend.bat`

> Only run after RDS is **Available**.

### Step 4/1 — VPC
- https://ap-south-1.console.aws.amazon.com/vpc/home?region=ap-south-1#vpcs:
- `vireon-prod-vpc` — CIDR `10.0.0.0/16`, DNS hostnames = **Enabled**

### Step 4/2 — Subnets
- https://ap-south-1.console.aws.amazon.com/vpc/home?region=ap-south-1#subnets:
- `vireon-prod-public-0` (10.0.0.0/24) and `vireon-prod-public-1` (10.0.1.0/24)
- Auto-assign public IPv4 = **Yes**

### Step 4/3 — Internet Gateway
- https://ap-south-1.console.aws.amazon.com/vpc/home?region=ap-south-1#igws:
- IGW attached to `vireon-prod-vpc` — State = **Attached**

### Step 4/4 — Security Groups
- https://ap-south-1.console.aws.amazon.com/vpc/home?region=ap-south-1#securityGroups:
- `vireon-prod-alb-sg` (`sg-09ac4104b4e8e41e7`) — Inbound: 80, 443 from 0.0.0.0/0
- `vireon-prod-backend-sg` (`sg-0141ead8a5ade5dfa`) — Inbound: 8000 from ALB SG

### Step 4/5 — IAM Role
- https://console.aws.amazon.com/iam/home#/roles
- `ecsTaskExecutionRole` exists with `AmazonECSTaskExecutionRolePolicy` and `AmazonEC2ContainerRegistryReadOnly`

### Step 4/6 — ECS Cluster
- https://ap-south-1.console.aws.amazon.com/ecs/v2/clusters?region=ap-south-1
- `vireon-prod-cluster` — Status: **Active**
- CloudWatch log group `/ecs/vireon-prod/backend` exists

### Step 4/7 — ALB + Target Group
- https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#LoadBalancers:
- `vireon-prod-alb` — State: **Active**, DNS: `vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com`
- https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#TargetGroups:
- `vireon-prod-backend-tg` — Port 8000, health check path `/health/ready`

### Step 4/8 — ECS Task Definition
- https://ap-south-1.console.aws.amazon.com/ecs/v2/task-definitions?region=ap-south-1
- `vireon-prod-backend` — Status: **ACTIVE**, revision 3+

### Step 4/9 — ECS Service
- https://ap-south-1.console.aws.amazon.com/ecs/v2/clusters/vireon-prod-cluster/services?region=ap-south-1
- `vireon-prod-backend` — Status: **Active**, Running: **1**
- Target health: **1 Healthy** (not Unhealthy)

**Test the API:**
- `http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com/health/live` → `{"status":"ok"}`
- `http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com/api/v1/docs` → Swagger UI

### If you see "Bad Gateway" or "1 Unhealthy"
The ECS task can't reach RDS. Run this to fix:
```powershell
aws ec2 authorize-security-group-ingress --group-id sg-0ccad704bdb2ee9b4 --protocol tcp --port 5432 --cidr 0.0.0.0/0 --region ap-south-1
aws ecs update-service --cluster vireon-prod-cluster --service vireon-prod-backend --force-new-deployment --region ap-south-1
```
Then wait 2-3 minutes.

---

## Step 5 — Run Database Migrations
**Run:** `scripts\aws\06_run_db_migrations.bat`

> Docker must be running.

**Verify:**
- https://ap-south-1.console.aws.amazon.com/rds/home?region=ap-south-1#databases:
- Click `vireon-postgres` → **Monitoring** tab → spike in **DatabaseConnections**

**Expected output:**
```
[OK] Migrations applied successfully
INFO  [alembic.runtime.migration] Running upgrade ...
```

---

## Step 6 — Deploy Workers
**Run:** `scripts\aws\05_deploy_workers.bat`

**Verify:**
- https://ap-south-1.console.aws.amazon.com/ecs/v2/clusters/vireon-prod-cluster/services?region=ap-south-1
- `vireon-prod-worker` — Running: **1**
- `vireon-prod-beat` — Running: **1**
- Log groups `/ecs/vireon-prod/worker` and `/ecs/vireon-prod/beat` exist

---

## Step 7 — Verify Full Deployment
**Run:** `scripts\aws\07_verify_deployment.bat`

| Resource | Expected |
|---|---|
| RDS `vireon-postgres` | `available` |
| ElastiCache `vireon-redis` | `available` |
| S3 `vireon-documents-732772501496` | EXISTS |
| ECS `vireon-prod-backend` | ACTIVE, Running: 1 |
| ECS `vireon-prod-worker` | ACTIVE, Running: 1 |
| ECS `vireon-prod-beat` | ACTIVE, Running: 1 |
| ALB `/health/live` | HTTP 200 |
| ALB `/health/ready` | HTTP 200 |

**Console links:**

| Service | URL |
|---|---|
| RDS | https://ap-south-1.console.aws.amazon.com/rds/home?region=ap-south-1#databases: |
| ElastiCache | https://ap-south-1.console.aws.amazon.com/elasticache/home?region=ap-south-1#/redis |
| S3 | https://s3.console.aws.amazon.com/s3/buckets |
| ECS Cluster | https://ap-south-1.console.aws.amazon.com/ecs/v2/clusters/vireon-prod-cluster/services?region=ap-south-1 |
| Load Balancer | https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#LoadBalancers: |
| Target Groups | https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#TargetGroups: |
| Task Definitions | https://ap-south-1.console.aws.amazon.com/ecs/v2/task-definitions?region=ap-south-1 |
| CloudWatch Logs | https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#logsV2:log-groups |
| ECR | https://ap-south-1.console.aws.amazon.com/ecr/repositories?region=ap-south-1 |

---

## Step 8 — Deploy Frontend (Amplify)
**Run:** `scripts\aws\08_deploy_frontend.bat`

**Verify:**
- https://ap-south-1.console.aws.amazon.com/amplify/home?region=ap-south-1
- `vireon-frontend` → `main` branch → Status: **Succeeded**
- Open: https://main.d1tzlh2fec7rai.amplifyapp.com

---

## Updating Secrets

```bat
scripts\aws\update_secret.bat GROQ_API_KEY your_new_key
scripts\aws\update_secret.bat MERGE_API_KEY your_new_key
```

---

## Force Redeploy Backend

```powershell
aws ecs update-service --cluster vireon-prod-cluster --service vireon-prod-backend --force-new-deployment --region ap-south-1
```

---

## Cleanup

```bat
scripts\aws\cleanup_vireon.bat
```

> Irreversible. Deletes all Vireon resources.
