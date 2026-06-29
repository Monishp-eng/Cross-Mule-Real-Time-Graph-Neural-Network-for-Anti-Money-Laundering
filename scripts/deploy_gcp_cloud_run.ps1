param(
  [Parameter(Mandatory = $true)]
  [string]$ProjectId,

  [Parameter(Mandatory = $false)]
  [string]$Region = "us-central1",

  [Parameter(Mandatory = $false)]
  [string]$ServiceName = "cross-mule-detection",

  [Parameter(Mandatory = $true)]
  [string]$ApiKey
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
  throw "gcloud CLI not found. Install Google Cloud SDK and run 'gcloud auth login'."
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  throw "ApiKey is required."
}

$neo4jUri = if ($env:NEO4J_URI) { $env:NEO4J_URI } else { "" }
$neo4jUsername = if ($env:NEO4J_USERNAME) { $env:NEO4J_USERNAME } else { "" }
$neo4jPassword = if ($env:NEO4J_PASSWORD) { $env:NEO4J_PASSWORD } else { "" }
$neo4jDatabase = if ($env:NEO4J_DATABASE) { $env:NEO4J_DATABASE } else { "neo4j" }

$tag = Get-Date -Format "yyyyMMdd-HHmmss"
$image = "gcr.io/$ProjectId/$ServiceName:$tag"

Write-Host "Setting project to $ProjectId"
gcloud config set project $ProjectId | Out-Null

Write-Host "Enabling required services"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com

Write-Host "Building and pushing image: $image"
gcloud builds submit --tag $image .

$envVars = @(
  "APP_ENV=production",
  "AUTH_REQUIRED=true",
  "API_KEY=$ApiKey",
  "SQLITE_PERSISTENCE_ENABLED=true",
  "SQLITE_DB_PATH=/tmp/mule_detection.sqlite3",
  "NEO4J_URI=$neo4jUri",
  "NEO4J_USERNAME=$neo4jUsername",
  "NEO4J_PASSWORD=$neo4jPassword",
  "NEO4J_DATABASE=$neo4jDatabase"
) -join ","

Write-Host "Deploying to Cloud Run service: $ServiceName"
gcloud run deploy $ServiceName `
  --image $image `
  --region $Region `
  --platform managed `
  --allow-unauthenticated `
  --port 8080 `
  --set-env-vars $envVars

$url = gcloud run services describe $ServiceName --region $Region --format "value(status.url)"
Write-Host "Deployment complete. Service URL: $url"
