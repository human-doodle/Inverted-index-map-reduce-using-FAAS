# Inverted-index-map-reduce-using-FAAS
Inverted index creation using map-reduce paradigm on Google Functions (FAAS)


Map-Reduce with Cloud Functions

1. Description

This report outlines the design and implementation of a parallel Map-Reduce system using Google Cloud Functions for the purpose of building a simple text-search engine. The system aims to compute an inverted index of a large text corpus, providing a web-based search interface like the early search engines.

 ![image](https://github.com/human-doodle/Inverted-index-map-reduce-using-FAAS/assets/46643099/a1f7d321-f2b4-4c1d-aece-56015af43f25)



2. Map-Reduce on Cloud Functions

The primary focus of this assignment is to leverage Functions as a Service (FaaS), Google Cloud Functions, to implement parallel Map-Reduce. The implementation involves launching multiple map tasks in parallel, barrier synchronization, parallel reduce operations, and efficient organization of output.

3. Data Source

The text corpus used for this project is derived from Project Gutenberg. Each text file is stored in a folder and then a key value pair is made with doc name(id) and content of the .txt. The data is stored on ingested in Google cloud bucket as a json file. Since mappers are fed data in chunks, the data is divided and stored according to the number of mappers. 

4. Map-Reduce Design for Index Construction:

All map and reduce operations are orchestrated within cloud functions. The design includes launching parallel map tasks, implementing a barrier synchronization mechanism using a master code, and executing parallel reduce tasks. 

![image](https://github.com/human-doodle/Inverted-index-map-reduce-using-FAAS/assets/46643099/39bd6cc8-ec44-491c-9c47-791dbd90e50c)


 
Ref: https://nlp.stanford.edu/IR-book/html/htmledition/distributed-indexing-1.html

In the context of index construction, the Map-Reduce paradigm is employed to efficiently handle the complexity of distributed indexing. For indexing, the key-value pairs take the form of (termID, (docID, count).
1.	Mapping Phase:
o	Map-Reduce utilizes parsers during the map phase to transform input data splits into key-value pairs, following a SPIMI parsing algorithm.
o	Parsers generate local intermediate files called segment files, representing different term partitions (e.g., a-f, g-p, q-z taken for simplicity. My code uses a hashing function: ord[key]%r).
2.	Reducing Phase:
o	To optimize data retrieval, keys are partitioned into term partitions (e.g., a-f, g-p, q-z), and each partition is assigned to an inverter during the reduce phase.
o	Inverters collect and process all values (docIDs) for a given key (termID) within a term partition.
o	The master assigns term partitions to inverters and reassigns in case of failures or delays.
3.	Task of Master:
o	Parsers and inverters are working on worker nodes; the master dynamically assigns tasks.

5. Front End

A front-end function is created for triggering search operations. It accepts search terms as parameters and returns a list of documents containing the search term. The order in which the documents are returned is based on the frequency of the term in the document. The user interface is a simple python stream-lit web-based UI hosted on Google Cloud Run.

Following are the screen shots showing two scenarios: 
1.	When inverted index is created, it returns the query result
2.	When inverted index generation is in progress

 
![image](https://github.com/human-doodle/Inverted-index-map-reduce-using-FAAS/assets/46643099/0f40b603-4926-4635-ba20-9e1f010ced6f)



![image](https://github.com/human-doodle/Inverted-index-map-reduce-using-FAAS/assets/46643099/d5b7884e-7747-44a1-ba0b-4ec9ec509b38)


 


6. Method Design

1. Mapper Function

1.1	Function Signature
def mapper(request: Request) -> str

1.2 Description
The mapper function receives an HTTP request (request) with parameters 'id', 'no_partition', and 'inputfile'. It reads a JSON file(input file chunk) from Cloud Storage, processes the content to extract terms and document information, performs mapping operations, and writes the results to intermediate files in Cloud Storage.
I implemented the mapper function using the SPIMI algorithm, a highly efficient approach for indexing large collections, which offers scalability, memory efficiency, and compression for improved performance in information retrieval systems. Following is the algorithm used for the code:
 

<img width="440" alt="image" src="https://github.com/human-doodle/Inverted-index-map-reduce-using-FAAS/assets/46643099/ad177e99-5633-4b73-bc81-d0edc4b3464b">


1.3 Trigger
The mapper function is triggered by an HTTP request. It is called by Master via a HTTP request.

The HTTP request should have the following JSON structure:

Request: Request
{
  "id": "unique_id_of_mapper",
  "no_partition": “number_of_term_partition”,
  "inputfile": "path/to/inputfile.json"
}
Where:

"id" is a unique identifier for the mapper.
"no_partition" specifies the number of term partions.
"inputfile" is the path to the JSON file in Cloud Storage containing the document data.

2. Reducer Function
2.1 Function Signature
def reducer(request: Request) -> str 

2.2 Description
The reducer function receives an HTTP request (request) with parameters 'input_files' and 'output_file'. It reads pickled data from Cloud Storage, combines among all term partitions, and reduces the data, and writes the results back to Cloud Storage. Returns a string with status. We try to spawn less reducers than the number of mappers, reason being, that it is necessary for each Map task to create an intermediate file for each Reduce task, and if there are too many Reduce tasks the number of intermediate files explodes.

2.3 Trigger
The reducer function is triggered by an HTTP request. It expects a JSON payload with 'input_files' and 'output_file' parameters.
The HTTP request should have the following JSON structure:

{ 
"input_files": ["path/to/input_file1", "path/to/input_file2"], 
"output_file": "path/to/output_file" 
} 
Where:
•	"input_files" is a list of paths to mapper intermediate files in Cloud Storage.
•	"output_file" is the path to the reducer output file in Cloud Storage where reducer is supposed to store it’s intermediate files.
The reducer function then processes the provided input parameters to perform reducing operations.

3. Master Function

3.1 Function Signature
def master(cloud_event) -> str 

3.2 Description
The master function serves as the coordinator for a MapReduce operation triggered by changes in a Google Cloud Storage bucket(whenever new files are added/ modified). Returns status as string. This function orchestrates the execution of mapper and reducer functions in parallel. The function performs the following tasks:

•	Mapper Function Execution: Initiates multiple instances of the mapper function (run_mapper) in parallel using the ThreadPool module. Each mapper processes a chunk of input data and generates intermediary files in Cloud Storage.

•	Reducer Function Execution: Initiates multiple instances of the reducer function (run_reducer) in parallel using the ThreadPool module. Each reducer processes the outputs generated by corresponding mappers and produces intermediary files.

•	Combining Reducer Outputs: Combines the outputs of reducer functions to create a consolidated inverted index. The combined data is stored in a single pickled file (inverted_index.pkl) within the Cloud Storage bucket.

•	Cleanup of Intermediary Files: Removes intermediary files generated by mappers and reducers to optimize storage resources.

•	Status Monitoring: Monitors and reports the status of each phase, ensuring the successful completion of both mappers and reducers. 

•	HTTP Request Payload Expectation: Expects a predefined JSON payload structure in the triggering HTTP request. This structure includes the paths to input and output files for both mappers and reducers.


3.3	Trigger
The function is triggered by changes in a specified Google Cloud Storage bucket, reacting to events such as file additions or modifications. Aimed to generate new inverted-index whenever there’s a new addition of text file in the Google storage.


7. Components

7.1. Web-based UI
The web-based UI is a static site hosted on Google Cloud Run. It has a single textbox for entering search terms and displays a list of documents containing the search term. If the inverted index generation is in progress, it shows Inverted-index creation is in progress.
I developed a Streamlit web application to provide a user-friendly interface for searching within the processed documents. The application includes a search page that queries a precomputed inverted index stored in Google Cloud Storage. The search results display the documents where a specified word is present, accompanied by the corresponding word frequencies in each document.
Implementation Steps
1.	Building the Streamlit Web App:
2.	Dockerization:
o	Developed a Dockerfile to containerize the Streamlit web application.
o	Created a requirements.txt file to specify the application dependencies.
Deployment Process
1.	Dockerfile and Requirements.txt:
o	Ensured a well-structured Dockerfile and requirements.txt to encapsulate the web application and its dependencies.
2.	Google Cloud Run Deployment:
o	Executed gcloud commands to build the Docker container image.
o	Deployed the containerized Streamlit web app on Google Cloud Run.
o	
# Build applocation
```
gcloud builds submit --tag gcr.io/shivani-pal-fall2023/streamlit-shivani  --project=shivani-pal-fall2023
```
# Command to deploy the application
```
gcloud run deploy --image gcr.io/shivani-pal-fall2023/streamlit-shivani --platform managed  --project=shivani-pal-fall2023 --allow-unauthenticated
```

The deployed Streamlit web application is accessible via the following URL:
 https://streamlit-shivani-kofasnhdsa-ue.a.run.app 
 

7.2. Streaming Search

It supports streaming search functionality, updating the inverted index as new documents are added to the corpus, and displays appropriate status when the generation is in progress.

The flow:

 
						<img width="1235" alt="image" src="https://github.com/human-doodle/Inverted-index-map-reduce-using-FAAS/assets/46643099/9a995077-a2a1-4920-b390-a63f9b62f240">



8. Clean Up
To maintain correctness and control costs, thorough cleanup of state between each run is essential. That is, once inverted index is generated, all mapper intermediate and reducer files are deleted from the google storage.

9. Tricky Parts

9.1. Barrier
To ensure effective coordination among parallel tasks in the MapReduce implementation, a barrier synchronization mechanism has been incorporated. That is, the reducer is initiated only when all mapper workers successfully complete their respective tasks. This synchronization is achieved through the use of status values returned by each mapper and reducer function.
Implementation Details
1.	Each mapper and reducer function returns a status value upon completion of its execution.
2.	The barrier condition is established by waiting for "OK" status from all the mapper tasks before proceeding to the execution of reducers. The synchronization is crucial to ensure that the reducer is only initiated when the mapping phase has been successfully completed.

9.2. Intermediate Data Communication
The master function serves as the central hub for communication within the MapReduce system, overseeing the coordination and data flow between mappers and reducers. It takes on the responsibility of collecting and disseminating crucial information, ensuring a seamless transition from the mapping to the reducing phase. For example, it does the following:
1.	Intermediate File Location Collection:
   
o	Upon the successful completion of all mapper tasks, the master function collects the location values of the generated intermediary files.

o	These intermediary files encapsulate partial results or outputs produced during the mapping phase.

3.	Communication with Reducers:
   
o	The master, having gathered all necessary information, communicates with the reducers.

o	It transmits the collected intermediary file locations to the reducers, enabling them to retrieve and process the relevant data for further computations.


10. References:

Justin Zobel and Alistair Moffat. 2006. Inverted files for text search engines. ACM Comput. Surv. 38, 2 (2006), 6–es. https://doi.org/10.1145/1132956.1132959
https://courses.engr.illinois.edu/cs423/sp2014/MPs/mp4/MP4.html#tok
https://github.com/HiGal/GUSE
https://courses.engr.illinois.edu/cs423/sp2014/MPs/mp4/MP4.html
https://www.dcs.bbk.ac.uk/~dell/teaching/cc/book/ditp/ditp_ch3.pdf
https://dmice.ohsu.edu/bedricks/courses/cs624/lecs/w2_lec1.pdf 
https://nlp.stanford.edu/IR-book/html/htmledition/distributed-indexing-1.html
https://nlp.stanford.edu/IR-book/html/htmledition/single-pass-in-memory-indexing-1.html
https://www.youtube.com/watch?v=sUCiLIXjENw
https://web.stanford.edu/class/archive/cs/cs110/cs110.1196/static/lectures/18-mapreduce.pdf
