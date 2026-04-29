# Vireon Deployment Guide — Vercel + Render

## Overview
- **Frontend** (Next.js): Deployed to Vercel
- **Backend** (FastAPI): Deployed to Render  
- **Database**: PostgreSQL (managed by Render, free tier)
- **Cache**: Redis (optional, managed by Render, free tier)

---

## Frontend Setup (Vercel)

### Prerequisites
- Vercel account (free): https://vercel.com

### Steps

1. **Connect GitHub to Vercel**
   - Go to https://vercel.com/dashboard
   - Click "Add New → Project"
   - Import your GitHub repo `vireon`
   - Select `frontend` as the Root Directory
   - Click "Deploy"

2. **Build & Deployment Settings (auto-configured)**
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`
   - Node.js Version: `20.x` (set in `frontend/vercel.json`)

3. **Environment Variables (in Vercel Dashboard)**
   - Go to Project Settings → Environment Variables
   - Add:
     ```
     NEXT_PUBLIC_API_BASE_URL=https://vireon-backend-xxx.onrender.com/api/v1
     ```
   - Redeploy after adding env vars

4. **Custom Domain (optional)**
   - Go to Project Settings → Domains
   - Add your custom domain

5. **Deployment Trigger**
   - Push to `main` branch → automatic deployment
   - Manual: Use `vercel deploy --prod` or GitHub Actions workflow

---

## Backend Setup (Render)

### Prerequisites
- Render account (free, no credit card): https://render.com
- GitHub repo connected to Render

### One-Time Setup (Free Tier, No Credit Card Required)

1. **Sign up on Render**
   - Go to https://render.com
   - Sign up with GitHub (easiest)
   - No credit card needed for free tier

2. **Create Backend Service**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repo `vireon`
   - Configure:
     - **Name**: `vireon-backend`
     - **Root Directory**: `backend`
     - **Runtime**: `Docker`
     - **Build Command**: (leave blank — Docker handles it)
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Plan**: `Free` (auto-stops after 15 min inactivity)
     - **Region**: Singapore or closest to you

3. **Add Database (Render Postgres)**
   - Still in Render dashboard
   - Click "New +" → "PostgreSQL"
   - Configure:
     - **Name**: `vireon-db`
     - **Database**: `vireon`
     - **User**: `vireon_user`
     - **Plan**: `Free` (0.5 GB storage)
   - Render auto-injects `DATABASE_URL` into your backend service

4. **Add Redis (Optional, for Celery/Caching)**
   - Click "New +" → "Redis"
   - Configure:
     - **Name**: `vireon-redis`
     - **Plan**: `Free` (256 MB)
   - Render auto-injects `REDIS_URL` into your backend service

5. **Set Backend Environment Variables**
   - Go to your `vireon-backend` service
   - Click "Environment"
   - Variables auto-set:
     - `DATABASE_URL` ✅ (from Postgres service)
     - `REDIS_URL` ✅ (from Redis service, if added)
   - Add manually:
     ```
     ENV=production
     ALLOWED_ORIGINS=https://vireon.vercel.app
     SECRET_KEY=your-secure-random-string
     OPENAI_API_KEY=sk-xxxxx  (if using OpenAI)
     GOOGLE_API_KEY=xxx  (if using Google AI)
     REQUIRE_REDIS_FOR_READINESS=false  (if no Redis)
     ```
   - Click "Save"

6. **Deploy**
   - Render auto-deploys when you push to `main`
   - Manually trigger: Go to your service → "Deployments" → "Manual Deploy"
   - Backend URL: `https://vireon-backend-xxxx.onrender.com`

---

## GitHub Actions Automation (Optional)

Once Render and Vercel are connected, GitHub Actions will auto-deploy on push to `main`:

### Backend Deployment Trigger (Render)
- File: `.github/workflows/deploy-backend.yml`
- Triggers on: push to `main` in `backend/**` or `render.yaml`
- Requires secrets: `RENDER_SERVICE_ID`, `RENDER_API_KEY`

### Frontend Deployment Trigger (Vercel)
- File: `.github/workflows/deploy-frontend.yml`
- Triggers on: push to `main` in `frontend/**`
- Requires secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

### How to Add GitHub Secrets

**For Render Backend:**
1. Go to Render Dashboard → Account Settings → API Keys
2. Create API key, copy it
3. Go to GitHub Repo → Settings → Secrets → New Secret
4. Add:
   - **Name**: `RENDER_API_KEY`
   - **Value**: (paste Render API key)
   - **Name**: `RENDER_SERVICE_ID`
   - **Value**: (find in Render service URL: `https://render.com/v1/services/srv-xxxxx`)

