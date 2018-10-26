#!/bin/bash

# This script creates a keyvault to be used with an Azure Function to store 
# storage credentials.  It also creates a Service Principal for the Azure 
# Function and assigns read only permissions to secrets within the Keyvault.
# The script:
#
#   - creates a keyvault
#   - creates a service principal for the application
#   - assigned permissions to the service principal into within the keyvault
#   - stores the service principal ID and Password into the Azure Function Application settings
#
# Usage: setup_keyvault_and_app_permissions_with_sp.sh <resource group> <keyvault name> <app name>

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

# Create a service principal for the application
APP_SP_INFO=`az ad sp create-for-rbac --name https://$APP_NAME.azurewebsites.net`
APP_SP_ID=`echo $APP_SP_INFO | jq -r .appId`
APP_SP_PASSWORD=`echo $APP_SP_INFO | jq -r .password`
APP_TENANT_ID=`echo $APP_SP_INFO | jq -r .tenant`

# Give the service principal read permissions for secrets in the keyvault
az keyvault set-policy --name $KV_NAME --spn $APP_SP_ID --secret-permissions get
if [ "$?" -ne "0" ]; then
    echo "Unable to give application permissions in keyvault"
    exit 1
fi

# Store the values in settings
APPNAME_UPPER=`echo $APP_NAME | awk '{print toupper($0)}'`
APP_SETTING_ID_KEY=$APPNAME_UPPER"_ID"
APP_SETTING_PASSWORD_KEY=$APPNAME_UPPER"_PASSWORD"
APP_SETTING_TENANT_ID_KEY=$APPNAME_UPPER"_TENANT_ID"
az functionapp config appsettings set --name $APP_NAME --resource-group $RG_NAME --settings $APP_SETTING_ID_KEY=$APP_SP_ID $APP_SETTING_PASSWORD_KEY=$APP_SP_PASSWORD $APP_SETTING_TENANT_ID_KEY=$APP_TENANT_ID