#!/bin/bash
set -e

# This script creates an initial function once it ensures that the requirements
# are installed.  The requirements are:
#
#   - Azure Functions Core Tools 2.x
#   - Azure CLI 2.0 or later
#
# Once the requirements are verified, the following steps are performed:
#
#   - Invoke the virtual environment
#   - Create the function project
#   - Create a new function within the project

# Check usage
if [ "$#" -ne "5" ]; then
    echo "Usage: create_function_project.sh <virtual environment dir> <project dir> <project name> <function name> <function template>"
    exit 1
fi

# Check Azure Functions Core Tools
which func >& /dev/null
if [ "$?" -ne "0" ]; then
    echo "Azure Functions Core Tools required"
    exit 1
fi
func azure functionapp --help >& /dev/null
if [ "$?" -ne "0" ]; then
    echo "func exists, does not appear to be part of Azure Functions Core Tools"
    exit 1
fi

# Check for Azure CLI
which az >& /dev/null
if [ "$?" -ne "0" ]; then
    echo "Azure CLI 2.0 or more recent required."
    exit 1
fi
az --version | grep "azure-cli" | grep "(2." >& /dev/null
if [ "$?" -ne "0" ]; then
    echo "Require 2.x or newer version of Azure CLI"
    exit 1
fi

# command line options
VIRTENV_DIR=$1
PROJECT_DIR=$2
PROJECT_NAME=$3
FUNCTION_NAME=$4
FUNCTION_TEMPLATE=$5

# Verify the virtual environment is there and activate it
if [ ! -d "$VIRTENV_DIR" ] || [ ! -e "$VIRTENV_DIR/bin/activate" ]; then
    echo "Please setup virtual environment"
    exit 1
fi
source "$VIRTENV_DIR/bin/activate"
if [ "$?" -ne "0" ]; then
    echo "Error activating virtual environment"
    exit 1
fi

# Create the project directory and change to it
mkdir -p $PROJECT_DIR
if [ "$?" -ne "0" ]; then
    echo "Unable to create project directory"
    exit 1
fi
cd $PROJECT_DIR

# Create the function
func init $PROJECT_NAME --worker-runtime python
if [ "$?" -ne 0 ]; then
    echo "Error initializing project"
    exit 1
fi
cd $PROJECT_NAME

# Create the function
func new --name $FUNCTION_NAME --template "$FUNCTION_TEMPLATE" 
if [ "$?" -ne 0 ]; then
    echo "Error creating the new function"
    exit 1
fi

# Instructions for continuing
echo "Function $FUNCTION_NAME is created within project $PROJECT_NAME"
echo "In order to operate with the function:"
echo "  - Activate the virtual environment"
echo "  - Change to $PROJECT_DIR/$PROJECT_NAME"