**For Vercel Frontend:**
1. Go to Vercel Dashboard → Account Settings → API Tokens
2. Create token, copy it
3. Go to GitHub Repo → Settings → Secrets
4. Add:
   - **Name**: `VERCEL_TOKEN`
   - **Value**: (paste token)
   - **Name**: `VERCEL_ORG_ID`
   - **Value**: (your Vercel org ID)
   - **Name**: `VERCEL_PROJECT_ID`
   - **Value**: (your Vercel project ID)

---

## Environment Variables Summary

### Backend (Render Environment)
| Variable | Required | Example |
|----------|----------|---------|
| `DATABASE_URL` | ✅ Auto-set | (injected by Render Postgres) |
| `REDIS_URL` | ❌ Auto-set if added | (injected by Render Redis) |
| `SECRET_KEY` | ❌ | JWT secret (auto-set if not provided) |
| `OPENAI_API_KEY` | ❌ | `sk-xxxxx` (if using OpenAI) |
| `GOOGLE_API_KEY` | ❌ | Google API key (if using Vertex AI) |
| `ENV` | ✅ | `production` |
| `ALLOWED_ORIGINS` | ❌ | `https://vireon.vercel.app` |

### Frontend (Vercel Environment Variables)
| Variable | Required | Example |
|----------|----------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ | `https://vireon-backend-xxxx.onrender.com/api/v1` |

---

## Health Checks & Monitoring

### Backend Health
```bash
curl https://vireon-backend-xxxx.onrender.com/health/live
curl https://vireon-backend-xxxx.onrender.com/health/ready
```

### Monitor Logs
- Render Dashboard → Select service → "Logs"

### Restart App
- Render Dashboard → Select service → "Restart" (top right)

---

## Database Migrations

### Auto-Migrations on Deploy
The `render.yaml` is already configured to run:
```yaml
buildCommand: pip install -r requirements.txt -r requirements_agent.txt && alembic upgrade head
```

This runs Alembic migrations before the app starts.

### Manual Migration
```bash
cd backend
alembic upgrade head
```

---

## Troubleshooting

### Backend Won't Start
1. Check logs: Render Dashboard → Logs
2. Verify `DATABASE_URL` is auto-injected (check Environment section)
3. If using Redis, ensure `REDIS_URL` is set or `REQUIRE_REDIS_FOR_READINESS=false`

### Frontend Blank/404
1. Verify `NEXT_PUBLIC_API_BASE_URL` is set in Vercel
2. Check that backend service is running: `curl https://vireon-backend-xxxx.onrender.com/health/live`
3. Check browser console for CORS/network errors

### Cold Starts
- Render free tier auto-stops after 15 min inactivity → first request takes ~30-40s
- Upgrade to paid plan to prevent auto-stop

### Service Not Redeploying
- Push to `main` branch to trigger auto-deploy
- Or manually trigger: Render Dashboard → "Manual Deploy"

---

## Cost Estimate (Free Tier, No Credit Card)

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Vercel Frontend | ✅ Free | Unlimited deployments, 100GB/mo bandwidth |
| Render Backend | ✅ Free | Auto-stops after 15 min inactivity, 1 web service |
| Render Postgres | ✅ Free | 0.5 GB storage, 1 instance |
| Render Redis | ✅ Free | 256 MB, 1 instance |
| **Total** | | **$0/month** |

---

## Quick Start Checklist

- [ ] Sign up on Render (no credit card)
- [ ] Create Backend Web Service (Docker, rootDir=`backend`)
- [ ] Create Postgres database (auto-links `DATABASE_URL`)
- [ ] (Optional) Create Redis instance (auto-links `REDIS_URL`)
- [ ] Set backend env vars: `ALLOWED_ORIGINS`, `SECRET_KEY`, API keys
- [ ] Backend deploys automatically from `main` branch
- [ ] Sign up on Vercel (no credit card)
- [ ] Create Frontend Project (rootDir=`frontend`)
- [ ] Set Vercel env var: `NEXT_PUBLIC_API_BASE_URL=https://vireon-backend-xxxx.onrender.com/api/v1`
- [ ] Redeploy frontend in Vercel
- [ ] Test: Open frontend URL in browser, check API calls in DevTools

---

## Next Steps

1. ✅ Create Render account (free, GitHub login)
2. ✅ Create Backend service (Docker, rootDir=`backend`)
3. ✅ Create Postgres + Redis on Render
4. ✅ Set environment variables in Render
5. ✅ Create Vercel project (GitHub import, rootDir=`frontend`)
6. ✅ Set `NEXT_PUBLIC_API_BASE_URL` in Vercel
7. ✅ Test endpoints & frontend

All free, no credit card required!
