# PowerShell deployment script for Cloud Run

# Option 1: Deploy WITHOUT Secret Manager (Quick Deploy)
gcloud run deploy sentinelops-api --source . --region us-central1 --allow-unauthenticated --set-env-vars "GCP_PROJECT_ID=avish-memnexus-2026,GCP_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash,USE_SECRET_MANAGER=false,MONGODB_URI=mongodb+srv://dbuser:<PASSWORD>@cluster0.qajn3ij.mongodb.net/?appName=Cluster0"
