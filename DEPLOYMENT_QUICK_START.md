# Quick Start: Deploy Vireon to Production

This guide provides the fastest path to deploying your Vireon app to production.

## 🚀 TL;DR - 5 Steps to Production

1. **Push code to GitHub** (ensure `render.yaml` and `vercel.json` are in root)
2. **Deploy backend on Render** using the Blueprint in `render.yaml`
3. **Deploy frontend on Vercel** by importing your GitHub repo
4. **Configure environment variables** in both platforms
5. **Update CORS** on backend to allow your frontend URL

## 📋 Files Created for Deployment

These files have been created in your repository root:

| File | Purpose |
|------|---------|
| `render.yaml` | Infrastructure as Code for Render deployment (backend + DB + Redis) |
| `vercel.json` | Build and deployment config for Vercel |
| `RENDER_DEPLOYMENT.md` | Detailed Render backend deployment guide |
| `VERCEL_DEPLOYMENT.md` | Detailed Vercel frontend deployment guide |
| `DEPLOYMENT_CHECKLIST.md` | Step-by-step checklist for complete deployment |
| `.env.production` | Template for production environment variables |

## 🎯 Quick Reference URLs

### Detailed Guides (Read These)
- Backend Deployment: See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)
- Frontend Deployment: See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)
- Complete Checklist: See [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)

### After Deployment URLs
- **Backend API**: `https://vireon-backend.onrender.com` (or your service name)
- **Backend Docs**: `https://vireon-backend.onrender.com/api/v1/docs`
- **Frontend**: `https://your-domain.vercel.app`

## 🔧 Current Project Setup

✅ **Backend**: FastAPI + PostgreSQL + Redis
- Port: 8000
- Framework: FastAPI with Uvicorn
- Database: PostgreSQL (provisioned by Render)
- Cache: Redis (provisioned by Render)
- Health checks: `/health/live` and `/health/ready`

✅ **Frontend**: Next.js + React
- Port: 3000
- Framework: Next.js 14 with TypeScript
- Build: Static optimization
- Environment variable: `NEXT_PUBLIC_API_URL`

## 🏗️ Architecture After Deployment

```
┌─────────────────────────────────────────┐
│         Vercel (Frontend)               │
│    https://your-domain.vercel.app       │
└─────────────┬───────────────────────────┘
              │
              │ API Calls
              │
┌─────────────▼───────────────────────────┐
│         Render (Backend)                │
│    https://vireon-backend.onrender.com  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  FastAPI Web Service (Port 8000) │  │
│  └───────────────┬──────────────────┘  │
│                  │                     │
│  ┌──────────────┴──────────────────┐  │
│  │   PostgreSQL Database Service   │  │
│  │       (vireon_db)               │  │
│  └─────────────────────────────────┘  │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │    Redis Cache Service          │  │
│  │       (vireon-redis)            │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 📊 Deployment Timeline

**Expected deployment time**: 10-15 minutes total

1. **Render setup** (3-5 min): Services provision and database initializes
2. **Backend migrations** (1-2 min): Run `alembic upgrade head` in Shell
3. **Vercel deployment** (2-3 min): Frontend builds and deploys
4. **Environment config** (2-3 min): Set env vars in both platforms
5. **Testing & verification** (2-3 min): Test API and frontend

## 🔑 Required API Keys

Before deploying, gather these:

1. **Groq API Key** (Free - https://console.groq.com)
   - Required for LLM functionality
   - Free tier includes generous usage limits

2. **OpenAI API Key** (Optional)
   - Only if you want OpenAI models
   - Requires paid account

3. **Merge.dev Credentials** (Optional)
   - Only if integrating with accounting software
   - Requires Merge.dev account setup

4. **ERPNext Credentials** (Optional)
   - Only if integrating with ERPNext instance

## ⚙️ Environment Variables Summary

### Backend (Set in Render)
```
ENV=production
ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
GROQ_API_KEY=gsk_xxxxx
SECRET_KEY=<random-secure-string>
DATABASE_URL=<auto-set>
REDIS_URL=<auto-set>
```

### Frontend (Set in Vercel)
```
NEXT_PUBLIC_API_URL=https://vireon-backend.onrender.com
```

## 🚨 Common Issues & Fixes

### ❌ Frontend shows blank page
- [ ] Check `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- [ ] Verify backend `ALLOWED_ORIGINS` includes your Vercel domain
- [ ] Check browser console for CORS errors

### ❌ Backend won't start
- [ ] Check DATABASE_URL is set in Render
- [ ] Run migrations: `alembic upgrade head`
- [ ] Check logs for specific errors

### ❌ API calls fail with CORS error
- [ ] Update backend `ALLOWED_ORIGINS` to include frontend URL
- [ ] Redeploy backend after updating env vars
- [ ] Wait 2-3 minutes for redeploy to complete

### ❌ Database connection refused
- [ ] Verify PostgreSQL service is running in Render
- [ ] Check DATABASE_URL format
- [ ] Try running migrations again

## 📚 Documentation References

- **Render Documentation**: https://docs.render.com
  - Deployment: https://docs.render.com/deploy-from-git
  - Blueprints: https://docs.render.com/infrastructure-as-code

- **Vercel Documentation**: https://vercel.com/docs
  - Next.js: https://vercel.com/docs/frameworks/nextjs
  - Environment Variables: https://vercel.com/docs/environment-variables

- **Framework Docs**:
  - FastAPI: https://fastapi.tiangolo.com
  - Next.js: https://nextjs.org/docs

## 🔐 Security Checklist

After deployment, ensure:
- [ ] No secrets are committed to git
- [ ] Environment variables use strong random values (SECRET_KEY)
- [ ] API keys are never exposed in client-side code
- [ ] CORS is restricted to your domain (not `*`)
- [ ] HTTPS is enabled (automatic on both platforms)
- [ ] Database backups are configured
- [ ] Rate limiting is enabled

## 📊 Monitoring & Maintenance

After deployment, set up:
1. **Error tracking** (Sentry, DataDog)
2. **Performance monitoring** (Render/Vercel dashboards)
3. **Log aggregation** (check Render/Vercel logs)
4. **Automated backups** (Render PostgreSQL)
5. **Uptime monitoring** (Pingdom, UptimeRobot)

## 🎓 Next Steps

1. Read the detailed guides:
   - [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for backend
   - [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) for frontend

2. Follow the checklist: [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)

3. After deployment:
   - Test API endpoints
   - Verify frontend connects to backend
   - Monitor logs for errors
   - Set up custom domain (optional)
   - Configure monitoring/alerts

## 💬 Support

If you encounter issues:
1. Check the Troubleshooting section of relevant deployment guide
2. Review the logs in Render/Vercel dashboards
3. Verify all environment variables are set correctly
4. Ensure GitHub repository is up to date

## 📞 Contact & Links

- **Repository**: [Your GitHub Repo]
- **Render Dashboard**: https://dashboard.render.com
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Original Project Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
