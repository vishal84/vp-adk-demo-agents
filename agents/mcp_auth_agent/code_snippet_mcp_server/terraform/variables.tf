variable "gcp_project_id" {
  description = "The GCP project ID."
}

variable "gcp_region" {
  description = "The GCP region."
}

variable "username" {
  description = "The GCP user in the project who can invoke the Cloud Run service."
}

variable "api_services" {
  type = list(string)
  default = [
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com"
  ]
}

variable "service_name" {
  description = "The name of the Cloud Run service."
}

variable "image_tag" {
  description = "Docker image tag for deployment (unique per build)."
  type        = string
  default     = "latest"
}
