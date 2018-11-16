#!/bin/bash
# Source environmental variables
set -a
sed -i 's/\r//g' $1
. $1
set +a
# Updating vars in config file
envsubst < $1 > cur_config.ini
# Update images from blob storage
echo "Updating Blob Folder"
python ${python_file_directory}/update_blob_folder.py cur_config.ini
# Create TFRecord from images + csv file on blob storage
echo "Download MS COCO tf model if it doesn't exist"
# Download tf model if it doesn't exist
if [ ! -d "$download_location/${init_model_name}" ]; then
  mkdir -p $download_location
  curl $init_pred_tf_url --create-dirs -o ${download_location}/${init_model_name}.tar.gz
  tar -xzf ${download_location}/${init_model_name}.tar.gz -C $download_location
fi


echo "Running pretratined model on the images"
python ${python_file_directory}/create_predictions.py cur_config.ini init_pred $init_model_graph
# Rename predictions and inference graph based on timestamp and upload
echo "Uploading new data"

az storage blob upload --container-name $label_container_name --file $untagged_output --name init_totag_$(date +%s).csv --account-name $AZURE_STORAGE_ACCOUNT --account-key $AZURE_STORAGE_KEY