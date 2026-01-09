# CI/CD Setup Guide for AI Context Bridge

## Overview
Automated deployment pipeline using GitHub Actions to deploy the FastAPI backend to Google Cloud Run whenever backend code changes.

## What We Set Up

### 1. GitHub Repository
- **Repository**: https://github.com/pranavrav09/ai-context-bridge
- **Branch**: `main` (protected with CI/CD)
- **Visibility**: Public

### 2. GCP Service Account
- **Name**: `github-actions@ai-context-bridge.iam.gserviceaccount.com`
- **Purpose**: Authenticates GitHub Actions to deploy to GCP
- **Permissions Granted**:
  - `roles/run.admin` - Deploy and manage Cloud Run services
  - `roles/cloudbuild.builds.editor` - Build Docker images
  - `roles/iam.serviceAccountUser` - Act as service accounts
  - `roles/storage.admin` - Manage Cloud Storage
  - `roles/artifactregistry.writer` - Push Docker images to GCR

### 3. GitHub Secrets
Stored securely in GitHub repository settings:
- **GCP_SA_KEY**: Service account JSON key for GCP authentication

### 4. GitHub Actions Workflow
- **File**: `.github/workflows/deploy-backend.yml`
- **Triggers**:
  - Push to `main` branch (only when `backend/**` files change)
  - Pull requests to `main` (builds but doesn't deploy)
  - Manual trigger via `workflow_dispatch`

## Workflow Steps

When code is pushed to the `main` branch:

1. **Checkout code** - Fetches the latest code from GitHub
2. **Authenticate to Google Cloud** - Uses service account key
3. **Set up Cloud SDK** - Configures gcloud CLI
4. **Configure Docker for GCR** - Authenticates Docker with Google Container Registry
5. **Build Docker image** - Builds the backend Docker image with two tags:
   - `gcr.io/ai-context-bridge/api:latest`
   - `gcr.io/ai-context-bridge/api:<commit-sha>`
6. **Push Docker image to GCR** - Pushes both tagged images
7. **Deploy to Cloud Run** - Updates the Cloud Run service with:
   - New Docker image
   - Cloud SQL connection
   - Secrets (DATABASE_URL, OPENAI_API_KEY)
   - Environment variables
8. **Test Deployment** - Runs health check to verify deployment
9. **Output Service URL** - Displays the deployed service URL

## Current Deployment

### Live Service
- **URL**: https://ai-context-api-elxaawma6a-uc.a.run.app
- **Health Check**: https://ai-context-api-elxaawma6a-uc.a.run.app/api/v1/health
- **API Docs**: https://ai-context-api-elxaawma6a-uc.a.run.app/docs

### Cloud Resources
- **Project**: `ai-context-bridge`
- **Region**: `us-central1`
- **Service Name**: `ai-context-api`
- **Cloud SQL Instance**: `ai-context-bridge:us-central1:ai-context-db`
- **Container Registry**: `gcr.io/ai-context-bridge/api`

## How to Use

### Automatic Deployment
Simply push your backend changes to the `main` branch:

```bash
# Make changes to backend files
git add backend/
git commit -m "Update backend feature"
git push origin main
```

GitHub Actions will automatically:
- Build the Docker image
- Push to Container Registry
- Deploy to Cloud Run
- Run health checks
- Report status

### Manual Deployment
Trigger deployment manually from GitHub:

1. Go to: https://github.com/pranavrav09/ai-context-bridge/actions
2. Click "Deploy Backend to Cloud Run"
3. Click "Run workflow"
4. Select branch and click "Run workflow"

### View Deployment Status
Monitor deployments in real-time:

```bash
# List recent workflow runs
gh run list --limit 5

# Watch a specific run
gh run watch <run-id>

# View logs
gh run view <run-id> --log
```

Or visit: https://github.com/pranavrav09/ai-context-bridge/actions

## Making Backend Changes

### Example: Update an API Endpoint

```bash
# 1. Make changes
vim backend/app/api/routes/contexts.py

# 2. Test locally
cd backend
uvicorn app.main:app --reload

# 3. Commit and push
git add backend/app/api/routes/contexts.py
git commit -m "Add pagination to contexts endpoint"
git push origin main

# 4. Watch deployment
gh run watch
```

The new version will be live in ~2-3 minutes!

### Example: Update Dependencies

```bash
# 1. Update requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# 2. Test locally
cd backend
pip install -r requirements.txt

# 3. Commit and push
git add backend/requirements.txt
git commit -m "Add new-package dependency"
git push origin main
```

### Example: Database Migration

```bash
# 1. Create migration
cd backend
alembic revision --autogenerate -m "Add new column"

# 2. Test migration locally
alembic upgrade head

# 3. Commit and push
git add backend/alembic/versions/
git commit -m "Add database migration for new column"
git push origin main
```

Migrations run automatically during deployment via `docker-entrypoint.sh`!

## Pull Request Workflow

When creating a pull request:

1. CI/CD builds the Docker image to verify it compiles
2. **Does NOT deploy** to production (only builds)
3. Comments on PR with build status
4. After merging to `main`, automatic deployment occurs

Example PR workflow:

```bash
# 1. Create feature branch
git checkout -b feature/new-endpoint

# 2. Make changes
vim backend/app/api/routes/new_feature.py

# 3. Push feature branch
git add backend/
git commit -m "Add new feature endpoint"
git push origin feature/new-endpoint

# 4. Create PR on GitHub
gh pr create --title "Add new feature endpoint" --body "Adds XYZ feature"

# 5. CI/CD runs build (no deployment)
# 6. After review, merge PR
gh pr merge

# 7. CI/CD deploys to production automatically
```

## Monitoring

### View Cloud Run Logs

```bash
# Recent logs
gcloud run services logs read ai-context-api --region=us-central1 --limit=50

# Follow logs in real-time
gcloud run services logs tail ai-context-api --region=us-central1

# Filter by severity
gcloud run services logs read ai-context-api --region=us-central1 --log-filter="severity>=ERROR"
```

### View GitHub Actions Logs

```bash
# List workflow runs
gh run list

# View specific run
gh run view 20840326117

# View logs
gh run view 20840326117 --log

# Download logs
gh run download 20840326117
```

### View Service Status

```bash
# Service details
gcloud run services describe ai-context-api --region=us-central1

# Current revision
gcloud run revisions list --service=ai-context-api --region=us-central1

# Traffic split
gcloud run services describe ai-context-api --region=us-central1 --format="value(status.traffic)"
```

## Rollback

If a deployment fails or has issues:

### Option 1: Rollback via Git

```bash
# Revert last commit
git revert HEAD
git push origin main

# CI/CD will deploy the previous version
```

### Option 2: Rollback via Cloud Run

```bash
# List revisions
gcloud run revisions list --service=ai-context-api --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic ai-context-api \
  --region=us-central1 \
  --to-revisions=ai-context-api-00001-xyz=100
```

### Option 3: Redeploy Specific Commit

```bash
# Find the commit SHA you want to deploy
git log --oneline

# Reset to that commit
git reset --hard <commit-sha>
git push --force origin main

# Or deploy specific image
gcloud run deploy ai-context-api \
  --image gcr.io/ai-context-bridge/api:<commit-sha> \
  --region=us-central1
```

## Security Best Practices

### Service Account Key
- ✅ Stored securely in GitHub Secrets (encrypted)
- ✅ Never committed to repository (in `.gitignore`)
- ✅ Minimum required permissions granted
- ⚠️ Rotate key periodically (every 90 days recommended)

### Secrets Management
- ✅ Database credentials in Secret Manager
- ✅ OpenAI API key in Secret Manager
- ✅ Secrets accessed via environment variables
- ✅ No secrets in code or logs

### Access Control
- ✅ Cloud Run service allows unauthenticated (public API)
- ✅ Rate limiting configured (100 req/hour per IP)
- ✅ CORS configured for extension origins
- 💡 Consider adding API key authentication for production

## Troubleshooting

### Workflow Fails at "Push Docker image"
**Error**: `Permission denied` or `artifactregistry.repositories.uploadArtifacts`

**Solution**: Grant Artifact Registry permissions
```bash
gcloud projects add-iam-policy-binding ai-context-bridge \
  --member="serviceAccount:github-actions@ai-context-bridge.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

### Workflow Fails at "Deploy to Cloud Run"
**Error**: `Cloud Run Admin API has not been enabled`

**Solution**: Enable Cloud Run API
```bash
gcloud services enable run.googleapis.com
```

### Deployment Succeeds but Health Check Fails
**Possible Issues**:
1. Database connection failed
2. Migrations didn't run
3. Secrets not accessible

**Debug**:
```bash
# Check Cloud Run logs
gcloud run services logs read ai-context-api --region=us-central1 --limit=100

# Check revision status
gcloud run revisions list --service=ai-context-api --region=us-central1

# Test health endpoint
curl https://ai-context-api-elxaawma6a-uc.a.run.app/api/v1/health
```

### Workflow Doesn't Trigger
**Check**:
1. Changes are in `backend/**` directory
2. Pushed to `main` branch
3. Workflow file is valid YAML

**Debug**:
```bash
# Manually trigger workflow
gh workflow run deploy-backend.yml

# Check workflow file syntax
yamllint .github/workflows/deploy-backend.yml
```

## Cost Optimization

Current CI/CD costs are minimal:

- **GitHub Actions**: Free (2,000 minutes/month for public repos)
- **Cloud Build**: First 120 build-minutes/day free
- **Container Registry Storage**: ~$0.02/GB/month
- **Cloud Run**: Only charged during deployments and requests

### Tips to Reduce Costs
1. Use caching for Docker layers (already configured)
2. Limit workflow runs to backend changes only (already configured)
3. Set max-instances to prevent runaway scaling (already set to 10)
4. Use Cloud Run min-instances=0 for auto-scaling to zero (already configured)

## Maintenance

### Rotate Service Account Key
Recommended every 90 days:

```bash
# 1. Create new key
gcloud iam service-accounts keys create new-github-actions-key.json \
  --iam-account=github-actions@ai-context-bridge.iam.gserviceaccount.com

# 2. Update GitHub secret
gh secret set GCP_SA_KEY < new-github-actions-key.json

# 3. Delete old key
gcloud iam service-accounts keys list \
  --iam-account=github-actions@ai-context-bridge.iam.gserviceaccount.com

gcloud iam service-accounts keys delete <old-key-id> \
  --iam-account=github-actions@ai-context-bridge.iam.gserviceaccount.com

# 4. Securely delete local key files
shred -u new-github-actions-key.json
```

### Update Workflow Dependencies
Keep GitHub Actions up to date:

```yaml
# Update in .github/workflows/deploy-backend.yml
- uses: actions/checkout@v4  # Check for v5
- uses: google-github-actions/auth@v2  # Check for newer versions
- uses: google-github-actions/setup-gcloud@v2
```

## Success Metrics

✅ **All Completed**:
- [x] GitHub repository created
- [x] Service account configured with proper permissions
- [x] GitHub Actions workflow created
- [x] Secrets configured securely
- [x] First deployment succeeded
- [x] Automated deployment working
- [x] Health checks passing
- [x] Documentation created

## Resources

- **Repository**: https://github.com/pranavrav09/ai-context-bridge
- **Actions**: https://github.com/pranavrav09/ai-context-bridge/actions
- **Cloud Console**: https://console.cloud.google.com/run?project=ai-context-bridge
- **Service URL**: https://ai-context-api-elxaawma6a-uc.a.run.app
- **API Docs**: https://ai-context-api-elxaawma6a-uc.a.run.app/docs

## Next Steps

Consider these enhancements:

1. **Add Testing Stage**: Run pytest before deployment
2. **Add Linting**: Run black, flake8, mypy in CI
3. **Staging Environment**: Deploy PRs to staging Cloud Run instance
4. **Notifications**: Slack/Discord notifications for deployments
5. **Performance Monitoring**: Add Sentry or Cloud Monitoring
6. **Custom Domain**: Map a custom domain to Cloud Run
7. **Blue-Green Deployments**: Use traffic splitting for zero-downtime

---

**Your CI/CD pipeline is live! Every push to `main` automatically deploys to production. 🚀**
