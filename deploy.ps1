# ==============================================================================
# Simple Cloud Run Deployment
# Pass your password as a parameter: .\deploy-simple.ps1 YOUR_PASSWORD_HERE
# ==============================================================================

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$MongoPassword
)

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Deploying SentinelOps to Cloud Run" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This may take 2-3 minutes..." -ForegroundColor Yellow
Write-Host ""

# Build MongoDB URI
$mongoUri = "mongodb+srv://dbuser:$MongoPassword@cluster0.qajn3ij.mongodb.net/?appName=Cluster0"

# Deploy to Cloud Run
gcloud run deploy sentinelops-api --source . --region us-central1 --allow-unauthenticated --set-env-vars "GCP_PROJECT_ID=avish-memnexus-2026,GCP_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash,USE_SECRET_MANAGER=false,MONGODB_URI=$mongoUri"

# Clear from memory
$MongoPassword = $null
$mongoUri = $null

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
