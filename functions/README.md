## Deploying functions to a Azure Function App and Add Settings

This tutorial talks about how to deploy a function to an Azure Function Application.  For
the example, we will use the function(s) within the `pipeline` application located in this
directory.

In order to set up the Azure Function Application, we will use [this](../tutorial/functions/docs/setup/initial/create_function_app.sh) script.  It should be noted, that
this example also assumes that one has properly setup their environment for working with
Azure Functions, including installing the Azure Function Core Tools.  That setup is discussed [here](../tutorial/functions/docs/setup/initial/README.md).

### Creating the application

Leveraging the `create_function_app.sh` script the application will be created for
us.  The script requires four pieces of information:

- Resource group name
- Resource group location
- Storage account name for the function application
- The name of the function application itself

Note, the resource group as well as the storage account will be created by the script.

Running the script:

```bash
export RESOURCE_GROUP=jmsactlrnrg
export RESOURCE_GROUP_LOCATION=westus
export STORAGE_ACCOUNT_NAME=jmslrnpipe
export FUNCTION_APP_NAME=jmsactlrnpipeline

jims@functional:~/code/src/github/jmspring/active-learning-detect$ ./tutorial/functions/docs/setup/initial/create_function_app.sh $RESOURCE_GROUP $RESOURCE_GROUP_LOCATION $STORAGE_ACCOUNT_NAME $FUNCTION_APP_NAME
{
  "id": "/subscriptions/3fee811e-11bf-abcd-9c62-adbeef517724/resourceGroups/jmsactlrnrg",
  "location": "westus",
  "managedBy": null,
  "name": "jmsactlrnrg",
  "properties": {
    "provisioningState": "Succeeded"
  },
  "tags": null
}
{
  "accessTier": null,
  "creationTime": "2018-10-28T03:36:16.816514+00:00",
  "customDomain": null,
  "enableHttpsTrafficOnly": false,
  "encryption": {
    "keySource": "Microsoft.Storage",
    "keyVaultProperties": null,
    "services": {
      "blob": {
        "enabled": true,
        "lastEnabledTime": "2018-10-28T03:36:16.894642+00:00"
      },
      "file": {
        "enabled": true,
        "lastEnabledTime": "2018-10-28T03:36:16.894642+00:00"
      },
      "queue": null,
      "table": null
    }
  },
  "id": "/subscriptions/3fee811e-11bf-abcd-9c62-adbeef517724/resourceGroups/jmsactlrnrg/providers/Microsoft.Storage/storageAccounts/jmslrnpipe",
  "identity": null,
  "isHnsEnabled": null,
  "kind": "Storage",
  "lastGeoFailoverTime": null,
  "location": "westus",
  "name": "jmslrnpipe",
  "networkRuleSet": {
    "bypass": "AzureServices",
    "defaultAction": "Allow",
    "ipRules": [],
    "virtualNetworkRules": []
  },
  "primaryEndpoints": {
    "blob": "https://jmslrnpipe.blob.core.windows.net/",
    "dfs": null,
    "file": "https://jmslrnpipe.file.core.windows.net/",
    "queue": "https://jmslrnpipe.queue.core.windows.net/",
    "table": "https://jmslrnpipe.table.core.windows.net/",
    "web": null
  },
  "primaryLocation": "westus",
  "provisioningState": "Succeeded",
  "resourceGroup": "jmsactlrnrg",
  "secondaryEndpoints": null,
  "secondaryLocation": null,
  "sku": {
    "capabilities": null,
    "kind": null,
    "locations": null,
    "name": "Standard_LRS",
    "resourceType": null,
    "restrictions": null,
    "tier": "Standard"
  },
  "statusOfPrimary": "available",
  "statusOfSecondary": null,
  "tags": {},
  "type": "Microsoft.Storage/storageAccounts"
}
Your Linux, cosumption plan, function app 'jmsactlrnpipeline' has been successfully created but is not active until content is published usingAzure Portal or the Functions Core Tools.
```

At this point, you have an Azure Function Application to which you can publish your functions to.

### Configuring the Application Environment

In a number of cases, one will need to set environment variables for their azure function to use.  The following
shows setting up the required variables for accessing a Postgres database that the data layer of the `pipeline`
application uses.

```bash
export DB_HOST="<db hostname>"
export DB_USER="<db admin name"
export DB_PASS="<db password>"
export DB_NAME="<db name>"

az functionapp config appsettings set --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP --settings DB_HOST=$DB_HOST DB_USER=$DB_USER DB_PASS=$DB_PASS DB_NAME=$DB_NAME
[
  {
    "name": "FUNCTIONS_WORKER_RUNTIME",
    "slotSetting": false,
    "value": "python"
  },
  {
    "name": "FUNCTIONS_EXTENSION_VERSION",
    "slotSetting": false,
    "value": "~2"
  },
  {
    "name": "AzureWebJobsStorage",
    "slotSetting": false,
    "value": "<storage endpoint connection string>"
  },
  {
    "name": "AzureWebJobsDashboard",
    "slotSetting": false,
    "value": "<dashboard connection string>"
  },
  {
    "name": "WEBSITE_CONTENTAZUREFILECONNECTIONSTRING",
    "slotSetting": false,
    "value": "<a connection string>"
  },
  {
    "name": "WEBSITE_CONTENTSHARE",
    "slotSetting": false,
    "value": "jmsactlrnpipeline"
  },
  {
    "name": "DB_HOST",
    "slotSetting": false,
    "value": "<dbhost>
  },
  {
    "name": "DB_USER",
    "slotSetting": false,
    "value": "<dbuser>"
  },
  {
    "name": "DB_PASS",
    "slotSetting": false,
    "value": "<dbpassword"
  },
  {
    "name": "DB_NAME",
    "slotSetting": false,
    "value": "<dbname>"
  }
]
```

### Deploying a function to the application

Once you have your configuration, it is time to deploy the application itself.  You use the 
Azure Function Core Utils tools to publish your functions into the Azure Function Application
created and configured above.  That looks like:

```bash
jims$ func azure functionapp publish $FUNCTION_APP_NAME --force
Getting site publishing info...
pip download -r /home/jims/code/src/github/jmspring/active-learning-detect/functions/pipeline/requirements.txt --dest /tmp/azureworkertczxe16l
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworker40w5hod2 azure_functions==1.0.0a5
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworker40w5hod2 azure_functions_worker==1.0.0a6
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworker40w5hod2 pg8000==1.12.3
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworker40w5hod2 setuptools==40.5.0
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworker40w5hod2 grpcio_tools==1.14.2
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworker40w5hod2 six==1.11.0
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworker40w5hod2 grpcio==1.14.2
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworker40w5hod2 protobuf==3.6.1

Preparing archive...
Uploading content...
Upload completed successfully.
Deployment completed successfully.
Removing 'WEBSITE_CONTENTSHARE' from 'jmsactlrnpipeline'
Removing 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING' from 'jmsactlrnpipeline'
Syncing triggers...
Functions in jmsactlrnpipeline:
    download - [httpTrigger]
        Invoke url: https://jmsactlrnpipeline.azurewebsites.net/api/download?code=AARPr45D5K6AIEWv8bEaqWalSaddrUzd4aydOxmhSPauGUrsPvzw==
```

Showing our function running:

```bash
curl "https://jmsactlrnpipeline.azurewebsites.net/api/download?code=AARPr45D5K6AIEWv8bEaqWalSaddrUzd4aydOxmhSPauGUrsPvzw==&imageCount=1"
["https://csehackstorage.blob.core.windows.net/image-to-tag/1.jpg"]
```