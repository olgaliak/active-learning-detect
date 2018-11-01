# Getting Starting With Active Learning Database Infrastructure

This directory contains database schemas, deployment script, and test data generation.

## Creating a PostgreSQL host on Azure

The _Deploy-Postgres-DB_ shell script will deploy a [PostgreSQL server in Azure](https://azure.microsoft.com/en-us/services/postgresql/). The script assumes you have the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) installed and are already [logged into the CLI](https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli?view=azure-cli-latest) with the subscription you wish to deploy to. 

Once the above is ready run the command below by replacing the 3 arguments 

```sh
$ sh Deploy-Postgres-DB.sh RESOURCE_GROUP_NAME POSTGRES_SERVER_NAME POSTGRES_USER
```

## Deploying a PostgreSQL database and installing resources

The _install-db-resources.py_ file will install SQL resources from the functions, tables, and triggers directories. A pre-requiste for installation is to set environment variables for **DB_HOST**, **DB_USER**, and **DB_PASS**

An example for setting the environment variables can be seen below

```sh
$ export DB_HOST=(POSTGRES_SERVER_NAME) DB_USER=(POSTGRES_USER@POSTGRES_SERVER) DB_PASS=(PASSWORD)
```

**Please note**: The DB_PASS is the same password used when executing the _Deploy-Postgres-DB_ shell file.

Now that environment variables are set execute the following where _(MyDatabaseName)_ is replaced with the name of the PostgreSQL database you want to create on the existing host.

```sh
$ python3 install-db-resources.py (MyDatabaseName)
```

If all is successful you will see list of installed files.

## Running an integration test on PostgreSQL DB on Azure

TODO