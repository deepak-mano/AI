These are excercise IBM course program to understand sampling and root access features
Command to start the server and client
    python mcp_http_server.py  
    python mcp_http_client_app.py http://127.0.0.1:8000 workspace
    python mcp_http_host_app.py http://127.0.0.1:8000 workspace

mcp_http_server.py  	==>  MCP server with the list of tools, resources and prompts.
mcp_http_client_base.py	==>  MCP client program that defines all the functions that need to be called
mcp_http_client_app.py  ==>  Gradio based interaction for mcp_http_client_base.py to test all the tools
mcp_http_host_app.py  	==>  Gradio based host program that used LLM to interact with tools	

