# Getting Starting With Active Learning Database Infrastructure

This directory contains database schemas, deployment script, and test data generation.

## Creating a PostgreSQL DB on Azure

The _Deploy-Postgres-DB_ shell script will deploy a [PostgreSQL database in Azure](https://azure.microsoft.com/en-us/services/postgresql/). The script assumes you have the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) installed and are already [logged into the CLI](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli?view=azure-cli-latest) with the subscription you wish to deploy to. 

Once the above is ready run the command below by replacing the 3 arguments 

```sh
$ sh Deploy-Postgres-DB.sh RESOURCE_GROUP_NAME POSTGRES_SERVER_NAME POSTGRES_USER
```

## Deploying table schemas to your PostgreSQL DB on Azure

TODO

## Running an integration test on PostgreSQL DB on Azure

TODO