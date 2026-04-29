# Vireon Deployment Guide

## Overview

This guide covers deploying Vireon using the recommended **Vercel (frontend) + Fly.io (backend)** stack.

### Why This Stack?

| Component | Platform | Why |
|-----------|----------|-----|
| **Frontend** | Vercel | Best-in-class Next.js support, zero-config, preview deployments, edge functions, free tier |
| **Backend** | Fly.io | Docker-native, global edge deployment, persistent volumes, free tier (3 VMs, 3GB), automatic HTTPS |

---

## Part 1: Frontend Deployment (Vercel)

### Prerequisites

- GitHub account with the Vireon repository
- Vercel account (free tier is sufficient)

### Steps

#### 1. Import Project to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"New Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework**: Next.js (auto-detected)
   - **Root Directory**: `/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next` (auto-detected from `vercel.json`)
   - **Install Command**: `npm install`
5. Add environment variables (if any):
   - `NEXT_PUBLIC_API_URL` (set to your Fly.io backend URL after deployment)
6. Click **Deploy**

That's it! Your frontend will be live at `https://<your-project>.vercel.app`

#### 2. Configure Environment Variables

After deployment, set:

```bash
NEXT_PUBLIC_API_URL=https://vireon-backend.fly.dev  # Your Fly.io backend URL
```

#### 3. Automatic Preview Deployments

Vercel automatically creates preview deployments for:
- Pull requests
- Branch pushes

Each PR gets its own unique preview URL.

---

## Part 2: Backend Deployment (Fly.io)

### Prerequisites

- Fly.io account (free tier)
- Fly CLI installed locally (optional, for manual management)
- GitHub Actions secrets configured

### Setup Fly.io CLI (Local)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Create app
fly apps create vireon-backend
```

### GitHub Actions Setup

#### 1. Get Fly.io API Token

```bash
# Generate a deploy token
fly tokens create deploy -a vireon-backend
```

Copy the token (starts with `flyt-`).

#### 2. Configure GitHub Secrets

In your GitHub repository → Settings → Secrets and Variables → Actions:

| Secret Name | Value |
|-------------|-------|
| `FLY_API_TOKEN` | Your Fly.io deploy token from above |

#### 3. Optional: Set Environment-Specific Secrets

| Secret Name | Description |
|-------------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `GROQ_API_KEY` | Groq LLM API key |
| `SECRET_KEY` | JWT signing key |

These can also be set in the Fly.io dashboard under your app's **Secrets** tab.

### Deploy via GitHub Actions

The workflow (`.github/workflows/deploy-fly.yml`) will automatically:

1. Deploy when you push to `main` branch
2. Run health checks
3. Verify basic API endpoints

**Manual deployment:**

```bash
fly deploy --config fly.toml --app vireon-backend
```

### Post-Deployment Configuration

#### 1. Attach a PostgreSQL Database (Optional but Recommended)

```bash
# Create a Fly Postgres cluster
fly postgres create \
  --name vireon-db \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1 \
  --region iad

