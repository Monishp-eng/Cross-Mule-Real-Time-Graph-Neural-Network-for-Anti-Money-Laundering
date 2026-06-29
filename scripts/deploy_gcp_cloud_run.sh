#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${1:-}"
REGION="${2:-us-central1}"
SERVICE_NAME="${3:-cross-mule-detection}"
API_KEY="${API_KEY:-}"

read_env_value() {
  local key="$1"
  local file="${2:-.env}"
  if [[ ! -f "$file" ]]; then
    return 0
  fi
  local line
  line="$(grep -E "^${key}=" "$file" | tail -n 1 || true)"
  printf '%s' "${line#*=}"
}

NEO4J_URI="${NEO4J_URI:-$(read_env_value NEO4J_URI)}"
NEO4J_USERNAME="${NEO4J_USERNAME:-$(read_env_value NEO4J_USERNAME)}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-$(read_env_value NEO4J_PASSWORD)}"
NEO4J_DATABASE="${NEO4J_DATABASE:-$(read_env_value NEO4J_DATABASE)}"
NEO4J_DATABASE="${NEO4J_DATABASE:-neo4j}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Usage: ./scripts/deploy_gcp_cloud_run.sh <PROJECT_ID> [REGION] [SERVICE_NAME]"
  exit 1
fi

if [[ -z "$API_KEY" ]]; then
  echo "Set API_KEY in your shell before running this script."
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI not found. Install Google Cloud SDK and run 'gcloud auth login'."
  exit 1
fi

TAG="$(date +%Y%m%d-%H%M%S)"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${TAG}"

gcloud config set project "$PROJECT_ID" >/dev/null

gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com

gcloud builds submit --tag "$IMAGE" .

gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "APP_ENV=production,AUTH_REQUIRED=true,API_KEY=${API_KEY},SQLITE_PERSISTENCE_ENABLED=true,SQLITE_DB_PATH=/tmp/mule_detection.sqlite3,NEO4J_URI=${NEO4J_URI},NEO4J_USERNAME=${NEO4J_USERNAME},NEO4J_PASSWORD=${NEO4J_PASSWORD},NEO4J_DATABASE=${NEO4J_DATABASE}"

URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')"
echo "Deployment complete. Service URL: ${URL}"
