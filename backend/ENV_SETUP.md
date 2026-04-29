# Backend Environment Configuration for Render

## Quick Reference: Required & Optional Environment Variables

### Database & Cache (REQUIRED for Production)
```bash
DATABASE_URL="postgresql://user:password@db.example.com:5432/vireon"
# AUTO-SET by Render if you link a Postgres instance
```

### Deployment & Health Checks
```bash
ENV="production"  # or "development", "staging"
REQUIRE_REDIS_FOR_READINESS="false"  # Set to true if Redis is mandatory
```

---

## Setting Environment Variables on Render

### Via Render Dashboard

1. Go to https://dashboard.render.com
2. Select your `vireon-backend` service
3. Click "Environment" tab
4. Auto-injected variables:
   - `DATABASE_URL` ✅ (from Postgres instance, if linked)
   - `REDIS_URL` ✅ (from Redis instance, if added)
5. Add custom variables:
   - Click "Add Environment Variable"
   - Enter key and value
   - Click "Save"

### Examples

```
ENV = production
ALLOWED_ORIGINS = https://vireon.vercel.app
SECRET_KEY = your-random-jwt-key-here
OPENAI_API_KEY = sk-xxxxx (if using OpenAI)
GOOGLE_API_KEY = xxx (if using Google AI)
REQUIRE_REDIS_FOR_READINESS = false (if no Redis)
```

---

## Database Connection String Examples

### PostgreSQL (Render auto-injects)
```
postgresql://username:password@host.region.provider.com:5432/dbname
```

### PostgreSQL with SSL
```
postgresql://username:password@host.region.provider.com:5432/dbname?sslmode=require
```

---

## Minimal Production Setup

If you only want the app running with basic features:

1. Create Postgres instance on Render (free tier)
2. Create Backend web service (rootDir=`backend`, Runtime=`Docker`)
3. Backend will auto-inject `DATABASE_URL`
4. Set in Environment:
   ```
   ENV = production
   REQUIRE_REDIS_FOR_READINESS = false
   ```
5. Click "Save" and service auto-redeploys

---

## Health Check Endpoints

Once deployed, verify:

```bash
# Liveness (app is running)
curl https://vireon-backend-xxxx.onrender.com/health/live

# Readiness (dependencies are healthy)
curl https://vireon-backend-xxxx.onrender.com/health/ready
```

Expected responses:
```json
{
  "status": "alive",
  "service": "vireon-backend",
  "environment": "production",
  "timestamp": 1234567890
}
```

```json
{
  "ready": true,
  "require_redis": false,
  "checks": {
    "database": {"ok": true, "latency_ms": 12, "error": null},
    "redis": {"ok": true, "latency_ms": 5, "error": null}
  },
  "environment": "production"
}
```

---

## Complete Environment Variables for Render

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `DATABASE_URL` | ✅ | None | Auto-set by Render Postgres |
| `REDIS_URL` | ❌ | None | Auto-set by Render Redis (if added) |
| `ENV` | ✅ | `development` | Set to `production` |
| `SECRET_KEY` | ❌ | Auto-generated | JWT signing key |
| `ALGORITHM` | ❌ | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `1440` | Token expiry (1 day) |
| `ALLOWED_ORIGINS` | ❌ | `http://localhost:3000` | CORS origins |
| `OPENAI_API_KEY` | ❌ | None | If using OpenAI |
| `GOOGLE_API_KEY` | ❌ | None | If using Google AI |
| `GEMINI_API_KEY` | ❌ | None | If using Gemini |
| `ERPNEXT_URL` | ❌ | None | If integrating ERPNext |
| `ERPNEXT_API_KEY` | ❌ | None | ERPNext credential |
| `ERPNEXT_API_SECRET` | ❌ | None | ERPNext credential |
| `ERPNEXT_SITE_NAME` | ❌ | None | ERPNext site name |
| `REQUIRE_REDIS_FOR_READINESS` | ❌ | `false` | Require Redis on startup |
| `STRICT_STARTUP_CHECKS` | ❌ | `false` | Fail if dependencies missing |
| `STARTUP_MAX_RETRIES` | ❌ | `15` | Retry attempts on startup |
| `STARTUP_RETRY_DELAY_SECONDS` | ❌ | `2` | Delay between retries |
