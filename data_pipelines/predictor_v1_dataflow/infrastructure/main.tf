terraform {
  backend "gcs" {}
}

# -------------------------------------------------------------------------
# General Bucket Config
# -------------------------------------------------------------------------

resource "google_storage_bucket" "pipeline_bucket" {
  project  = var.project_id
  location = var.region
  name     = var.pipeline_bucket_name
}
