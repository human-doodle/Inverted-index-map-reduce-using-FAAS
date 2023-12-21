import os
import pickle, json
from google.cloud import storage
import functions_framework

storage_client = storage.Client.from_service_account_json('shivani-pal-fall2023.json')


input_bucket_name = 'shivanipal-upload-files'
output_bucket_name = 'shivanipal-files'
input_bucket = storage_client.bucket(input_bucket_name)
output_bucket = storage_client.bucket(output_bucket_name)

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def fileprocess(cloud_event):
    num = 3
    def create_dict_from_files():
        
        blobs = input_bucket.list_blobs()
        file_dict = {}
        for blob in blobs:
            file_name = blob.name
            contents = blob.download_as_text()
            file_dict[file_name] = contents

        return file_dict
    
    def dump_dict_to_json(file_dict, output_bucket_name, total_jsons):
        # Calculate the number of files to include in each JSON file
        total_files = len(file_dict)
        files_per_json = total_files // total_jsons
        remainder = total_files % total_jsons

        start_idx = 0
        
        files = []
        for i in range(total_jsons):
            end_idx = start_idx + files_per_json + (1 if remainder>0 else 0)
            output_file_name = f'file_{i + 1}.json'
            files.append(output_file_name)
            # Extract the relevant portion of the dictionary
            subset_dict = {k: file_dict[k] for k in list(file_dict.keys())[start_idx:end_idx]}

            blob_output = output_bucket.blob(output_file_name)
            json_string = json.dumps(subset_dict)
            blob_output.upload_from_string(json_string, content_type='application/json')
        return files

    # remake index, so make chunks : only this part is serial
    file_dict = create_dict_from_files()
    dump_dict_to_json(file_dict, output_bucket_name, num)
    

    return 'OK'

