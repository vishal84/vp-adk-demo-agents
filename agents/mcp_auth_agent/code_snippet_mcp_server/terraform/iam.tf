# add roles needed to default compute engine 
# service account to run cloud build jobs
# resource "google_project_iam_member" "compute_sa_roles" {
#   for_each = toset(local.compute_sa_roles)

#   project = var.gcp_project_id
#   role    = each.value
#   member  = "serviceAccount:${local.compute_sa}"
# }

# add role manually with gcloud using below
# gcloud projects add-iam-policy-binding gsi-gemini-ent \
#   --member="serviceAccount:64898369892-compute@developer.gserviceaccount.com" \
#   --role="roles/artifactregistry.admin"

# gcloud projects add-iam-policy-binding gsi-gemini-ent \
#   --member="serviceAccount:64898369892-compute@developer.gserviceaccount.com" \
#   --role="roles/run.admin"

# gcloud projects add-iam-policy-binding gsi-gemini-ent \
#   --member="serviceAccount:64898369892-compute@developer.gserviceaccount.com" \
#   --role="roles/logging.logWriter"

# gcloud projects add-iam-policy-binding gsi-gemini-ent \
#   --member="serviceAccount:64898369892-compute@developer.gserviceaccount.com" \
#   --role="roles/iam.serviceAccountUser"

# gcloud projects add-iam-policy-binding gsi-gemini-ent \
#   --member="serviceAccount:64898369892-compute@developer.gserviceaccount.com" \
#   --role="roles/serviceusage.serviceUsageConsumer"

# gcloud projects add-iam-policy-binding gsi-gemini-ent \
#   --member="serviceAccount:64898369892-compute@developer.gserviceaccount.com" \
#   --role="roles/storage.admin"
