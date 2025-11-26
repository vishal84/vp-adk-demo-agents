# 1. Enable necessary APIs
resource "google_project_service" "enable_apis" {
  for_each = toset(var.api_services)

  project = var.gcp_project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}
