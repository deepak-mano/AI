import socket
import asyncio
from fastmcp import FastMCP, Client
from mcp import stdio_client  
from fastmcp.client.transports import StreamableHttpTransport, StdioTransport
from langchain_core.tools import tool
import os

#Port availability check - if the port is already in use, the server will not start

PORT = 8000
"""
def test_port(port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

f"Port {PORT} is available: {not test_port()}"

#Print information about the read/write streams and session ID
def print_stream_info(read, write, _sid, verbose=False):
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

"""

mcp = FastMCP(
    name="Calculator_MCP_http_Server",
    instructions="""
        This server provides data analysis tools.
        Call get_average() to analyze numerical data.
    """)
print('mcp object',mcp)

@mcp.tool
def add(a: int, b: int) -> int:
   return a + b


@mcp.tool
def subtract(a: int, b: int) -> int:
    return a - b

"""
if test_port():
    print(f"Port {PORT} is already in use. Please free the port and try again.")
    exit(1)
"""

if __name__ == "__main__":
    # Run the server explicitly over HTTP transport
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp"
    )

