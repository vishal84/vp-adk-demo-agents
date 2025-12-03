# Creating a service account
resource "google_service_account" "code_snippet_agent_sa" {
  account_id   = var.service_account_name
  display_name = var.service_account_display_name
  project      = var.gcp_project_id
}

# Granting the role of Cloud Run Invoker to the service account
resource "google_project_iam_member" "run_invoker" {
  project = var.gcp_project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.code_snippet_agent_sa.email}"
}

# Granting the role of Logs Writer to the service account
resource "google_project_iam_member" "writer" {
  project = var.gcp_project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.code_snippet_agent_sa.email}"
}

# Granting the user the ability to impersonate the service account
resource "google_service_account_iam_member" "token_creator" {
  service_account_id = google_service_account.code_snippet_agent_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "user:${var.username}"
}
