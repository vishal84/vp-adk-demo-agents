variable "gcp_project_id" {
  description = "The GCP project ID."
}

variable "gcp_region" {
  description = "The GCP region."
}

variable "username" {
  description = "The GCP user in the project who can impersonate the service account TF creates toinvoke the Cloud Run service."
}

variable "service_account_name" {
  description = "The name of the service account to be created."
}

variable "service_account_display_name" {
  description = "The display name of the service account to be created."
}

variable "service_name" {
  description = "The name of the Cloud Run service."
}

output "code_snippet_agent_service_account_email" {
  description = "The email of the service account created for the code snippet agent."
  value       = google_service_account.code_snippet_agent_sa.email
}
