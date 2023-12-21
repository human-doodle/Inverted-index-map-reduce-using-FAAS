import os
import pickle
from google.cloud import storage
import functions_framework

storage_client = storage.Client.from_service_account_json('shivani-pal-fall2023.json')
bucket_name = 'bucket-shivanipal'
folder = 'mapreduce/'  
bucket = storage_client.bucket(bucket_name)

@functions_framework.http
def reducer(request):
    request_json = request.get_json(silent=True)

    if request_json and 'input_files' in request_json and 'output_file' in request_json:
        input_files = request_json['input_files']
        output_file = request_json['output_file']
    else:
        return 'Error: Missing input_files or output_file parameter.', 400


    def read_pickle_from_bucket(file_path):
        try:
            
            blob = bucket.blob(file_path)
            
            # Download the pickled data as bytes
            pickled_data_bytes = blob.download_as_bytes()
            
            # Deserialize the pickled data
            data_dict = pickle.loads(pickled_data_bytes)
            
            return data_dict
        except Exception as e:
            print(f"Error reading pickled data from bucket: {e}")
            raise

    def write_pickle_to_bucket(file_path, data_dict):
        print(file_path)
        try:
            blob = bucket.blob(file_path)
            
            # Serialize the data to pickle format
            pickled_data_bytes = pickle.dumps(data_dict)
            
            # Upload the pickled data to Google Cloud Storage
            blob.upload_from_string(pickled_data_bytes, content_type='application/octet-stream')
        except Exception as e:
            print(f"Error writing pickled data to bucket: {e}")
            raise

    combined_data = {}
    for input_file in input_files:
        data_dict = read_pickle_from_bucket(input_file)
        for key, doc_freq_list in data_dict.items():
            
            if key not in combined_data:
                existing_doc_ids = {}
                for doc_id, freq in doc_freq_list:
                    if doc_id in existing_doc_ids:
                        existing_doc_ids[doc_id] += freq
                    else:
                        existing_doc_ids[doc_id] = freq
                combined_data[key] =  list(sorted(existing_doc_ids.items(), key=lambda item: item[1], reverse=True))
            else:
                existing_doc_ids = {doc_id: freq for doc_id, freq in combined_data[key]}
                for doc_id, freq in doc_freq_list:
                    if doc_id in existing_doc_ids:
                        existing_doc_ids[doc_id] += freq
                    else:
                        existing_doc_ids[doc_id] = freq

                # Convert the updated doc_id frequencies back to a list
                combined_data[key] =  list(sorted(existing_doc_ids.items(), key=lambda item: item[1], reverse=True))

    write_pickle_to_bucket(output_file, combined_data)

    return 'OK'

