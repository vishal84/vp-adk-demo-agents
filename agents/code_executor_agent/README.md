# Code Executor Agent

To use this agent, you will need to first run the agent via adk web locally. This will create a Code Executor Vertex AI Extension in the GCP project the agent will be deployed to. On the first deploy locally you will see that the agent does not detect the Code Executor extension and will create one automatically for you in the project referenced in the `.env` file.

After running `adk web` locally to deploy the agent, go to the Vertex AI Extensions page in your project:
[Vertex AI Extensions](https://console.cloud.google.com/vertex-ai/extensions) to copy the ID of the Extension.

Once copied, add the Code Extension ID to the `.env` file for `CODE_INTERPRETER_EXTENSION_NAME`.

## Add IAM Role for utilizing the Extension

At the time of writing this sample, Vertex AI Extensions is in preview. You will require adding a custom IAM Role to the service account used to run Agent Engine agents in order for the agent to retrieve the Code Executor extension.

To do so, in the GCP console navigate to:

1. __IAM & Admin__ > __Roles__.

2. Click __Create role__ at the top of the screen.

3. Enter the following information for the custom role:

- Title: AI Platform Extension User (Custom)
- ID: AIPlatformExtensionUserCustom
- Role Launch Stage: General Availability

Click __+ Add Permissions__ and add the following permissions:
- aiplatform.extensions.delete
- aiplatform.extensions.execute
- aiplatform.extensions.get
- aiplatform.extensions.import
- aiplatform.extensions.list
- aiplatform.extensions.update

4. Once the permissions have been added click __Create__.

It will take a few minutes for the Role creation to propagage before you can assign it to the service account used by Agent Engine in the next step.

5. After creating, the custom role navigate to __IAM & Admin__ > __IAM__ in the GCP console.

6. Select the `Include Google-provided role grants` checkbox at the top right of the screen.

7. Find the `service-[GCP PROJECT NUMBER]@gcp-sa-aiplatform-re.iam.gserviceaccount.com` service account in the list and select the __Edit pencil__ on the right hand side of the screen to apply the custom Role created in the last step to the service account.

8. Select __+ Add another role__ then select __Custom__ under the quick filters. Select the custom IAM Role created earlier then click __Save__.


