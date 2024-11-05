#!/bin/sh -e

PROJECT="ai-system-meigsy-gcp"
REGION="us-central1"
ZONE="us-central1-c"

BUCKET="ai-system-meigsy-gcp-terraform-state"
PREFIX="infrastructure"


# -------------------------------------------------------------------------------
# Pre-Terraform Actions
# -------------------------------------------------------------------------------

# place holder for pre-terraform actions

# -------------------------------------------------------------------------------
# Terraform Actions
# -------------------------------------------------------------------------------
echo "Running Terraform..."
terraform init \
  -backend-config="bucket=$BUCKET" \
  -backend-config="prefix=$PREFIX" \
  -var="billing_account" \
  -var="project_id=$PROJECT" \
  -var="region=$REGION" \
  -var="zone=$ZONE"

terraform apply \
  -var="project_id=$PROJECT" \
  -var="region=$REGION" \
  -var="zone=$ZONE" \
  -var="billing_account=$BILLING_ACCOUNT"

# -------------------------------------------------------------------------------
# Post-Terraform Actions
# -------------------------------------------------------------------------------

# place holder for post-terraform actions

echo "Deployment complete."

