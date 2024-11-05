variable "project_id" {
  description = "GCP Project ID"
  type        = string

  validation {
    condition     = length(var.project_id) > 0
    error_message = "The project_id variable cannot be empty. Please provide a valid GCP Project ID."
  }
}

variable "region" {
  description = "Region for services like Cloud Run, Cloud Functions, etc."
  type        = string

  validation {
    condition     = length(var.region) > 0
    error_message = "The region variable cannot be empty. Please provide a valid region."
  }
}

variable "pipeline_bucket_name" {
  description = "The name of the GCS bucket used for general storage"
  type        = string

  validation {
    condition     = length(var.pipeline_bucket_name) > 0
    error_message = "The pipeline_bucket_name variable cannot be empty. Please provide a valid GCS bucket name."
  }
}