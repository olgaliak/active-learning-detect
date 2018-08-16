#!/bin/bash
# Source environmental variables
set -a
sed -i 's/\r//g' $1
. $1
set +a
# Make all necessary directories
mkdir -p $image_dir
# Download all images
az storage blob download-batch --source $image_container_name --destination $image_dir
# Create TFRecord from images + csv file on blob storage
# TODO: Try to import create_predictions into this
envsubst < $1 > cur_config.ini
python ${python_file_directory}/initialize_vott_pull.py cur_config.ini 
