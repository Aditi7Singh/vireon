#!/usr/bin/env bash
set -euo pipefail

# One-command EC2 bootstrap for Vireon production deployment.
# Installs Docker, prepares env files, deploys compose stack, and pulls Ollama models.

PROJECT_DIR="${PROJECT_DIR:-/opt/vireon}"
REPO_URL="${REPO_URL:-}"
REPO_BRANCH="${REPO_BRANCH:-main}"
COMPOSE_FILE="docker-compose.prod.yml"

USE_LOCAL_LLM="${USE_LOCAL_LLM:-true}"
USE_OLLAMA_PROFILE="${USE_OLLAMA_PROFILE:-true}"
OLLAMA_MODEL_FAST="${OLLAMA_MODEL_FAST:-llama3.1:8b}"
OLLAMA_MODEL_THINK="${OLLAMA_MODEL_THINK:-qwen2.5:14b}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"

POSTGRES_DB="${POSTGRES_DB:-vireon}"
POSTGRES_USER="${POSTGRES_USER:-vireon}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-change-me}"
NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing command: $1"
    exit 1
  fi
}

set_or_append_env() {
  local key="$1"
  local value="$2"
  local file="$3"

  if grep -qE "^${key}=" "$file"; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" "$file"
  else
    echo "${key}=${value}" >> "$file"
  fi
}

install_docker_if_needed() {
  if command -v docker >/dev/null 2>&1; then
    echo "Docker already installed"
    return
  fi

  echo "Installing Docker and dependencies"
  sudo apt-get update -y
  sudo apt-get install -y ca-certificates curl gnupg lsb-release git
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
}

prepare_repo() {
  if [[ -d "$PROJECT_DIR/.git" ]]; then
    echo "Using existing repository at $PROJECT_DIR"
  else
    if [[ -z "$REPO_URL" ]]; then
      echo "REPO_URL is required when PROJECT_DIR does not contain a git repository"
      exit 1
    fi
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown -R "$USER":"$USER" "$PROJECT_DIR"
    git clone --branch "$REPO_BRANCH" "$REPO_URL" "$PROJECT_DIR"
  fi

  cd "$PROJECT_DIR"
}

prepare_env_files() {
  if [[ ! -f "backend/.env" ]]; then
    cp backend/.env.example backend/.env
  fi

  cat > .env <<EOF
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
USE_LOCAL_LLM=${USE_LOCAL_LLM}
OLLAMA_BASE_URL=${OLLAMA_BASE_URL}
OLLAMA_MODEL_FAST=${OLLAMA_MODEL_FAST}
OLLAMA_MODEL_THINK=${OLLAMA_MODEL_THINK}
STRICT_STARTUP_CHECKS=true
REQUIRE_REDIS_FOR_READINESS=true
STARTUP_MAX_RETRIES=30
STARTUP_RETRY_DELAY_SECONDS=2
EOF

  set_or_append_env "DATABASE_URL" "postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}" "backend/.env"
  set_or_append_env "USE_LOCAL_LLM" "${USE_LOCAL_LLM}" "backend/.env"
  set_or_append_env "OLLAMA_BASE_URL" "${OLLAMA_BASE_URL}" "backend/.env"
  set_or_append_env "OLLAMA_MODEL_FAST" "${OLLAMA_MODEL_FAST}" "backend/.env"
  set_or_append_env "OLLAMA_MODEL_THINK" "${OLLAMA_MODEL_THINK}" "backend/.env"
  set_or_append_env "STRICT_STARTUP_CHECKS" "true" "backend/.env"
  set_or_append_env "REQUIRE_REDIS_FOR_READINESS" "true" "backend/.env"
}

deploy_stack() {
  local profile_args=()
  if [[ "$USE_OLLAMA_PROFILE" == "true" ]]; then
    profile_args+=(--profile with-ollama)
  fi

  docker compose -f "$COMPOSE_FILE" "${profile_args[@]}" pull || true
  docker compose -f "$COMPOSE_FILE" "${profile_args[@]}" up -d --build
}

pull_models() {
  if [[ "$USE_LOCAL_LLM" != "true" ]]; then
    echo "Skipping model pull because USE_LOCAL_LLM is not true"
    return
  fi
  if [[ "$USE_OLLAMA_PROFILE" != "true" ]]; then
    echo "Skipping model pull because Compose Ollama profile is disabled"
    return
  fi

  docker compose -f "$COMPOSE_FILE" exec -T ollama ollama pull "$OLLAMA_MODEL_FAST"
  docker compose -f "$COMPOSE_FILE" exec -T ollama ollama pull "$OLLAMA_MODEL_THINK"
}

post_deploy_checks() {
  echo "Waiting for backend readiness"
  for _ in {1..45}; do
    status="$(curl -s -o /tmp/vireon-ready.json -w "%{http_code}" http://localhost:8000/health/ready || true)"
    if [[ "$status" == "200" ]]; then
      echo "Backend is ready"
      cat /tmp/vireon-ready.json
      return
    fi
    sleep 2
  done

  echo "Backend did not become ready in time"
  docker compose -f "$COMPOSE_FILE" logs --tail=100 backend
  exit 1
}

main() {
  require_cmd curl
  install_docker_if_needed
  require_cmd git
  require_cmd docker

  prepare_repo
  prepare_env_files
  deploy_stack
  pull_models
  post_deploy_checks

  echo "Deployment complete"
  echo "Frontend: ${NEXT_PUBLIC_API_URL/http:\/\/localhost:8000/http:\/\/localhost:3000}"
  echo "Backend docs: http://localhost:8000/api/v1/docs"
}

main "$@"
