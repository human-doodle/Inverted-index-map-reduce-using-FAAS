import functions_framework
from multiprocessing.pool import ThreadPool
from google.cloud import storage
import requests
import pickle

from config import input_data, num_mappers, num_reducers




# Define the Google Cloud Storage client
storage_client = storage.Client.from_service_account_json('shivani-pal-fall2023.json')
bucket_name = 'bucket-shivanipal'
folder = 'mapreduce/'  
bucket = storage_client.bucket(bucket_name)

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def master(cloud_event):

    data = cloud_event.data

    

    def getfullpath(path):
        return folder+path



    # Function to clean up files in a bucket directory
    def clean_up_dir(directory):
        try:
            blobs = bucket.list_blobs(prefix=getfullpath(directory))
            for blob in blobs:
                blob.delete()
            return True
        except Exception as e:
            return False 

    def run_mapper(input_data_chunk,  unique_id, num_reducers):
        function_url = "https://us-central1-shivani-pal-fall2023.cloudfunctions.net/mapper"

        # Prepare the payload for the HTTP request
        payload = {
            "id": unique_id,
            "no_partition": num_reducers,
            "inputfile": input_data_chunk
        }

        # Make an HTTP request to trigger the function
        response = requests.post(function_url, json=payload)

        # Check the response
        if response.status_code == 200:
            response_dict = response.json()
            return "OK", response_dict.get('files', [])  
        else:
            return "Error", response.text

    def run_reducer(input_data_chunk, output_directory):
        cloud_function_url = "https://us-central1-shivani-pal-fall2023.cloudfunctions.net/reducer"
        output_file_path = f"{output_directory}/{input_data_chunk[0].split('/')[3].split('.')[0]}.pkl"
        print(input_data_chunk)
        
        try:
            # Assuming input_data_chunk is a list of strings
            payload = {
                'input_files': input_data_chunk,
                'output_file': getfullpath(output_file_path)
            }
            
            response = requests.post(cloud_function_url, json=payload)
            
            if response.status_code == 200:
                return "OK", output_file_path
            else:
                return "Error", f"HTTP request failed with status code {response.status_code}"
        except Exception as e:
            return "Error", str(e)

    def run_map_reduce_parallel(input_data, num_mappers, num_reducers):
        # Step 1: Map Phase (Run mappers in parallel)
        
        with ThreadPool(processes=num_mappers) as pool:
            unique_ids = range(len(input_data))  # Unique IDs for each mapper
            mapper_inputs = [(chunk,  unique_id, num_reducers) for chunk, unique_id in zip(input_data, unique_ids)]
            status, mapper_outputs = zip(*pool.starmap(run_mapper, mapper_inputs))

            while True:
                if all(s == "OK" for s in status ) and len(status)==num_mappers:
                    print("All mappers completed successfully.")
                    break
                else:
                    print("Some mappers failed. Check the status for details.")
                   
        

        # Step 3: Reduce Phase
        reducer_outputs = []
    
        output_directory_path = 'reducer_output'

        with ThreadPool(processes=num_reducers) as pool:
            
            reducer_inputs = [([file[0][r] for file in mapper_outputs], output_directory_path) for r in range(num_reducers)]
            
            status, reducer_outputs = zip(*pool.starmap(run_reducer, reducer_inputs))

            while True:
                if all(s == "OK" for s in status) and len(status)==num_reducers:
                    print("All mappers completed successfully.")
                    break
                else:
                    print("Some reducers failed. Check the status for details.")
        
       

        combine_pickle_files(list(reducer_outputs), 'inverted_index.pkl')

        clean_up_dir('mapper_intermediate_file')

        clean_up_dir('reducer_output')

    def combine_pickle_files(input_files, output_file):
        combined_data = {}

        for input_file in input_files:
            blob = bucket.blob(getfullpath(input_file))
            data = pickle.loads(blob.download_as_string())
            # data = pickle.loads(blob.download_as_bytes())
            
            combined_data.update(data)

        blob_output = bucket.blob(getfullpath(output_file))
        blob_output.upload_from_string(pickle.dumps(combined_data), content_type='application/octet-stream')

    ii_del = clean_up_dir('inverted_index.pkl')
    if ii_del:
        print("updating inverted index...")

    # run map reduce 
    result = run_map_reduce_parallel(input_data, num_mappers, num_reducers)
    print(result)
    
    return "OK"



