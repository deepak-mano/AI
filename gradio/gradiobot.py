import os
import gradio as gr
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSequence, RunnableMap, RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI, OpenAI # OpenAI chat model integration
from langchain_litellm import ChatLiteLLM, ChatLiteLLMRouter
from langchain_core.output_parsers import JsonOutputParser,CommaSeparatedListOutputParser
from pydantic import BaseModel, Field

def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
warnings.filterwarnings('ignore')

openai_model = ChatOpenAI(
    model="claude-3-5-sonnet-20241022",      # Must match the model_name in config.yaml
    openai_api_base="http://localhost:4000", # Your LiteLLM Proxy URL
    openai_api_key="sk-1234567890",  # Pass your virtual key if auth is enabled
    temperature=0.7
)

params = {
        "max_new_tokens": 128,
        "min_new_tokens": 10,
        "temperature": 0.5,
        "top_p": 0.2,
        "top_k": 1
    }


def generate_response(prompt_txt):
    generated_response = openai_model.invoke(prompt_txt,config={"metadata": params})
    return generated_response.content

# Create Gradio interface
chat_application = gr.Interface(
    fn=generate_response,
	#allow_flagging="never",
    inputs=gr.Textbox(label="Input", lines=2, placeholder="Type your question here..."),
    outputs=gr.Textbox(label="Output"),
    title="Chatbot",
    description="Ask any question and the chatbot will try to answer."
)

# Launch the app
chat_application.launch(server_name="127.0.0.1", server_port= 7860)