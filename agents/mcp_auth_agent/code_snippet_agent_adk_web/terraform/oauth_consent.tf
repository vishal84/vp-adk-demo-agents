# Get Project Info (needed for Project Number if brand exists)
data "google_project" "project" {
  project_id = var.gcp_project_id
}

# 1. Enable IAP API
resource "google_project_service" "iap_api" {
  project            = var.gcp_project_id
  service            = "iap.googleapis.com"
  disable_on_destroy = false
}

# 2. Create Brand (Only if create_brand is true)
resource "google_iap_brand" "project_brand" {
  count = var.create_brand ? 1 : 0

  support_email     = var.username
  application_title = var.oauth_application_title
  project           = var.gcp_project_id

  depends_on = [google_project_service.iap_api]
}

# 3. Create Client (Links to new Brand OR existing Brand ID)
resource "google_iap_client" "project_client" {
  display_name = "Code Snippet Agent Client"

  # Logic:
  # If we created a brand, use its name.
  # If not, construct the ID: projects/[number]/brands/[number]
  brand = var.create_brand ? google_iap_brand.project_brand[0].name : "projects/${data.google_project.project.number}/brands/${data.google_project.project.number}"

  depends_on = [google_project_service.iap_api]
}
