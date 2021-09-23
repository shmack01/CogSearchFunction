## Deploy Cognitive Search Service and Components for your Index
The scripts in this repo can be used to deploy Cognitive Search, create shared private endpoints, and also all the components of an index(s)

### Deploy Cognitive Services with Powershell:
</br>

To deploy Cog Search with PowerShell see file: [DeployCogSearch.ps1](/CogSearch/DeployCogSearch.ps1)
The script has comments included.  You will need to update the parameter values before running. 

### Add Shared Shared Private Access to your Cognitive Services
This is needed for all services that are setup with Private Endpoint Access.  Some Services can be setup with the portal others can not, like the function.

>For the function app use file: [DeploySharedPrivateEndpoint.azcli](/CogSearch/DeploySharedPrivateEndpoint.azcli)

<br/>
This sample script is written to run using BASH and you will need to update the values of the parameters along with a some values in file: create-pe.json
### Deploy your Index and components for the index
To deploy your data source, index, skillset, and indexer see file: [CogSearchHelper.ps1](/CogSearchHelper.ps1)
</br>
This file includes small scripts to broke up into 4 steps with notes on how to use each step. There are other helpful REST calls to get information about your index and status of indexers.  The PowerShell scripts use web requests using the Cognitive Search Rest API.  These are examples on how to use the REST API and can be included into a CI/CD process.

1.  Create Data Source - which is for your index using a storage account.  Make sure to update parameter values to match your services values
2.  Create Index -uses the index.json template for your indexes schema.  If you would like to add columns / fields to your index you will need to update the index.json file.  If changing the schema of your index, it will require you to drop the index and create a new one.  (there is an example API call in the file for this)
3.  Create Skillset - this uses the skillset-customskillsNoKB.json file for the core template of a skillset with a custom skill for the function endpoint to handle the OCR of a PDF. You do not need to modify the json file just set the parameter values to match your services. 
4.  Create/Update indexer - this API uses the indexer.json file, just like the other steps you do not need to modify the .json file just the parameter values

In order to work with Cog Search behind a private link connection you will need to use the Rest API(s).  There are examples and some notes in the about file to check on the status of the indexer, reset and rerun an indexer job and reference links to the MS Docs pages. 

## Turning on **Allow access from the Portal** in Azure Government cloud is currently not supported and will cause your cognitive services instance to become unstable and fail. At this time do not enable this feature from the portal until it is supported.

---

For additional reference information see: https://docs.microsoft.com/en-us/rest/api/searchservice/