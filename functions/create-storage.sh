#!/bin/bash

# Need commands to fail early.
set -e
set -o pipefail

if ! [ -x "$(command -v az)" ]; then
    echo "Error Azure CLI not installed."; >&2
    echo "See: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest to install Azure CLI"; >&2
    exit 1
fi

if [ -z "$RESOURCE_GROUP" ]; then
    echo "Need to set resource group in the environment."; >&2
    exit 1
fi

if [ -z "$STORAGE_NAME" ]; then
    echo "Need to set storage name in the environment."; >&2
    exit 1
fi

echo "Creating Storage Account"

az storage account create --resource-group $RESOURCE_GROUP --name $STORAGE_NAME --sku Standard_LRS
STORAGE_KEY=`az storage account keys list -n $STORAGE_NAME --query [0].value`


echo "Creating Temporary Storage Container"
az storage container create -n temporary --account-key $STORAGE_KEY --account-name $STORAGE_NAME

echo "Creating Permanent Storage Container"
az storage container create -n permanent --account-key $STORAGE_KEY --account-name $STORAGE_NAME

echo "Done!"