# Attach to your backend
fly postgres attach vireon-db --app vireon-backend
```

This automatically:
- Creates a PostgreSQL 15 database
- Sets `DATABASE_URL` in your app secrets
- Configures private networking

#### 2. Run Migrations

```bash
# Run migrations manually
fly ssh console -C "cd /app && alembic upgrade head" -a vireon-backend
```

Or use the GitHub workflow to run migrations as part of deployment.

#### 3. Set Up Redis (Optional, for Celery)

```bash
# Create a Redis instance using Upstash (free tier)
# Or run Redis on Fly.io (requires separate app)
```

Then set:

```bash
fly secrets set REDIS_URL=redis://user:pass@host:6379/0 -a vireon-backend
```

#### 4. Configure Environment Variables

```bash
# Set secrets via flyctl
fly secrets set GROQ_API_KEY=your_key_here -a vireon-backend
fly secrets set SECRET_KEY=$(openssl rand -hex 32) -a vireon-backend
fly secrets set ALLOWED_ORIGINS=https://your-frontend.vercel.app -a vireon-backend
```

Or copy from `.env.fly.example`:

```bash
fly secrets set-from-file -a vireon-backend < .env.fly.example
```

---

## Part 3: Domain & SSL

### Custom Domain

1. In Fly.io dashboard, go to your app → **Domains**
2. Add your domain (e.g., `api.vireon.com`)
3. Update DNS:
   - Type: `A` or `CNAME`
   - Value: Point to Fly.io IP (shown in dashboard)
4. Fly automatically provisions Let's Encrypt SSL

### Vercel Domain

1. In Vercel dashboard, go to your project → **Domains**
2. Add your domain (e.g., `app.vireon.com`)
3. Follow DNS instructions
4. Automatic SSL is enabled

Update `NEXT_PUBLIC_API_URL` to point to your custom backend domain.

---

## Part 4: Production Checklist

- [ ] Frontend deployed on Vercel
- [ ] Backend deployed on Fly.io
- [ ] PostgreSQL database attached (preferably managed)
- [ ] Redis configured for Celery (if using background tasks)
- [ ] `SECRET_KEY` set securely (not default)
- [ ] `GROQ_API_KEY` or other LLM provider configured
- [ ] SSL certificates active (automatic on Fly.io & Vercel)
- [ ] Health checks passing (`/health/ready` and `/health/live`)
- [ ] CORS allowed origins configured
- [ ] Monitoring/logging enabled
- [ ] Database migrations run
- [ ] Domain names configured (optional)
- [ ] Backups configured (for PostgreSQL)

---

## Part 5: Scaling & Optimization

### Free Tier Limits

| Service | Free Limit |
|---------|-----------|
| **Fly.io** | 3 shared-cpu VMs (256MB each), 3GB volume |
| **Vercel** | 100GB bandwidth, serverless functions |
| **Fly Postgres** | 1 cluster, 1GB RAM, 3GB storage |

### Scaling Up

#### Backend (Fly.io)

Edit `fly.toml`:

```toml
# For always-on (no cold starts)
min_machines_running = 1

# For more memory
[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 1024  # 1GB
```

#### Database

Upgrade Fly Postgres:

```bash
fly postgres update vireon-db --vm-size shared-cpu-2x --memory-size 2048
```

Or migrate to a managed service (Supabase, AWS RDS, etc.).

#### Frontend (Vercel)

- Upgrade to Pro plan for more build minutes and edge functions
- Use ISR (Incremental Static Regeneration) for faster page loads

---

## Part 6: Monitoring

### Health Checks

Automatically available at:

- `https://vireon-backend.fly.dev/health/ready` - App is ready to serve requests
- `https://vireon-backend.fly.dev/health/live` - App is alive (may be starting)

### Logs

```bash
# View recent logs
fly logs -a vireon-backend

# Stream logs in real-time
fly logs -a vireon-backend --tail
```

### Status

```bash
# Check app status
fly status -a vireon-backend

# Check VM status
fly vm status -a vireon-backend
```

---

## Part 7: Troubleshooting

### Deployment Fails

```bash
# Check build logs
fly deploy --config fly.toml --app vireon-backend --verbose

# Check app status
fly status -a vireon-backend

# View logs
fly logs -a vireon-backend
```

### 502 Bad Gateway

- Backend not running: Check `fly status`
- Health checks failing: Verify `/health/ready` endpoint works locally
- Port mismatch: Ensure `internal_port` in `fly.toml` matches backend port (8000)

### Database Connection Issues

```bash
# Test connection
fly ssh console -C "psql $DATABASE_URL -c '\dt'" -a vireon-backend

# Run migrations
fly ssh console -C "alembic upgrade head" -a vireon-backend
```

### Cold Starts

Set `min_machines_running = 1` in `fly.toml` to keep one VM always running.

---

## Part 8: CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy-fly.yml`) provides:

1. **Automatic deployment** on push to `main`
2. **Health checks** after deployment
3. **API verification** tests
4. **Environment separation** (production vs staging)

To deploy to staging:

```bash
gh workflow run deploy-fly.yml -f environment=staging
```

---

## Part 9: Local Development

### Using Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Or use development compose file
docker-compose up -d
```

### Testing Deployment Locally

```bash
# Build backend image
cd backend && docker build -t vireon-backend:local .

# Run locally
docker run -p 8000:8000 -e PORT=8000 vireon-backend:local
```

---

## Resources

- [Fly.io Documentation](https://fly.io/docs/)
- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Fly.io + FastAPI Example](https://fly.io/docs/languages-and-frameworks/fastapi/)
