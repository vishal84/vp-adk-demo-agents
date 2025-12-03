# Output the URL of the deployed service
output "service_url" {
  value = google_cloud_run_v2_service.mcp_server.uri
}
