# Vireon Deployment Guide

**Last updated:** April 8, 2026

## Overview

This is the single deployment guide for Vireon. It covers local development, Docker Compose, and production deployment. The backend API docs are served at `/api/v1/docs`.

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Docs

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## Docker Compose

### Start the stack

```bash
docker compose up -d --build
```

### Services

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6379`
- Mailhog: `http://localhost:8025`

### Health checks

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### Database migrations

```bash
cd backend
alembic upgrade head
```

## Environment Variables

Set these in `backend/.env` and, for frontend builds, in the frontend build environment when needed:

- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_FROM`
- `ERPNEXT_URL`
- `ERPNEXT_API_KEY`
- `ERPNEXT_API_SECRET`
- `NEXT_PUBLIC_API_URL`

## Production Deployment

### Recommended topology

- ALB or Nginx in front
- Frontend service on port 3000
- Backend service on port 8000
- PostgreSQL in a private network
- Redis in a private network
- Optional Ollama service for local LLM fallback

### Frontend production image

The production frontend image is defined in [frontend/Dockerfile.prod](frontend/Dockerfile.prod).

### AWS/ECS flow

1. Build backend and frontend images.
2. Push the images to your registry.
3. Run database migrations.
4. Deploy backend, worker, beat, and frontend services.
5. Verify `/health/ready` and `/api/v1/docs`.

## Troubleshooting

- If you see `404: This page could not be found`, verify you are using a valid frontend route or the `/api/v1/docs` backend docs URL.
- If the frontend shows old routes, rebuild the container so the latest Next.js app is deployed.
- If backend startup is slow, check PostgreSQL and Redis readiness first.

## Related Files

- [PROJECT_STATUS.md](PROJECT_STATUS.md)
- [README.md](README.md)
- [frontend/Dockerfile.prod](frontend/Dockerfile.prod)
- [backend/main.py](backend/main.py)