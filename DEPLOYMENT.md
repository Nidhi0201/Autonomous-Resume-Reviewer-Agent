# Deployment Guide

This guide covers deploying the Resume Reviewer Agent to production.

## Architecture

- **Frontend (Next.js)**: Deploy to Netlify
- **Backend (FastAPI)**: Deploy to Netlify Functions (recommended), Railway, Render, or Fly.io

> **Note**: The easiest option is deploying both frontend and backend on Netlify using Netlify Functions. See "Option 0: Netlify Functions" below.

## Frontend Deployment (Netlify)

### Prerequisites

1. A Netlify account (sign up at https://netlify.com)
2. Git repository with your code
3. Backend deployed and accessible via URL

### Steps

1. **Prepare your repository**
   ```bash
   # Make sure you have a .gitignore
   # Commit your code
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Connect to Netlify**
   - Go to https://app.netlify.com
   - Click "Add new site" → "Import an existing project"
   - Connect to your Git provider (GitHub, GitLab, Bitbucket)
   - Select your repository

3. **Configure build settings**
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `.next` (Netlify Next.js plugin handles this automatically)

4. **Set environment variables**
   In Netlify dashboard → Site settings → Environment variables, add:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   ```
   Replace `https://your-backend-url.com` with your actual backend URL.

5. **Deploy**
   - Netlify will automatically build and deploy
   - Your site will be available at `https://your-site-name.netlify.app`

### Alternative: Deploy via Netlify CLI

```bash
cd frontend
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

---

## Backend Deployment Options

### Option 1: Railway (Recommended - Easiest)

Railway makes deploying FastAPI apps simple.

1. **Sign up**: https://railway.app

2. **Create a new project**
   - Click "New Project"
   - Select "Deploy from GitHub repo" (recommended) or "Empty Project"

3. **Configure deployment**
   - If using GitHub: Select your repository and set root directory to `backend`
   - If using Empty Project: Use Railway CLI
     ```bash
     cd backend
     railway login
     railway init
     railway up
     ```

4. **Set environment variables**
   In Railway dashboard → Variables tab:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   PORT=8080
   ```

5. **Configure build**
   Railway auto-detects Python projects, but you can set:
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Railway will run `pip install -r requirements.txt` automatically

6. **Get your backend URL**
   - Railway provides a URL like `https://your-app.railway.app`
   - Use this in your Netlify `NEXT_PUBLIC_API_URL` variable

### Option 2: Render

1. **Sign up**: https://render.com

2. **Create a new Web Service**
   - Connect your GitHub repository
   - Set root directory to `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Set environment variables**
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Get your backend URL**
   - Render provides: `https://your-app.onrender.com`
   - Use this in your Netlify `NEXT_PUBLIC_API_URL` variable

### Option 3: Fly.io

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and launch**
   ```bash
   cd backend
   fly auth login
   fly launch
   ```

3. **Set secrets**
   ```bash
   fly secrets set GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Get your backend URL**
   - Fly provides: `https://your-app.fly.dev`
   - Use this in your Netlify `NEXT_PUBLIC_API_URL` variable

### Option 4: Google Cloud Run (You already have this setup!)

If you want to use the existing Google Cloud Run deployment:

1. **Update your backend code** (if needed)
   ```bash
   cd backend
   gcloud builds submit --tag gcr.io/resume-agent-484309/resume-backend
   gcloud run deploy resume-backend \
     --image gcr.io/resume-agent-484309/resume-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory=2Gi
   ```

2. **Get your Cloud Run URL**
   - It should be: `https://resume-backend-311152392390.us-central1.run.app`
   - Use this in your Netlify `NEXT_PUBLIC_API_URL` variable

---

## Quick Deployment Checklist

### Frontend (Netlify)
- [ ] Code pushed to Git repository
- [ ] Netlify site created and connected
- [ ] Build settings configured (base directory: `frontend`)
- [ ] Environment variable `NEXT_PUBLIC_API_URL` set to backend URL
- [ ] Site deployed and accessible

### Backend (Choose one)
- [ ] **Railway/Render/Fly.io**:
  - [ ] Project created
  - [ ] Code deployed
  - [ ] Environment variables set (GROQ_API_KEY)
  - [ ] Backend URL obtained
- [ ] **OR Google Cloud Run**:
  - [ ] Docker image built and pushed
  - [ ] Cloud Run service deployed
  - [ ] Backend URL confirmed

### Testing
- [ ] Frontend loads correctly
- [ ] Backend health check works: `https://your-backend-url.com/health`
- [ ] Full workflow tested (submit resume → get results)
- [ ] CORS configured correctly (backend allows frontend origin)

---

## Environment Variables Reference

### Frontend (Netlify)
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### Backend (Railway/Render/Fly.io/Cloud Run)
```bash
GROQ_API_KEY=gsk_your_groq_api_key_here
PORT=8080  # Usually auto-set by platform
```

---

## Troubleshooting

### Frontend Issues

**Build fails on Netlify**
- Check Node.js version (should be 18+)
- Verify `package.json` scripts are correct
- Check build logs for specific errors

**API calls fail (CORS errors)**
- Ensure backend CORS middleware allows Netlify domain
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend is accessible

### Backend Issues

**Deployment fails**
- Check `requirements.txt` is up to date
- Verify all dependencies are listed
- Check Python version (3.11+)

**API calls fail (500 errors)**
- Check environment variables are set correctly
- Verify GROQ_API_KEY is valid
- Check backend logs for errors

**Connection timeout**
- Railway/Render free tiers may have cold starts
- Consider upgrading or using Google Cloud Run
- For local testing, use `http://localhost:8000`

---

## Cost Estimates

### Free Tier Options

**Frontend (Netlify)**
- ✅ Free tier: 100GB bandwidth, 300 build minutes/month
- Perfect for MVP

**Backend**
- **Railway**: $5/month after $5 free credit (easy setup)
- **Render**: Free tier available (may sleep after inactivity)
- **Fly.io**: Free tier available (limited resources)
- **Google Cloud Run**: Pay per use, $300 free credit

### Recommended for Production
- **Frontend**: Netlify (Free tier is sufficient)
- **Backend**: Railway ($5/month) or Google Cloud Run (if you have credits)

---

## Next Steps After Deployment

1. **Set up custom domain** (optional)
   - Netlify: Site settings → Domain management
   - Backend: Configure custom domain in your hosting platform

2. **Enable HTTPS** (automatic on most platforms)

3. **Set up monitoring**
   - Use Netlify Analytics (paid)
   - Add error tracking (Sentry)

4. **Optimize performance**
   - Enable Netlify caching
   - Optimize images
   - Use CDN for static assets
