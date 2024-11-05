resource "google_cloud_scheduler_job" "predictor_job" {
  name        = var.service_name
  project     = var.project_id
  region      = var.region
  description = "${var.service_name}"
  schedule    = "0 2-23/4 * * *"
  time_zone   = "Etc/UTC"

  http_target {
    uri         = "${google_cloud_run_service.cloud_run_app.status[0].url}/predict"
    http_method = "POST"
    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(jsonencode({
      limit = 2000
    }))

    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }

  attempt_deadline = "1800s" # 30 minutes
  paused = true
}