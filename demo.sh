#!/bin/bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║      Vireon — Autonomous AI CFO  Demo Mode       ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
  echo "❌  Docker not found. Install Docker Desktop from https://docker.com"
  exit 1
fi

if ! docker info &> /dev/null 2>&1; then
  echo "❌  Docker is not running. Please start Docker Desktop and retry."
  exit 1
fi

# Copy demo env if no .env exists yet
if [ ! -f backend/.env ]; then
  cp backend/.env.demo backend/.env
  echo -e "${GREEN}✅  Demo environment configured from .env.demo${NC}"
else
  echo -e "${GREEN}✅  Using existing backend/.env${NC}"
fi

echo ""
echo -e "${YELLOW}⏳  Building and starting services (first run ~3 min)...${NC}"
docker compose -f docker-compose.demo.yml up -d --build

# Wait for backend health (up to 3 minutes)
echo ""
echo -e "${YELLOW}⏳  Waiting for backend to be ready...${NC}"
RETRIES=36
until curl -sf http://localhost:8000/health/ready > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  RETRIES=$((RETRIES - 1))
  printf "."
  sleep 5
done
echo ""

if [ "$RETRIES" -eq 0 ]; then
  echo -e "${YELLOW}⚠️   Backend taking longer than expected.${NC}"
  echo -e "    Check logs: docker compose -f docker-compose.demo.yml logs backend"
else
  echo -e "${GREEN}✅  Backend ready${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║          Vireon Demo is Live! 🚀                 ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Dashboard :${NC}  http://localhost:3000"
echo -e "  ${CYAN}API       :${NC}  http://localhost:8000"
echo -e "  ${CYAN}API Docs  :${NC}  http://localhost:8000/api/v1/docs"
echo ""
echo -e "  Demo company : ${BOLD}Orchard Analytics Inc.${NC} (B2B SaaS, Series A)"
echo -e "  12 months of financial data + 7 pre-loaded anomalies seeded"
echo ""
echo -e "To stop:  ${BOLD}docker compose -f docker-compose.demo.yml down${NC}"
echo ""
