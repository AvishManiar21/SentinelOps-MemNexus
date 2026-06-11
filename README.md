# 🚨 SentinelOps: Autonomous SRE Memory Agent & Portal
### Google Cloud Rapid Agent Hackathon Submission (MongoDB Atlas Track)

[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Deployed-blue?logo=google-cloud)](https://sentinelops-api-782741881130.us-central1.run.app)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb)](https://www.mongodb.com/cloud/atlas)
[![Gemini 2.5](https://img.shields.io/badge/Gemini-2.5%20Flash%20%7C%20Pro-orange?logo=google)](https://ai.google.dev/)

**SentinelOps** is an autonomous SRE (Site Reliability Engineering) agent built for the **MongoDB Atlas Track**. It combines **Google Cloud's Gemini 2.5 Enterprise Agent Platform** with **MongoDB Atlas Vector Search** to deliver intelligent incident response, semantic document grounding, and persistent memory.

This hackathon submission showcases MongoDB Atlas integration with vector search, real-time data visualization, AI-synthesized agent memory, and semantic grounding across 10+ SRE runbooks — with matched runbooks and cosine-similarity scores surfaced live in the chat UI.

**🎯 MongoDB Atlas Track Submission** - All core features utilize MongoDB Atlas M0 free tier for vector embeddings, persistent state, and agent memory.

---

## 🎥 Demo Video

**Watch the full demo**: [https://youtu.be/QrElopiAmoU](https://youtu.be/QrElopiAmoU)

[![SentinelOps Demo](https://img.youtube.com/vi/QrElopiAmoU/maxresdefault.jpg)](https://youtu.be/QrElopiAmoU)

---

## ⚡ Try It in 60 Seconds

**Live App (frontend)**: [https://avishmaniar21.github.io/SentinelOps-MemNexus/](https://avishmaniar21.github.io/SentinelOps-MemNexus/)
**Live API (backend)**: [https://sentinelops-api-782741881130.us-central1.run.app](https://sentinelops-api-782741881130.us-central1.run.app)

```bash
# 1. Confirm everything is online (backend, Vertex AI, MongoDB, MCP)
curl https://sentinelops-api-782741881130.us-central1.run.app/api/health

# 2. Ask the agent a real SRE question — watch it ground on a runbook via Atlas Vector Search
curl -X POST https://sentinelops-api-782741881130.us-central1.run.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I fix Nginx rate limiting during a DDoS?","user_id":"demo"}'
```

The chat response includes a `grounding_sources` array showing exactly which runbooks MongoDB Atlas Vector Search matched, and how strongly.

---

## 🎬 Live Demo Walkthrough

A 4-minute guided tour of the dashboard:

1. **System Status (top-right badge)** — Click it. All four services report live health: Backend, Vertex AI, MongoDB Atlas, and the MongoDB MCP Server. Auto-refreshes every 30s.
2. **SRE Diagnostic Chat** — Ask *"How do I fix Redis cache key eviction?"* The agent runs MongoDB Atlas Vector Search, then answers grounded on the matched runbook. Below the answer, the **📚 MongoDB Atlas Vector Search Results** panel shows the top 3 matched runbooks with **% match** scores.
3. **Switch the model** — Toggle **⚡ Flash → 🧠 Pro** and re-ask. Flash answers in ~7s; Pro takes longer (~20s) but returns more structured, deeply-reasoned output. Same vector grounding on both.
4. **MongoDB Memory Core** — Open this tab to browse the three live Atlas collections: `users` (with **Gemini-synthesized** memory summaries), `sessions` (chat history), and `knowledge_vectors` (runbooks with truncated 768-dim embeddings shown).
5. **Webhook (optional)** — Fire an authenticated alert at `/api/webhook/alert` (see below) to trigger autonomous diagnosis from an external observability tool.

> **Note**: Dynatrace and GitLab panels in the UI are clearly badged **SIMULATION / DEMO DATA**. The core graded integration is **MongoDB Atlas**.

---

## 🔍 How Vector Search Grounding Works

Every chat query flows through MongoDB Atlas Vector Search before the model answers:

1. The user's message is embedded with Google `text-embedding-004` (768 dimensions).
2. An Atlas `$vectorSearch` aggregation finds the closest runbooks by **cosine similarity**.
3. The top matches are injected into Gemini's context, so answers are grounded in real SRE runbooks — not hallucinated.
4. The matched titles + scores are returned in `grounding_sources` and rendered in the chat UI.

**Real example** — query: *"How do I fix Nginx rate limiting during a DDoS?"*

```
📚 MongoDB Atlas Vector Search Results
  #1  Nginx Reverse Proxy Rate Limiting & DDoS Prevention   86% match
  #2  Dynatrace Server Latency Spike — CPU 98.4% Recovery   78% match
  #3  MongoDB Connection Fault & Pooling Guide              74% match
```

---

## ✨ Key Features

**🤖 AI-Powered**: Dual Gemini models (Flash/Pro) • Vector search across 10+ SRE runbooks (768-dim embeddings) • Persistent chat history • Autonomous diagnostics

**📚 Visible Grounding**: Matched runbooks and cosine-similarity scores shown live in the chat UI, so you can see *why* the agent answered the way it did

**🔍 Search System**: Content search • Command palette • Smart suggestions • Live results with 300ms debounce

**🔔 Notifications**: Real-time alerts (critical/warning/info) • Dropdown panel with badge counter • Dismissible notifications

**🔗 Webhook Integration**: `/api/webhook/alert` endpoint • Built-in tester • Cloud Logging • Optional X-Webhook-Secret authentication

> **Note**: Dynatrace and GitLab features in UI are demonstration simulations (clearly badged). Core integration is **MongoDB Atlas** (hackathon track).

**🧠 MongoDB Atlas Integration** (Primary Track Feature)
- Vector Search with 768-dim embeddings (cosine similarity)
- 3 Collections: `users`, `sessions`, `knowledge_vectors`
- **AI Memory Synthesis**: Gemini automatically generates user summaries from conversation history
- **Grounding sources**: matched runbooks + relevance scores surfaced in the UI
- Live database explorer in UI
- Batch ingestion API for 10 runbooks
- Atlas M0 free tier with connection pooling

**🎨 Modern UI/UX**: Glassmorphic dark theme • Fixed sidebar • Responsive layout • Smooth animations • System status monitor with auto-refresh

**📊 System Status**: Real-time health checks (Backend, Vertex AI, MongoDB, MCP) • 3 states: Online 🟢 / Degraded 🟡 / Offline 🔴 • Interactive badge • 30s auto-refresh

---

## 📁 Project Structure

```
SentinelOps-MemNexus/
├── src/                           # Backend Python code
│   ├── agent.py                  # Flask API with Gemini, MongoDB MCP client
│   └── index_docs.py             # MongoDB document ingestion script
├── scripts/                       # Utility scripts
│   ├── batch_ingest_via_api.py   # Batch SRE runbooks ingestion via API
│   └── ingest_sre_library.py     # Local runbook ingestion script
├── docs/                          # Documentation
│   ├── DEPLOYMENT.md             # Cloud Run deployment guide
│   ├── SECURITY.md               # Security & credential management
│   └── TEST-DEPLOYMENT.md        # Post-deployment testing guide
├── index.html                     # Main dashboard UI (GitHub Pages)
├── app.js                         # Frontend controller with status monitoring
├── styles.css                     # Modern glassmorphic styles
├── config.js                      # Environment detection & API config
├── LICENSE                        # MIT License (hackathon requirement)
├── deploy.ps1                     # Secure Cloud Run deployment script
├── Dockerfile                     # Multi-runtime container (Python + Node.js)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── .gitignore                     # Git ignore patterns
├── .gcloudignore                  # Cloud Run deployment exclusions
└── README.md                      # This file
```

### 📦 Key Components

**Backend (`src/agent.py`)**:
- Flask REST API with CORS enabled
- Gemini 2.5 Flash & Pro model integration
- MongoDB Atlas client with connection pooling
- MongoDB MCP Server client (JSON-RPC 2.0)
- Google Cloud Storage for runbook backups
- Google Cloud Logging for audit trails
- 4 Vertex AI tools: search_knowledge_base, load_user_memory, save_chat_history, execute_mongodb_mcp_tool

**Frontend (GitHub Pages)**:
- Vanilla JavaScript (no frameworks)
- Real-time system status monitoring
- Vector-search grounding display in chat
- Advanced search with autocomplete
- Interactive notification system
- Responsive glassmorphic design

**Container (`Dockerfile`)**:
- Python 3.11 slim base image
- Node.js 20+ for MongoDB MCP server
- Multi-runtime support (Python + Node.js)
- Optimized for Cloud Run deployment

---

## 🎯 Live Demo

**Production Deployment**: [https://sentinelops-api-782741881130.us-central1.run.app](https://sentinelops-api-782741881130.us-central1.run.app)

**API Endpoints**:
- `GET /` - Basic API status check
- `GET /api/health` - Comprehensive system health monitoring
- `GET /api/db/collections` - View all MongoDB collections
- `POST /api/chat` - Chat with Gemini agent (model selection + grounding sources)
- `POST /api/diagnose` - Autonomous incident diagnosis
- `POST /api/runbook/ingest` - Upload single runbook
- `POST /api/runbook/ingest-library` - Batch upload 10 runbooks
- `POST /api/webhook/alert` - Receive observability alerts

---

## 🛠️ Technology Stack

**Backend**: Python 3.9+ (Flask) • Gemini 2.5 (Flash/Pro) • MongoDB Atlas Vector Search • GCS Backup • Cloud Logging • Docker

**Frontend**: Vanilla JS • HTML5 & CSS3 (glassmorphic) • Flexbox/Grid • Custom animations

**Cloud**: Google Cloud Run • Vertex AI • MongoDB Atlas M0 • GitHub Pages

---

## 🚀 Quick Start

### Prerequisites
- Google Cloud Account with $100 credits or free trial
- MongoDB Atlas account (free M0 cluster)
- Python 3.9 or higher
- Google Cloud SDK CLI installed

### 1. Clone the Repository
```bash
git clone https://github.com/AvishManiar21/SentinelOps-MemNexus.git
cd SentinelOps-MemNexus
```

### 2. Google Cloud Setup
```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable logging.googleapis.com
```

### 3. MongoDB Atlas Setup
1. Create a free M0 cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create database: `memnexus_db`
3. Create a Vector Search Index named `vector_index` on the `knowledge_vectors` collection:
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
4. **Important**: Add `0.0.0.0/0` to Network Access (IP Whitelist) to allow Cloud Run connections

### 4. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
# GCP_PROJECT_ID=your-project-id
# MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net
# WEBHOOK_SECRET=your-secure-random-secret   # protects /api/webhook/alert
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Run Locally
```bash
# Start Flask API
python src/agent.py

# In another terminal, serve the frontend
python -m http.server 8000

# Open http://localhost:8000 in your browser
```

### 7. Deploy to Cloud Run
```bash
# Deploy using the deployment script
.\deploy.ps1 YOUR_MONGODB_PASSWORD

# Or manually:
gcloud run deploy sentinelops-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=your-project,MONGODB_URI=your-connection-string,WEBHOOK_SECRET=your-secret"
```

### 8. Populate Sample Data
```bash
# After deployment, populate 10 SRE runbooks
python scripts/batch_ingest_via_api.py
```

---

## 🎖️ MongoDB Atlas Track - Core Integration

### Why MongoDB Atlas?

SentinelOps uses **MongoDB Atlas as the foundational data layer** for all agent memory, state, and semantic search capabilities. Here's the complete integration:

### 1. **Vector Search Implementation**
```python
# Atlas Vector Search Index Configuration (index name: "vector_index")
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

### 2. **Collections Architecture**
- **`knowledge_vectors`** - 10 SRE runbooks with 768-dim embeddings from `text-embedding-004`
- **`sessions`** - All chat conversations with timestamps and user context
- **`users`** - User profiles with AI-synthesized memory summaries (Gemini-powered)

### 3. **Agent Tools Using MongoDB**
```python
# Four production tools integrated with Gemini
1. search_knowledge_base(query: str) → Vector search across runbooks
2. load_user_memory(user_id: str) → Retrieve user context
3. save_chat_history(user_id, message, response) → Persist conversations + AI memory synthesis
4. execute_mongodb_mcp_tool(tool_name, arguments) → Execute MCP server tools
```

### 4. **MongoDB MCP Server Integration** (Hackathon Compliance)
- **Official MCP Server**: Uses `mongodb-mcp-server` (pre-installed in the container)
- **JSON-RPC 2.0 Protocol**: Custom Python client for subprocess communication
- **Cross-Platform Support**: Works on Windows (local dev) and Linux (Cloud Run)
- **25 MCP Tools Available**: Database queries, aggregations, schema inspection, index operations
- **Gemini Integration**: MCP tools accessible to the AI agent as Vertex AI functions
- **Health Monitoring**: MCP server status tracked in real-time via `/api/health`

### 5. **Real-time Data Visualization**
The dashboard includes a live **MongoDB Memory Core** tab with:
- User profiles viewer (with Gemini-synthesized summaries)
- Chat history explorer
- Vector runbooks browser
- Real-time collection updates

### 6. **Production Deployment**
- **Atlas M0 Free Tier** - Fully operational
- **Network Access** - Configured for Cloud Run connectivity
- **Connection String** - Securely managed via environment variables

---

## 📋 Hackathon Compliance

### ✅ Phase 1: Core Frameworks & Environment
- Google Cloud Vertex AI SDK integration
- Gemini 2.5 Flash and Pro model support
- Application Default Credentials authentication
- $100 GCP credits utilized for premium features

### ✅ Phase 2: Action Mechanisms (Tool Use)
- Four production tools integrated with Gemini:
  - `search_knowledge_base()` - Vector search function
  - `load_user_memory()` - User context retrieval
  - `save_chat_history()` - Conversation persistence + AI memory synthesis
  - `execute_mongodb_mcp_tool()` - MongoDB MCP server integration
- Function calling with structured outputs
- Dynamic tool registration based on MCP availability

### ✅ Phase 3: Partner Integration - **MongoDB Atlas Track**
- **MongoDB Atlas M0** cluster with Vector Search
- **768-dimension embeddings** using text-embedding-004
- **Three production collections**: users, sessions, knowledge_vectors
- **Cosine similarity** semantic search with grounding scores in UI
- **10 pre-loaded SRE runbooks** with full vectorization
- **Real-time synchronization** between agent and database
- **Connection pooling** for production performance
- **Official MongoDB MCP Server** (`mongodb-mcp-server`)
- **JSON-RPC 2.0 client** for MCP communication
- **25 MCP tools** for database operations

### ✅ Phase 4: State, Secrets, & Logic Hosting
- Google Cloud Secret Manager integration (optional)
- Secure credential management via environment variables
- MongoDB connection string securely configured
- Cloud Run deployment with managed secrets support

### ✅ Phase 5: Deployment & Safety Guardrails
- Multi-runtime Docker container (Python 3.11 + Node.js 20+)
- Deployed to Cloud Run (serverless)
- Gemini safety filters configured
- Webhook authentication (X-Webhook-Secret) to prevent quota abuse
- CORS enabled for cross-origin requests
- Graceful subprocess management with cleanup

### ✅ Open Source Compliance
- **MIT License** included in repository root
- Public repository with visible license badge
- Open-source contributions enabled

---

## 🎨 UI Features

**Dashboard Tabs**: Incident Command | SRE Diagnostic Chat | MongoDB Memory Core | Runbook Ingester

**Interactive Components**: System Status Monitor • Global Search • Notification Bell • Model Selector • Vector-Search Grounding Display • Webhook Tester • Terminal Logs

---

## 📊 Pre-Loaded SRE Runbooks

**10 pre-configured incident response guides** (vectorized with text-embedding-004):
MongoDB Connection Fault • Node.js OOM Heap Leak • Nginx Rate Limiting & DDoS • Kubernetes Disk Exhaustion • Redis Cache Eviction • DNS Resolution Failure • SSL/TLS Certificate Expiry • Database Replication Lag • Dynatrace CPU Recovery • GCP IAM Access Denied

---

## 🎮 Usage Examples

**Chat**: Ask "How do I fix MongoDB connection timeouts?" → Agent searches runbooks using vector similarity and shows the matched sources + scores

**Search**: Type "redis cache" → Finds Redis runbook instantly

**Webhook**: Send observability alerts via `/api/webhook/alert` (requires `X-Webhook-Secret` header if `WEBHOOK_SECRET` env var is set)

```bash
curl -X POST https://sentinelops-api-782741881130.us-central1.run.app/api/webhook/alert \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-webhook-secret" \
  -d '{"alert_name": "CPU Critical", "severity": "CRITICAL", "source": "Dynatrace"}'
```

---

## 🔧 API Reference

**Key Endpoints:**
- `GET /api/health` - System health monitoring (4 services: backend, vertex_ai, mongodb, mcp_server)
- `POST /api/chat` - Chat with Gemini agent (params: message, user_id, model; returns response, model_used, grounding_sources, traces)
- `GET /api/db/collections` - View all MongoDB collections (users, sessions, knowledge_vectors)
- `POST /api/runbook/ingest-library` - Batch upload 10 SRE runbooks
- `POST /api/webhook/alert` - Receive observability alerts (requires X-Webhook-Secret)

**Status Values**: `online` | `degraded` | `offline` | `unknown`

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| MongoDB connection offline | Add `0.0.0.0/0` to MongoDB Atlas Network Access |
| Vector search returns nothing | Ensure the index is named `vector_index` on `knowledge_vectors` |
| Cloud Run deployment fails | Ensure `.gcloudignore` excludes temp directories |
| Runbooks not appearing | Run `python scripts/batch_ingest_via_api.py` |
| Search not working | Hard refresh browser cache (Ctrl+Shift+R) |

---

## 🌟 Additional Features

- **Cloud Storage**: Automatic backup of ingested runbooks to GCS
- **Cloud Logging**: All API requests and webhook alerts logged with severity tracking
- **Model Selection**: Switch between Gemini 2.5 Flash (fast) and Pro (deep reasoning) mid-conversation
- **AI Memory Synthesis**: Gemini generates concise per-user memory summaries from chat history
- **Notification System**: Real-time alerts for critical events, CPU/memory warnings, and backup status

---

## 🤝 Contributing

This project was built for the Google Cloud Rapid Agent Hackathon. Contributions welcome! Fork → Feature branch → Pull Request.

---

## 📄 License & Author

**MIT License** | **Avish Maniar** ([@AvishManiar21](https://github.com/AvishManiar21))

**Built for the Google Cloud Rapid Agent Hackathon** - Powered by Gemini 2.5 & MongoDB Atlas
