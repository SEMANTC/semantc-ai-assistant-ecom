#!/bin/bash
set -e

# Define color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="semantc-sandbox"
REGION="us-central1"
REPO="gcr.io"
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
IMAGE_NAME="${REPO}/${PROJECT_ID}/ai-assistant-ecom:${IMAGE_TAG}"
LATEST_IMAGE="${REPO}/${PROJECT_ID}/ai-assistant-ecom:latest"
SERVICE_NAME="ai-assistant-ecom"

# Function to log messages with timestamp
log() {
    local level=$1
    shift
    echo -e "${level}[$(date +'%Y-%m-%d %H:%M:%S')] $*${NC}"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    log "${RED}" "Error: gcloud CLI is not installed"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    log "${RED}" "Error: docker is not installed"
    exit 1
fi

# Verify project ID
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    log "${YELLOW}" "Switching to project: ${PROJECT_ID}"
    gcloud config set project ${PROJECT_ID}
fi

# Print configuration
log "${YELLOW}" "Build Configuration:"
log "${YELLOW}" "Project ID: ${PROJECT_ID}"
log "${YELLOW}" "Region: ${REGION}"
log "${YELLOW}" "Image: ${IMAGE_NAME}"

# Validate resource requirements
if [ $((16 * 1024)) -gt 32768 ]; then  # 16Gi to MB
    log "${YELLOW}" "Warning: Memory request exceeds Cloud Run maximum"
fi

# Save previous revision for potential rollback
PREVIOUS_REVISION=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.latestReadyRevision)' 2>/dev/null || echo "None")
if [ "$PREVIOUS_REVISION" != "None" ]; then
    log "${YELLOW}" "Previous revision: ${PREVIOUS_REVISION}"
fi

# Authenticate with GCP
log "${GREEN}" "Authenticating with Google Cloud..."
gcloud auth configure-docker gcr.io --quiet

# Build Docker image
log "${GREEN}" "Building Docker image..."
docker build --platform linux/amd64 \
    -t ${IMAGE_NAME} \
    -t ${LATEST_IMAGE} \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VERSION=${IMAGE_TAG} \
    --no-cache .

# Push Docker image
log "${GREEN}" "Pushing Docker image..."
docker push ${IMAGE_NAME}
docker push ${LATEST_IMAGE}

log "${GREEN}" "Docker image pushed successfully"

# Deploy to Cloud Run
log "${GREEN}" "Deploying to Cloud Run with GPU..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --cpu=4 \
    --memory=16Gi \
    --timeout=3600 \
    --gpu-type=nvidia-tesla-t4 \
    --gpu-count=1 \
    --set-env-vars="ENVIRONMENT=production" \
    --set-env-vars="MAX_WORKERS=4" \
    --set-env-vars="LOG_LEVEL=INFO"

DEPLOY_STATUS=$?

if [ $DEPLOY_STATUS -eq 0 ]; then
    log "${GREEN}" "Deployment completed successfully!"
    
    # Print service URL
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')
    log "${GREEN}" "Service is available at: ${SERVICE_URL}"
else
    log "${RED}" "Deployment failed!"
    
    if [ "$PREVIOUS_REVISION" != "None" ]; then
        log "${YELLOW}" "Rolling back to previous revision: ${PREVIOUS_REVISION}"
        gcloud run services update-traffic ${SERVICE_NAME} \
            --region=${REGION} \
            --to-revisions=${PREVIOUS_REVISION}=100
        
        if [ $? -eq 0 ]; then
            log "${GREEN}" "Rollback successful"
        else
            log "${RED}" "Rollback failed"
        fi
    fi
    
    exit 1
fi

# Optional: verify the deployment
log "${GREEN}" "Verifying deployment..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/health" || echo "failed")

if [ "$HEALTH_CHECK" == "200" ]; then
    log "${GREEN}" "Health check passed"
else
    log "${YELLOW}" "Warning: Health check returned status ${HEALTH_CHECK}"
fi

log "${GREEN}" "Build and deployment process completed!"