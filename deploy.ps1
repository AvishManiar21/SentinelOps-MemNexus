# ==============================================================================
# ⚠️ INSECURE: This script has your password in plain text
# USE deploy-secure.ps1 INSTEAD for secure deployment
# ==============================================================================
# PowerShell deployment script for Cloud Run
# Replace <PASSWORD> with your actual MongoDB password before running
# ==============================================================================

Write-Host "⚠️  WARNING: This script requires you to edit it and add your password" -ForegroundColor Yellow
Write-Host "For secure deployment, use: .\deploy-secure.ps1" -ForegroundColor Green
Write-Host ""

# Option 1: Deploy WITHOUT Secret Manager (Quick Deploy)
# REPLACE <PASSWORD> WITH YOUR ACTUAL PASSWORD
gcloud run deploy sentinelops-api --source . --region us-central1 --allow-unauthenticated --set-env-vars "GCP_PROJECT_ID=avish-memnexus-2026,GCP_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash,USE_SECRET_MANAGER=false,MONGODB_URI=mongodb+srv://dbuser:<PASSWORD>@cluster0.qajn3ij.mongodb.net/?appName=Cluster0"
