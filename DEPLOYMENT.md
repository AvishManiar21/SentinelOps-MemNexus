# SentinelOps Deployment Guide

## 🌐 GitHub Pages (Frontend)

### Live URL
**Your dashboard is live at:** https://avishmaniar21.github.io/SentinelOps-MemNexus/

### Setup Instructions
GitHub Pages has been automatically configured via GitHub CLI. The frontend is now live!

### How It Works
- The frontend automatically detects the environment
- **Local development**: Uses `http://localhost:5000`
- **GitHub Pages**: Uses `https://sentinelops-api-782741881130.us-central1.run.app`

### Configuration
All environment detection is handled in:
- `config.js` - Global configuration
- `app.js` - Automatic API endpoint resolution

## ☁️ Cloud Run (Backend API)

### Deployment Command (PowerShell)

```powershell
# Replace <YOUR_NEW_PASSWORD> with your actual MongoDB password
gcloud run deploy sentinelops-api --source . --region us-central1 --allow-unauthenticated --set-env-vars "GCP_PROJECT_ID=avish-memnexus-2026,GCP_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash,USE_SECRET_MANAGER=false,MONGODB_URI=mongodb+srv://dbuser:<YOUR_NEW_PASSWORD>@cluster0.qajn3ij.mongodb.net/?appName=Cluster0"
```

**⚠️ SECURITY NOTE**: Never commit your actual MongoDB password to the repository. Use Secret Manager for production (see below).

### Expected Output
```
Service URL: https://sentinelops-api-782741881130.us-central1.run.app
```

### Verify Deployment
```powershell
curl https://sentinelops-api-782741881130.us-central1.run.app/
```

Expected response:
```json
{
  "status": "online",
  "service": "SentinelOps Agent Backend API",
  "vertex_ai": "connected",
  "mongodb": "connected"
}
```

## 🧪 Local Development

### Frontend (Local)
```bash
python -m http.server 8000
# Visit: http://localhost:8000
```

### Backend (Local)
```bash
python agent.py
# API runs on: http://localhost:5000
```

The frontend will automatically use `localhost:5000` when running locally.

## 🔧 Environment Variables

### Cloud Run
- `GCP_PROJECT_ID` - Your GCP project ID
- `GCP_LOCATION` - GCP region (us-central1)
- `GEMINI_MODEL` - AI model (gemini-2.5-flash)
- `USE_SECRET_MANAGER` - Use Secret Manager (false for direct env vars)
- `MONGODB_URI` - MongoDB Atlas connection string

### Local (.env)
```env
GCP_PROJECT_ID=avish-memnexus-2026
GCP_LOCATION=us-central1
MONGODB_URI=mongodb+srv://...
GEMINI_MODEL=gemini-2.5-flash
USE_SECRET_MANAGER=false
```

## 🚀 Full Stack Testing

1. **Deploy backend to Cloud Run**
2. **Visit GitHub Pages** at https://avishmaniar21.github.io/SentinelOps-MemNexus/
3. **Test features:**
   - Navigate to "SRE Diagnostic Chat"
   - Send a message
   - Check "MongoDB Memory Core" for live data
   - Try "Runbook Ingester" to add documents

## 📊 Monitoring

### Cloud Run Logs
```powershell
gcloud run services logs read sentinelops-api --region us-central1 --limit 50
```

### Frontend Debugging
Open browser console (F12) to see:
- Environment detection
- API endpoint being used
- Request/response logs

## 🔒 Security Notes

- Frontend is **public** (GitHub Pages)
- Backend allows **unauthenticated access** (for hackathon demo)
- MongoDB credentials in environment variables (consider Secret Manager for production)

## 🎉 Success Checklist

- ✅ GitHub Pages enabled and live
- ✅ Cloud Run backend deployed
- ✅ Frontend auto-detects environment
- ✅ MongoDB Atlas connected
- ✅ Vertex AI Gemini integrated
- ✅ All features working end-to-end
