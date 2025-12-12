import os
import json
import sys
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

def upload_documents():
    # Prefer Project Number if available to avoid RESOURCE_PROJECT_INVALID errors
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_NUMBER") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
    data_store_id = os.environ.get("DATA_STORE_ID")
    input_file = "data/organization_data_discovery_engine.json"

    if not all([project_id, data_store_id]):
        print("Error: GOOGLE_CLOUD_PROJECT and DATA_STORE_ID must be set.")
        sys.exit(1)

    print(f"Uploading to Project: {project_id}, Location: {location}, Data Store: {data_store_id}")

    #  For Vertex AI Search, the location is usually 'global' or specific regions.
    #  The endpoint might need to be configured if it's not global.
    client_options = None
    if location != "global":
        api_endpoint = f"{location}-discoveryengine.googleapis.com"
        client_options = ClientOptions(api_endpoint=api_endpoint)

    client = discoveryengine.DocumentServiceClient(client_options=client_options)
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch",
    )
    print(f"Using parent path: {parent}")

    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        sys.exit(1)

    print(f"Found {len(lines)} documents to upload.")

    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        doc_data = json.loads(line)
        doc_id = doc_data.get("id")
        
        # Remove 'id' from the body as it's passed separately in the request usually, 
        # but the Document object also has an 'id' field.
        
        document = discoveryengine.Document(
            id=doc_id,
            struct_data=doc_data.get("structData"),
            content=doc_data.get("content"), # In case we have content
        )

        # CreateDocument approach
        # document.name is not required for CreateDocument, but document_id is.
        # We don't set document.name here.
        
        request = discoveryengine.CreateDocumentRequest(
            parent=parent,
            document=document,
            document_id=doc_id
        )

        try:
            client.create_document(request=request)
            print(f"[{i+1}/{len(lines)}] Created document: {doc_id}")
        except Exception as e:
            if "ALREADY_EXISTS" in str(e):
                print(f"[{i+1}/{len(lines)}] Document {doc_id} already exists. Updating...")
                # Fallback to update if it exists
                document.name = f"{parent}/documents/{doc_id}"
                update_request = discoveryengine.UpdateDocumentRequest(
                    document=document,
                    allow_missing=True
                )
                client.update_document(request=update_request)
                print(f"[{i+1}/{len(lines)}] Updated document: {doc_id}")
            else:
                print(f"Error uploading document {doc_id}: {e}")

if __name__ == "__main__":
    upload_documents()
