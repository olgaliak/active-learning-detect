#!/bin/bash

#Exit on error
set -e

ResourceGroup=$1
ServerName=$2
DBUserName=$3
Local_IP_Address=$(curl -s http://whatismyip.akamai.com/)

# Check if any of the args are empty
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Expected usage: 'sh $0 (Azure Resource Group Name) (PostGres ServerName) (PostGres UserName)'"
    exit 1
fi

echo
echo "Entire a password for Postgres user '$DBUserName@$ServerName':" 
read -s DBPassword
echo

# See Azure password policy: https://docs.microsoft.com/en-us/previous-versions/azure/jj943764(v=azure.100)
PasswordLength=${#DBPassword}
if [ $PasswordLength -lt 8 -o $PasswordLength -gt 16 ]; then
    echo "Password must be between 8 to 16 characters"
    exit 1
fi

if [[ "$DBPassword" != *[A-Z]* || "$DBPassword" != *[a-z]* ]]; then
    echo "Password must have upper and lower case characters"
    exit 1
fi

if [[ "$DBPassword" != *[0-9]* ]]; then
    echo "Password must contain numbers"
    exit 1
fi

echo
echo "Create a resource group (if it does not exist for the current subscription)"
echo
az group create \
    --name $ResourceGroup \
    --location westus

echo
echo "Create an Azure Postgres host on the cheapest SKU. This may take SEVERAL MINUTES..."
echo
az postgres server create \
    --resource-group $ResourceGroup \
    --name $ServerName \
    --location westus \
    --admin-user $DBUserName \
    --admin-password $DBPassword \
    --sku-name B_Gen5_2 \
    --version 9.6 \

echo
echo "Create a firewall rule for the local host IP address $Local_IP_Address"
echo
RuleDate=$(date +%F_%H-%M-%S)
az postgres server firewall-rule create \
    --resource-group $ResourceGroup \
    --server-name $ServerName \
    --name "AllowMyIP_$RuleDate" \
    --start-ip-address $Local_IP_Address \
    --end-ip-address $Local_IP_Address