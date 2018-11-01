#!/bin/bash

#Exit on error
set -e

ResourceGroup=$1	
NamePrefix=$2

az resource create \
    --resource-group $ResourceGroup \
    --resource-type "Microsoft.Insights/components" \
    --name $NamePrefix-appinsights \
    --location WestUS2 \
    --properties '{"Application_Type":"other", "Flow_Type":"Redfield", "Request_Source":"IbizaAIExtension","HockeyAppId": null,"SamplingPercentage": null}'