#!/bin/bash
# Source environmental variables
set -a
sed -i 's/\r//g' $1
. $1
set +a
# Update images from blob storage
echo "Updating Blob Folder"
python ${python_file_directory}/update_blob_folder.py
# Create TFRecord from images + csv file on blob storage
echo "Creating TF Record"
python ${python_file_directory}/convert_tf_record.py
# pipeline.config from bash variables
echo "Making pipeline file from env vars"
temp_pipeline=${pipeline_file%.*}_temp.${pipeline_file##*.}
envsubst < $pipeline_file > $temp_pipeline
# Train model on TFRecord
echo "Training model"
rm -rf $train_dir
python ${tf_location}/train.py --logtostderr --train_dir=$train_dir --pipeline_config_path=$temp_pipeline
# Export inference graph of model
echo "Exporting inference graph"
rm -rf $inference_output_dir
python ${tf_location}/export_inference_graph.py --input_type image_tensor --pipeline_config_path $temp_pipeline --trained_checkpoint_prefix ${train_dir}/model.ckpt-$train_iterations --output_directory $inference_output_dir
# TODO: Validation on Model, keep track of MAP etc.
# Use inference graph to create predictions on untagged images
echo "Creating new predictions"
python ${python_file_directory}/create_predictions.py
# Rename predictions and inference graph based on timestamp and upload
echo "Uploading new data"
az storage blob upload --container-name activelearninglabels --file ${inference_output_dir}/frozen_inference_graph.pb --name model_$(date +%s).pb  --account-name $AZURE_STORAGE_ACCOUNT --account-key $AZURE_STORAGE_KEY
az storage blob upload --container-name activelearninglabels --file $untagged_output --name totag_$(date +%s).csv --account-name $AZURE_STORAGE_ACCOUNT --account-key $AZURE_STORAGE_KEY
