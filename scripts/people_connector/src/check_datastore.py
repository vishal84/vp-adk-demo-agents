import os
from google.cloud import discoveryengine_v1 as discoveryengine

def list_data_stores():
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("GOOGLE_CLOUD_PROJECT not set")
        return

    print(f"Checking Data Stores in project: {project_id}")
    
    locations = ["global", "us", "eu", "us-central1"]
    
    found = False
    for location in locations:
        print(f"Checking location: {location}")
        try:
            client = discoveryengine.DataStoreServiceClient()
            parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
            # Note: ListDataStoresRequest requires parent to be collection
            
            # We need to set the API endpoint for non-global
            client_options = None
            if location != "global":
                api_endpoint = f"{location}-discoveryengine.googleapis.com"
                # For us-central1, it might be us-central1-discoveryengine.googleapis.com or just discoveryengine.googleapis.com?
                # Actually, regional endpoints are usually region-discoveryengine.googleapis.com
                # But let's try.
                from google.api_core.client_options import ClientOptions
                client_options = ClientOptions(api_endpoint=api_endpoint)
                client = discoveryengine.DataStoreServiceClient(client_options=client_options)

            request = discoveryengine.ListDataStoresRequest(parent=parent)
            page_result = client.list_data_stores(request=request)
            
            for ds in page_result:
                print(f"Found Data Store: {ds.name}")
                print(f"  ID: {ds.name.split('/')[-1]}")
                print(f"  DisplayName: {ds.display_name}")
                found = True
        except Exception as e:
            print(f"  Error checking {location}: {e}")

    if not found:
        print("No Data Stores found in checked locations.")

if __name__ == "__main__":
    list_data_stores()
