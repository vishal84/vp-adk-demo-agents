# 2. Create an Artifact Registry repository to store the container image
resource "google_artifact_registry_repository" "repo" {
  project       = var.gcp_project_id
  location      = var.gcp_region
  repository_id = "${var.service_name}-repo"
  format        = "DOCKER"
  description   = "Docker repository for the Code Snippet MCP server."

  depends_on = [google_project_service.enable_apis]
}

# 3. Deploy the service to Cloud Run
resource "google_cloud_run_v2_service" "mcp_server" {
  project  = var.gcp_project_id
  name     = var.service_name
  location = var.gcp_region

  template {
    containers {
      image = local.image_name
      ports {
        container_port = 8080
      }
    }
  }

  depends_on = [
    google_project_service.enable_apis,
    google_artifact_registry_repository.repo
  ]
}

# 4. Apply IAM policy to the Cloud Run service to make it private
resource "google_cloud_run_service_iam_binding" "iam_invoker" {
  project  = google_cloud_run_v2_service.mcp_server.project
  location = google_cloud_run_v2_service.mcp_server.location
  service  = google_cloud_run_v2_service.mcp_server.name
  role     = "roles/run.invoker"
  members = [
    "user:${var.username}"
  ]
}

# Output the URL of the deployed service
output "service_url" {
  value = google_cloud_run_v2_service.mcp_server.uri
}
