terraform {
  backend "gcs" {
    bucket = "gsi-gemini-ent-tfstate" # The bucket you just created
    prefix = "mcp_auth_server"        # This creates the "folder" structure
  }
}
