# 2. Create an Artifact Registry repository to store the container image
resource "google_artifact_registry_repository" "repo" {
  project       = var.gcp_project_id
  location      = var.gcp_region
  repository_id = "${var.service_name}-repo"
  format        = "DOCKER"
  description   = "Docker repository for the Code Snippet MCP server."

  depends_on = [google_project_service.enable_apis]
}

# Trigger Cloud Build to build and push the image
resource "null_resource" "build_and_push_image" {
  triggers = {
    # Re-run if the source code or cloudbuild.yaml changes
    src_hash = local.source_hash
  }

  provisioner "local-exec" {
    working_dir = "${path.module}/.."
    # Pass the calculated hash as the BUILD_ID substitution to Cloud Build
    command = <<EOT
      gcloud builds submit \
        --config=cloudbuild.yaml \
        --project=${var.gcp_project_id} \
        --region=${var.gcp_region} \
        --substitutions=_REGION=${var.gcp_region},_REPO_NAME=${google_artifact_registry_repository.repo.repository_id},_SERVICE_NAME=${var.service_name},_BUILD_ID=${local.source_hash}
    EOT
  }

  depends_on = [google_artifact_registry_repository.repo]
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
    google_artifact_registry_repository.repo,
    null_resource.build_and_push_image
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

