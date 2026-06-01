# 🔒 Security Guide - MongoDB Credentials Management

## ⚠️ IMPORTANT: Password Leaked - Action Required

Your MongoDB credentials were accidentally committed to the public repository. Follow these steps immediately:

---

## 🔑 Step 1: Change MongoDB Password (URGENT)

1. **Go to MongoDB Atlas**: https://cloud.mongodb.com/
2. **Navigate to Database Access**:
   - Click on "Database Access" in the left sidebar
   - Or direct link: https://cloud.mongodb.com/v2#/security/database/users
3. **Find user `dbuser`** and click **Edit**
4. **Change the password**:
   - Click "Edit Password"
   - Generate a strong password (or use your own)
   - **SAVE THIS PASSWORD SECURELY** (password manager, etc.)
5. **Click "Update User"**
   - Wait 10 seconds for changes to propagate

✅ **Old password is now invalid** - your database is secure!

---

## 🚀 Step 2: Deploy with New Password

### **Option A: Secure Script (Recommended for Quick Deploy)**

Use the secure deployment script with your password as parameter:

```powershell
.\deploy.ps1 <YOUR_NEW_PASSWORD>
```

This script:
- ✅ Takes password as parameter
- ✅ Never stores password on disk
- ✅ Clears password from memory after deployment
- ✅ Safe for repeated use

### **Option B: Manual Command (One-time Deploy)**

```powershell
# Replace <YOUR_NEW_PASSWORD> with your actual password
gcloud run deploy sentinelops-api --source . --region us-central1 --allow-unauthenticated --set-env-vars "GCP_PROJECT_ID=avish-memnexus-2026,GCP_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash,USE_SECRET_MANAGER=false,MONGODB_URI=mongodb+srv://dbuser:<YOUR_NEW_PASSWORD>@cluster0.qajn3ij.mongodb.net/?appName=Cluster0"
```

⚠️ **Warning**: This shows your password in command history. Use Option A or C instead.

### **Option C: Secret Manager (BEST for Production)**

The most secure approach - credentials never appear in commands or logs.

#### **Setup Secret Manager (One-time)**

```powershell
# 1. Create the secret with your NEW password
$mongoPassword = Read-Host "Enter your NEW MongoDB password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($mongoPassword)
$password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

echo -n "mongodb+srv://dbuser:$password@cluster0.qajn3ij.mongodb.net/?appName=Cluster0" | gcloud secrets create mongodb-atlas-uri --data-file=-

# 2. Grant Cloud Run access
gcloud secrets add-iam-policy-binding mongodb-atlas-uri --member="serviceAccount:782741881130-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"

# 3. Clear password from memory
$password = $null
```

#### **Deploy with Secret Manager**

```powershell
gcloud run deploy sentinelops-api --source . --region us-central1 --allow-unauthenticated --set-env-vars "GCP_PROJECT_ID=avish-memnexus-2026,GCP_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash,USE_SECRET_MANAGER=true"
```

✅ **Benefits**:
- Credentials stored securely in Google Cloud
- Automatic encryption at rest
- Access logging and auditing
- No credentials in code or commands
- Easy password rotation

---

## 📋 Security Checklist

After changing your password:

- [ ] MongoDB password changed in Atlas
- [ ] New password saved in password manager
- [ ] Deployed to Cloud Run with new credentials
- [ ] Tested deployment (visit Cloud Run URL)
- [ ] Verified frontend connects to backend
- [ ] (Optional) Set up Secret Manager for production

---

## 🔍 What Was Exposed

The following were committed to the public repository:
- MongoDB connection string with password
- Database cluster hostname
- Database username

**What this means**:
- Anyone could have accessed your MongoDB database
- Could read/write/delete data
- Could use your database resources

**What's protected now**:
- Old password is invalid (after you change it)
- New password never committed to git
- Repository cleaned of credentials

---

## 🛡️ Prevention Tips

### **Never Commit These to Git:**
- ❌ Database passwords
- ❌ API keys
- ❌ Private keys
- ❌ OAuth tokens
- ❌ Any credentials

### **Always Use:**
- ✅ `.env` files (in `.gitignore`)
- ✅ Secret Manager for production
- ✅ Environment variables
- ✅ Password managers

### **Files Already Protected:**
- `.env` - In `.gitignore` (not tracked)
- `venv/` - In `.gitignore` (not tracked)
- All passwords now use placeholders

---

## 🔄 Rotating Credentials (Future)

If you need to change your password again:

1. Change in MongoDB Atlas
2. Update Secret Manager:
   ```powershell
   echo -n "mongodb+srv://dbuser:NEW_PASSWORD@cluster0..." | gcloud secrets versions add mongodb-atlas-uri --data-file=-
   ```
3. Redeploy Cloud Run (picks up new version automatically)

---

## 📞 Need Help?

- MongoDB Atlas Security: https://www.mongodb.com/docs/atlas/security/
- Google Secret Manager: https://cloud.google.com/secret-manager/docs
- Cloud Run Environment Variables: https://cloud.google.com/run/docs/configuring/environment-variables

---

## ✅ You're Safe Once You:

1. ✅ Change MongoDB password in Atlas
2. ✅ Deploy with new password
3. ✅ Verify it works

The repository is already clean - just update Atlas and redeploy!
