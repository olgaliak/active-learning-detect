#!/bin/bash

# This script sets up the azure function space that will host the Python
# functions developed.  
#
# To set up the function, you need to do the following:
#
#   - create a resource group
#   - create a storage account
#   - create the function app

# Needed:
#   - resource group name
#   - location
#   - storage account name
#   - application name

# Check inputs
if [ "$#" -ne "4" ]; then
    echo "Usage: create_function_app.sh <resource group name> <resource group location> <storage account name> <application name>"
    exit 1
fi

RG_NAME=$1
LOCATION=$2
SA_NAME=$3
APP_NAME=$4

# Create the resource group
az group create --name $RG_NAME --location $LOCATION
if [ "$?" -ne 0 ]; then
    echo "Unable to create resource group."
    exit 1
fi

# Create a storage account in the resource group for the functions to store
# their state / metadata
az storage account create --name $SA_NAME --location $LOCATION --resource-group $RG_NAME --sku Standard_LRS
if [ "$?" -ne 0 ]; then
    echo "Unable to create storage account."
    exit 1
fi

# Create the functions app.  This is the environment the functions will fu
az functionapp createpreviewapp --resource-group $RG_NAME --consumption-plan-location $LOCATION --name $APP_NAME --storage-account $SA_NAME --runtime python --is-linux