terraform {
  backend "gcs" {
    bucket = "gsi-gemini-ent-tfstate"
    prefix = "mcp_auth_server" # folder under bucket for workload..
  }
}
