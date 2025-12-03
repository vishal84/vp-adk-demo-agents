output "code_snippet_agent_service_account_email" {
  description = "The email of the service account created for the code snippet agent."
  value       = google_service_account.code_snippet_agent_sa.email
}

output "oauth_client_id" {
  description = "The OAuth 2.0 Client ID"
  value       = google_iap_client.project_client.client_id
}

output "oauth_client_secret" {
  description = "The OAuth 2.0 Client Secret"
  value       = google_iap_client.project_client.secret
  sensitive   = false
}
