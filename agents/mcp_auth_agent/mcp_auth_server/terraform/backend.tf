terraform {
  backend "gcs" {
    bucket = "${var.gcp_project_id}-tfstate" # The bucket you just created
    prefix = "mcp_auth_server"               # This creates the "folder" structure
  }
}
