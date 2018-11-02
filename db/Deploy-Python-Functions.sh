#!/bin/bash

#Automation based from instructions hre: https://github.com/Azure/Azure-Functions/wiki/Azure-Functions-on-Linux-Preview

#Exit on error
set -e

ResourceGroup=$1
StorageName=$2
FunctionAppName=$3
AppInsightsName=$4

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
    echo "Usage: 'sh $0 (Azure Resource Group Name) (Azure Function Storage Name) (Azure Function App Name) (AppInsightsName)'"
    exit 1
fi

StorageNameLength=${#StorageName}
if [ $StorageNameLength -lt 3 -o $StorageNameLength -gt 24 ]; then
    echo "Storage account name must be between 3 and 24 characters in length."
    exit 1
fi

if [[ "$StorageName" != *[a-z0-9]* ]]; then
    echo "Storage account name must use numbers and lower-case letters only"
    exit 1
fi


#$filtered_output=$(az extension list)
# See http://jmespath.org/tutorial.html for querying
filtered_output=$(az extension list --query "[?name=='functionapp'].name")

if [[ $filtered_output =~ "functionapp" ]];
then
    echo
    echo "Removing existng Azure CLI extension..."
    az extension remove -n functionapp
fi

TempDownloadLocation="/tmp/functionapp-0.0.2-py2.py3-none-any.whl"

echo
echo "Downloading Azure CLI extension for the Azure Functions Linux Consumption preview"
echo
curl -s -o $TempDownloadLocation "https://functionscdn.azureedge.net/public/docs/functionapp-0.0.2-py2.py3-none-any.whl"

echo
echo "Installing Azure CLI extension for the Azure Functions Linux Consumption preview"
echo
az extension add --yes --source $TempDownloadLocation

echo
echo "Create a resource group (if it does not exist for the current subscription)"
echo
az group create -n $ResourceGroup -l "WestUS"

echo
echo "Create a storage account for the function (if it does not exist for the current subscription)"
echo
az storage account create -n $StorageName -l "WestUS" -g $ResourceGroup --sku Standard_LRS


echo
echo "Create a function app (if it does not exist for the current subscription)"
echo
az functionapp createpreviewapp -n $FunctionAppName -g $ResourceGroup -l "WestUS" -s $StorageName --runtime python --is-linux

echo
echo "Retrieving App Insights Id for $AppInsightsName"
echo
AppInsightsKey=$(az resource show -g $ResourceGroup -n $AppInsightsName --resource-type "Microsoft.Insights/components" --query properties.InstrumentationKey)

echo
echo "Setting application setting APPINSIGHTS_INSTRUMENTATIONKEY on $FunctionAppName"
echo
az functionapp config appsettings set --name $FunctionAppName --resource-group $ResourceGroup --settings "APPINSIGHTS_INSTRUMENTATIONKEY = $AppInsightsKey"