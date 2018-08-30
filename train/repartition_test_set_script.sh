#!/bin/bash
# Source environmental variables
set -a
sed -i 's/\r//g' $1
. $1
set +a
envsubst < $1 > cur_config.ini
python repartition_test_set.py cur_config.ini
