# Sample Runbooks for Ingestion

Use these runbooks in the **Runbook Ingester** tab to add new SRE knowledge to MongoDB Atlas. Each runbook will be:
1. Embedded using Google `text-embedding-004` (768 dimensions)
2. Stored in MongoDB Atlas `knowledge_vectors` collection
3. Backed up to Google Cloud Storage
4. Searchable via vector similarity in chat

---

## 1. PostgreSQL High Connection Count

**Title**: PostgreSQL High Connection Count Troubleshooting

**Content**:
When PostgreSQL reaches max_connections limit, new connections are rejected with "FATAL: remaining connection slots reserved for non-replication superuser connections" errors.

**Diagnosis Steps**:
1. Check current connection count: SELECT count(*) FROM pg_stat_activity;
2. Identify idle connections: SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';
3. Review max_connections setting: SHOW max_connections;
4. Check for connection leaks in application logs

**Solution**:
1. Immediate: Kill idle connections older than 30 minutes
2. Short-term: Increase max_connections in postgresql.conf (requires restart)
3. Long-term: Implement connection pooling with PgBouncer or pgpool
4. Application fix: Ensure proper connection closure in application code

**Prevention**:
- Set connection pooling at application layer
- Configure statement_timeout and idle_in_transaction_session_timeout
- Monitor pg_stat_activity regularly
- Implement connection limit alerts at 80% threshold

---

## 2. Elasticsearch Cluster Yellow Status

**Title**: Elasticsearch Cluster Yellow Status Resolution

**Content**:
Yellow cluster status indicates that all primary shards are allocated but some replica shards are unassigned. While the cluster remains functional, it's at risk of data loss if nodes fail.

**Common Causes**:
1. Insufficient nodes for replica allocation
2. Shard allocation settings preventing assignment
3. Disk watermark thresholds exceeded
4. Node version mismatches preventing replica placement

**Diagnosis**:
1. Check cluster health: GET _cluster/health?pretty
2. View unassigned shards: GET _cat/shards?v&h=index,shard,prirep,state,node,unassigned.reason
3. Review allocation explain: GET _cluster/allocation/explain
4. Check disk usage: GET _cat/nodes?v&h=name,disk.used_percent

**Resolution Steps**:
1. If insufficient nodes: Add new nodes to cluster or reduce replica count
2. If disk issues: Clean old indices, increase disk space, or adjust watermark settings
3. If allocation disabled: Re-enable with cluster.routing.allocation.enable: "all"
4. For specific shard issues: Use reroute API to manually assign shards

**Prevention**:
- Monitor cluster status continuously
- Set up alerts for yellow/red status
- Maintain adequate node capacity for replica distribution
- Regular index lifecycle management and cleanup

---

## 3. Docker Container Out of Memory

**Title**: Docker Container OOM (Out of Memory) Troubleshooting

**Content**:
When a Docker container exceeds its memory limit, the kernel OOM killer terminates processes, causing container crashes with exit code 137.

**Detection**:
1. Check container exit code: docker inspect <container_id> --format='{{.State.ExitCode}}'
2. View container logs: docker logs <container_id>
3. Check kernel logs: dmesg | grep -i oom
4. Review container stats: docker stats <container_id>

**Immediate Actions**:
1. Restart the container: docker restart <container_id>
2. Increase memory limit temporarily: docker update --memory="2g" <container_id>
3. Check for memory leaks in application logs
4. Identify memory-intensive processes inside container

**Long-term Solutions**:
1. Optimize application memory usage (profile with tools like pprof, valgrind)
2. Set appropriate memory limits in docker-compose.yml or Kubernetes manifests
3. Implement memory limit monitoring and alerts
4. Use multi-stage Docker builds to reduce image size
5. Configure memory reservations and soft limits

**Docker Compose Example**:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

**Prevention**:
- Monitor container memory usage with Prometheus/Grafana
- Set memory limits based on load testing results
- Implement graceful degradation when approaching limits
- Regular memory leak testing in CI/CD pipeline

---

## 4. Kafka Consumer Lag Spike

**Title**: Apache Kafka Consumer Lag Resolution

**Content**:
Consumer lag occurs when consumers cannot keep up with the rate of messages being produced. High lag leads to delayed processing and potential data loss if retention expires.

**Diagnosis**:
1. Check consumer lag: kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group <group_id>
2. Monitor offset lag per partition
3. Review consumer throughput metrics
4. Check broker performance and disk I/O
5. Analyze consumer logs for errors or slow processing

**Common Causes**:
1. Slow message processing in consumer application
2. Insufficient consumer instances for partition count
3. Network issues between consumers and brokers
4. Broker performance degradation
5. Large message batches causing processing delays

**Resolution Steps**:
1. Immediate: Scale consumer group (add more consumer instances)
2. Optimize consumer batch size and fetch settings
3. Increase consumer poll timeout if processing is slow
4. Review and optimize message processing logic
5. Consider increasing partition count for better parallelism

**Configuration Tuning**:
```properties
# Increase fetch size for better throughput
fetch.min.bytes=1024
max.partition.fetch.bytes=1048576

# Adjust session timeout
session.timeout.ms=30000
heartbeat.interval.ms=3000

# Optimize commit strategy
enable.auto.commit=false  # Manual commit for better control
```

