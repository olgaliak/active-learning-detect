#!/bin/bash

# This script creates a keyvault to be used with an Azure Function to store 
# storage credentials.  The script:
#
#   - creates a keyvault
#   - assigns and retrieves the identity of the specified function app
#   - adds that identity to the permissions for they keyvault
#
# Usage: setup_keyvault_and_app_permissions.sh <resource group> <keyvault name> <app name>

# Verify the command line args:
if [ "$#" -ne "3" ]; then
    echo "Usage: setup_keyvault_and_app_permissions.sh <resource group> <keyvault name> <app name>"
    exit 1
fi

RG_NAME=$1
KV_NAME=$2
APP_NAME=$3

# Create the key vault
az keyvault create --name $KV_NAME --resource-group $RG_NAME
if [ "$?" -ne "0" ]; then
    echo "Unable to create key vault"
    exit 1
fi

# Assign and retrieve the application identity
APP_ID = az functionapp identity assign -g $RG_NAME -n $APP_NAME
if [ "$?" -ne "0" ]; then
    echo "Unable to assign identity to application"
    exit 1
fi

# Give the application read permissions for secrets in the keyvault
az keyvault set-policy --name $KV_NAME --object-id $APP_ID --secret-permissions get
if [ "$?" -ne "0" ]; then
    echo "Unable to give application permissions in keyvault"
    exit 1
fi