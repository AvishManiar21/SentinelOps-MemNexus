# 🚀 Deployment Testing & Verification Guide

## Step 1: Get Your Cloud Run URL

Run this command to get your service URL:

```powershell
gcloud run services describe sentinelops-api --region us-central1 --format="value(status.url)"
```

**Expected output:**
```
https://sentinelops-api-XXXXXXXXXX-uc.a.run.app
```

Copy this URL - you'll need it!

---

## Step 2: Test Your Backend API

### Test 1: Health Check

```powershell
curl https://sentinelops-api-XXXXXXXXXX-uc.a.run.app/
```

**Expected response:**
```json
{
  "status": "online",
  "service": "SentinelOps Agent Backend API",
  "vertex_ai": "connected",
  "mongodb": "connected"
}
```

✅ If you see this, your backend is working!

### Test 2: Database Collections

```powershell
curl https://sentinelops-api-XXXXXXXXXX-uc.a.run.app/api/db/collections
```

**Expected response:**
```json
{
  "users": [...],
  "sessions": [...],
  "knowledge_vectors": [...]
}
```

✅ If you see data, MongoDB is connected!

---

## Step 3: Test Your Frontend on GitHub Pages

### Open Your Live Dashboard

🌐 **Visit:** https://avishmaniar21.github.io/SentinelOps-MemNexus/

### Check Browser Console

1. Press **F12** to open Developer Tools
2. Click **Console** tab
3. Look for:
   ```
   🚨 SentinelOps Configuration Loaded
   Environment: GitHub Pages
   API Endpoint: https://sentinelops-api-XXXXXXXXXX-uc.a.run.app
   ```

✅ If you see your Cloud Run URL, frontend is configured correctly!

---

## Step 4: Test End-to-End Functionality

### Test 1: Incident Command Tab

1. Click **Incident Command** in sidebar
2. See active incidents displayed
3. Click **"Diagnose with Gemini ➔"** button
4. Should switch to chat and start diagnosis

### Test 2: SRE Diagnostic Chat

1. Click **SRE Diagnostic Chat** tab
2. Type a message: `"Tell me about SRE incident response"`
3. Click **Send ➔**
4. Watch for:
   - Message appears in chat
   - Terminal logs show agent processing
   - Gemini responds with answer
   - MongoDB saves conversation

**Expected terminal logs:**
```
[HH:MM:SS] [SYS] Received SRE request: "Tell me about SRE incident response"
[HH:MM:SS] [TOOL] Tool Triggered: search_knowledge_base
[HH:MM:SS] [INFO] RAG search returning 3 matching manuals
[HH:MM:SS] [SUCCESS] Conversation exchange saved
```

### Test 3: MongoDB Memory Core

1. Click **MongoDB Memory Core** tab
2. Should see 3 sub-tabs:
   - 🍃 SRE Profiles (user data)
   - 🕒 Incident Sessions (chat history)
   - 🔗 Vector Runbooks (embeddings)
3. Click through each tab
4. Verify data is loading

**Expected:**
- User profile for AvishManiar21
- Recent chat sessions
- Indexed runbooks with embeddings

### Test 4: Runbook Ingester

1. Click **Runbook Ingester** tab
2. Fill in the form:
   - **Title:** "Test Runbook"
   - **Content:** "This is a test document for vector search."
3. Click **"Embed & Upload to MongoDB Atlas"**
4. Watch terminal for:
   ```
   [HH:MM:SS] Generating 768-dimension semantic vector
   [HH:MM:SS] Document indexed successfully
   ```
5. Go back to **MongoDB Memory Core** → **Vector Runbooks**
6. Your new document should appear!

---

## Step 5: Performance Check

### Backend Response Times

Test with multiple requests:

```powershell
# Run this 3 times
Measure-Command { curl https://sentinelops-api-XXXXXXXXXX-uc.a.run.app/ }
```

**Expected:**
- First request: 1-3 seconds (cold start)
- Subsequent requests: 0.5-1.5 seconds (warm)

### Frontend Load Time

1. Open https://avishmaniar21.github.io/SentinelOps-MemNexus/
2. Press F12 → Network tab
3. Reload page
4. Check load times

**Expected:**
- HTML: < 200ms
- CSS: < 300ms
- JS: < 400ms
- Total: < 1 second

---

## ✅ Success Checklist

- [ ] Cloud Run URL obtained
- [ ] Backend health check passes
- [ ] MongoDB connection verified
- [ ] Frontend loads on GitHub Pages
- [ ] Browser console shows correct API endpoint
- [ ] Chat sends messages successfully
- [ ] Gemini responds to queries
- [ ] Terminal logs show agent activity
- [ ] Database collections load
- [ ] Can add new runbooks
- [ ] New documents appear in MongoDB tab

---

## 🐛 Troubleshooting

### Frontend Can't Connect to Backend

**Issue:** CORS errors in browser console

**Fix:**
```powershell
# Verify CORS is enabled in agent.py
# Should see: CORS(app)
```

### Backend Returns 500 Error

**Issue:** MongoDB connection failed

**Fix:**
1. Check password is correct
2. Verify MongoDB Atlas allows Cloud Run IPs
3. Check logs:
   ```powershell
   gcloud run services logs read sentinelops-api --region us-central1 --limit 50
   ```

### Chat Not Working

**Issue:** No response from Gemini

**Check:**
1. Vertex AI API enabled?
2. GCP_PROJECT_ID correct?
3. Check Cloud Run logs for errors

### Database Shows Empty

**Issue:** Collections are empty

**Fix:**
1. Run `python index_docs.py` locally first
2. Or use Runbook Ingester to add documents

---

## 📊 View Logs

### Cloud Run Logs

```powershell
# Real-time logs
gcloud run services logs tail sentinelops-api --region us-central1

# Last 50 lines
gcloud run services logs read sentinelops-api --region us-central1 --limit 50
```

### Filter for Errors

```powershell
gcloud run services logs read sentinelops-api --region us-central1 --limit 100 | Select-String "ERROR"
```

---

## 🎉 Demo Ready!

Once all checks pass, your hackathon project is fully deployed and ready to demo:

**Live URLs:**
- 🌐 **Frontend:** https://avishmaniar21.github.io/SentinelOps-MemNexus/
- ☁️ **Backend:** https://sentinelops-api-XXXXXXXXXX-uc.a.run.app
- 📦 **GitHub:** https://github.com/AvishManiar21/SentinelOps-MemNexus

**What You Can Demo:**
1. ✅ Live chat with Gemini AI agent
2. ✅ MongoDB Atlas vector search
3. ✅ Real-time database updates
4. ✅ SRE incident response simulation
5. ✅ Document ingestion and retrieval
6. ✅ Persistent user memory
7. ✅ Full-stack Google Cloud deployment

---

## 📸 Screenshots for Submission

Take these screenshots:
1. **Dashboard** - Incident Command view
2. **Chat** - Conversation with agent + terminal logs
3. **MongoDB** - Database collections with data
4. **Ingester** - Successfully added document
5. **Browser Console** - Showing API connection
6. **Cloud Run** - Deployment status

---

## 🏆 Submission Checklist

- [ ] GitHub repo is public
- [ ] README.md is comprehensive
- [ ] Live demo URL works
- [ ] All features functional
- [ ] Screenshots captured
- [ ] Video demo recorded (optional)
- [ ] Submitted to Devpost

**Your project is production-ready!** 🚀
