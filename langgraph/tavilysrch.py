import os
import json
import getpass
from typing import (Annotated,Sequence,TypedDict,List,Dict)
from pydantic import BaseModel, Field
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage, SystemMessage
from langchain_tavily._utilities import TavilySearchAPIWrapper
from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langgraph.graph import END,  StateGraph, MessagesState, MessageGraph
from langgraph.graph.message import add_messages
import warnings 
warnings.filterwarnings('ignore')

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
import os
import json

print("Model Defintion")
#Model Defintion
llm = ChatOpenAI(
    model="llama3.2-3b",      # Must match the model_name in config.yaml
    openai_api_base="http://localhost:4000", # Your LiteLLM Proxy URL
    openai_api_key="sk-1234567890",  # Pass your virtual key if auth is enabled
    temperature=0.7
)


class AgentState(TypedDict):
    """The state of the agent."""

    # add_messages is a reducer
    # See https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
    messages: Annotated[Sequence[BaseMessage], add_messages]

class Reflection(BaseModel):
	missing: str = Field(description="What information is missing")
	superfluous: str = Field(description="What information is unnecessary")

class AnswerQuestion(BaseModel):
	answer: str = Field(description="Main response to the question")
	reflection: Reflection = Field(description="Self-critique of the answer")
	search_queries: List[str] = Field(description="Queries for additional research")
     
print("prompt template definition")
#Prompt templates
prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are Dr. Paul Saladino, "Carnivore MD," advocating for animal-based nutrition and challenging plant-centric dietary dogma. Focus on the superior bioavailability of animal foods and the potential toxicity of plant compounds such as oxalates, lectins, and phytates.

        Your response must follow these steps:
        1. {first_instruction}
        2. Present the evolutionary and biochemical rationale for animal-based nutrition, emphasizing nutrient density, bioavailability, and the absence of plant antinutrients.
        3. Challenge conventional "plants are healthy" narratives with mechanistic evidence about plant defense compounds and their impact on human physiology.
        4. Reflect and critique your answer. Be rigorous about evolutionary consistency and nutrient science.
        5. After the reflection, **list 1-3 search queries separately** for researching antinutrients, bioavailability studies, or evolutionary nutrition. Do not include them inside the reflection.

        Focus on: organ meats as superfoods, the carnivore elimination protocol, and why "fiber is unnecessary" based on human evolutionary biology.
        """
    ),
    MessagesPlaceholder(variable_name="messages"),
    (
        "system", 
        "Answer the user's question above using the required format, emphasizing the superiority of animal-based nutrition."
    ),
])

question="Any ideas for a healthy breakfast"
first_responder_prompt = prompt_template.partial(first_instruction="Provide a detailed ~250 word answer")


revise_instructions = """Revise your previous answer using the new information, applying the rigor and evidence-based approach of Dr. David Attia.
- Incorporate the previous critique to add clinically relevant information, focusing on mechanistic understanding and individual variability.
- You MUST include numerical citations referencing peer-reviewed research, randomized controlled trials, or meta-analyses to ensure medical accuracy.
- Distinguish between correlation and causation, and acknowledge limitations in current research.
- Address potential biomarker considerations (lipid panels, inflammatory markers, and so on) when relevant.
- Add a "References" section to the bottom of your answer (which does not count towards the word limit) in the form of:
- keep the response with in 250 words
- [1] https://example.com
- [2] https://example.com
- Use the previous critique to remove speculation and ensure claims are supported by high-quality evidence. Keep response under 250 words with precision over volume.
- When discussing nutritional interventions, consider metabolic flexibility, insulin sensitivity, and individual response variability.
"""
revisor_prompt = prompt_template.partial(first_instruction=revise_instructions)
# Langgraph code
tavily_tool=TavilySearch(max_results=1)
MAX_ITERATIONS = 2

class ReviseAnswer(AnswerQuestion):    
    """Revise your original answer to your question."""
    references: List[str] = Field(description="Citations motivating your updated answer.")

print("Tavily Defintion")
def _set_if_undefined(var: str) -> None:
    if os.environ.get(var):
        return
    os.environ[var] = getpass.getpass(var)
_set_if_undefined("TAVILY_API_KEY")


def event_loop(state: AgentState) :
    print("Event Loop Executing")    
    #print(state["messages"])
    count_tool_visits = sum(isinstance(item, ToolMessage) for item in state["messages"])
    num_iterations = count_tool_visits
    print (f'num_iterations :  {num_iterations}')
    if num_iterations >= MAX_ITERATIONS:
        return END
    print("Event Loop Ended")   
    return "execute_tools"


def gen_init_resp(state: AgentState) :
    """ uses the LLM to get the response for the prompt"""
    print("gen_init_resp started")

    #print(f'[HumanMessage("content")]   : {[HumanMessage("content")]}')

    initial_chain = first_responder_prompt| llm.bind_tools(tools=[AnswerQuestion])
    response=initial_chain.invoke({"messages":[HumanMessage("content")]})
    #print(f'response : {response} \n')
    state["messages"] = add_messages(state["messages"], [response])
    #print("state messages")
    #print (state["messages"])
    print("gen+init+resp ended")
    return state


def review_resp(state: AgentState) :
    """ uses the LLM to review the tool response"""
    print("review_resp started")
    #print(f'state[messages]  : {state["messages"][-1]}  \n')
    #tool_messages = [state["messages"][-1]]
    revisor_chain = revisor_prompt | llm.bind_tools(tools=[ReviseAnswer])
    #response=revisor_chain.invoke({"messages":[ToolMessage("content")]})
    response=revisor_chain.invoke(state["messages"])
    #print(f'response : {response} \n')
    state["messages"] = add_messages(state["messages"], [response])
    #print("state messages")
    #print (state["messages"])
    print("review_resp ended")
    return state



def execute_tools(state: AgentState) :
    """ triggers the tool provided by the llm and provides the response"""
    print("execute_tools executing starts")   
    #print(f'state[messages]  : {state["messages"][-1]}  \n')
    tool_messages = [state["messages"][-1]]
    tool_message=[]
    #for tool_call in last_ai_message.tool_calls:
    for tool_call in state["messages"][-1].tool_calls:
        if tool_call["name"] in ["AnswerQuestion", "ReviseAnswer"]:
            call_id = tool_call["id"]
            search_queries = tool_call["args"].get("search_queries", [])
            query_results = {}
            #print(f' args    : { tool_call["args"] } ')
            #print(f' call-id : {tool_call["id"]}')
            #print(f'queries   :  { tool_call["args"].get("search_queries", [])}')
            #print(f'search_queries  :  {search_queries}')
            tavily_tool=TavilySearch(max_results=1)
            for query in search_queries:
                result = tavily_tool.invoke(query)
                query_results[query] = result
            #print(f'query_result   : {query_results}  \n ')
            #tool_message.append(ToolMessage(
            #    content=json.dumps(query_results),
            #    name=tool_call["name"],
            #    tool_call_id=call_id)
            #)
            tool_message = ToolMessage(
            content=json.dumps(query_results),
            name=tool_call["name"],
            tool_call_id=tool_call["id"])
            print(f'tool_messages   {tool_message}')
    state["messages"] = add_messages(state["messages"], [tool_message])        
    print("execute_tools executing ends")
    return state

def print_stream(stream):
    """Helper function for formatting the stream nicely."""
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

#graph=MessageGraph()

builder=StateGraph(State)
#builder.add_node("respond", initial_chain)
builder.add_node("respond", gen_init_resp)
builder.add_node("execute_tools", execute_tools)
builder.add_node("revisor", review_resp)
builder.add_edge("respond", "execute_tools")
builder.add_edge("execute_tools", "revisor")
builder.add_conditional_edges("revisor", event_loop)
builder.set_entry_point("respond")

question=    """I'm pre-diabetic and need to lower my blood sugar, and I have heart issues.
    What breakfast foods should I eat and avoid"""

app = builder.compile()

inputs = {"messages": [HumanMessage(content=question)]}

print_stream(app.stream(inputs, stream_mode="values"))


# Tavily results understanding displays
"""
#tavily_tool=TavilySearchResults(max_results=1)
tavily_tool=TavilySearch(max_results=1)
sample_query = "healthy breakfast recipes"
search_results = tavily_tool.invoke(sample_query)
print(f' Tavily search :  {search_results}')


