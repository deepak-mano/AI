This Project is done to demonstrate MCP functionlaity with the logging, context, async and progress tracking using Yfinance.

stock_server.py ->    supports the following tools
                    
        get_most_active_stocks  ->  list of actively traded stocks
        get_growth_stocks       ->  list of growth stocks
        get_short_sqeeze        ->  list of short squeeze stocks
        get_ticker_info         ->  retrieves ticker details
        get_ticker_list         ->  list of ticker with the provided similar ticker

stock_client.py ->  Uses langchain agent and Nvidia Nim models through Litellm proxy for using the tools optimally for stock chatbot. 
