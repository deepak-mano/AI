import socket
import asyncio
from fastmcp import FastMCP, Client, Context
from mcp import stdio_client  
from fastmcp.dependencies import CurrentContext
from fastmcp.server.dependencies import get_context
from fastmcp.server.context import Context
from fastmcp.client.transports import StreamableHttpTransport, StdioTransport
from langchain_core.tools import tool
import os
from fastmcp.server.elicitation import (
    AcceptedElicitation, 
    DeclinedElicitation, 
    CancelledElicitation,
)

#Port availability check - if the port is already in use, the server will not start

PORT = 8000
async def test_port(port=PORT, ctx: Context = CurrentContext()):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            await ctx.error("Port already allocated")
            return True
print(f"Port {PORT} is available: {not test_port()}")

#Print information about the read/write streams and session ID
async def print_stream_info(read, write, _sid, verbose=False):
    #print information about the read/write streams and session ID.
    if verbose:
        print("READ (receives FROM server):")
        print(read)
        print()
        
        print("WRITE (sends TO server):")
        print(write)
        print()
        
        print("SESSION ID:")
        print(_sid())


mcp = FastMCP(
    name="Calculator_MCP_http_Server",
    instructions="""
        This server provides data analysis tools.
        Call get_average() to analyze numerical data.
    """)

print('mcp object',mcp)

@mcp.tool
async def add(a: int, b: int, ctx: Context = CurrentContext()) -> int:
   """ 
    Adds the input a  and b and return the result
    
    input:  a   :   int
            b   :   int

    output: c :   int  
    """
   ctx = get_context()
   await ctx.info(f"Processing addition of {a} and {b}")
   await ctx.debug(f"completed processing addition")
   await ctx.warning(f"No errors")
   await ctx.report_progress(progress=1, total=1) 

   c = a + b

   return int(c)


@mcp.tool
async def subtract(a: int, b: int, ctx: Context = CurrentContext()) -> int:
    """ 
    Substracts the inputs b from a and return the result
    
    input:  a   :   int
            b   :   int

    output: a - b :   int  
    """
    if b > a:
        result = await ctx.elicit(message="Enter the value of 2nd number:",
        response_type=str)
        print ("Elicit response received")
        print(f'result : {result}')
        if result.action == "accept":
            print("accept")
            b = int(result.data)
        elif result.action == "decline":
            print("decline")
            return 0 
        else:
            print("else")
            return 0

    await ctx.info(f"Processing substraction of {a} and {b}")
    await ctx.debug(f"completed processing substraction")
    await ctx.warning(f"No errors")
    await ctx.report_progress(progress=1, total=1) 
    return a - b

if __name__ == "__main__":
    # Run the server explicitly over HTTP transport
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"
    )

