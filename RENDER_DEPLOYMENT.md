# Render Backend Deployment Guide

## Prerequisites

1. A [Render](https://render.com) account
2. The backend code pushed to a GitHub repository
3. Required API keys (Groq, OpenAI, etc.)

## Deployment Steps

### 1. Connect GitHub Repository to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** and select **"Blueprint"**
3. Connect your GitHub account
4. Select the repository containing your code
5. Render will detect `render.yaml` automatically

### 2. Review and Deploy

1. Render will show you the services defined in `render.yaml`:
   - `vireon-backend` (Web service)
   - `vireon-db` (PostgreSQL database)
   - `vireon-redis` (Redis service)
2. Click **"Create Resources"**
3. Render will provision all services and deploy automatically

### 3. Configure Environment Variables

After deployment, update the environment variables in the Render Dashboard:

1. Go to **Dashboard** → **vireon-backend** → **Environment**
2. Set the following variables:
   - `ALLOWED_ORIGINS`: Your Vercel frontend URL (e.g., `https://yourdomain.vercel.app`)
   - `GROQ_API_KEY`: Your Groq API key from https://console.groq.com
   - `SECRET_KEY`: A secure random string (use Python: `import secrets; print(secrets.token_urlsafe(32))`)
   - `OPENAI_API_KEY`: Your OpenAI API key (if needed)
   - `MERGE_API_KEY`: Merge.dev API key (if using)
   - `MERGE_SECRET_KEY`: Merge.dev secret key (if using)
   - `ERPNEXT_URL`: ERPNext instance URL (if integrating)
   - `ERPNEXT_API_KEY`: ERPNext API key (if integrating)
   - `ERPNEXT_API_SECRET`: ERPNext API secret (if integrating)

### 4. Database Setup

PostgreSQL is automatically provisioned. The connection string is:
```
postgresql://vireon_user:PASSWORD@HOST:5432/vireon
```

**Run migrations on first deployment:**
1. Go to **vireon-backend** → **Shell**
2. Run:
   ```bash
   alembic upgrade head
   ```
3. Optionally seed demo data:
   ```bash
   python seed_demo_data.py
   ```

### 5. Verify Deployment

1. Your backend will be available at: `https://vireon-backend.onrender.com`
2. Check API docs: `https://vireon-backend.onrender.com/api/v1/docs`
3. Health check: `https://vireon-backend.onrender.com/health/live`

## Auto-Redeploy

Render automatically redeployes when you push to the connected GitHub repository.

## Scaling

- Increase instances: Dashboard → **vireon-backend** → **Instance Count**
- Upgrade database tier: Dashboard → **vireon-db** → **Plan**
- Upgrade Redis tier: Dashboard → **vireon-redis** → **Plan**

## Logs

View live logs:
1. Go to **vireon-backend** → **Logs**
2. Or stream from CLI: `render logs --service vireon-backend`

## Troubleshooting

### Service won't start
1. Check logs for errors
2. Verify all required environment variables are set
3. Ensure DATABASE_URL is correct and database is accessible

### Database connection errors
1. Verify PostgreSQL service is running
2. Check DATABASE_URL format
3. Run migrations: `alembic upgrade head`

### Redis connection errors
1. Check Redis service is running
2. Verify REDIS_URL format
3. Set `REQUIRE_REDIS_FOR_READINESS=false` if Redis is optional for your use case

## Costs

- Free tier available for testing
- Standard tier pricing:
  - Web service: ~$7/month
  - PostgreSQL: ~$9-15/month depending on size
  - Redis: ~$9-15/month depending on size
