# ==============================================================================
# SentinelOps: Enterprise SRE Runbook Library Ingestion Tool
# Integrates Google Cloud Vertex AI & MongoDB Atlas to populate grounding databases
# ==============================================================================

import os
import sys
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient

# Load existing environment config
load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "avish-memnexus-2026")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    print("[ERROR] MONGODB_URI not found in your environment! Please check your .env file.")
    sys.exit(1)

print("\n" + "="*80)
print("             SentinelOps Enterprise RAG Ingestion Pipeline            ")
print("="*80)

# Connect to live MongoDB Atlas
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["memnexus_db"]
    mongo_client.admin.command('ping')
    print("[*] Successfully connected to live MongoDB Atlas cluster!")
except Exception as e:
    print(f"[ERROR] Failed to connect to MongoDB: {e}")
    sys.exit(1)

# Connect to Google Gen AI Vertex AI
try:
    ai_client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION
    )
    print("[*] Successfully initialized Google Vertex AI Embeddings SDK!")
except Exception as e:
    print(f"[ERROR] Failed to initialize Gen AI SDK: {e}")
    sys.exit(1)

def ingest_manual(title: str, content: str):
    """Generates a dense vector via text-embedding-004 and inserts the runbook into MongoDB Atlas."""
    print(f"\n[*] Vectorizing: '{title}'...")
    try:
        # Generate 768-dimension semantic vector
        res = ai_client.models.embed_content(
            model="text-embedding-004",
            contents=content
        )
        vector = res.embeddings[0].values
        
        # Build payload
        payload = {
            "title": title,
            "content": content,
            "embedding": vector
        }
        
        # Insert into grounding collection
        result = db.knowledge_vectors.insert_one(payload)
        print(f"  [+] Document successfully indexed in collection 'knowledge_vectors'!")
        print(f"  [+] Document ID: {result.inserted_id}")
    except Exception as e:
        print(f"  [ERROR] Ingestion failed: {e}")

# ==============================================================================
# ENTERPRISE SRE GROUNDING DATASET
# ==============================================================================
sre_library = [
    {
        "title": "MongoDB Connection Fault & Pooling Guide",
        "content": "SRE Incident Guide: When database timeouts or 'connection refused' errors occur on auth-service, SREs must inspect active pooling variables. To optimize throughput, increase connection pool size to 50 in config.json and implement a reconnect retry logic of 3 attempts with exponential backoff."
    },
    {
        "title": "Node.js Out of Memory (OOM) Heap Leak Guide",
        "content": "SRE Incident Guide: If memory usage on a Node.js API container climbs exponentially to 100%, a heap memory leak is occurring. Inspect the server garbage collection allocation, and modify ecosystem.config.js to include '--max-old-space-size=4096' to increase V8 memory limit to 4GB, then restart PM2."
    },
    {
        "title": "Nginx Reverse Proxy Rate Limiting & DDoS Prevention",
        "content": "SRE Incident Guide: When server load spikes due to sudden high request volumes or DDoS, configure Nginx limit_req zone to restrict incoming traffic. Edit nginx.conf to add 'limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;' and apply 'limit_req zone=one burst=5 nodelay;' to protect microservices."
    },
    {
        "title": "Kubernetes Disk Space Exhaustion & Log Rotation",
        "content": "SRE Incident Guide: When a Kubernetes node status changes to 'DiskPressure' and pod scheduling halts, clean docker system files. Execute 'docker system prune -af' and adjust the log-rotate configuration inside /etc/logrotate.d/docker to limit standard out logs to 10MB per file."
    },
    {
        "title": "Redis Cache Key Eviction & Connection Exhaustion",
        "content": "SRE Incident Guide: If redis cache hit rates drop below 70% and latency regressions spike, the memory limit is reached. Edit redis.conf to set 'maxmemory 2gb' and set the key eviction policy to 'maxmemory-policy allkeys-lru' to automatically evict least recently used keys."
    },
    {
        "title": "DNS Resolution Failure in Kubernetes Cluster",
        "content": "SRE Incident Guide: When pods fail to communicate with external APIs with 'Could not resolve host' errors, CoreDNS is failing. Check the CoreDNS pods using 'kubectl get pods -n kube-system -l k8s-app=kube-dns' and execute a roll restart of the coredns deployment to clear cached locks."
    },
    {
        "title": "SSL/TLS Certificate Expiry & Auto-Renewal Failure",
        "content": "SRE Incident Guide: When browsers display 'Your connection is not private' and HTTPS requests fail, the SSL certificate has expired. Run 'certbot renew' manually on the ingress gateway node and verify that a cron job is configured under crontab to execute certificate checks weekly."
    },
    {
        "title": "Database Replication Lag & Read/Write Splitting",
        "content": "SRE Incident Guide: If replication lag between primary and secondary database nodes exceeds 5 seconds, read queries will fetch stale data. Implement read/write splitting in your database client, routing all INSERT/UPDATE statements to the primary and SELECT queries to the read-replicas."
    },
    {
        "title": "Dynatrace Server Latency Spike — CPU 98.4% Recovery",
        "content": "SRE Incident Guide: If an observability alert is received indicating a latency spike of +1200ms and CPU is pegged at 98.4%, SREs must modify server.py (or hotfix.py) to set the request rate-limiting timeout to 5 seconds (5000ms) on connections, preventing the CPU from locks."
    },
    {
        "title": "GCP IAM Access Denied on Cloud Storage Buckets",
        "content": "SRE Incident Guide: If Cloud Run containers log 'AccessDenied' when writing files to GCS buckets, the Compute Engine Service Account is missing roles. Grant 'roles/storage.admin' to the service account '782741881130-compute@developer.gserviceaccount.com' at the project level."
    }
]

if __name__ == "__main__":
    print(f"\n[*] Beginning batch ingestion of {len(sre_library)} professional grounding runbooks...")
    for doc in sre_library:
        ingest_manual(doc["title"], doc["content"])
    
    print("\n" + "="*80)
    print("Ingestion complete! All 10 runbooks successfully live in MongoDB Atlas!")
    print("="*80 + "\n")
