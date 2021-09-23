#This is a PowerShell Helper File to deploy your Cog Search Index, Data Source, Indexer, Skill Set
#When working with Cog Search via Private Endpoints you will need to mange the service and indexes via Rest, PowerShell, Azure CLI
#The below has examples for deploying and working with Cog Search


#Set Univerisal Params to be used with Rest API calls 
#These will be used to create and update Cog Search Index, Data Sources, Indexer and Skillset

#API OPTIONS:  2020-06-30, 2021-04-01-preview
$serviceName    = "<Enter Cog Search Service Name>"
$indexName      = "<Enter Name for Index>"
$queryKey       = "<Enter Cog Search Query Key>"
$adminKey       = "<Enter Cog Search Admin Key>"
$apiVersion     = "2020-06-30"
$baseURI        = ".search.azure.us/"
$contentType    = "application/json"


#Step 1 - Create a data source (https://docs.microsoft.com/en-us/azure/search/search-howto-indexing-azure-blob-storage)
$api                    = "datasources"
$uri                    = "https://$($serviceName)$($baseURI)$($api)?api-version=$($apiVersion)"
$storageAccountName     = "<Enter Name of Storage Account>"
$storageAccountKey      = "<Enter Storage Account Key>"
$dataSourceName         = "<Enter Name for Data Source>"
$container              = "<Enter Name of Container for Data Source>"
$directory              = "<Enter Directory Name if using one, else leave blank>"

$body = @"
 {
    "name" : "$dataSourceName",
    "type" : "azureblob",
    "credentials" : { "connectionString" : "DefaultEndpointsProtocol=https;AccountName=$($storageAccountName);AccountKey=$($storageAccountKey);EndpointSuffix=core.usgovcloudapi.net;" },
    "container" : { "name" : "$container", "query" : "$directory" }
 }
"@

$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'POST'
    Body        = $body
    URI         = $uri
    Verbose    = $true
}
Invoke-WebRequest @parms 


#To Pull lest of Current Data Sources
$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'Get'
    URI         = $uri
    Verbose    = $true
}
$results = Invoke-WebRequest @parms 
$dataSource = ($results.Content | convertfrom-json | Select-object).value 
$dataSource.name


#Step 2 Create Index (https://docs.microsoft.com/en-us/rest/api/searchservice/create-index)
#Use Post to Create a New Index, Use Put to Update the current index

$api            = "indexes"
$uri            = "https://$($serviceName)$($baseURI)$($api)?api-version=$($apiVersion)"
$contentType    = "application/json"
$index          = (Get-Content '.\CogSearch\index.json' -Raw).Replace("index-name", $indexName) 

#Create Index
$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'POST'
    Body        = $index
    URI         = $uri
    Verbose    = $true}
Invoke-WebRequest @parms 

#If you need to update an index run the below.
#Some fields can't be changed, you will need to delete and recreate the index
$api            = "indexes"
$index          = (Get-Content '.\REST - Scripts\CogSearch\index.json' -Raw).Replace("index-name", $indexName) 
$uri            = "https://$($serviceName)$($baseURI)$($api)/$($indexName)?api-version=$($apiVersion)"
$contentType    = "application/json"

$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'PUT'
    Body        = $index
    URI         = $uri
    Verbose    = $true}
Invoke-WebRequest @parms 

#Delete Index if needing to update schema or settings
$api            = "indexes"
$uri            = "https://$($serviceName)$($baseURI)$($api)/$($indexName)?api-version=$($apiVersion)"
$contentType    = "application/json"

$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'DELETE'
    URI         = $uri
    Verbose    = $true}
Invoke-WebRequest @parms 

#To Get List of Indexes
$api            = "indexes"
$uri            = "https://$($serviceName)$($baseURI)$($api)?api-version=$($apiVersion)"
$contentType    = "application/json"

$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'GET'
    URI         = $uri
    Verbose    = $true}
$results = Invoke-WebRequest @parms 
$indexes = ($results.Content | convertfrom-json | Select-object).value 
$indexes.name

#Get Index Detials:
$api            = "indexes"
$uri            = "https://$($serviceName)$($baseURI)$($api)/$($indexName)?api-version=$($apiVersion)"
$contentType    = "application/json"
$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'GET'
    URI         = $uri
    Verbose    = $true}
$results = Invoke-WebRequest @parms 
$index = ($results.Content | convertfrom-json)


