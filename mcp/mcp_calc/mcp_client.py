# Standard library imports
from fastmcp import FastMCP, Client
from fastmcp.client.elicitation import ElicitResult, ElicitRequestParams
#from mcp.client.context import ClientRequestContext
from mcp import stdio_client, ClientSession, StdioServerParameters 
from fastmcp.client.transports import StreamableHttpTransport, StdioTransport
from langchain_core.tools import tool
from langchain.agents.middleware.tool_call_limit import ToolCallLimitMiddleware
import os
from langchain_mcp_adapters.client import MultiServerMCPClient # Connects to MCP servers
from langchain.agents import create_agent # Creates ReAct-style agents
from langgraph.checkpoint.memory import InMemorySaver # Provides conversation memory
from langchain_openai import ChatOpenAI # OpenAI chat model integration
from langchain_litellm import ChatLiteLLM, ChatLiteLLMRouter
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import sys
import socket
import asyncio

PORT = 8000

server_params = StdioServerParameters(
    command="python",
    args=["mcp_stdio_server.py"],
)


def disp_agent_comm(agent_response):
    for i in agent_response['messages']:
        if isinstance(i, HumanMessage):
            message_type = "HUMAN"
        elif isinstance(i, AIMessage):
            message_type = "AI"
        elif isinstance(i, ToolMessage):
            message_type = "TOOL"
        else:
            message_type = "OTHER"

        if i.content == '':
            i.content = "tool call"
        
        print(f"[{message_type}] {i.content}")

#async def elicitation_handler(message: str, response_type: type):
    #, params, context
    # Present the message to the user and collect input
#async def elicitation_handler(message: str, response_type=str) -> ElicitResult: 
async def elicitation_handler(message: str, schema: str ) -> ElicitResult:
    print(f'message {message}')
    user_input=[]
    user_input = input(f"Enter a small number for the 2nd one")
    
    # Create response using the provided dataclass type
    # FastMCP converted the JSON schema to this Python type for you
    if not user_input:
        return ElicitResult(action="decline")  # User declined

    if user_input == "cancel":
        return ElicitResult(action="cancel")   # Cancel entire operation
    else:
        return ElicitResult(
            action="accept",
            content={"value" : user_input})
        
    # You can return data directly - FastMCP will implicitly accept the elicitation
    # Or explicitly return an ElicitResult for more control
    # return ElicitResult(action="accept", content=response_data)


client = MultiServerMCPClient(
    {
        "stdio-client": {
                            "command": "python",
                            "args": ["mcp_stdio_server.py"],
                            "transport": "stdio"
                        },
        "http-client": {
            "url": f"http://127.0.0.1:{PORT}/mcp",
            "transport": "streamable_http",
            "session_kwargs": {"elicitation_callback": elicitation_handler}
                        }
    }
)

"""
client_elicit = Client(
    "mcp_http_server.py",
    elicitation_handler=elicitation_handler,
)
"""

async def main():
    openai_model = ChatOpenAI(
        #model="llama3.2-3b",
        model="claude-3-5-sonnet-20241022",
        openai_api_base="http://localhost:4000",
        openai_api_key="sk-1234567890",
        temperature=0.1,
    )

#    tool_limit_middleware = ToolCallLimitMiddleware(
#        limits={
#            "purchase_item": {"run_limit": 1, "thread_limit": 1},  # Max 1 purchase per turn, 2 per session
#            "__all__": {"run_limit": 1}                           # Global fallback cap to stop loops
#        },
#        exit_behavior="error"  # Can also be "end" to stop gracefully and return current state
#    )

    # Retrieve all available tools from the configured MCP servers
    # These tools allow the agent to interact with external services
    
    try:
        tools = await client.get_tools()
    except Exception as e:
        print("Failed to get tools:", e)
        tools = None

    print("Retrieved tools:", tools)

    #to keep the context and conversation in memory
    checkpointer = InMemorySaver()

    #to keep the conversation thread
    config = {"configurable": {"thread_id": "conversation_id"}}


    agent = create_agent(
        model=openai_model,         # The language model to use, replace with watsonx_model if you receive rate limiting errors
        tools=tools,                # Available tools from MCP servers
        checkpointer=checkpointer   # Memory system for conversation history
    )

    print("Your Math question")
    query = input("> ")

    agent_response = await agent.ainvoke(
            {"messages": [
                # System message defines the agent's role and personality
                {"role": "system", "content": """You are a tool-use assistant. Critical Rules:
1. When a tool returns a result, pass the data immediately to answer the user. Do not modify the result if its wrong
2. NEVER call the same tool again consecutively with the same values . 
3. If the tool output contains the final answer or an error, STOP calling tools and summarize the result."""},
{"role":"user","content":query}]}
            ,config=config  # Use the conversation thread for memory persistence
        )
    
    disp_agent_comm(agent_response)

    while True:
        # Display menu options to the user
        choice = input("""type exit to quit) >>>""")

        if choice != "exit":
            # Get user's question
            print("Your question")
            query = input("> ")
            response = await agent.ainvoke(
                {"messages": query}        # User's current question
               ,config=config              # Maintains conversation thread
            )
            disp_agent_comm(response)
        else:
            # Exit the program for any choice other than "1"
            print("Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())

