# 🍃 MemNexus: Context-Aware Enterprise Memory Agent & Portal
### Google Cloud Rapid Agent Hackathon Submission (MongoDB Atlas Track)
---

**MemNexus** is a production-ready, context-aware artificial intelligence agent that bridges **Google Cloud's Gemini Enterprise Agent Platform** and **MongoDB Atlas** to implement persistent user memory and semantic document grounding.

This project represents a fully compliant end-to-end integration covering all 5 core phases of the hackathon rules.

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
1. **Safety Filters**: The model uses strict configurations in `agent.py` setting high-integrity filters against hate speech, harassment, and dangerous content.
2. **Containerization**: To host your agent backend on **Cloud Run**, compile the application into a standard Docker image:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8080
   CMD ["python", "agent.py"]
   ```
3. **Deploy to Cloud Run**: Run the following command using GCP CLI:
   ```bash
   gcloud run deploy memnexus-agent --source . --region us-central1 --allow-unauthenticated
   ```

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
python agent.py
```
Type queries and inspect how your MongoDB collections update dynamically behind the scenes!

### 2. Launch the Premium Companion Hub & Dashboard
Double-click `index.html` or run a local HTTP server in this directory:
```bash
# Using Python's built-in server:
python -m http.server 8000
```
Open [http://localhost:8000](http://localhost:8000) in your web browser. You will be greeted by a gorgeous, glassmorphic obsidian dashboard tracking your hackathon metrics, featuring a live **MemNexus Chat & Brain Visualizer**!
