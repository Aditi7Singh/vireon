# Vireon Deployment Guide — Vercel + Fly.io

## Overview
- **Frontend** (Next.js): Deployed to Vercel
- **Backend** (FastAPI): Deployed to Fly.io  
- **Database**: PostgreSQL (managed, external)
- **Cache**: Redis (optional, managed)

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
     NEXT_PUBLIC_API_BASE_URL=https://vireon-backend.fly.dev/api/v1
     ```
   - Redeploy after adding env vars

4. **Custom Domain (optional)**
   - Go to Project Settings → Domains
   - Add your custom domain

5. **Deployment Trigger**
   - Push to `main` branch → automatic deployment
   - Manual: Use `vercel deploy --prod` or GitHub Actions workflow

---

## Backend Setup (Fly.io)

### Prerequisites
- Fly.io account (free tier available): https://fly.io
- Fly CLI installed: `brew install flyctl` (macOS)
- PostgreSQL database URL
- (Optional) Redis URL

### One-Time Setup (Local)

1. **Authenticate with Fly.io**
   ```bash
   flyctl auth signup  # or flyctl auth login
   ```

2. **Create App on Fly.io**
   ```bash
   cd backend
   flyctl launch --generate-name  # Creates app and fly.toml
   # When prompted:
   #   - Postgres: "Would you like to add Postgres? [y/N]" → Choose based on your needs
   #   - Copy the generated app name (e.g., "vireon-backend-1234")
   ```
   
   **OR** use the pre-configured `fly.toml` in this repo:
   ```bash
   cd backend
   flyctl deploy --remote-only
   # You will be prompted to create the app if it doesn't exist
   ```

3. **Set Fly.io Secrets**
   ```bash
   flyctl secrets set \
     DATABASE_URL="postgresql://user:password@host:port/dbname" \
     REDIS_URL="redis://user:password@host:port/0" \
     SECRET_KEY="your-jwt-secret-key" \
     OPENAI_API_KEY="sk-xxx" \
     GOOGLE_API_KEY="your-google-key" \
     ENV="production"
   ```
   
   **Example minimal set** (if you only use database, no Redis/AI):
   ```bash
   flyctl secrets set \
     DATABASE_URL="postgresql://user:password@host:port/dbname" \
     ENV="production"
   ```

4. **Deploy**
   ```bash
   cd backend
   flyctl deploy
   ```
   
   Fly.io will:
   - Build Docker image
   - Run migrations (if `Dockerfile` includes them; currently not auto-run)
   - Start the app
   - Assign a public URL: `https://vireon-backend.fly.dev`

5. **Check Status**
   ```bash
   flyctl status
   flyctl logs
   ```

---

## GitHub Actions Automation

Once Fly.io and Vercel are connected, GitHub Actions will auto-deploy on push to `main`:

### Backend Deployment Trigger
- File: `.github/workflows/deploy-backend.yml`
- Triggers on: push to `main` in `backend/**`
- Requires secret: `FLY_API_TOKEN`

### Frontend Deployment Trigger
- File: `.github/workflows/deploy-frontend.yml`
- Triggers on: push to `main` in `frontend/**`
- Requires secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

### How to Add GitHub Secrets

**For Fly.io Backend:**
1. Go to GitHub Repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add:
   - **Name**: `FLY_API_TOKEN`
   - **Value**: Run `flyctl tokens create deploy -x 0` locally (no expiry) and paste the token

**For Vercel Frontend:**
1. Go to Vercel Dashboard → Project Settings → API Tokens
2. Create a new token, copy it
3. Go to GitHub Repo → Settings → Secrets and variables → Actions
4. Add:
   - **Name**: `VERCEL_TOKEN`
   - **Value**: Paste the Vercel token
   - **Name**: `VERCEL_ORG_ID`
   - **Value**: Your Vercel org ID (visible in Vercel URL)
   - **Name**: `VERCEL_PROJECT_ID`
   - **Value**: Your Vercel project ID (visible in Vercel project settings)

---

## Environment Variables Summary

### Backend (Fly.io Secrets)
| Variable | Required | Example |
|----------|----------|---------|
| `DATABASE_URL` | ✅ | `postgresql://user:pass@db.example.com:5432/vireon` |
| `REDIS_URL` | ❌ | `redis://user:pass@redis.example.com:6379/0` |
| `SECRET_KEY` | ❌ | JWT secret (auto-set if not provided) |
| `OPENAI_API_KEY` | ❌ | `sk-xxxxx` (if using OpenAI) |
| `GOOGLE_API_KEY` | ❌ | Google API key (if using Vertex AI) |
| `ENV` | ✅ | `production` |
| `ALLOWED_ORIGINS` | ❌ | `https://vireon.vercel.app,https://yourfrontend.com` |

### Frontend (Vercel Environment Variables)
| Variable | Required | Example |
|----------|----------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ | `https://vireon-backend.fly.dev/api/v1` |

---

## Health Checks & Monitoring

### Backend Health
```bash
curl https://vireon-backend.fly.dev/health/live
curl https://vireon-backend.fly.dev/health/ready
```

### Monitor Logs
```bash
flyctl logs  # Tail real-time logs
```

### Restart App
```bash
flyctl restart
```

### Scale (Fly.io)
```bash
flyctl scale count 2  # Run 2 instances
flyctl scale memory 512  # Increase memory to 512MB
```

---

## Database Migrations

### Create Tables on Deploy

Currently, the FastAPI app auto-creates tables on startup:
```python
# In backend/main.py
models.Base.metadata.create_all(bind=database.engine)
bootstrap.run_bootstrap()
```

If you need explicit migrations (Alembic):
```bash
cd backend
alembic upgrade head
```

To include this in Fly.io deploy, add to `Dockerfile`:
```dockerfile
RUN alembic upgrade head  # Run before starting app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Troubleshooting

### Backend Won't Start
1. Check logs: `flyctl logs`
2. Verify `DATABASE_URL` is accessible
3. Check if app expects Redis but it's not available → set `REQUIRE_REDIS_FOR_READINESS=false`

### Frontend Blank/404
1. Verify `NEXT_PUBLIC_API_BASE_URL` is set in Vercel
2. Check that backend is running and accessible
3. Check browser console for CORS/network errors

### Cold Starts
- Fly.io free tier scales to zero. First request may be slow (~5-10s).
- Upgrade to paid plan or use `always_on = true` in `fly.toml` to prevent scale-to-zero.

### Secrets Not Updating
- Redeploy after changing secrets: `flyctl deploy`

---

## Cost Estimate (Free Tier)

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Vercel Frontend | ✅ Free | Unlimited deployments, 100GB/mo bandwidth |
| Fly.io Backend | ✅ Free | 3 shared-cpu VMs, scales to zero (cold starts) |
| PostgreSQL | 🔄 Depends | Use external (AWS RDS free tier, Supabase free, etc.) |
| Redis | 🔄 Depends | Use external or skip if not needed |

---

## Next Steps

1. ✅ Create Fly.io account & authenticate locally
2. ✅ Create Vercel account & connect GitHub
3. ✅ Set up database (PostgreSQL)
4. ✅ Deploy backend: `cd backend && flyctl deploy`
5. ✅ Deploy frontend: Push to `main` or manual Vercel deploy
6. ✅ Add GitHub Actions secrets for CI/CD
7. ✅ Test endpoints: `/health/live`, `/health/ready`, frontend URL
