# AWS Deployment Guide (With Ollama)

This guide gives two production-ready deployment options for Vireon on AWS.

## Recommended Architecture

Option A: EC2 runs Ollama, app stack runs in Docker Compose on same EC2 host.
- Best when you want low latency and simple networking.
- GPU instance recommended for larger models.

Option B: Dedicated Ollama EC2, app stack on separate EC2 or ECS.
- Better isolation and independent scaling.
- Requires private VPC networking and security group controls.

## Instance Sizing

- CPU-only baseline: c7i.xlarge for backend/frontend/worker + lightweight Ollama models.
- Better quality with local model: g5.xlarge (NVIDIA GPU) for Ollama.
- Storage: use gp3 EBS, at least 100 GB if pulling multiple models.
- RAM guideline:
  - 8B model: 16 to 24 GB RAM
  - 14B model: 32 GB RAM recommended

## Security Baseline

- Put instances in private subnets; expose only via ALB/Nginx.
- Do not expose port 11434 publicly.
- Security group rules:
  - 80/443 from internet to reverse proxy only
  - 8000/3000 internal only
  - 11434 internal VPC only
- Store secrets in AWS Secrets Manager or SSM Parameter Store.
- Rotate all API keys and set strong DB credentials.

## Production Compose

Use [docker-compose.prod.yml](../../../docker-compose.prod.yml) instead of dev compose.

## One-Command EC2 Bootstrap

Run the bootstrap script on a fresh Ubuntu EC2 host:

```bash
curl -fsSL https://raw.githubusercontent.com/<your-org>/<your-repo>/main/scripts/ec2_bootstrap.sh -o ec2_bootstrap.sh
chmod +x ec2_bootstrap.sh
REPO_URL=https://github.com/<your-org>/<your-repo>.git \
POSTGRES_PASSWORD='<strong-password>' \
./ec2_bootstrap.sh
```

If the repository is already on the machine:

```bash
cd /opt/vireon
POSTGRES_PASSWORD='<strong-password>' ./scripts/ec2_bootstrap.sh
```

What it does:
- Installs Docker + Compose plugin
- Prepares `backend/.env` and root `.env`
- Starts production stack with `docker-compose.prod.yml`
- Pulls Ollama models (`OLLAMA_MODEL_FAST`, `OLLAMA_MODEL_THINK`)
- Waits for `/health/ready`

### Start with local Ollama container

```bash
cd /opt/vireon
cp backend/.env.example backend/.env
# set real values in backend/.env

docker compose -f docker-compose.prod.yml --profile with-ollama up -d --build
```

### Start with external Ollama on separate EC2

In backend/.env:

```env
USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://10.0.2.15:11434
OLLAMA_MODEL_FAST=llama3.1:8b
OLLAMA_MODEL_THINK=qwen2.5:14b
```

Then run without the Ollama profile:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## Load Models

If using Compose-managed Ollama:

```bash
docker compose -f docker-compose.prod.yml exec ollama ollama pull llama3.1:8b
docker compose -f docker-compose.prod.yml exec ollama ollama pull qwen2.5:14b
```

## Health Checks

- Backend health: GET /api/v1/docs should load
- Agent chat endpoint: POST /api/v1/agent/chat
- Redis: `redis-cli ping`
- Postgres: `pg_isready`

## CI/CD Suggestions

- Build and push Docker images to ECR.
- Use GitHub Actions:
  - run tests
  - build backend/frontend images
  - push to ECR
  - deploy with SSH or SSM Run Command
- Tag releases (`vX.Y.Z`) and pin image tags in production.

## Industrial-Standard Must-Haves

- Observability: OpenTelemetry + Prometheus + Grafana + centralized logs.
- Resilience: retries/timeouts around ERPNext and model calls.
- Data quality: scheduled data reconciliation job and anomaly backtesting.
- Security: least-privilege IAM roles and regular dependency scans.
- DR: daily encrypted DB backups + restore drills.

## Common Mistakes to Avoid

- Running dev compose in production (bind mounts, reload mode).
- Using tiny models (1B class) for complex financial reasoning.
- Exposing Ollama or Postgres directly to public internet.
- Hardcoding secrets in .env tracked by git.
