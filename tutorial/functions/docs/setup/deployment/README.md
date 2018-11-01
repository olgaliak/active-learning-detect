## Deploying a Python Azure Function application

Assuming one has gone through the [instructions to setup the environment](../setup/initial/README.md)
for developing a Python based Azure Function, the skeleton applicaiton created with an `HttpTrigger`
app can be deployed.

At it's simplest, deploying the function is to uses the Azure Functions CLI tools that were
previously installed.  The command is `func azure functionapp publish $AZURE_FUNC_APP_NAME --force`.
The below assumes that one has activated the Python virtual environment.

```bash
export AZURE_FUNC_APP_NAME=jmsazfunapp1
$ func azure functionapp publish $AZURE_FUNC_APP_NAME --force
Getting site publishing info...
pip download -r /home/jims/code/src/github/jmspring/azure_python_functions/scratch/azfuncprj/testprj1/requirements.txt --dest /tmp/azureworkerda2e6auj
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworkergtpit9y9 grpcio_tools==1.14.2
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworkergtpit9y9 six==1.11.0
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworkergtpit9y9 azure_functions==1.0.0a4
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworkergtpit9y9 grpcio==1.14.2
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworkergtpit9y9 setuptools==40.4.3
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworkergtpit9y9 protobuf==3.6.1
pip download --no-deps --only-binary :all: --platform manylinux1_x86_64 --python-version 36 --implementation cp --abi cp36m --dest /tmp/azureworkergtpit9y9 azure_functions_worker==1.0.0a4

Preparing archive...
Uploading content...
Upload completed successfully.
Deployment completed successfully.
Removing 'WEBSITE_CONTENTSHARE' from 'jmsazfunapp1'
Removing 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING' from 'jmsazfunapp1'
Syncing triggers...
```

Note the above uses the flag `--force` this is simply because the initial creation of the Azure
Function application set things up such that the Application use Azure Files for publishing
and deployment.  Without the `--force`, the result would look something like:

```bash
$ func azure functionapp publish $AZURE_FUNC_APP_NAME
Your app is configured with Azure Files for editing from Azure Portal.
To force publish use --force. This will remove Azure Files from your app.
```

This may be a Preview thing or it may be the default.  As things mature, the above directions will 
be cleaned up.

Hitting the default web serice, using curl, the result is as follows:

```bash
$ curl https://jmsazfunapp1.azurewebsites.net/api/httpfunc1?name=foo
Hello foo!
```

At this point, you have a Python function deployed to Azure Functions.