#model response diaplays

print("llm response verification")
question="Any ideas for a healthy breakfast"
response=llm.invoke(question).content
print(f' LLM response : {response}')




response=initial_chain.invoke({"messages":[HumanMessage(question)]})
print("---Full Structured Output---")
print(response.tool_calls)

answer_content = response.tool_calls[0]['args']['answer']
print("---Initial Answer---")
print(answer_content)

Reflection_content = response.tool_calls[0]['args']['reflection']
print("---Reflection Answer---")
print(Reflection_content)

search_queries = response.tool_calls[0]['args']['search_queries']
print("---Search Queries---")
print(search_queries)

#response_list keeps a state of all conversational messages
response_list=[]
response_list.append(HumanMessage(content=question))
response_list.append(response)




#formatting the  initial response for responder call
tool_response = execute_tools(response_list)

# Use .extend() to add all tool messages from the list
#.append adds the list to list making a nested list
response_list.extend(tool_response)

print(f'tool_response  : {tool_response} \n')
print(f'response_list  :  {response_list} \n')

#calling the responsder function with the initial response
response = revisor_chain.invoke({"messages": response_list})
print("---Revised Answer with References---")
print(response.tool_calls[0]['args'])
response_list.append(response)

print(f' response from responder : {response}')


responses = app.invoke({"messages":[HumanMessage(question)]})
print("--- Initial Draft Answer ---")
initial_answer = responses[1].tool_calls[0]['args']['answer']
print(initial_answer)
print("\n")

print("--- Intermediate and Final Revised Answers ---")
answers = []

# Loop through all messages in reverse to find all tool_calls with answers
for msg in reversed(responses):
    if getattr(msg, 'tool_calls', None):
        for tool_call in msg.tool_calls:
            answer = tool_call.get('args', {}).get('answer')
            if answer:
                answers.append(answer)


# Print all collected answers
for i, ans in enumerate(answers):
    label = "Final Revised Answer" if i == 0 else f"Intermediate Step {len(answers) - i}"
    print(f"{label}:\n{ans}\n")
"""