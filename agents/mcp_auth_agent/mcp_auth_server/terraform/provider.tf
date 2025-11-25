terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.40"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}
