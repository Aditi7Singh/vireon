# Vercel Frontend Deployment Guide

## Prerequisites

1. A [Vercel](https://vercel.com) account
2. The frontend code pushed to a GitHub repository
3. Your Render backend URL (from backend deployment)

## Deployment Steps

### 1. Connect GitHub Repository to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Select **"Import Git Repository"**
4. Search for your repository and click **"Import"**

### 2. Configure Build Settings

Vercel will auto-detect Next.js configuration from `next.config.mjs`. Accept the defaults:
- **Framework Preset**: Next.js
- **Root Directory**: `frontend` (if monorepo) or leave blank
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`

### 3. Set Environment Variables

Before deploying, set the environment variables:

1. Go to **Project Settings** → **Environment Variables**
2. Add the following variables:
   ```
   NEXT_PUBLIC_API_URL = https://vireon-backend.onrender.com
   ```
   (Replace with your actual Render backend URL)

3. Click **"Save"**

### 4. Deploy

1. Click **"Deploy"**
2. Vercel will build and deploy your frontend
3. Once complete, you'll get a deployment URL like: `https://vireon.vercel.app`

### 5. Update Backend CORS

After getting your Vercel URL, update the backend's ALLOWED_ORIGINS:

1. Go to Render Dashboard → **vireon-backend** → **Environment**
2. Update `ALLOWED_ORIGINS` to include your Vercel URL:
   ```
   https://your-vercel-domain.vercel.app
   ```
3. This allows your frontend to make requests to the backend

## Custom Domain (Optional)

1. Go to **Project Settings** → **Domains**
2. Click **"Add"**
3. Enter your domain name
4. Follow DNS instructions to point your domain to Vercel

## Environment Variables Reference

The frontend uses these environment variables:

- `NEXT_PUBLIC_API_URL`: Backend API base URL
  - Example: `https://vireon-backend.onrender.com`
  - Used for all API requests from frontend
  - Must be accessible from the browser

## Build & Deployment Options

### Git Push Auto-Deploy
- Default: Automatically deploys on push to main branch
- Configure: **Project Settings** → **Git** to change trigger branch

### Manual Deploy
```bash
vercel deploy --prod
```

### Preview Deployments
- Every PR to main automatically gets a preview deployment
- Useful for testing before merging

## Logs & Monitoring

### View Build Logs
1. Go to **Deployments** tab
2. Click on a deployment to view logs

### Runtime Logs
1. Go to **Logs** section
2. Select **Functions** or **Static**

## Performance Optimization

Vercel provides built-in optimization:
- **Image Optimization**: Automatic via `next/image`
- **Code Splitting**: Automatic per-route
- **Edge Functions**: Deploy at edge locations
- **Caching**: Smart caching for static assets

### Enable ISR (Incremental Static Regeneration)
Update `next.config.mjs` to enable caching:
```javascript
export default {
  headers: async () => [
    {
      source: '/api/:path*',
      headers: [
        {
          key: 'Cache-Control',
          value: 'no-store',
        },
      ],
    },
  ],
};
```

## Analytics

View real-time analytics:
1. Go to **Analytics** tab
2. Monitor:
   - Requests per second
   - Error rate
   - Response time
   - Edge bandwidth

## Troubleshooting

### Build Fails
1. Check **Build Logs** for errors
2. Ensure all dependencies are in `package.json`
3. Verify Node.js version compatibility (should be 20.x)

### Blank Page or 404 Errors
1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check if backend is accessible from Vercel
3. Clear browser cache
4. Check browser console for CORS errors

### API Calls Fail with CORS Error
1. Backend's `ALLOWED_ORIGINS` must include your Vercel URL
2. Update it in Render Dashboard and redeploy
3. Wait a few minutes for redeploy to complete

### Environment Variables Not Loading
1. Verify variables are prefixed with `NEXT_PUBLIC_` if used in browser
2. Redeploy after adding/changing environment variables
3. Check **Settings** → **Environment Variables** for correct values

## Rollback

If something goes wrong:
1. Go to **Deployments**
2. Find the previous working deployment
3. Click the three dots → **Promote to Production**

## Costs

- **Free tier**: Suitable for development/testing
- **Pro tier**: $20/month for production-grade performance
- **Enterprise**: Custom pricing

## Next Steps

1. Update your domain DNS if using a custom domain
2. Set up monitoring and error tracking (e.g., Sentry)
3. Configure git branch protection rules
4. Set up team access in Vercel
