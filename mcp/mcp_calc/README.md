1) This is a basic calculator that perform addition, substraction, multiplication and division using mcp tools. 
2) mcp_http_server.py sets up the mcp server for addition and substraction that uses http protocol
3) mcp_stdio_server.py sets up multiplication and division using stdio 
4) mcp client uses langchain reach agent that connects to servers using multiservermcp. This uses the tools exposed by the server to perform the requested operation. 
5) NVIDIA NIM models are used through litellm proxy

(Added Context and elicitation feature )
