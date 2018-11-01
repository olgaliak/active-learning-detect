## Using Azure Keyvault to Store and Manage Secrets in Python Azure Functions

One issue with service lifecycle, including functions, is how to handle secrets.  One
solution is to inject the secrets into a particular script at time of deployment.  
Another is to use checked in configuration files with variations based upon deployment
type.  Yet another, if dealing with Docker based applications (or similar) is to 
inject values as environment variables -- this is usually the cleanest option.

However, with Azure Functions, the environment variables are a hard coded configuration
file which requires management.  Another option is to use a service that protects
secrets, like Azure Keyvault.

In the first release of functions and those not using the Linux Management Plan, MSI 
or Managed Service Identity is available.  What MSI does is explicitly gives your 
application an Identity that can then be used to access additional services.  In the 
case of Keyvault, one can configure the Keyault to allow granular access to secrets 
within the Keyvault, for instace Read-Only permissions on secrets.

Since MSI is not currently supported in the version of functions we are currently
using, the functions will create what is referred to as a Service Principal (an 
Azure AD entity) that has an ID and Password and we will assign that Serice 
Principal access to the Keyault Secrets.
In fact, it is possible to configure access to and enable an Azure Function to use
Azure Keyvault through a service known as MSI or Managed Service Identity.  In order
to enable this, one must first:

- Create an Azure Keyvault
- Give your Azure Function application an identity
- Configure the Azure Function identity to have access to the Azure Keyvault

Azure Keyvault has granular access policies.  For this example we assume the 
function just requires read access to secrets.

Once the Keyvault is setup and configured, the function itself needs to be 
configured to know the location of the Keyvault as well as the names of the 
secrets to retrieve.  This still requires configuring the environment, but it
does not expose the secrets outside of Keyvault.

The script `setup_keyvault_and_app_permissions.sh` handles the three steps 
above.  In order to run it, it needs three commandline values:

- Resource Group Name --> `RESOURCE_GROUP_NAME`
- Keyvault Name --> `KEYVAULT_NAME`
- Application Name --> `AZURE_FUNC_APP_NAME`

For the example below, the values used for [this](../../setup/initial/README.md)
walkthrough are used, specifically for `RESOURCE_GROUP_NAME` and  `AZURE_FUNC_APP_NAME`.
For the Keyvault Name, we will use the value `jmsfunckv` as the name.

To launch the script:

