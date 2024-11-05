# ---------------------------------------------------------------------------
# Create the GCP Project
# ---------------------------------------------------------------------------

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project" "ai_system_project" {
  name            = "AI System"
  project_id      = var.project_id
  billing_account = var.billing_account

  lifecycle {
    prevent_destroy = true
  }
}

data "google_project" "project" {
  project_id = var.project_id
}

# ---------------------------------------------------------------------------
# Enable Google APIs
# ---------------------------------------------------------------------------

resource "google_project_service" "enable_cloud_build" {
  project = var.project_id
  service = "cloudbuild.googleapis.com"
}

resource "google_project_service" "enable_artifact_registry" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
}

resource "google_project_service" "enable_bigquery" {
  project = var.project_id
  service = "bigquery.googleapis.com"
}

resource "google_project_service" "enable_cloud_run" {
  project = var.project_id
  service = "run.googleapis.com"
}

resource "google_project_service" "compute_engine_api" {
  project = var.project_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "enable_cloud_scheduler" {
  project = var.project_id
  service = "cloudscheduler.googleapis.com"
}

resource "google_project_service" "enable_dataflow" {
  project = var.project_id
  service = "dataflow.googleapis.com"
}

# ---------------------------------------------------------------------------
# Setup Services
# ---------------------------------------------------------------------------

resource "google_artifact_registry_repository" "cloud_run_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = "cloud-run-source-deploy"
  format        = "DOCKER"

  depends_on = [
    google_project_service.enable_artifact_registry
  ]
}

# ---------------------------------------------------------------------------
# Setup Project Level IAM
# ---------------------------------------------------------------------------

resource "google_project_iam_member" "compute_engine_default_artifact_registry_writer" {
  project = google_project.ai_system_project.project_id
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  role    = "roles/artifactregistry.writer"  # Allows uploading to Artifact Registry
}

resource "google_project_iam_member" "compute_engine_default_cloud_build_service_agent" {
  project = google_project.ai_system_project.project_id
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  role    = "roles/cloudbuild.builds.builder"  # Enables Cloud Build operations
}

resource "google_project_iam_member" "compute_engine_default_storage_access_list" {
  project = google_project.ai_system_project.project_id
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  role    = "roles/storage.objectViewer"
}

# Add storage permissions to the Cloud Build service account
resource "google_project_iam_member" "cloud_build_storage_permissions" {
  project = google_project.ai_system_project.project_id
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  role    = "roles/storage.objectAdmin"  # Allows access to storage objects (get, create, update, delete)
}

# Grant Storage Object Viewer (read) permission to Cloud Build service account
resource "google_project_iam_member" "cloud_build_storage_object_viewer" {
  project = google_project.ai_system_project.project_id
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  role    = "roles/storage.objectViewer"  # Allows read access to objects in GCS
}

# Grant Storage Object Creator (write) permission to Cloud Build service account
resource "google_project_iam_member" "cloud_build_storage_object_creator" {
  project = google_project.ai_system_project.project_id
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  role    = "roles/storage.objectCreator"  # Allows write access to objects in GCS
}


# Grant BigQuery job creation permission to the service account
resource "google_project_iam_binding" "bigquery_job_user" {
  project = var.project_id

  role = "roles/bigquery.jobUser"

  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  ]
}

# Grant BigQuery read permission to the Dataflow worker service account
resource "google_project_iam_binding" "bigquery_data_viewer" {
  project = var.project_id

  role = "roles/bigquery.dataViewer"

  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  ]
}

# Grant BigQuery dataEditor permission to the Dataflow worker service account for writing data to BigQuery
resource "google_project_iam_binding" "bigquery_data_editor" {
  project = var.project_id

  role = "roles/bigquery.dataEditor"

  members = [
    "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  ]
}

# adding this here to allow default compute to deploy dataflow jobs for now because the cloud run apps are using it.
resource "google_project_iam_member" "default_compute_sa_dataflow_developer" {
  project = var.project_id
  role    = "roles/dataflow.developer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}


# -------------------------------------------------------------------------
# Dataflow Bucket Config
# -------------------------------------------------------------------------

resource "google_storage_bucket" "dataflow_templates" {
  project  = var.project_id
  location = var.region
  name     = "${var.project_id}-dataflow"
}


# ---------------------------------------------------------------------------
# Terraform state
# ---------------------------------------------------------------------------

resource "google_storage_bucket" "state_bucket" {
  name     = "${var.project_id}-terraform-state"
  location = "US"
  project  = var.project_id

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

terraform {
  backend "gcs" {}
}