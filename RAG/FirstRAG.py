def warn(*args, **kwargs):
    pass

import warnings
warnings.warn = warn
warnings.filterwarnings("ignore")

import wget
import os
#from huggingface_hub import login
#login()
# This saves the token securely to your local HF home directory
#login(token=os.environ.get("HF_TOKEN"))

os.environ["USER_AGENT"] = "MyRAG/1.0 (contact: deep-man@example.com)"
# LangChain
from langchain_community.document_loaders import TextLoader, PyPDFLoader, WebBaseLoader
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.chains import RetrievalQA, ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAI # OpenAI chat model integration
from langchain_litellm import ChatLiteLLM, ChatLiteLLMRouter
from langchain_core.output_parsers import JsonOutputParser,CommaSeparatedListOutputParser

# IBM watsonx
#from ibm_watsonx_ai.foundation_models import Model
#from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
#from ibm_watsonx_ai.foundation_models.utils.enums import (
#    ModelTypes,
#    DecodingMethods,
#)
#from langchain_ibm import WatsonxLLM

print("All imports successful!")

filename = 'companyPolicies.txt'
url = 'https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/6JDbUb_L3egv_eOkouY71A.txt'

# Use wget to download the file
wget.download(url, out=filename)
print('file downloaded')

with open(filename, 'r') as file:
    # Read the contents of the file
    contents = file.read()
 #   print(contents)

Chunk_size=int(input("Enter the chunk size: "))

print("1) Print complete contents of the file\n")
print("2) Print the count of the chunks\n")
print("3) Print all the chunks\n")

opt1=input("Enter an option (1, 2, or 3) and press Enter to continue...")

loader = TextLoader(filename)
documents = loader.load()
#text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=Chunk_size, chunk_overlap=30, separators=["\n\n", "\n", ".", "!", "?", " ", ""],)
chunks = text_splitter.split_documents(documents)

if opt1 == '1':
    print(contents) 

elif opt1 == '2':
    print(f"Total number of chunks: {len(chunks)}")

elif opt1 == '3':
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(chunk.page_content)


embeddings = HuggingFaceEmbeddings()
docsearch = Chroma.from_documents(chunks, embeddings)  # store the embedding in docsearch using Chromadb
print('document ingested')

openai_model = ChatOpenAI(
    model="claude-3-5-sonnet-20241022",      # Must match the model_name in config.yaml
    openai_api_base="http://localhost:4000", # Your LiteLLM Proxy URL
    openai_api_key="sk-1234567890",  # Pass your virtual key if auth is enabled
    temperature=0.7
)

#context and question are keywords in the RetrievalQA, so LangChain can automatically recognize them as document content and query.
prompt_template = """Use the information from the document to answer the question at the end. If you don't know the answer, just say that you don't know, definitely do not try to make up an answer.

{context}

Question: {question}
"""


PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

chain_type_kwargs = {"prompt": PROMPT}
memory = ConversationBufferMemory(memory_key = "chat_history", return_message = True)

qa = RetrievalQA.from_chain_type(llm=openai_model, 
                                 chain_type="stuff", 
                                 retriever=docsearch.as_retriever(),
                                 memory = memory, 
#                                 get_chat_history=lambda h : h,
                                 chain_type_kwargs=chain_type_kwargs, 
                                 return_source_documents=False)


#query=input("Enter your query: ")
#response = qa.invoke(query)
#print(response)

history = []
while True:
    query = input("Question: ")

    if query.lower() in ["quit","exit","bye"]:
        print("Answer: Goodbye!")
        break

    response = qa.invoke(query)
    print("Answer: ", response["result"])
     
 #   result = qa({"question": query}, {"chat_history": history})
 #   history.append((query, result["answer"]))

    