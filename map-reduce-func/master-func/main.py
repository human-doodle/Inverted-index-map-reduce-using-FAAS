import re
import json
import pickle
from google.cloud import storage
import functions_framework

# Define the Google Cloud Storage client
storage_client = storage.Client.from_service_account_json('shivani-pal-fall2023.json')
bucket_name = 'bucket-shivanipal'
folder = 'mapreduce/'  
bucket = storage_client.bucket(bucket_name)


bucket_name_for_files = 'shivanipal-files'
bucket_forfiles =  storage_client.bucket(bucket_name_for_files)



@functions_framework.http
def mapper(request):
    request_json = request.get_json(silent=True)
    if not request_json or 'id' not in request_json or 'no_partition' not in request_json or 'inputfile' not in request_json:
        return 'Bad Request: JSON payload must include "id", "no_partition", and "inputfile".'

    def read_json_from_bucket(file_path):
        """Read a JSON file from Google Cloud Storage and parse it into a Python dictionary."""
        print(file_path)
        blob = bucket_forfiles.blob(file_path)
        # Download the content of the JSON file as bytes
        json_content_bytes = blob.download_as_bytes()
        # Decode the bytes into a string and parse it as JSON
        json_content = json_content_bytes.decode('utf-8')
        document_dict = json.loads(json_content)

        return document_dict


    def getfullpath(path):
        return folder + path


    def process_token_stream(token_stream):
        output_files = []

        while True:
            dictionary = {}

            while True:
                token = next(token_stream, None)

                if token is None:
                    break

                term = extract_term(token)

                if term in dictionary:
                    postings_list = dictionary[term]
                else:
                    postings_list = []

                postings_list.append(extract_docID(token))
                dictionary[term] = postings_list
            output_file = divide_dictionary(dictionary)
            output_files.append(output_file)

            if token is None:
                break

        return output_files


    def extract_term(token):
        term = token[0]
        return term


    def extract_docID(token):
        docid = token[1]
        return docid


    def write_block_to_disk(dictionary, part):
        output_file_path = getfullpath(f'mapper_intermediate_file/m{doc_counter}/{part}.pkl')
        blob = bucket.blob(output_file_path)
        blob.upload_from_string(pickle.dumps(dictionary), content_type='application/octet-stream')

        return output_file_path


    def divide_dictionary(dictionary):
        partitions = [{} for _ in range(no_partition)]
        op_files = []
        for key, value in dictionary.items():
            first_letter = key[0].lower()
            partition_index = ord(first_letter) % no_partition

            partitions[partition_index][key] = value
        for i, partition in enumerate(partitions):
            op_files.append(write_block_to_disk(partition, i))
        return op_files


    def tokenize(text):
        # return re.findall(r'\b\w+\b', text.lower())
        return re.findall(r'\b\w+\b', re.sub(r'[\r\n]', ' ', text.lower()))



    def parse_documents(document_dict):
        for doc_id, document in document_dict.items():
            terms = tokenize(document)
            for term in terms:
                yield (term, (doc_id, 1))

    id = request_json['id']
    no_partition = request_json['no_partition']
    inputfile = request_json['inputfile']

    document_dict = read_json_from_bucket(inputfile)

    doc_counter = id

    term_doc_generator = parse_documents(document_dict)
    token_stream = ((token, (doc_id, count)) for token, (doc_id, count) in term_doc_generator)

    output_files = process_token_stream(token_stream)

    return json.dumps({"status": "OK", "files": output_files})