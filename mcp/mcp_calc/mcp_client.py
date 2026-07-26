# Standard library imports
from fastmcp import FastMCP, Client
from mcp import stdio_client, ClientSession, StdioServerParameters  
from fastmcp.client.transports import StreamableHttpTransport, StdioTransport
from langchain_core.tools import tool
import os
from langchain_mcp_adapters.client import MultiServerMCPClient # Connects to MCP servers
from langgraph.prebuilt import create_react_agent # Creates ReAct-style agents
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
    args=["stdio_server.py"],
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


client = MultiServerMCPClient(
    {
        "stdio-client": {
                            "command": "python",
                            "args": ["mcp_stdio_server.py"],
                            "transport": "stdio"
                        },
        "http-client": {
            "url": f"http://127.0.0.1:{PORT}/mcp",
            "transport": "streamable_http"
                        }
    }
)

async def main():
    openai_model = ChatOpenAI(
        model="claude-3-5-sonnet-20241022",
        openai_api_base="http://localhost:4000",
        openai_api_key="sk-1234567890",
        temperature=0.7,
    )

    # Retrieve all available tools from the configured MCP servers
    # These tools allow the agent to interact with external services
    
    try:
        tools = await client.get_tools()
    except Exception as e:
        print("Failed to get tools:", e)
        tools = None

    print("Retrieved tools:", tools)
    checkpointer = InMemorySaver()

    config = {"configurable": {"thread_id": "conversation_id"}}


    agent = create_react_agent(
        model=openai_model,         # The language model to use, replace with watsonx_model if you receive rate limiting errors
        tools=tools,                # Available tools from MCP servers
        checkpointer=checkpointer   # Memory system for conversation history
    )

    agent_response = await agent.ainvoke(
            {"messages": [
                # System message defines the agent's role and personality
                {"role": "system", "content": "You are a smart, useful agent that does mathematical calculations using tools."}            ]},
            config=config  # Use the conversation thread for memory persistence
        )

        
    while True:
        # Display menu options to the user
        choice = input("""type exit to quit) >>>""")

        if choice != "exit":
            # Get user's question
            print("Your question")
            query = input("> ")
            response = await agent.ainvoke(
                {"messages": query},        # User's current question
                config=config              # Maintains conversation thread
            )
            disp_agent_comm(response)
        else:
            # Exit the program for any choice other than "1"
            print("Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())

