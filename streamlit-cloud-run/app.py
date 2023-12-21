import streamlit as st
import pickle


from google.cloud import storage

def get_inverted_index(bucket_name = 'bucket-shivanipal', file_name = 'mapreduce/inverted_index.pkl'):
    try:
        storage_client = storage.Client.from_service_account_json('shivani-pal-fall2023.json')
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        # Check if the blob (file) exists
        if not blob.exists():
            return None  # Return None to indicate that the file is not present

        content = blob.download_as_string()
        inverted_index = pickle.loads(content)
        return inverted_index
    except Exception as e:
        print(f"Error: {e}")
        return None

# Function to search the inverted index
def search_inverted_index(query, inverted_index):
    results = inverted_index.get(query, [])
    return results

def main():
    st.title("Inverted Index Search App")

    # Sidebar for user input
    st.sidebar.header("Search Parameters")
    query = st.sidebar.text_input("Enter search term:", "")

    if st.sidebar.button("Search"):
        if not query:
            st.warning("Please enter a search term.")
        else:
            inverted_index = get_inverted_index()

            if inverted_index is None:
                st.warning("The inverted index file is still in progress. Please try again later.")
            else:
                results = search_inverted_index(query, inverted_index)

                # Display search results
                st.subheader("Search Results")
                if results:
                    for result in results:
                        st.write(f"- Document: {result}")
                else:
                    st.write("No matching documents found.")

if __name__ == "__main__":
    main()

