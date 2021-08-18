az cloud set --name AzureUSGovernment
Az login
az account set -s "<subscription name>"

az functionapp config appsettings set --name MyFunctionApp --resource-group MyResourceGroup --settings "OCR_SUBSCRIPTION_KEY=<your key>"
