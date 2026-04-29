# Backend Environment Configuration for Fly.io

## Quick Reference: Required & Optional Environment Variables

### Database & Cache (REQUIRED for Production)
```bash
DATABASE_URL="postgresql://user:password@db.example.com:5432/vireon"
REDIS_URL="redis://user:password@redis.example.com:6379/0"  # Optional if REQUIRE_REDIS_FOR_READINESS=false
```

### Authentication & Security (RECOMMENDED)
```bash
SECRET_KEY="your-secure-random-string"  # JWT signing key
ALGORITHM="HS256"  # JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES="1440"  # Token expiry in minutes (1 day = 1440)
```

### API Keys (OPTIONAL — Only if using these services)
```bash
OPENAI_API_KEY="sk-..."  # OpenAI GPT models
GOOGLE_API_KEY="..."  # Google Generative AI
GEMINI_API_KEY="..."  # Alternative: Gemini API
```

### ERPNext Integration (OPTIONAL)
```bash
ERPNEXT_URL="https://erpnext.example.com"
ERPNEXT_API_KEY="your-api-key"
ERPNEXT_API_SECRET="your-api-secret"
ERPNEXT_SITE_NAME="site1"
```

### Deployment & Health Checks
```bash
ENV="production"  # or "development", "staging"
REQUIRE_REDIS_FOR_READINESS="false"  # Set to true if Redis is mandatory
STRICT_STARTUP_CHECKS="false"  # Set to true for strict dependency checks
STARTUP_MAX_RETRIES="15"  # Number of startup retry attempts
STARTUP_RETRY_DELAY_SECONDS="2"  # Delay between retries
```

### CORS (Frontend Communication)
```bash
ALLOWED_ORIGINS="https://vireon.vercel.app,https://yourdomain.com"
```

---

## Setting Secrets on Fly.io

### Option 1: Interactive
```bash
flyctl secrets set
# Follow prompts to enter each variable
```

### Option 2: Batch
```bash
flyctl secrets set \
  DATABASE_URL="postgresql://..." \
  REDIS_URL="redis://..." \
  SECRET_KEY="your-key" \
  ENV="production"
```

### Option 3: From .env file (local only, not recommended for production)
```bash
export $(cat .env | xargs)
flyctl secrets set DATABASE_URL=$DATABASE_URL REDIS_URL=$REDIS_URL
```

---

## View Current Secrets
```bash
flyctl secrets list  # Shows secret names (not values)
```

---

## Database Connection String Examples

### PostgreSQL (Neon, AWS RDS, etc.)
```
postgresql://user:password@host.region.provider.com:5432/dbname
```

### PostgreSQL with SSL
```
postgresql://user:password@host.region.provider.com:5432/dbname?sslmode=require
```

---

## Redis Connection String Examples

### Standard Redis
```
redis://username:password@host:6379/0
```

### Redis Cluster / Sentinel
```
redis://host1:6379,host2:6379,host3:6379?mode=sentinel&sentinelServiceName=mymaster
```

---

## Minimal Production Setup
If you only want the app running with basic features:

```bash
flyctl secrets set \
  DATABASE_URL="postgresql://user:password@localhost:5432/vireon" \
  ENV="production" \
  REQUIRE_REDIS_FOR_READINESS="false"
```

Then:
```bash
cd backend
flyctl deploy
```

---

## Health Check Endpoints
Once deployed, verify:

```bash
# Liveness (app is running)
curl https://vireon-backend.fly.dev/health/live

# Readiness (dependencies are healthy)
curl https://vireon-backend.fly.dev/health/ready
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
