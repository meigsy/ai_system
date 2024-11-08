#!/bin/sh -e

PROJECT="ai-system-meigsy-gcp"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format="value(projectNumber)")
REGION="us-central1"
BQ_LOCATION="US"

SERVICE_NAME="predictor_v1"  # snake_case (for everything except where kebab-case is mandatory)
SERVICE_NAME_KEBAB_CASE=$(echo "$SERVICE_NAME" | tr '_' '-')

# Service Account Names must be 6-30 characters, lowercase alphanumeric. If the name prevents this, you may need to use an abbreviation.
# DO NOT ABBREVIATE THE SERVICE NAME ITSELF. USE AN ABBREVIATION FOR THE SERVICE ACCOUNT NAME ONLY.
SERVICE_ACCOUNT_RUN="${SERVICE_NAME_KEBAB_CASE}-run"
SERVICE_ACCOUNT_CRON="${SERVICE_NAME_KEBAB_CASE}-cron"  # must be 6-30 characters, lowercase alphanumeric
SERVICE_ACCOUNT_BEAM="${SERVICE_NAME_KEBAB_CASE}-beam"  # must be 6-30 characters, lowercase alphanumeric

PIPELINE_BUCKET_NAME="${SERVICE_NAME_KEBAB_CASE}-${PROJECT_NUMBER}"
BACKUP_BUCKET_NAME="backup-${PIPELINE_BUCKET_NAME}"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/${SERVICE_NAME_KEBAB_CASE}"
IMAGE_TAGGED="${IMAGE_NAME}:latest"
REBUILD=""

if [[ -z "${OPENAI_API_KEY}" ]]; then
  echo "Error: OPENAI_API_KEY is not set or is empty."
  exit 1
fi


usage() {
  echo "Usage: $0 -b t|f | --build t|f"
  echo "  -b, --build    Specify whether to rebuild the Docker image ('t' = yes, 'f' = no)"
  echo "  -h, --help     Display this help message"
  exit 1
}

# Parse command-line arguments
while [ $# -gt 0 ]; do
  case "$1" in
    -b|--build)
      if [ -n "$2" ] && echo "$2" | grep -iq '^[tfTF]$'; then
        case "$2" in
          t|T)
            REBUILD="yes"
            ;;
          f|F)
            REBUILD="no"
            ;;
        esac
        shift 2
      else
        echo "Error: Argument for $1 must be 't' or 'f'."
        usage
      fi
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Error: Unknown option: $1"
      usage
      ;;
  esac
done

# Check if REBUILD was set; if not, show usage and exit
if [ -z "$REBUILD" ]; then
  echo "Error: The -b or --build flag with 't' or 'f' is required."
  usage
fi

# ------------------------------------------------------------------------------
# Pre-Terraform Actions
# ------------------------------------------------------------------------------

if [ "$REBUILD" = "yes" ]; then
  echo "Building Docker image..."
  if ! gcloud builds submit --tag "$IMAGE_TAGGED" ./src --project="$PROJECT"; then
    echo "Error: Docker image build failed."
    exit 1
  fi
else
  echo "Skipping Docker image build."
fi

# Get the image digest
echo "Getting image digest..."
DIGEST=$(gcloud artifacts docker images describe "$IMAGE_TAGGED" --format='get(image_summary.digest)')

if [ -z "$DIGEST" ]; then
  echo "Error: Failed to retrieve image digest. Ensure the image exists."
  exit 1
fi

IMAGE="${IMAGE_NAME}@${DIGEST}"

echo "Using image: $IMAGE"

# ------------------------------------------------------------------------------
# Terraform Actions
# ------------------------------------------------------------------------------

echo "Running Terraform..."

# Initialize Terraform
if ! terraform -chdir=./infrastructure init \
  -backend-config="bucket=ai-system-meigsy-gcp-terraform-state" \
  -backend-config="prefix=$SERVICE_NAME" \
  -var="project_id=$PROJECT" \
  -var="region=$REGION" \
  -var="bq_location=$BQ_LOCATION" \
  -var="service_name=$SERVICE_NAME" \
  -var="service_name_kebab_case=$SERVICE_NAME_KEBAB_CASE" \
  -var="service_account_run=$SERVICE_ACCOUNT_RUN" \
  -var="service_account_cron=$SERVICE_ACCOUNT_CRON" \
  -var="service_account_beam=$SERVICE_ACCOUNT_BEAM" \
  -var="image=$IMAGE" \
  -var="pipeline_bucket_name=$PIPELINE_BUCKET_NAME" \
  -var="backup_bucket_name=$BACKUP_BUCKET_NAME" \
  -var="openai_api_key=$OPENAI_API_KEY"; then
  echo "Error: Terraform init failed."
  exit 1
fi

# Apply Terraform configuration
if ! terraform -chdir=./infrastructure apply \
  -var="project_id=$PROJECT" \
  -var="region=$REGION" \
  -var="bq_location=$BQ_LOCATION" \
  -var="service_name=$SERVICE_NAME" \
  -var="service_name_kebab_case=$SERVICE_NAME_KEBAB_CASE" \
  -var="service_account_run=$SERVICE_ACCOUNT_RUN" \
  -var="service_account_cron=$SERVICE_ACCOUNT_CRON" \
  -var="service_account_beam=$SERVICE_ACCOUNT_BEAM" \
  -var="image=$IMAGE" \
  -var="pipeline_bucket_name=$PIPELINE_BUCKET_NAME" \
  -var="backup_bucket_name=$BACKUP_BUCKET_NAME" \
  -var="openai_api_key=$OPENAI_API_KEY"; then
  echo "Error: Terraform apply failed."
  exit 1
fi

# ------------------------------------------------------------------------------
# Post-Terraform Actions
# ------------------------------------------------------------------------------

# Placeholder for post-Terraform actions -Sly 10/17/2024

echo "Deployment complete."
