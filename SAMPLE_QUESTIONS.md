# Sample Questions for SentinelOps Chat

Try these questions in the **SRE Diagnostic Chat** to see MongoDB Atlas Vector Search in action. Each question will trigger vector search to find relevant runbooks and display grounding sources with similarity scores.

## 🔴 Critical Infrastructure Issues

### Redis & Caching
- How do I fix Redis cache key eviction under high traffic?
- What's the best practice for Redis cache hit rate optimization?
- How do I troubleshoot Redis connection exhaustion?
- What are the common causes of Redis memory issues?

### MongoDB & Databases
- How do I fix MongoDB connection timeout errors?
- What's the solution for MongoDB high latency issues?
- How do I optimize MongoDB connection pooling?
- What are the best practices for MongoDB replica set configuration?

### Nginx & Load Balancing
- How do I fix Nginx rate limiting during a DDoS attack?
- What's the configuration for Nginx reverse proxy optimization?
- How do I troubleshoot Nginx 502 Bad Gateway errors?
- What are the best practices for Nginx SSL/TLS configuration?

## 🟡 Performance & Optimization

### System Resources
- How do I diagnose high CPU usage in production?
- What's the approach for troubleshooting memory leaks?
- How do I optimize disk I/O performance?
- What are the best practices for container resource limits?

### Application Performance
- How do I reduce API response latency?
- What's the solution for database query optimization?
- How do I troubleshoot slow application startup times?
- What are the best practices for caching strategies?

## 🟢 Monitoring & Observability

### Alerting & Monitoring
- How do I set up effective SRE alerting?
- What metrics should I monitor for production systems?
- How do I implement distributed tracing?
- What's the best practice for log aggregation?

### Incident Response
- What's the SRE incident response protocol?
- How do I conduct effective post-mortems?
- What's the runbook for handling production outages?
- How do I implement chaos engineering practices?

## 🔵 Infrastructure & DevOps

### Kubernetes & Containers
- How do I troubleshoot Kubernetes pod crashes?
- What's the solution for container networking issues?
- How do I optimize Kubernetes resource allocation?
- What are the best practices for Kubernetes security?

### CI/CD & Deployment
- How do I implement blue-green deployments?
- What's the best practice for canary releases?
- How do I troubleshoot failed deployments?
- What are the rollback strategies for production?

## 🟣 Security & Compliance

### Security Best Practices
- How do I secure API endpoints?
- What's the solution for implementing rate limiting?
- How do I prevent SQL injection attacks?
- What are the best practices for secrets management?

### SSL/TLS & Certificates
- How do I fix expired SSL certificates?
- What's the process for certificate renewal?
- How do I troubleshoot SSL handshake failures?
- What are the best practices for certificate rotation?

## 💡 Testing the System

### Quick Tests
Try these to see different features:

1. **Vector Search Grounding**:
   - "How do I fix Redis cache eviction?"
   - Watch the **📚 MongoDB Atlas Vector Search Results** panel show matched runbooks with % scores

2. **Model Comparison**:
   - Ask the same question with **⚡ Flash** (fast, ~7s)
   - Switch to **🧠 Pro** and ask again (slower, ~20s, more detailed)

3. **Memory Synthesis**:
   - Change User ID to a new name (e.g., "sarah_sre")
   - Ask 2-3 questions
   - Go to **MongoDB Memory Core → SRE Profiles**
   - See your new profile with AI-synthesized summary

4. **Real-time Data**:
   - Open **MongoDB Memory Core** tab
   - Browse the three collections: Users, Sessions, Knowledge Vectors
   - See live data from MongoDB Atlas

## 📝 Notes

- All questions trigger MongoDB Atlas vector search (768-dim embeddings, cosine similarity)
- Grounding sources show which runbooks were used with similarity scores
- Responses are factually grounded in your runbook library, not hallucinated
- Chat history is saved to MongoDB Atlas for memory synthesis
- You can switch models mid-conversation to compare responses
