# 🚨 SentinelOps: Autonomous SRE Memory Agent & Portal
### Google Cloud Rapid Agent Hackathon Submission (MongoDB Atlas Track)

[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Deployed-blue?logo=google-cloud)](https://sentinelops-api-yucauzs4lq-uc.a.run.app)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb)](https://www.mongodb.com/cloud/atlas)
[![Gemini 2.5](https://img.shields.io/badge/Gemini-2.5%20Flash%20%7C%20Pro-orange?logo=google)](https://ai.google.dev/)

**SentinelOps** (formerly MemNexus) is a production-ready, autonomous SRE (Site Reliability Engineering) agent that combines **Google Cloud's Gemini 2.5 Enterprise Agent Platform** with **MongoDB Atlas Vector Search** to deliver intelligent incident response, semantic document grounding, and persistent memory.

This project represents a fully compliant end-to-end integration covering all 5 core phases of the hackathon requirements with premium production features.

---

## ✨ Key Features

### 🤖 AI-Powered Features
- **Dual Gemini Models**: Switch between Gemini 2.5 Flash (fast) and Pro (deep reasoning)
- **Semantic Search**: Vector search across 10+ pre-loaded SRE runbooks using 768-dimension embeddings
- **Context-Aware Chat**: Persistent conversation history with MongoDB storage
- **Autonomous Diagnostics**: Simulated incident analysis with automated hotfix generation

### 🔍 Advanced Search System
- **Content Search**: Search across chat history, runbooks, and user profiles
- **Command Palette**: Quick actions with keyword matching
- **Smart Suggestions**: Recent searches and popular queries with autocomplete
- **Live Search**: 300ms debounce with real-time results dropdown

### 🔔 Notification System
- **Real-time Alerts**: Critical, warning, and info notifications
- **Notification Panel**: Dropdown with badge counter and pulse animation
- **Mark as Read**: Click to dismiss individual notifications
- **Sample Notifications**: CPU alerts, memory warnings, backup status

### 🔗 Webhook Integration
- **Alert Endpoint**: `/api/webhook/alert` for observability tools (Dynatrace, Datadog)
- **Webhook Tester**: Built-in UI to test alert payloads
- **Cloud Logging**: All webhooks logged to Google Cloud Logging
- **Automated Response**: Trigger autonomous diagnostics from external alerts

### 🧠 MongoDB Integration
- **Vector Search**: Cosine similarity search with 768-dim embeddings
- **Three Collections**: `users`, `sessions`, `knowledge_vectors`
- **Live Database Explorer**: Real-time MongoDB data visualization
- **Batch Ingestion**: API endpoint to populate 10 SRE runbooks instantly

### 🎨 Modern UI/UX
- **Glassmorphic Design**: Dark theme with orange accent colors
- **Fixed Sidebar**: Navigation stays in place while content scrolls
- **Responsive Layout**: Single scrollbar, no layout displacement
- **Smooth Animations**: Transitions, hover effects, and scroll behaviors
- **Notification Bell**: Functional dropdown with unread count

---

## 📁 Project Structure

```
SentinelOps-MemNexus/
├── src/                    # Backend Python code
│   ├── agent.py           # Flask API server with Gemini integration
│   └── index_docs.py      # MongoDB document ingestion script
├── docs/                   # Documentation
│   ├── DEPLOYMENT.md      # Cloud Run deployment guide
│   ├── SECURITY.md        # Security & credential management
│   └── TEST-DEPLOYMENT.md # Post-deployment testing guide
├── index.html             # Main dashboard (GitHub Pages)
├── app.js                 # Frontend JavaScript controller
├── styles.css             # Modern UI styles
├── config.js              # Environment detection & API config
├── deploy.ps1             # Secure deployment script
├── Dockerfile             # Container configuration
├── requirements.txt       # Python dependencies
└── .env.example           # Environment variable template
```

---

## 🛠️ Step-by-Step Hackathon Roadmap

### 📦 Phase 1: Core Frameworks & Environment
1. **Google Cloud Account**: Ensure you have activated your account and applied the **$100 credits** (or started your no-cost trial).
2. **Enable APIs**: Navigate to Google Cloud Console and enable the **Vertex AI API** (Gemini Enterprise Agent Platform API).
3. **Install Google Cloud SDK CLI** on your system.
4. **Authenticate Local Shell**: Open a command line / PowerShell and run:
   ```powershell
   gcloud auth application-default login
   ```
   This allows the Python developer SDK to inherit your $100 GCP credentials automatically.
5. **Python Environment Setup**:
   Ensure you have Python 3.9+ installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

### 🔗 Phase 2 & 3: Action Mechanisms (Tools) & MongoDB Atlas Integration
1. **MongoDB Atlas Free Tier**: Create a free M0 Cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. **Atlas Vector Search Index**: Create a Vector Search Index on a collection named `knowledge_vectors` inside a database named `memnexus_db`. Use the default mapping:
   ```json
   {
     "fields": [
       {
         "numDimensions": 768,
         "path": "embedding",
         "similarity": "cosine",
         "type": "vector"
       }
     ]
   }
   ```
3. **Connection String**: Copy your connection string and add it to your local environment (see `.env` config below).

### 🧠 Phase 4: State, Secrets, & Logic Hosting
To abide by Phase 4 security requirements, the agent implements dynamic credential resolution using **Google Cloud Secret Manager**:
1. Store your MongoDB Connection URI securely under a secret named `mongodb-atlas-uri` in Secret Manager.
2. Grant your local user account or Cloud Run service account access to read this secret.
3. Configure `USE_SECRET_MANAGER=true` in your `.env` file to retrieve the URI dynamically at runtime instead of hardcoding it.

### 🚀 Phase 5: Deployment & Safety Guardrails
1. **Safety Filters**: The model uses strict configurations in `src/agent.py` setting high-integrity filters against hate speech, harassment, and dangerous content.
2. **Containerization**: The application is containerized using Docker (see `Dockerfile`). The deployment script handles building and deploying to Cloud Run.
3. **Deploy to Cloud Run**: Use the secure deployment script:
   ```powershell
   .\deploy.ps1 YOUR_MONGODB_PASSWORD
   ```
   For detailed deployment instructions, see `docs/DEPLOYMENT.md`.

---

## ⚙️ Configuration Setup

1. Copy `.env.example` to `.env` in this directory:
   ```bash
   copy .env.example .env
   ```
2. Open `.env` and fill in:
   - `GCP_PROJECT_ID` (your live Google Cloud Project ID).
   - `MONGODB_URI` (your MongoDB Atlas connection string).

---

## 🏃 Run the Application

### 1. Run the Python Agent Console
Run the main script to start talking to the SRE/Enterprise memory agent:
```bash
python src/agent.py
```
Type queries and inspect how your MongoDB collections update dynamically behind the scenes!

### 2. Launch the Premium Companion Hub & Dashboard
Double-click `index.html` or run a local HTTP server in this directory:
```bash
# Using Python's built-in server:
python -m http.server 8000
```
Open [http://localhost:8000](http://localhost:8000) in your web browser. You will be greeted by a gorgeous, glassmorphic obsidian dashboard tracking your hackathon metrics, featuring a live **MemNexus Chat & Brain Visualizer**!