```bash
$ export RESOURCE_GROUP_NAME=jmsazfunc1rg
$ export KEYVAULT_NAME=jmsfunckv
$ export AZURE_FUNC_APP_NAME=jmsazfunapp1
$ ./setup_keyvault_and_app_permissions.sh $RESOURCE_GROUP_NAME $KEYVAULT_NAME $AZURE_FUNC_APP_NAME
{
  "id": "/subscriptions/3fee811e-11bf-4b5c-9c62-a2f28b517724/resourceGroups/jmsazfunc1rg/providers/Microsoft.KeyVault/vaults/jmsfunckv1",
  "location": "westus",
  "name": "jmsfunckv1",
  "properties": {
    "accessPolicies": [
      {
        "applicationId": null,
        "objectId": "86a607ff-039e-497e-bab1-92247bc5ed02",
        "permissions": {
          "certificates": [
            "get",
            "list",
            "delete",
            "create",
            "import",
            "update",
            "managecontacts",
            "getissuers",
            "listissuers",
            "setissuers",
            "deleteissuers",
            "manageissuers",
            "recover"
          ],
          "keys": [
            "get",
            "create",
            "delete",
            "list",
            "update",
            "import",
            "backup",
            "restore",
            "recover"
          ],
          "secrets": [
            "get",
            "list",
            "set",
            "delete",
            "backup",
            "restore",
            "recover"
          ],
          "storage": [
            "get",
            "list",
            "delete",
            "set",
            "update",
            "regeneratekey",
            "setsas",
            "listsas",
            "getsas",
            "deletesas"
          ]
        },
        "tenantId": "72f988bf-86f1-41af-91ab-2d7cd011db47"
      }
    ],
    "createMode": null,
    "enablePurgeProtection": null,
    "enableSoftDelete": null,
    "enabledForDeployment": false,
    "enabledForDiskEncryption": null,
    "enabledForTemplateDeployment": null,
    "networkAcls": null,
    "provisioningState": "Succeeded",
    "sku": {
      "name": "standard"
    },
    "tenantId": "72f988bf-86f1-41af-91ab-2d7cd011db47",
    "vaultUri": "https://jmsfunckv1.vault.azure.net/"
  },
  "resourceGroup": "jmsazfunc1rg",
  "tags": {},
  "type": "Microsoft.KeyVault/vaults"
}
Retrying role assignment creation: 1/36
{
  "id": "/subscriptions/aaaaaaaa-11bf-4b5c-9c62-dddddddddddd/resourceGroups/jmsazfunc1rg/providers/Microsoft.KeyVault/vaults/jmsfunckv1",
  "location": "westus",
  "name": "jmsfunckv1",
  "properties": {
    "accessPolicies": [
      {
        "applicationId": null,
        "objectId": "86a607ff-039e-497e-bab1-92247bc5ed02",
        "permissions": {
          "certificates": [
            "get",
            "list",
            "delete",
            "create",
            "import",
            "update",
            "managecontacts",
            "getissuers",
            "listissuers",
            "setissuers",
            "deleteissuers",
            "manageissuers",
            "recover"
          ],
          "keys": [
            "get",
            "create",
            "delete",
            "list",
            "update",
            "import",
            "backup",
            "restore",
            "recover"
          ],
          "secrets": [
            "get",
            "list",
            "set",
            "delete",
            "backup",
            "restore",
            "recover"
          ],
          "storage": [
            "get",
            "list",
            "delete",
            "set",
            "update",
            "regeneratekey",
            "setsas",
            "listsas",
            "getsas",
            "deletesas"
          ]
        },
        "tenantId": "aaaaaaaa-86f1-41af-cccc-dddddddddddd"
      },
      {
        "applicationId": null,
        "objectId": "ad828a3b-5d98-41cf-81e0-f1530798513e",
        "permissions": {
          "certificates": null,
          "keys": null,
          "secrets": [
            "get"
          ],
          "storage": null
        },
        "tenantId": "aaaaaaaa-86f1-41af-cccc-dddddddddddd"
      }
    ],
    "createMode": null,
    "enablePurgeProtection": null,
    "enableSoftDelete": null,
    "enabledForDeployment": false,
    "enabledForDiskEncryption": null,
    "enabledForTemplateDeployment": null,
    "networkAcls": null,
    "provisioningState": "Succeeded",
    "sku": {
      "name": "standard"
    },
    "tenantId": "aaaaaaaa-86f1-41af-cccc-dddddddddddd",
    "vaultUri": "https://jmsfunckv1.vault.azure.net/"
  },
  "resourceGroup": "jmsazfunc1rg",
  "tags": {},
  "type": "Microsoft.KeyVault/vaults"
}
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
    "value": "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=jmsazfunc1sa;AccountKey=Foo=="
  },
  {
    "name": "AzureWebJobsDashboard",
    "slotSetting": false,
    "value": "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=jmsazfunc1sa;AccountKey=Foo=="
  },
  {
    "name": "WEBSITE_RUN_FROM_ZIP",
    "slotSetting": false,
    "value": "https://jmsazfunc1sa.blob.core.windows.net/function-releases/20181008222714-7ab1234-b18b-4466-ad1a-775522548388.zip?sv=2018-03-28&sr=b&sig=Wfoo&st=2018-10-08T22%3A22%3A30Z&se=2028-10-08T22%3A27%3A30Z&sp=r"
  },
  {
    "name": "JMSAZFUNAPP1_ID",
    "slotSetting": false,
    "value": "aaaaaaaa-ea2d-4d11-b2c8-bbbbbbbbbbbb"
  },
  {
    "name": "JMSAZFUNAPP1_PASSWORD",
    "slotSetting": false,
    "value": "aaaaaaaa-483f-4bb3-926b-bbbbbbbbbbbb"
  },
  {
    "name": "JMSAZFUNAPP1_TENANT_ID",
    "slotSetting": false,
    "value": "aaaaaaaa-86f1-41af-cccc-dddddddddddd"
  },
  {
    "name": "APPLICATION_PREFIX",
    "slotSetting": false,
    "value": "JMSAZFUNAPP1"
  }
]
```

Notice that three entried for accessing the Keyvault hae been entered into application settings 
above.  The Azure Function application name is `jmsazfunapp1`, therefore the entries for the settings
were generated as <APP NAME IN UPPER CASE>_[ID, PASSWORD, TENANT].

The application itself is stored as `APPLICATION_PREFIX` in the settings.  This value can then be
used within the Python function itself to pull in the other values.

As noted previously, when Python for Azure Functions supports MSI, this step will not be necessary
as MSI will handle access control internally.