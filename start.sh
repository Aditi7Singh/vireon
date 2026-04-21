#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'
RED='\033[0;31m';   BOLD='\033[1m';      NC='\033[0m'

log()  { echo -e "${CYAN}[vireon]${NC} $*"; }
ok()   { echo -e "${GREEN}[vireon]${NC} $*"; }
warn() { echo -e "${YELLOW}[vireon]${NC} $*"; }
err()  { echo -e "${RED}[vireon]${NC} $*"; }

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║         Vireon — Autonomous AI CFO 🚀            ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Check / auto-start Docker ─────────────────────────────────────────────
ensure_docker_running() {
    if docker info >/dev/null 2>&1; then return 0; fi

    if docker --context default info >/dev/null 2>&1; then
        docker context use default >/dev/null
        return 0
    fi

    if [[ "$(uname -s)" == "Darwin" ]]; then
        warn "Starting Docker Desktop..."
        open -a Docker || true
        for i in $(seq 1 60); do
            if docker info >/dev/null 2>&1; then ok "Docker ready."; return 0; fi
            sleep 2
            (( i % 10 == 0 )) && warn "Waiting for Docker... (${i}/60)"
        done
    fi

    err "Cannot reach Docker daemon. Start Docker Desktop and retry."
    exit 1
}

ensure_docker_running

# ── 2. Ensure backend/.env exists ─────────────────────────────────────────────
if [[ ! -f "$DIR/backend/.env" ]]; then
    if [[ -f "$DIR/backend/.env.demo" ]]; then
        cp "$DIR/backend/.env.demo" "$DIR/backend/.env"
        ok "Copied .env.demo → backend/.env"
        warn "Add your GROQ_API_KEY to backend/.env to enable AI chat."
    else
        err "backend/.env not found."
        echo "  Run:  cp backend/.env.example backend/.env"
        echo "  Then edit it and run ./start.sh again."
        exit 1
    fi
else
    ok "backend/.env found."
fi

# ── 3. Build & start all services in background ───────────────────────────────
log "Building and starting all services..."
docker compose up -d --build

# ── 4. Wait for backend health ────────────────────────────────────────────────
log "Waiting for backend to be ready..."
RETRIES=40
until curl -sf http://localhost:8000/health/ready >/dev/null 2>&1 || [[ $RETRIES -eq 0 ]]; do
    RETRIES=$((RETRIES - 1))
    printf "."
    sleep 5
done
echo ""

if [[ $RETRIES -eq 0 ]]; then
    warn "Backend taking longer than expected."
    warn "Check logs: docker compose logs backend"
else
    ok "Backend is healthy."
fi

# ── 5. Run database migrations ────────────────────────────────────────────────
log "Running database migrations..."
if docker compose exec -T backend alembic upgrade head 2>&1; then
    ok "Migrations applied."
else
    warn "Alembic not configured or migrations already current — skipping."
fi

# ── 6. Seed demo data (skip if data already exists) ──────────────────────────
log "Seeding demo data (Orchard Analytics Inc.)..."
if docker compose exec -T backend python scripts/demo_full_seed.py 2>&1; then
    ok "Demo data ready."
else
    warn "Seed script encountered an issue — app will still work with bootstrapped data."
fi

# ── 7. Open browser (macOS) ───────────────────────────────────────────────────
if [[ "$(uname -s)" == "Darwin" ]]; then
    sleep 1
    open "http://localhost:3000" 2>/dev/null || true
fi

# ── 8. Summary ────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║           All services are running! ✅           ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Dashboard   :${NC}  http://localhost:3000"
echo -e "  ${CYAN}API         :${NC}  http://localhost:8000"
echo -e "  ${CYAN}API Docs    :${NC}  http://localhost:8000/api/v1/docs"
echo -e "  ${CYAN}Mailhog     :${NC}  http://localhost:8025"
echo ""
echo -e "  Services running: postgres · redis · backend · worker · beat · frontend"
echo ""
echo -e "  ${YELLOW}Useful commands:${NC}"
echo -e "    docker compose logs -f backend     # live backend logs"
echo -e "    docker compose logs -f worker      # live Celery logs"
echo -e "    docker compose ps                  # service status"
echo -e "    docker compose down                # stop everything"
echo ""
