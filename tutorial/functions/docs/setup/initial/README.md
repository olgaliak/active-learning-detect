## Setting up a function environment

In the following document, we explore using the scripts in this folder to walk through
setting up an environment for and deploying a python funciton into Azure Functions.  
Python for Azure Functions is in preview at the moment, so, things may change.  The 
following prerequisites are assumed:

- You have an active Azure account
- The prerequisites for working with Azure Functions have been installed, per [here](https://github.com/Azure/Azure-Functions/wiki/Azure-Functions-on-Linux-Preview)
- Per prerequisites, the scripts below assume one has created a resource group

### Python for Azure Functions in practice

One thing most of the documents around Python for Azure Functions do not call out is 
the fact that function development requires a virtual environment to be setup.  The 
script `setup_environment.sh` does just that.  The syntax is:

```bash
$ ./setup_environment.sh <path to virtual environment>
```

For purposes of this write up will use environment variables to illustrate the process,
we will first assume our virtual environment is in `~/python/venv/azfuncprj`, so the 
above becomes:

```bash
$ export VIRTUAL_ENV_DIR=~/python/venv/azfuncprj
$ ./setup_environment.sh $VIRTUAL_ENV_DIR
```

Running the above we get:

```bash
$ export VIRTUAL_ENV_DIR=~/python/venv/azfuncprj
$ ./setup/setup_environment.sh $VIRTUAL_ENV_DIR
Running virtualenv with interpreter /usr/bin/python3.6
Using base prefix '/usr'
New python executable in /home/jims/python/venv/azfuncprj/bin/python3.6
Also creating executable in /home/jims/python/venv/azfuncprj/bin/python
Installing setuptools, pip, wheel...done.
To activate the virtualenv run: source python/venv/azfuncprj/bin/activate
```

### Creating the function project

The next step in working with Python for Azure Functions is to create a project and a
function within that project.  This is handled by the script `create_function_project.sh`.
For this funciton you will need to know:

- The virtual environment path (created above), `VIRTUAL_ENV_DIR`
- The directory where you want the project to live, this will be defined with the
  environment variable `PYFUNC_PROJECT_DIR`
- The project name, defined with the environment variable `PYFUNC_PROJECT_NAME`
- The name of the function within the project, `PYFUNC_FUNCTION_NAME`
- The type of function to create/function template.  In this case we will use an
  HttpTrigger app, so `PYFUNC_FUNCTION_TYPE=HttpTrigger`

Invoking the `create_function_project.sh` script:

```bash
$ export VIRTUAL_ENV_DIR=~/python/venv/azfuncprj
$ export PYFUNC_PROJECT_DIR=~/python/azfuncprj
$ export PYFUNC_PROJECT_NAME=testprj
$ export PYFUNC_FUNCTION_NAME=testhttpfunc
$ export PYFUNC_FUNCTION_TYPE=HttpTrigger
$ ./create_function_project.sh $VIRTUAL_ENV_DIR $PYFUNC_PROJECT_DIR $PYFUNC_PROJECT_NAME $PYFUNC_FUNCTION_NAME $PYFUNC_FUNCTION_TYPE
Installing wheel package
Installing azure-functions==1.0.0a4 package
Installing azure-functions-worker==1.0.0a4 package
Running pip freeze
Writing .gitignore
Writing host.json
Writing local.settings.json
Writing /home/jims/python/azfuncprj/testprj/.vscode/extensions.json
Select a language: Select a template: HttpTrigger
Function name: [HttpTriggerPython] Writing /home/jims/python/azfuncprj/azfuncprj/testprj/httpfunc1/sample.dat
Writing /home/jims/python/azfuncprj/testprj/httpfunc1/__init__.py
Writing /home/jims/python/azfuncprj/testprj/httpfunc1/function.json
The function "testhttpfunc" was created successfully from the "HttpTrigger" template.
Function httpfunc1 is created within project testprj1
In order to operate with the function:
  - Activate the virtual environment
  - Change to ~/python/azfuncprj/testprj
```

### Create a Azure Function Application to host your Python function

Per this [document](https://github.com/Azure/azure-functions-python-worker/wiki/Create-your-first-Python-function)
one can run functions locally.  If one wants to actually host them in Azure, then one 
needs to create an Azure Function application to do so.  Outside of the prerequisites mentioned
above, this is the first piece of this setup that actually interacts with Azure itself.

The script `create_function_app.sh` sets this up.  It requires that a `resource group` has been
previously created.  For purposes of Python support in Azure Functions, the resource group (during 
preview) must be created in one of the following regions:

- West US
- East US
- West Europe
- East Asia

The example below will assume the `resource group` will be named `jmsazfunc1rg` and located
in `West US`.  The Azure CLI command to do so is:

```bash
export RESOURCE_GROUP_NAME=jmsazfunc1rg
export RESOURCE_GROUP_LOCATION=westus
$ az group create --name $RESOURCE_GROUP_NAME --location $RESOURCE_GROUP_LOCATION
{
  "id": "/subscriptions/3fee811e-11bf-4b5c-9c62-a2f28b517724/resourceGroups/jmsazfunc1rg",
  "location": "westus",
  "managedBy": null,
  "name": "jmsazfunc1rg",
  "properties": {
    "provisioningState": "Succeeded"
  },
  "tags": null
}
```

To create the Azure Function application, the following need to be defined:

- Resource Group --> `export RESOURCE_GROUP_NAME=jmsazfunc1rg`
- Resource Group/Function Location --> `export RESOURCE_GROUP_LOCATION=westus`
- Storage Account Name --> `export STORAGE_ACCOUNT_NAME=jmsazfunc1sa`
- Azure Function Applicaiton Name --> `export AZURE_FUNC_APP_NAME=jmsazfunapp1`

The storage account, `jmsazfun1sa`, is needed as that is the locaiton that the Azure Function
state is stored.  The name of the applciaiton, for this example is `jmsazfunapp1`.  Resource
group name and location were defined previously.

Executing the script:

```bash
$ export RESOURCE_GROUP_NAME=jmsazfunc1rg
$ export RESOURCE_GROUP_LOCATION=westus
$ export STORAGE_ACCOUNT_NAME=jmsazfunc1sa
$ export AZURE_FUNC_APP_NAME=jmsazfunapp1
$ ./create_function_app.sh $RESOURCE_GROUP_NAME $RESOURCE_GROUP_LOCATION $STORAGE_ACCOUNT_NAME $AZURE_FUNC_APP_NAME
{
  "id": "/subscriptions/3fee811e-11bf-4b5c-9c62-a2f28b517724/resourceGroups/jmsazfunc1rg",
  "location": "westus",
  "managedBy": null,
  "name": "jmsazfunc1rg",
  "properties": {
    "provisioningState": "Succeeded"
  },
  "tags": null
}
{
  "accessTier": null,
  "creationTime": "2018-10-08T18:52:49.001675+00:00",
  "customDomain": null,
  "enableHttpsTrafficOnly": false,
  "encryption": {
    "keySource": "Microsoft.Storage",
    "keyVaultProperties": null,
    "services": {
      "blob": {
        "enabled": true,
        "lastEnabledTime": "2018-10-08T18:52:49.118545+00:00"
      },
      "file": {
        "enabled": true,
        "lastEnabledTime": "2018-10-08T18:52:49.118545+00:00"
      },
      "queue": null,
      "table": null
    }
  },
  "id": "/subscriptions/3fee811e-11bf-4b5c-9c62-a2f28b517724/resourceGroups/jmsazfunc1rg/providers/Microsoft.Storage/storageAccounts/jmsazfunc1sa",
  "identity": null,
  "isHnsEnabled": null,
  "kind": "Storage",
  "lastGeoFailoverTime": null,
  "location": "westus",
  "name": "jmsazfunc1sa",
  "networkRuleSet": {
    "bypass": "AzureServices",
    "defaultAction": "Allow",
    "ipRules": [],
    "virtualNetworkRules": []
  },
  "primaryEndpoints": {
    "blob": "https://jmsazfunc1sa.blob.core.windows.net/",
    "dfs": null,
    "file": "https://jmsazfunc1sa.file.core.windows.net/",
    "queue": "https://jmsazfunc1sa.queue.core.windows.net/",
    "table": "https://jmsazfunc1sa.table.core.windows.net/",
    "web": null
  },
  "primaryLocation": "westus",
  "provisioningState": "Succeeded",
  "resourceGroup": "jmsazfunc1rg",
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
Your Linux, cosumption plan, function app 'jmsazfunapp1' has been successfully created but is not active until content is published usingAzure Portal or the Functions Core Tools.
```