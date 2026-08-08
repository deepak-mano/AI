# Import necessary libraries and modules
import os
import gradio as gr
from llama_index.core import Settings, Document, SimpleDirectoryReader, VectorStoreIndex, GPTVectorStoreIndex, StorageContext, get_response_synthesizer, load_index_from_storage
from llama_index.readers.web import SimpleWebPageReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.core import get_response_synthesizer
from llama_index.core.data_structs import Node
from llama_index.core.response_synthesizers import ResponseMode

#from gradio.gradiobot import generate_response
#from pydantic import BaseModel, Field
#from langchain_community.chat_models import ChatOpenAI

Settings.llm = OpenAILike(
    model="claude-3-5-sonnet-20241022",
    api_key="sk-1234567890",
    api_base="http://localhost:4000",
    is_chat_model=True,
    is_local=True,
    is_function_calling_model=False,
    context_window=32000,
)

def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
warnings.filterwarnings('ignore')


#define Model and parameters


llm = OpenAILike(
    model="claude-3-5-sonnet-20241022",
    api_key="sk-1234567890",
    api_base="http://localhost:4000",
    is_chat_model=True,
    is_local=True,
    is_function_calling_model=False,
    context_window=32000,
)

os.environ["USER_AGENT"] = "MyRAG/1.0 (contact: deep-man@example.com)"

params = {
        "max_new_tokens": 128,
        "min_new_tokens": 10,
        "temperature": 0.5,
        "top_p": 0.2,
        "top_k": 1
    }


#Url
url="https://developer.nvidia.com/ai-models"
#Reading the Website content using SimpleWebPageReader
documents = SimpleWebPageReader(html_to_text=True).load_data([url])


#splitting into chunks/nodes
Settings.chunk_size = 300
Settings.chunk_overlap = 50
embed_model = HuggingFaceEmbedding()
index = VectorStoreIndex.from_documents(documents,embed_model=embed_model)

def generate_response1(prompt_txt):
    query_engine = index.as_query_engine(llm=llm, response_mode="tree_summarize", verbose=True, similarity_top_k=2)
    response = query_engine.query(prompt_txt)
    return str(response)

def generate_response2(prompt_txt):
    retriever = index.as_retriever(similarity_top_k=2)
    synthesizer = get_response_synthesizer(response_mode=ResponseMode.COMPACT)
    chunk = retriever.retrieve(prompt_txt)
    for node in chunk:
        print("- Node Text:", node.node.get_content())
        print("- Score:", node.score)
    response = synthesizer.synthesize(prompt_txt,nodes=chunk)
    return str(response)

print("AI Model Details")
type=input("Enter the type of index you want to search (query(1) or stepbystep(2): ")
prompt_txt = input("Enter your query: ")

if type=='1':
    Answer=generate_response1(prompt_txt)
    print("Answer: ", Answer)   
elif type=='2':
    Answer=generate_response2(prompt_txt)
    print("Answer: ", Answer)   


"""
# Create Gradio interface
chat_application = gr.Interface(
    fn=generate_response,
    inputs=gr.Textbox(label="Input Text", value="Enter text here"),
    outputs=gr.Textbox( label="Output Text", value="Response will appear here"),
    title="Chatbot",
    description="Ask any question and the chatbot will try to answer."
)


# Launch the app
chat_application.launch(server_name="127.0.0.1", server_port= 7860,share=False)
"""
