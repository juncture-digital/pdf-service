#!/bin/bash

# Google Cloud Run deployment script for PDF converter (using Artifact Registry)
set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-visual-essays}"
SERVICE_NAME="pdf-converter"
REGION="us-central1"
REPOSITORY_NAME="pdf-converter-repo"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${SERVICE_NAME}"

echo "🚀 Deploying PDF converter to Google Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Image: ${IMAGE_NAME}"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    echo "❌ Please authenticate with Google Cloud first:"
    echo "   gcloud auth login"
    exit 1
fi

# Set the project
echo "🔧 Setting project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository if it doesn't exist
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create ${REPOSITORY_NAME} \
    --repository-format=docker \
    --location=${REGION} \
    --description="PDF converter Docker repository" \
    2>/dev/null || echo "Repository already exists"

# Configure Docker to use Artifact Registry
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build the Docker image using Cloud Build
echo "🏗️  Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 1800 \
    --concurrency 10 \
    --max-instances 10

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)')

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "🧪 Test endpoints:"
echo "   Health check: curl \"${SERVICE_URL}/health\""
echo "   API docs: ${SERVICE_URL}/docs"
echo "   PDF generation: curl \"${SERVICE_URL}/pdf?url=https://example.com\" --output test.pdf"
echo ""
echo "📊 Usage examples:"
echo "   # Basic PDF"
echo "   curl \"${SERVICE_URL}/pdf?url=https://example.com\" -o example.pdf"
echo ""
echo "   # Custom viewport and hide elements"
echo "   curl \"${SERVICE_URL}/pdf?url=https://example.com&viewportWidth=1920&hideElements=nav,footer\" -o clean.pdf"
echo ""
echo "   # Page breaks and formatting"
echo "   curl \"${SERVICE_URL}/pdf?url=https://example.com&pageBreakBefore=h1&format=A4\" -o formatted.pdf"
echo ""
echo "💰 Pricing info:"
echo "   - First 2 million requests/month: Free"
echo "   - Beyond that: \$0.40 per million requests"
echo "   - CPU/Memory: \$0.00002400 per vCPU-second, \$0.00000250 per GiB-second"
echo ""
echo "🔍 Monitor your service:"
echo "   gcloud run services logs tail ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "🗂️  Artifact Registry:"
echo "   Repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}"
echo "   Image: ${IMAGE_NAME}"
echo ""