import chromadb
from chromadb.utils import embedding_functions

# 1. Initialize the client (use PersistentClient to save to disk)
client = chromadb.PersistentClient(path="./my_chroma_db")

# 2. Create or get a collection
def perform_get_collection(coll_name):
    query_text=input("Enter the query text : ")
    topics=input("Enter the topic : ")
    try:
        collection = client.get_collection(name=coll_name)
        results=collection.query(
            query_texts=[query_text],
            n_results=1,
            where={'topic': topics},
            where_document={'$not_contains': 'library'}
                )
    
        # Check if no results are returned or if the results array is empty
        if not results or not results['ids'] or len(results['ids'][0]) == 0:
            # Log a message indicating that no similar documents were found for the query term
            print(f'No documents found similar to "{query_text}"')
            return

        print(f'Top 3 similar documents to "{query_text}":')
        # Access the nested arrays in 'results["ids"]' and 'results["distances"]'
        for i in range(min(3, len(results['ids'][0]))):
            doc_id = results['ids'][0][i]  # Get ID from 'ids' array
            score = results['distances'][0][i]  # Get score from 'distances' array
            # Retrieve text data from the results
            text = results['documents'][0][i]
            if not text:
                print(f' - ID: {doc_id}, Text: "Text not available", Score: {score:.4f}')
            else:
                print(f' - ID: {doc_id}, Text: "{text}", Score: {score:.4f}')

    except Exception as error:
        print(f"Error in deleting collection: {error}")
