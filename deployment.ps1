az cloud set --name AzureUSGovernment
Az login
az account set -s "<subscription name>"

az functionapp config appsettings set --name MyFunctionApp --resource-group MyResourceGroup --settings "OCR_SUBSCRIPTION_KEY=<your key>"

az cloud set --name AzureUSGovernment
Az login
az account set -s "Azure CXP FTA Internal Subscription FRGAROFA (GOV)"

az functionapp config appsettings set --name ftagov-funcations --resource-group ftagov-cogsearch --settings "OCR_SUBSCRIPTION_KEY=ece422658f8b4cdd80f45d4aec0865f8"
az functionapp config appsettings set --name ftagov-funcations --resource-group ftagov-cogsearch --settings "OCR_ENDPOINT=https://ftagov-vision.cognitiveservices.azure.us"