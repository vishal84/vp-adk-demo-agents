terraform {
  backend "gcs" {
    bucket = "gsi-gemini-ent-tfstate"
    prefix = "code_snippet_agent_adk_web"
  }
}
