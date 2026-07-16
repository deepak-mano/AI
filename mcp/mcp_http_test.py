"""
Client: A communication outlet between an application (host) and an MCP server.
StdioTransport: Communication run on subprocesses (read only input, write only output) for local MCP servers.
StreamableHttpTransport: Communication for production deployments that run over bidirectional streaming on HTTP connections.
Requests is a Python Library that allows you to send HTTP/1.1 requests easily
"""
import requests
import os
import sys
import asyncio 
from mcp import stdio_client  
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport, StdioTransport

http_transport = StreamableHttpTransport(
    url="https://mcp.context7.com/mcp"
)

print("This is MCP CLient for Context7")
print("Enter one of the options that you want to execute for context7 search:")
print("1. List tools")
print("2. Call tool-resolve-library-id")
print("3. Call tool-query-docs")
option = input("Enter your choice (1, 2, or 3): ")

env_config = {
    "EXTERNAL_SERVICE_API_KEY": os.environ.get("MY_CTXT7_API_KEY")
}

"""
instantiate an StdioTransport with the following parameters:

command="npx": We use npx to run the published Context7 MCP server package
args=[...]: The Node package that contains the server with the -y flag to say "yes" to all prompts during installation
Think of this as: “Start the server for me and wire up stdin/stdout so we can chat.”
"""



if option == "1":
    async def main():
        http_client = Client(http_transport)
        async with http_client as client:
            tools = await client.list_tools()
            for tool in tools:
                print(
                    f""" name: {tool.name}: \n
                    description: {tool.description} \n
                    inputSchema: {tool.inputSchema}""")
    if __name__ == "__main__":
        asyncio.run(main())
                
        print("Done")
            
elif option == "2":

    async def fetch():
        http_client = Client(http_transport)
        async with http_client as client:
            libname = input("Enter the library name (e.g., fastmcp): ")
            query = input("Enter your query (e.g., I want to create a new MCP server using the fastmcp Python framework): ")
            # Find a library ID via a search query
            response = await client.call_tool("resolve-library-id", {
                "libraryName": libname,
                "query": query
            })
        
        print(response.content[0].text)

    if __name__ == "__main__":
        asyncio.run(fetch())
                    
    print("Done")


elif option == "3":

    async def qry():
        http_client = Client(http_transport)
        async with http_client as client:
            libid = input("library_id: (e.g., /punkpeye/fastmcp) ")
            
            query = input("Enter your query (e.g., I want to fetch the code snippets and " \
            "the documentation): ")
            print("library_id: ", libid)
      
            # Find a library ID via a search query
            docs = await client.call_tool("query-docs", {
                "libraryId": libid,
                "query": query
            })
            
            print(docs.content[0].text[:5000]) 

    if __name__ == "__main__":
        asyncio.run(qry())
                    
    print("Done")

