import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings

# 1. Initialize the client (use PersistentClient to save to disk)
#client = chromadb.PersistentClient(path="./my_chroma_db",settings=Settings(anonymized_telemetry=False))
client = chromadb.PersistentClient(path="./my_chroma_db")

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

#local lib import
from chroma_create_test import perform_create_collection, perform_list_collection, perform_delete_collection
from chroma_insert_test import perform_insert_collection
from chroma_read_test import perform_get_collection




def main():
    coll_name=input("Enter the Collection Name : ")
    print("(1) Create Collection ")
    print("(2) Read Collection")
    print("(3) Insert data into collection ")
    print("(4) List Collection")
    print("(5) Delete Collection")
    print("(6) Exit")
    opt=input("Enter an option (1/2/3/4/5/6) : ")

    if opt=="1":
       perform_create_collection(coll_name) 
    elif opt=="2":
        perform_get_collection(coll_name)
    elif opt=="3":
        perform_insert_collection(coll_name)
    elif opt=="4":
        perform_list_collection()
    elif opt=="5":
        perform_delete_collection(coll_name)
    else:
        print("Exit")
    

if __name__ == "__main__":
    main()