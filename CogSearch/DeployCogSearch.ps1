Login-AzAccount -Environment AzureUSGovernment


#Deploy Cog Search
#Ref:   https://docs.microsoft.com/en-us/powershell/module/az.search/new-azsearchservice?view=azps-6.0.0
#       https://docs.microsoft.com/en-us/azure/search/search-manage-powershell
#       https://docs.microsoft.com/en-us/azure/search/search-sku-tier#billing-rates

#The Below can be used to depoy Cog Search Via Powershell



#If you need to use Private Endpoints with Cognitive Search you need to deploy a min sku of: Standard2

$params = @{
    ResourceGroupName   = '<Enter Resource Group Name>'
    Name                = '<Enter Name for Cog Search Service>'
    Sku                 = 'Standard2'
    Location            = "usgovvirginia"
    PartitionCount      = 4
    ReplicaCount        = 1
    HostingMode         = 'Default'
    Verbose             = $true
}

#Can be used to deploy a new search Service
$result = New-AzSearchService  @params

#Get Admin Keys
$result | Get-AzSearchAdminKeyPair 

#Get Query Keys
$result | Get-AzSearchQueryKey
