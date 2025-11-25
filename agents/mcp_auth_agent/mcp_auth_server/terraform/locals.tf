# The image name, which we will build and push manually.
locals {
  image_name = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.repo.repository_id}/${var.service_name}:latest"
}
