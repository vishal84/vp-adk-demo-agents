# data source to get the project number for service account reference
data "google_project" "project" {
  project_id = var.gcp_project_id
}

locals {
  # Calculate hash of src directory and cloudbuild.yaml file, if either changes the build will update cloud run
  source_hash = sha1(join("", [for f in fileset("${path.module}/../src", "**") : filesha1("${path.module}/../src/${f}")], [filesha1("${path.module}/../cloudbuild.yaml")]))

  # Use the hash as the image tag. This ensures the image string changes when code changes.
  image_name = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.repo.repository_id}/${var.service_name}:${local.source_hash}"

  # add roles to default compute engine account needed to run cloud build jobs
  # compute_sa = "${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  # compute_sa_roles = [
  #   "roles/artifactregistry.admin",
  #   "roles/run.admin",
  #   "roles/logging.logWriter",
  #   "roles/iam.serviceAccountUser",
  #   "roles/serviceusage.serviceUsageConsumer",
  #   "roles/storage.admin"
  # ]
}
