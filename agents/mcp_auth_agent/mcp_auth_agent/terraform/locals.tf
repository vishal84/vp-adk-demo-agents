# data source to get the project number for service account reference
data "google_project" "project" {
  project_id = var.gcp_project_id
}

locals {

}
