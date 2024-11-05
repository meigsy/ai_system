resource "google_cloud_scheduler_job" "table_snapshot_job" {
  name        = "${var.service_name}_table_snapshot"
  project     = var.project_id
  region      = var.region
  description = "${var.service_name}"
  schedule = "0 2 * * 0"
  time_zone   = "Etc/UTC"

  http_target {
    uri         = "${google_cloud_run_service.cloud_run_app.status[0].url}/table_snapshot"
    http_method = "POST"
    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(jsonencode({}))

    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }

  attempt_deadline = "1800s" # 30 minutes
  paused = false
}