output "code_snippet_agent_service_account_email" {
  description = "The email of the service account created for the code snippet agent."
  value       = google_service_account.code_snippet_agent_sa.email
}

