import os
#IBM WatsonX imports
#from ibm_watsonx_ai.foundation_models import Model
#from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
#from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes
#from langchain_ibm import WatsonxLLM
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSequence, RunnableMap, RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
#from langchain.chains import LLMChain  # Still using this for backward compatibility
from langchain_openai import ChatOpenAI, OpenAI # OpenAI chat model integration
from langchain_litellm import ChatLiteLLM, ChatLiteLLMRouter
from langchain_core.output_parsers import JsonOutputParser,CommaSeparatedListOutputParser
from pydantic import BaseModel, Field
#from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.documents import Document
#from langchain.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
###ignore warnings
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
warnings.filterwarnings('ignore')

#Chat model definition
openai_model = ChatOpenAI(
    model="claude-3-5-sonnet-20241022",      # Must match the model_name in config.yaml
    openai_api_base="http://localhost:4000", # Your LiteLLM Proxy URL
    openai_api_key="sk-1234567890",  # Pass your virtual key if auth is enabled
    temperature=0.7
)

#model defintion
model = OpenAI(
    model="claude-3-5-sonnet-20241022",      # Must match the model_name in config.yaml
    openai_api_base="http://localhost:4000", # Your LiteLLM Proxy URL
    openai_api_key="sk-1234567890",  # Pass your virtual key if auth is enabled
    temperature=0.7
)

#model invocation function
def llm_model(prompt_txt, params=None):
    
    response = openai_model.invoke(prompt_txt,config={"metadata": params})
    return response

print("1) Welcome to the Langchain Prompting Loop! Type 'exit' or 'quit' to end the session.\n")
print("2) prompting templates\n")
print("3) Difference between model and chat model\n")
print("4) chat model prompting with system and human messages\n")
print("5) output parsers\n")
print("6) document loaders\n")
print("7) text splitters\n")

opt1=input("Enter the option: ")

if opt1=='1':

    #prompting loop
    params = {
        "max_new_tokens": 128,
        "min_new_tokens": 10,
        "temperature": 0.5,
        "top_p": 0.2,
        "top_k": 1
    }
    prompt=input("Enter the prompt: ")
    while prompt!='exit' and prompt!='quit':
        response = llm_model(prompt, params)
        print(f"prompt: {prompt}\n")
        print(f"response : {response.content}\n")
        prompt=input("Enter the prompt: ")

elif opt1=='2':
    #prompting templates
    Adjective = input("Enter an adjective: ")
    Content = input("Enter the content: ")
    template = "Tell me a {adjective} joke about {content}."
    prompt = PromptTemplate.from_template(template)
    params = {
        "max_new_tokens": 128,
        "min_new_tokens": 10,
        "temperature": 0.9,
        "top_p": 0.2,
        "top_k": 1
    }

    #prompting template function    
    def format_prompt(variables):
            return prompt.format(**variables)
    

    joke_chain = (RunnableLambda(format_prompt)  | openai_model  | StrOutputParser())

    response = joke_chain.invoke({"adjective": Adjective, "content": Content})
    print(response)

elif opt1=='3':
    params = {
             "max_new_tokens": 128,
             "min_new_tokens": 10,
             "temperature": 0.5,
             "top_p": 0.2,
             "top_k": 1
         }
    description=input("Enter the description: ")
    msg1=model.invoke(description)   
    msg2=openai_model.invoke(description)
    print(f"model response      : {msg1}\n")
    print(f"chat model response : {msg2.content}\n")

elif opt1=='4':
    params = {
            "max_new_tokens": 128,
            "min_new_tokens": 10,
            "temperature": 0.1,
            "top_p": 0.2,
            "top_k": 1
        }
    Genre=input("Enter the genre: ")
    msg1=openai_model.invoke([
        SystemMessage(content="You are a helpful AI bot that assists a user in choosing the one perfect movie to watch based on their preferences. The response will be just one movie name"),
        HumanMessage(content="I enjoy adventure films, what should I watch?")])
    print(f"chat model response for adventure movies : {msg1.content}\n")

    prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a helpful AI bot that assists a user in choosing the one perfect movie to watch based on their preferences. The response will be just one movie name"),
     ("user", "I enjoy {genre} films, what should I watch?")
     ])
    
    input_={"genre": Genre}
    prompt_value=prompt.invoke({"genre": Genre})
    print(f"prompt value : {prompt_value}\n")
    chain=prompt | openai_model | StrOutputParser()
    msg3=chain.invoke(input_)
    print(f"chat model response for {Genre} films : {msg3}\n")

elif opt1=='5':
    parsr=input("Enter the parser type (json/comma): ")
    movie=input("Enter the movie name: ")

    class MovieSummary(BaseModel):
        title: str = Field(description="The official title of the movie")
        release_year: int = Field(description="The year the movie was released")
        genres: list[str] = Field(description="A list of genres matching the movie")
        one_sentence_plot: str = Field(description="A brief summary of the main plot")

    if parsr=='json':
        parser1 = JsonOutputParser(pydantic_object=MovieSummary)
        
        prompt1 = PromptTemplate(
        template="Answer the user query based on the following format instructions.\n{format_instructions}\n\nQuery: {query}",
        input_variables=["query"],
        partial_variables={"format_instructions": parser1.get_format_instructions()},)

        chain1 = prompt1 | openai_model | parser1

        result = chain1.invoke({"query": f"Tell me about the movie {movie}"})

    elif parsr=='comma':
        parser2 = CommaSeparatedListOutputParser(pydantic_object=MovieSummary)

        prompt2 = PromptTemplate(
        template="Answer the user query based on the following format instructions.\n{format_instructions}\n\nQuery: {query}",
        input_variables=["query"],
        partial_variables={"format_instructions": parser2.get_format_instructions()},)
        
        chain2 = prompt2 | openai_model | parser2

        result = chain2.invoke({"query": f"Tell me about the movie {movie}"})

    print(result)

elif opt1=='6':
    ld=input("Enter the loader type (pdf/html): ")
    print("In development")
    if ld=='pdf':
        loader = PyPDFLoader("https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf")
    elif ld=='html':
        loader = WebBaseLoader("https://docs.pytorch.org/tutorials/beginner/basics/intro.html")
    document = loader.load()
    print(f"Document content: {document[0].page_content[:1000]}")  # print the page 1's first 1000 tokens
    print(f"Document metadata: {document[0].metadata}")  # print the page 1's metadata

elif opt1=='7':
    web_url = "https://www.york.ac.uk/teaching/cws/wws/webpage1.html"
    web_loader = WebBaseLoader(web_url)
    web_document = web_loader.load()
    splitter_1 = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30, separators=["\n\n", "\n", ".", "!", "?", " ", ""],)
    chunks_1 = splitter_1.split_documents(web_document)

    for chunk in chunks_1:
        print(f"Chunk content: {chunk.page_content[:300]}")  # print the first 1000 tokens of each chunk 