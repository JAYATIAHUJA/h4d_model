# Delhi Flood Monitor - Deployment Guide

## Quick Deploy (5 minutes)

### Step 1: Deploy Backend (FastAPI) on Render

1. **Go to [render.com](https://render.com)** and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `delhi-flood-api`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
5. Click **"Create Web Service"**
6. Wait 5-10 minutes for deployment
7. **Copy your backend URL**: `https://delhi-flood-api.onrender.com`

### Step 2: Deploy Frontend (Next.js) on Vercel

1. **Go to [vercel.com](https://vercel.com)** and sign up (free)
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
5. **Add Environment Variable**:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://delhi-flood-api.onrender.com` (your Render URL)
6. Click **"Deploy"**
7. Wait 2-3 minutes
8. **Your app is live!** Share the Vercel URL with your friend

### Step 3: Update CORS in Backend

After deploying, update `backend/api/main.py` line 40 to allow your Vercel domain:

```python
allow_origins=["https://your-app.vercel.app", "http://localhost:3000"],
```

Then push to GitHub - Render will auto-redeploy.

---

## Alternative: Railway.app (Easier, Both in One Place)

1. **Go to [railway.app](https://railway.app)** and sign up
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway auto-detects both services:
   - **backend** (Python/FastAPI)
   - **frontend** (Node.js/Next.js)
5. Set environment variables:
   - Frontend: `NEXT_PUBLIC_API_URL` = (Railway backend URL)
6. Click **"Deploy"**
7. Done! Both services deployed

---

## Testing Your Deployment

### Test Backend API:
```bash
curl https://delhi-flood-api.onrender.com/api/health
curl -X POST https://delhi-flood-api.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{"rainfall": 42.5, "water_logging_reports": 12, "pothole_count": 5}'
```

### Test Frontend:
Open `https://your-app.vercel.app` in browser - map should load with live data!

---

## Free Tier Limits

**Render.com (Backend)**:
- ✅ Free forever
- ⚠️ Spins down after 15 min inactivity (first request takes 30s to wake)
- 750 hours/month free

**Vercel (Frontend)**:
- ✅ Free forever for personal projects
- 100 GB bandwidth/month
- Unlimited deployments

**Railway.app (Both)**:
- $5 free credit/month
- After credit runs out, $0.000463/GB-hour

---

## Pro Tips

1. **Keep backend alive**: Add UptimeRobot.com to ping your API every 5 min (free)
2. **Custom domain**: Add free domain from Freenom.com
3. **Analytics**: Add Vercel Analytics (built-in, free)
4. **Monitoring**: Render has built-in logs and metrics

Your friend can now access the app from anywhere! 🚀