#Step 3: Create an skillset (https://docs.microsoft.com/en-us/rest/api/searchservice/create-skillset)
#schedule Optional, but runs once immediately if unspecified.
$api                = "skillsets"
$apiVersion         = "2020-06-30"
$skillsetName       = "<Enter Skill Set Name>"
#URI for Custom Skill endpoint for Vision API example:  https://demo-funcations.azurewebsites.us/api/ocrcustomwebskill
$funcationEndpoint  = "<Enter Endpoint for Custom SKill funcation API>"  
#KnowledgeStore Settings for Storage Account if using a KB
$StorageAccountName = "<Enter Storage Account Name if using a knowledge store else blank>"
$StorageAccountKey  = "<Enter Storage Account Key if using a knowledge store else blank>"
$cogKey             = "<Enter Cog Service Key if useing Cog Service, else leave blank>"
$endPoint           = "core.usgovcloudapi.net"

#Get SkillSet JASON
$jsonFile            = "skillset-customskillsNoKB.json"
$skillset           = (Get-Content ".\CogSearch\$jsonFile" -Raw).Replace("skillset-name-z", $skillsetname).Replace("storeageaccount-z", "$storageAccountName").Replace("storeagKey-z", "$storageAccountKey").Replace("storeEndpoint-z", "$endPoint").Replace("skillset-custuri-z","$funcationEndpoint")
$uri                = "https://$($serviceName)$($baseURI)$($api)/$($skillsetName)?api-version=$($apiVersion)"

$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'PUT'
    Body        = $skillset
    URI         = $uri
    Verbose    = $true}
Invoke-WebRequest @parms 



#Step 4: Create/Update an indexer (https://docs.microsoft.com/en-us/rest/api/searchservice/create-indexer)
#schedule Optional, but runs once immediately if unspecified.

$api                = "indexers"
$apiVersion         = "2020-06-30"
$indexerName        = "<Enter Indexer Name>"
$dataSourceName     = "<Enter Data Source Name Created in Step 1>"
$skillsetName       = "<Enter Skill Set Name>"
$targetIndex        = "<Enter Index Name>"
#Storage Cache Setup
#https://docs.microsoft.com/en-us/azure/search/cognitive-search-incremental-indexing-conceptual?WT.mc_id=Portal-Microsoft_Azure_Search
$storageAccountName = "<Enter Storage Account Name>"

$endPoint           = "core.usgovcloudapi.net"
$indexerBody        = (Get-Content '.\CogSearch\indexer.json' -Raw).Replace("azureblob-indexer-z", $indexerName).Replace("dataSourceName-z", "$dataSourceName").Replace("skillset-name-z",$skillsetName).Replace("index-name-z",$targetIndex).Replace("storeageaccount-z", "$storageAccountName").Replace("storeagKey-z", "$storageAccountKey").Replace("storeEndpoint-z", "$endPoint")
$uri                = "https://$($serviceName)$($baseURI)$($api)/$($indexerName)?api-version=$($apiVersion)"


$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'PUT'
    Body        = $indexerBody
    URI         = $uri
    Verbose    = $true}
Invoke-WebRequest @parms 


#Reset indexer if you update index or schemas or skillset mapping
    $api                = "indexers"
    $indexerName        = "<Ender Indexer Name>"
    $uri                = "https://$($serviceName)$($baseURI)$($api)/$($indexerName)/reset?api-version=$($apiVersion)"
$parms = @{
        ContentType = $contentType
        Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
        Method      = 'POST'
        URI         = $uri
        Verbose    = $true}
    Invoke-WebRequest @parms 

#Run indexer after reset or updated data sources (Used to kick off Indexer Job)
$api                = "indexers"
$indexerName        = "<Enter Indexer Name>"
$uri                = "https://$($serviceName)$($baseURI)$($api)/$($indexerName)/run?api-version=$($apiVersion)"
$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'POST'
    URI         = $uri
    Verbose    = $true}
Invoke-WebRequest @parms 


#Get Status of Indexer
$api                = "indexers"
$indexerName        = "<Enter Indexer Name>"
$uri                = "https://$($serviceName)$($baseURI)$($api)/$($indexerName)/status?api-version=$($apiVersion)"
$parms = @{
    ContentType = $contentType
    Headers     = @{'Content-Type' = $contentType; 'api-key' = $adminKey}
    Method      = 'GET'
    URI         = $uri
    Verbose    = $true}
$status = Invoke-WebRequest @parms 
($status.Content | ConvertFrom-Json)

($status.Content | ConvertFrom-Json).lastResult
($status.Content | ConvertFrom-Json).lastResult.errors