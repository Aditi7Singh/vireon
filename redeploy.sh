#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# redeploy.sh  –  Rebuild, push, and redeploy changed services to AWS ECS
#
# Usage:
#   ./redeploy.sh              # redeploy both backend and frontend
#   ./redeploy.sh backend      # redeploy backend only
#   ./redeploy.sh frontend     # redeploy frontend only
#   ./redeploy.sh migrations   # run DB migrations only
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Config ───────────────────────────────────────────────────────────────────
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="732772501496"
ECR_BACKEND="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/vireon-prod-backend"
ECR_FRONTEND="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/vireon-prod-frontend"
CLUSTER="vireon-prod-cluster"
ALB_URL="http://vireon-prod-alb-1058854410.us-east-1.elb.amazonaws.com"
NEXT_PUBLIC_API_URL="${ALB_URL}"

TARGET="${1:-all}"
IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

# ── ECR Login ────────────────────────────────────────────────────────────────
ecr_login() {
  echo "→ Logging into ECR..."
  aws ecr get-login-password --region "$AWS_REGION" \
    | docker login --username AWS --password-stdin \
        "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
}

# ── Build & Push Backend ─────────────────────────────────────────────────────
deploy_backend() {
  echo "→ Building backend image (tag: $IMAGE_TAG)..."
  docker build -t "${ECR_BACKEND}:${IMAGE_TAG}" -t "${ECR_BACKEND}:latest" ./backend

  echo "→ Pushing backend to ECR..."
  docker push "${ECR_BACKEND}:${IMAGE_TAG}"
  docker push "${ECR_BACKEND}:latest"

  echo "→ Forcing new backend deployment..."
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service vireon-prod-backend \
    --force-new-deployment \
    --query 'service.serviceName' --output text

  echo "→ Forcing new worker deployment..."
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service vireon-prod-worker \
    --force-new-deployment \
    --query 'service.serviceName' --output text

  echo "→ Forcing new beat deployment..."
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service vireon-prod-beat \
    --force-new-deployment \
    --query 'service.serviceName' --output text

  echo "→ Waiting for backend to stabilize..."
  aws ecs wait services-stable \
    --cluster "$CLUSTER" \
    --services vireon-prod-backend
  echo "✓ Backend deployed"
}

# ── Build & Push Frontend ────────────────────────────────────────────────────
deploy_frontend() {
  echo "→ Building frontend image (tag: $IMAGE_TAG, API_URL: $NEXT_PUBLIC_API_URL)..."
  docker build \
    -f frontend/Dockerfile.prod \
    --build-arg NEXT_PUBLIC_API_URL="$NEXT_PUBLIC_API_URL" \
    -t "${ECR_FRONTEND}:${IMAGE_TAG}" \
    -t "${ECR_FRONTEND}:latest" \
    ./frontend

  echo "→ Pushing frontend to ECR..."
  docker push "${ECR_FRONTEND}:${IMAGE_TAG}"
  docker push "${ECR_FRONTEND}:latest"

  echo "→ Forcing new frontend deployment..."
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service vireon-prod-frontend \
    --force-new-deployment \
    --query 'service.serviceName' --output text

  echo "→ Waiting for frontend to stabilize..."
  aws ecs wait services-stable \
    --cluster "$CLUSTER" \
    --services vireon-prod-frontend
  echo "✓ Frontend deployed"
}

# ── Run DB Migrations ────────────────────────────────────────────────────────
run_migrations() {
  echo "→ Running Alembic migrations..."

  # Get network config from backend service
  SUBNETS=$(aws ecs describe-services \
    --cluster "$CLUSTER" \
    --services vireon-prod-backend \
    --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets' \
    --output json)
  SGS=$(aws ecs describe-services \
    --cluster "$CLUSTER" \
    --services vireon-prod-backend \
    --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups' \
    --output json)

  NET_JSON="{\"awsvpcConfiguration\":{\"subnets\":${SUBNETS},\"securityGroups\":${SGS},\"assignPublicIp\":\"DISABLED\"}}"

  TASK_ARN=$(aws ecs run-task \
    --cluster "$CLUSTER" \
    --task-definition vireon-prod-backend \
    --launch-type FARGATE \
    --network-configuration "$NET_JSON" \
    --overrides '{"containerOverrides":[{"name":"backend","command":["alembic","upgrade","head"]}]}' \
    --query 'tasks[0].taskArn' \
    --output text)

  echo "  Migration task: $TASK_ARN"
  aws ecs wait tasks-stopped --cluster "$CLUSTER" --tasks "$TASK_ARN"

  EXIT_CODE=$(aws ecs describe-tasks \
    --cluster "$CLUSTER" \
    --tasks "$TASK_ARN" \
    --query 'tasks[0].containers[0].exitCode' \
    --output text)

  if [ "$EXIT_CODE" = "0" ]; then
    echo "✓ Migrations completed successfully"
  else
    echo "✗ Migration failed with exit code $EXIT_CODE"
    exit 1
  fi
}

# ── Health Check ─────────────────────────────────────────────────────────────
health_check() {
  echo "→ Verifying deployment..."
  sleep 5
  STATUS=$(curl -sf "${ALB_URL}/health/ready" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d['ready'] else 'FAIL')" 2>/dev/null || echo "UNREACHABLE")
  echo "  Health: $STATUS"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Live URL:  $ALB_URL"
  echo "  API Docs:  $ALB_URL/api/v1/docs"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ── Main ─────────────────────────────────────────────────────────────────────
ecr_login

case "$TARGET" in
  backend)
    run_migrations
    deploy_backend
    ;;
  frontend)
    deploy_frontend
    ;;
  migrations)
    run_migrations
    ;;
  all|*)
    run_migrations
    deploy_backend
    deploy_frontend
    ;;
esac

health_check
