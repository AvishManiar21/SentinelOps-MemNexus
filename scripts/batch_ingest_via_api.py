"""
Batch ingest SRE runbooks via the existing /api/runbook/ingest endpoint.
This works with the CURRENT Cloud Run deployment without needing to redeploy.
"""

import requests
import time

API_URL = "https://sentinelops-api-yucauzs4lq-uc.a.run.app"

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

print("=" * 80)
print("  Batch Ingesting 10 SRE Runbooks via Cloud Run API")
print("=" * 80)
print()

success_count = 0
for i, doc in enumerate(sre_library, 1):
    print(f"[{i}/10] Ingesting: {doc['title'][:60]}...")

    try:
        response = requests.post(
            f"{API_URL}/api/runbook/ingest",
            json=doc,
            timeout=60
        )

        if response.status_code == 200:
            print(f"  [OK] Success!")
            success_count += 1
        else:
            print(f"  [FAIL] Failed: {response.status_code} - {response.text[:100]}")

    except Exception as e:
        print(f"  [ERROR] Error: {e}")

    time.sleep(2)  # Wait 2 seconds between requests

print()
print("=" * 80)
print(f"Batch Ingestion Complete: {success_count}/10 runbooks successfully ingested!")
print("=" * 80)
