# Setup
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="./my_chroma_db")

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


# Function to perform a similarity search in the collection
def perform_create_collection(coll_name):
    try:
        # Collection creation
        client = chromadb.PersistentClient(path="./my_chroma_db")
        collection = client.create_collection(
            name=coll_name,
            metadata={"topic": "query testing"},
            configuration={
                "hnsw": {
                    "space": "cosine",
                    "ef_search": 100,
                    "ef_construction": 100,
                    "max_neighbors": 16
                },
                "embedding_function": ef
            }
        )

    except Exception as error:
        print(f"Error in creating collection: {error}")


def perform_list_collection():
    try:
        # Collection creation
        collections = client.list_collections(limit=100, offset=0)
        for collection in collections:
            print(collection.name)
    except Exception as error:
        print(f"Error in retrieving collection list: {error}")


def perform_delete_collection(coll_name):
    try:
        # Collection creation
        client.delete_collection(name=coll_name)

    except Exception as error:
        print(f"Error in deleting collection: {error}")

