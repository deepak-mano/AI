import chromadb
from chromadb.utils import embedding_functions


# 1. Initialize the client (use PersistentClient to save to disk)
client = chromadb.PersistentClient(path="./my_chroma_db")
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)



def perform_insert_collection(coll_name):
    try:
        ef = embedding_functions.SentenceTransformerEmbeddingFunction( model_name="all-MiniLM-L6-v2")
        collection = client.get_or_create_collection(name=coll_name,embedding_function=ef)
        docs=[
                    "Giant pandas are a bear species that lives in mountainous areas.",
                    "A pandas DataFrame stores two-dimensional, tabular data",
                    "I think everyone agrees that pandas are some of the cutest animals on the planet",
                    "A direct comparison between pandas and polars indicates that polars is a more efficient library than pandas.",
                ]
        meta=[
                {"topic": "animals"},
                {"topic": "data analysis"},
                {"topic": "animals"},
                {"topic": "data analysis"},
            ]
        id = [f"food_{index + 1}" for index, _ in enumerate(docs)]

        collection.add(documents=docs,metadatas=meta,ids=id)

    except Exception as error:
            print(f"Error in inserting data: {error}")