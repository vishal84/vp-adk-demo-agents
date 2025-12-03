# Creating a service account
resource "google_service_account" "service_account" {
  account_id   = var.service_account_name
  display_name = var.service_account_display_name
  project      = var.gcp_project_id
}

# Granting the role of Cloud Run Invoker to the service account
resource "google_project_iam_member" "invoker" {
  project = var.gcp_project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.service_account.email}"
}

# Granting the role of Logs Writer to the service account
resource "google_project_iam_member" "writer" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.service_account.email}"
}
