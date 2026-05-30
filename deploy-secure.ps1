# ==============================================================================
# Secure Cloud Run Deployment Script
# Prompts for MongoDB password instead of hardcoding it
# ==============================================================================

Write-Host "================================" -ForegroundColor Cyan
Write-Host "SentinelOps Secure Deployment" -ForegroundColor Cyan  
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Prompt for MongoDB password securely
$mongoPassword = Read-Host "Enter your MongoDB Atlas password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($mongoPassword)
$password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Build MongoDB URI
$mongoUri = "mongodb+srv://dbuser:$password@cluster0.qajn3ij.mongodb.net/?appName=Cluster0"

Write-Host ""
Write-Host "Deploying to Cloud Run..." -ForegroundColor Green
Write-Host ""

# Deploy to Cloud Run
gcloud run deploy sentinelops-api `
  --source . `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars "GCP_PROJECT_ID=avish-memnexus-2026,GCP_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash,USE_SECRET_MANAGER=false,MONGODB_URI=$mongoUri"

# Clear password from memory
$password = $null
$mongoUri = $null

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
