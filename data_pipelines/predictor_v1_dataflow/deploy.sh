#!/bin/sh -e

PROJECT="ai-system-meigsy-gcp"
SERVICE_NAME="predictor-v1-dataflow"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format="value(projectNumber)")
PIPELINE_BUCKET_NAME="${SERVICE_NAME}-${PROJECT_NUMBER}"
SHA=$(git rev-parse HEAD)
IMAGE="gcr.io/${PROJECT}/${SERVICE_NAME}"
TEMPLATE="gs://${PROJECT}-dataflow/templates/${SERVICE_NAME}-template"
REGION="us-central1"

echo "PROJECT: ${PROJECT}"
echo "NAME: ${NAME}"
echo "IMAGE: ${IMAGE}"
echo "TEMPLATE: ${TEMPLATE}"
echo "REGION: ${REGION}"

# ------------------------------------------------------------------------------
# Pre-Terraform Actions
# ------------------------------------------------------------------------------

# Placeholder for pre-Terraform actions -Sly 10/18/2024

# ------------------------------------------------------------------------------
# Terraform Actions
# ------------------------------------------------------------------------------

echo "Running Terraform..."

# IF THIS IS THE FIRST TIME YOU'VE RUN THIS, DO NOT MIGRATE CONFIG.
# USE THE RECONFIGURE OPTION TO CREATE THE NEW SPACE OR YOU WILL BLOW UP ANOTHER PIPELINE'S CONFIG!
if ! terraform -chdir=./infrastructure init \
  -backend-config="bucket=ai-system-meigsy-gcp-terraform-state" \
  -backend-config="prefix=$SERVICE_NAME" \
  -var="project_id=$PROJECT" \
  -var="region=$REGION" \
  -var="pipeline_bucket_name=$PIPELINE_BUCKET_NAME"; then
  echo "Error: Terraform init failed."
  exit 1
fi

if ! terraform -chdir=./infrastructure apply \
  -var="project_id=$PROJECT" \
  -var="region=$REGION" \
  -var="pipeline_bucket_name=$PIPELINE_BUCKET_NAME"; then
  echo "Error: Terraform apply failed."
  exit 1
fi

# ------------------------------------------------------------------------------
# Post-Terraform Actions
# ------------------------------------------------------------------------------

echo "Building container -----------------------------"
gcloud builds submit --project "${PROJECT}" --substitutions _IMAGE_NAME=${IMAGE}:${SHA},_DOCKERFILE_PATH=Dockerfile --config cloudbuild.yaml . || true

echo "Tagging container -----------------------------"
yes | gcloud container images add-tag "${IMAGE}:${SHA}" "${IMAGE}:latest"

echo "Building flex template -----------------------------"
gcloud dataflow flex-template build "${TEMPLATE}" --project "${PROJECT}" --image "${IMAGE}" --sdk-language "PYTHON" --metadata-file "metadata.json"

echo "Deployment complete."
