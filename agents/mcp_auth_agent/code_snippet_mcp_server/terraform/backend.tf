terraform {
  backend "gcs" {
    bucket = "gsi-gemini-ent-tfstate"
    prefix = "code_snippet_mcp_server" # folder under bucket for workload..
  }
}
