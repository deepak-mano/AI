import socket
import asyncio
from fastmcp import FastMCP, Client
from mcp import stdio_client  
from fastmcp.client.transports import StreamableHttpTransport, StdioTransport
from langchain_core.tools import tool
import os


mcp = FastMCP(
    name="Calculator_MCP_stdio_Server",
    instructions="""
        This server provides data analysis tools.
        Call get_average() to analyze numerical data.
    """)
print('mcp object',mcp)

@mcp.tool
def multiply(a: int, b: int) -> int:
    """ 
    Multiplies the inputs a  and b and return the product
   
    input:  a   :   int
            b   :   int

    output: a * b :   int  
    """
    return a * b


@mcp.tool
def division(a: int, b: int) -> int:
    """ 
    divides the input a from b and return the result
    
    input:  a   :   int
            b   :   int

    output: a / b :   int  
    """
    return a // b

"""
if test_port():
    print(f"Port {PORT} is already in use. Please free the port and try again.")
    exit(1)
"""

if __name__ == "__main__":
    # Run the server explicitly over HTTP transport
    mcp.run(transport="stdio")

