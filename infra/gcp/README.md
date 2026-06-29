# GCP Cloud Run Deployment

This is a fresh deployment scaffold for Google Cloud Run.

## Prerequisites

1. Install Google Cloud SDK (`gcloud`).
2. Authenticate:
   - `gcloud auth login`
3. Ensure billing is enabled for your GCP project.

## Option A: Windows PowerShell

Run from repository root:

```powershell
./scripts/deploy_gcp_cloud_run.ps1 -ProjectId "<your-project-id>" -Region "us-central1" -ServiceName "cross-mule-detection" -ApiKey "<strong-random-api-key>"
```

## Option B: Bash

Run from repository root:

```bash
chmod +x scripts/deploy_gcp_cloud_run.sh
export API_KEY="<strong-random-api-key>"
./scripts/deploy_gcp_cloud_run.sh <your-project-id> us-central1 cross-mule-detection
```

## What gets deployed

- Multi-stage container image built from the repository `Dockerfile`
- Cloud Run service exposing port `8080`
- Production environment variables including API key and local SQLite fallback

## Post-deploy checks

1. Open `<service-url>/health/live` and confirm `{"status":"ok"}`.
2. Open `<service-url>/` and verify the frontend loads.
3. Login with seeded staff credentials if you kept defaults.
