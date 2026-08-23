import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient # Connects to MCP servers
from langgraph.checkpoint.memory import InMemorySaver # Provides conversation memory
from langchain_openai import ChatOpenAI # OpenAI chat model integration
from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult, ElicitRequestParams
from fastmcp.client.transports import StreamableHttpTransport
from langchain.agents import create_agent # Creates ReAct-style agents
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_mcp_adapters.callbacks import Callbacks, CallbackContext



# 1. Define your progress callback function

async def my_progress_handler(
    progress: float, 
    total: float | None, 
    message: str | None, 
    context: CallbackContext
) -> None:
    """
    Handles real-time tool execution progress updates from the MCP Server.
    """
    # Calculate percentage safely if total is provided
    percent = (progress / total * 100) if total else progress
    
    # Retrieve contextual metadata injected by LangChain
    server = context.server_name
    tool = f" ({context.tool_name})" if context.tool_name else ""
    
    # Build a clean progress message
    msg = f" - {message}" if message else ""
    
    print(f"[{server}{tool}] Progress: {percent:.1f}%{msg}")

# 2. Package your handler inside the LangChain Callbacks manager
mcp_callbacks = Callbacks(
    on_progress=my_progress_handler
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


async def main():


    print("""Supported functionality
        get_most_active_stocks  ->  list of actively traded stocks 
        get_growth_stocks       ->  list of growth stocks 
        get_short_sqeeze        ->  list of short squeeze stocks 
        get_ticker_info         ->  retrieves ticker details 
        get_ticker_list         ->  list of ticker with the provided similar ticker""")
    client = MultiServerMCPClient(
        {
            "http-client": {
                "url": f"http://127.0.0.1:{8000}/mcp",
                "transport": "streamable_http",
                "session_kwargs": {"elicitation_callback": elicitation_handler}
                            }
        },callbacks=mcp_callbacks
    )    

    openai_model = ChatOpenAI(
        model="claude-3-5-sonnet-20241022",      # Must match the model_name in config.yaml
        openai_api_base="http://localhost:4000", # Your LiteLLM Proxy URL
        openai_api_key="sk-1234567890",  # Pass your virtual key if auth is enabled
        temperature=0.7
    )


    # Retrieve all available tools from the configured MCP servers
    # These tools allow the agent to interact with external services
    tools = await client.get_tools()

    # Set up conversation memory using InMemorySaver
    # This allows the agent to remember previous messages in the conversation
    checkpointer = InMemorySaver()

    # Configuration for conversation persistence
    # The thread_id ensures all messages in this session are grouped together
    config = {"configurable": {"thread_id": "conversation_id"}}

    try:
        tools = await client.get_tools()
    except Exception as e:
        print("Failed to get tools:", e)
        tools = None

    #print("Retrieved tools:", tools)

    # Create the ReAct agent with all components
    # ReAct = Reasoning + Acting (agent can reason about and use tools)
    agent = create_agent(
        model=openai_model,         # The language model to use, replace with watsonx_model if you receive rate limiting errors
        tools=tools,                # Available tools from MCP servers
        checkpointer=checkpointer   # Memory system for conversation history
    )


    print("Your stock query")
    query = input("> ")

    agent_response = await agent.ainvoke(
            {"messages": [
                # System message defines the agent's role and personality
                {"role": "system", "content": """You are a stock market analyst . Critical Rules:
1. When a tool returns a result, pass the data immediately to answer the user. Do not modify the result if its wrong
2. NEVER call the same tool again consecutively with the same values . 
3. If the tool output contains the final answer or an error, STOP calling tools and summarize the result.
4. DO NOT format the output data from the tool. Pass the same tool output to the user"""},
{"role":"user","content":query}]}
            ,config=config  # Use the conversation thread for memory persistence
        )
    
    disp_agent_comm(agent_response)

    while True:
        # Display menu options to the user
        choice = input("""type exit to quit or enter your query) >>>""")

        if choice != "exit":
            # Get user's question
            response = await agent.ainvoke(
            {"messages": [
                            # System message defines the agent's role and personality
                            {"role": "system", "content": """You are a stock market analyst . Critical Rules:
            1. When a tool returns a result, pass the data immediately to answer the user. Do not modify the result if its wrong
            2. NEVER call the same tool again consecutively with the same values . 
            3. If the tool output contains the final answer or an error, STOP calling tools and summarize the result.
            4. DO NOT format the output data from the tool. Pass the same tool output to the user"""},
            {"role":"user","content":choice}]}
            ,config=config  # Use the conversation thread for memory persistence
            )
            disp_agent_comm(response)
        else:
            # Exit the program for any choice other than "1"
            print("Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
