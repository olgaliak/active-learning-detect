# Separate test set
filearr=($(shuf -e $(find "$image_dir" -type f -name $filetype)))
test_num=$(echo "scale=0;${#filearr[@]}*${test_percentage}/1" | bc)

mkdir -p ${image_dir}/test
mkdir -p ${image_dir}/train
# Separate test set
filearr=($(shuf -e $(ls -pL $image_dir | grep -v /)))
split=$(echo "scale=0;${#filearr[@]}*${train_percentage}/1" | bc)
for i in "${!filearr[@]}"; do
  if (("$i" < "$split")); then
    mv ${image_dir}/${filearr[$i]} ${image_dir}/train/${filearr[$i]}
  else
    mv ${image_dir}/${filearr[$i]} ${image_dir}/test/${filearr[$i]}    
  fi
done

printf "%s\n" "${filearr[@]:0:$test_num}" > ${image_dir}/test.txt
az storage blob upload --container-name activelearninglabels --file ${image_dir}/test.txt --name test_$(date +%s).csv --account-name $AZURE_STORAGE_ACCOUNT --account-key $AZURE_STORAGE_KEY