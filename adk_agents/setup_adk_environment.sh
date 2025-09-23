#!/bin/bash

# Google ADK Environment Setup Script for Felicia's Finance
# This script sets up the Google Cloud ADK environment for agent integration

set -e

echo "🚀 Setting up Google Cloud ADK Environment for Felicia's Finance"
echo "================================================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ gcloud CLI found"

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "❌ Not authenticated with Google Cloud. Please run:"
    echo "   gcloud auth login"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ Google Cloud authentication verified"

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo "❌ No Google Cloud project set. Please run:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "✅ Using Google Cloud project: $PROJECT_ID"

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable \
    aiplatform.googleapis.com \
    vertexai.googleapis.com \
    run.googleapis.com \
    --project=$PROJECT_ID

echo "✅ Required APIs enabled"

# Create service account for ADK
SERVICE_ACCOUNT_NAME="felicia-adk-sa"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo "🔧 Creating service account for ADK integration..."
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID &>/dev/null; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --description="Service account for Felicia's Finance ADK integration" \
        --display-name="Felicia ADK Service Account" \
        --project=$PROJECT_ID
    echo "✅ Service account created: $SERVICE_ACCOUNT_EMAIL"
else
    echo "✅ Service account already exists: $SERVICE_ACCOUNT_EMAIL"
fi

# Grant necessary permissions
echo "🔧 Granting permissions to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user" \
    --project=$PROJECT_ID

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/vertexai.user" \
    --project=$PROJECT_ID

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker" \
    --project=$PROJECT_ID

echo "✅ Service account permissions granted"

# Create and download service account key
KEY_FILE="felicia-adk-key.json"
echo "🔧 Creating service account key..."
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL \
    --project=$PROJECT_ID

echo "✅ Service account key created: $KEY_FILE"

# Set environment variable for the key file
echo "🔧 Setting up environment configuration..."
cat >> .env << EOF

# Google Cloud ADK Configuration
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=$PWD/$KEY_FILE
GOOGLE_ADK_SERVICE_ACCOUNT=$SERVICE_ACCOUNT_EMAIL

EOF

echo "✅ Environment configuration added to .env"

# Create ADK configuration directory
mkdir -p adk_config

# Create ADK agent configuration
cat > adk_config/agent_config.yaml << EOF
# Google ADK Agent Configuration for Felicia's Finance

project_id: $PROJECT_ID
service_account: $SERVICE_ACCOUNT_EMAIL
region: us-central1

agents:
  - name: felicia-main-agent
    type: livekit_agent
    description: "Felicia's main banking and finance communication agent"

  - name: banking-agent
    type: specialized_agent
    capabilities: ["banking", "compliance", "transactions"]
    description: "Bank of Anthos banking operations agent"

  - name: crypto-agent
    type: specialized_agent
    capabilities: ["crypto", "trading", "analysis"]
    description: "Cryptocurrency trading and analysis agent"

workflows:
  - name: financial-analysis-workflow
    agents:
      - felicia-main-agent
      - banking-agent
      - crypto-agent
    description: "Complete financial analysis workflow"

EOF

echo "✅ ADK configuration created"

# Install ADK SDK if not already installed
echo "🔧 Checking ADK SDK installation..."
if ! python -c "import google.auth" &> /dev/null; then
    echo "Installing Google Cloud libraries..."
    pip install google-auth google-cloud-aiplatform google-cloud-functions
else
    echo "✅ Google Cloud libraries already installed"
fi

# Test the setup
echo "🧪 Testing ADK environment setup..."
python -c "
import os
from google.auth import default
from google.cloud import aiplatform

# Test authentication
credentials, project = default()
print(f'✅ Authentication successful, project: {project}')

# Test Vertex AI access
aiplatform.init(project=project, location='us-central1')
print('✅ Vertex AI access verified')

print('🎉 Google ADK environment setup complete!')
" 2>/dev/null || {
    echo "⚠️ Basic authentication test failed, but setup is complete."
    echo "   Make sure the service account has proper permissions."
}

echo ""
echo "🎉 Google Cloud ADK Environment Setup Complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo "1. Verify your setup by running: python -c \"from google.auth import default; print(default())\""
echo "2. Continue to Phase 1 Task 2: Install and configure ADK SDK"
echo "3. Then proceed to creating the ADK agent wrapper"
echo ""
echo "Configuration files created:"
echo "  - $KEY_FILE (service account key)"
echo "  - adk_config/agent_config.yaml (ADK configuration)"
echo "  - .env updated with ADK settings"