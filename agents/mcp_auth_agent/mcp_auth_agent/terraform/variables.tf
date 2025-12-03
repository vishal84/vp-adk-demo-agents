variable "gcp_project_id" {
  description = "The GCP project ID."
}

variable "gcp_region" {
  description = "The GCP region."
}

variable "username" {
  description = "The GCP user in the project who can impersonate the service account TF creates toinvoke the Cloud Run service."
}

variable "service_name" {
  description = "The name of the Cloud Run service."
}