**Prevention**:
- Monitor consumer lag continuously with alerts
- Implement auto-scaling for consumer groups
- Regular performance testing under peak load
- Set appropriate retention periods
- Use monitoring tools (Kafka Manager, Confluent Control Center)

---

## 5. GitLab CI/CD Pipeline Timeout

**Title**: GitLab CI/CD Pipeline Timeout Troubleshooting

**Content**:
Pipeline timeouts occur when jobs exceed configured time limits, often due to slow build steps, network issues, or resource contention on runners.

**Common Timeout Types**:
1. Job timeout (default 1 hour)
2. Runner timeout
3. Project-level timeout
4. Network timeout during artifact/cache operations

**Diagnosis Steps**:
1. Review pipeline job logs for stuck operations
2. Check runner system resources (CPU, memory, disk)
3. Analyze which stage is timing out
4. Review network connectivity to external dependencies
5. Check for stuck Docker builds or slow dependency downloads

**Quick Fixes**:
1. Increase job timeout in .gitlab-ci.yml:
```yaml
job_name:
  timeout: 2h
  script:
    - long_running_command
```

2. Use pipeline caching effectively:
```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
    - .npm/
```

3. Parallelize slow stages:
```yaml
test:
  parallel: 4
  script:
    - npm run test
```

**Optimization Strategies**:
1. Use Docker layer caching for faster builds
2. Implement dependency caching (npm, pip, maven)
3. Parallelize test suites
4. Use GitLab's DIND (Docker-in-Docker) efficiently
5. Optimize Dockerfile with multi-stage builds
6. Use artifacts wisely (only necessary files)

**Runner Configuration**:
```toml
[[runners]]
  [runners.docker]
    privileged = true
    pull_policy = "if-not-present"
    cache_dir = "/cache"
```

**Prevention**:
- Monitor pipeline duration trends
- Set reasonable timeout limits per job type
- Regular runner maintenance and updates
- Implement pipeline efficiency metrics
- Use dedicated runners for resource-intensive jobs

---

## 6. Terraform State Lock Conflict

**Title**: Terraform State Lock Resolution

**Content**:
State locks prevent concurrent modifications to infrastructure. Lock conflicts occur when multiple users/processes attempt to modify state simultaneously or locks aren't properly released.

**Error Message**:
```
Error: Error acquiring the state lock
Lock Info:
  ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Path: terraform.tfstate
  Operation: OperationTypeApply
  Who: user@hostname
  Version: 1.5.0
  Created: 2026-01-15 10:30:00
```

**Diagnosis**:
1. Check lock status in backend (S3, Terraform Cloud, etc.)
2. Verify if lock holder process is still running
3. Review recent Terraform operations
4. Check for orphaned CI/CD jobs
5. Examine backend access logs

**Safe Resolution**:
1. Confirm lock is truly orphaned (process crashed/killed)
2. Verify no other operations are running
3. Check with team members before force-unlock

**Force Unlock (Use with Caution)**:
```bash
# Get lock ID from error message
terraform force-unlock <LOCK_ID>

# Or for specific workspace
terraform force-unlock -force <LOCK_ID>
```

**Prevention Strategies**:
1. Use remote state backend with proper locking (S3 + DynamoDB, Terraform Cloud)
2. Implement CI/CD pipeline safeguards:
```yaml
terraform:
  script:
    - terraform init
    - terraform plan -lock-timeout=5m
    - terraform apply -lock-timeout=5m -auto-approve
  timeout: 30m
```

3. Configure automatic lock timeout:
```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

4. Use Terraform workspaces for isolation
5. Implement proper access controls and RBAC
6. Regular state backup and versioning

---

## How to Use These Runbooks

### In the UI:
1. Open **Runbook Ingester** tab
2. Copy the **Title** into the "Runbook Title" field
3. Copy the **Content** into the "Runbook Content" textarea
4. Click **"Embed & Upload to MongoDB Atlas"**
5. Watch the terminal logs show:
   - 768-dimensional embedding generation
   - MongoDB Atlas insertion
   - GCS backup confirmation

### Expected Output:
```
[INFO] Initializing text grounding ingestion workflow...
[INFO] Chunk limits computed at max 2000 characters.
[INFO] Generating 768-dimension embeddings using text-embedding-004...
[SUCCESS] Document indexed successfully! Collection: knowledge_vectors
[SUCCESS] ✓ Backup saved to Google Cloud Storage: gs://your-bucket/runbooks/...
[SUCCESS] Pipeline compilation successful. Grounding database synchronized!
```

### Testing:
After ingesting a runbook, ask related questions in the chat:
- PostgreSQL runbook → "How do I fix PostgreSQL connection issues?"
- Kafka runbook → "What causes Kafka consumer lag?"
- Docker runbook → "How to troubleshoot container memory problems?"

You'll see the ingested runbook appear in the grounding sources with high similarity scores!

---

## 📝 Notes

- Each runbook is embedded as a 768-dimensional vector using Google's text-embedding-004
- Vectors are stored in MongoDB Atlas `knowledge_vectors` collection
- Automatic backup to Google Cloud Storage (GCS)
- Searchable via cosine similarity in vector search
- Truncate long runbooks to ~2000 characters for optimal embedding quality
- You can ingest runbooks in any technical domain (not just these examples)
