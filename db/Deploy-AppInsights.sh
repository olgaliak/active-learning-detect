#!/bin/bash

#Exit on error
set -e

ResourceGroup=$1	
AppInsightsName=$2

# Check if any of the args are empty
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: 'sh $0 (Azure Resource Group Name) (AppInsights Name)'"
    exit 1
fi

az resource create \
    --resource-group $ResourceGroup \
    --resource-type "Microsoft.Insights/components" \
    --name $AppInsightsName \
    --location WestUS2 \
    --properties '{"Application_Type":"other", "Flow_Type":"Redfield", "Request_Source":"IbizaAIExtension","HockeyAppId": null,"SamplingPercentage": null}'