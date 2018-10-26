#!/bin/bash

# Azure Python Functions require that a Python virtual environment be setup
# prior to initializing and creating the function.
#
# This script will setup and activate the specified virtual environment.  If 
# specified, the virtual environment will be activated.
#
# Usage: setup_environment.sh <path for virtual environment> <activate>
#
if [ "$#" -ne "1" ]; then
    echo "Usage: setup_environment.sh <path for virtual environment>"
    exit 1
fi

# Is machine configured properly?  Requirements:
#   - Python 3.6 or later
#   - virtualenv installed

# Determine Python version
which python >& /dev/null
if [ "$?" -eq "0" ]; then
    PYTHON_VERSION=`python --version | awk '{print $2}'`
    if [ "$PYTHON_VERSION" -lt "3.6" ]; then
        PYTHON_VERSION=""
    fi
fi
if [ -z "$PYTHON_VERSION" ] || [ "$PYTHON_VERSION" -lt "3.6" ]; then
    which python3 >& /dev/null
    if [ "$?" -eq "0" ]; then
        PYTHON_VERSION=`python3 --version | awk '{print $2}'`
    fi
fi
if [ -z "$PYTHON_VERSION" ]; then
    echo "Python 3.6 or later must be installed."
    exit 1
elif [ $(echo "${PYTHON_VERSION:0:3}<3.6" | bc) -eq 1 ]; then
    echo "Python 3.6 or later must be installed.  Version installed is $PYTHON_VERSION"
    exit 1
fi

# Check if virtualenv is installed
virtualenv --version >& /dev/null
if [ "$?" -ne "0" ]; then
    echo "virtualenv must be installed"
    exit 1
fi

# Create virtualenv
VIRTUALENV_DIR="$1"
virtualenv --python=python${PYTHON_VERSION:0:3} $VIRTUALENV_DIR

# How to activate the virtualenv
echo "To activate the virtualenv run: source $VIRTUALENV_DIR/bin/activate"