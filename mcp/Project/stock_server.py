import json
import yfinance as yf
from yfinance import EquityQuery
from fastmcp import FastMCP, Context
import logging
import warnings
import re
import sys
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from requests.exceptions import RequestException
import logging
from fastmcp.utilities.logging import get_logger
from typing import TypedDict, List

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("Stock Http Server").setLevel(logging.WARNING)

mcp = FastMCP("Stock Http Server")

class Stockinfo(TypedDict):
    industry: str
    currentPrice: float
    targetHighPrice: float
    targetLowPrice: float
    averageAnalystRating: str
    symbol: str
    regularMarketPrice: float
    longName: str 

    

def fix_list(data: dict):

    #print(f'fix_list :  {data}', file=sys.stderr)
    data_list="["
    for items in data:
        data_list = data_list  + '{ "symbol" : "' + items["symbol"] + '"' + "," 
        data_list = data_list  + ' "shortname" :' + '"' + items["shortname"] + '"' + '},'                               
    data_list = data_list[0:-2]  + "}]"                
    fix_data=json.loads(data_list)
    return fix_data              

def parse_malformed_string(raw_str):
    # 1. Wrap unquoted keys in double quotes
    #print(f'valid_json_str : {raw_str}')

    json_like = re.sub(r"(\b\w+\b)\s*:", r'"\1":', raw_str)

    # 2. Wrap unquoted text values in double quotes, leaving numbers alone
    def quote_values(match):
        key = match.group(1)
        val = match.group(2).strip()

        # If it's a numeric float or int, don't add quotes
        if re.match(r"^-?\d+(?:\.\d+)?$", val):
            return f"{key}: {val}"

        # Otherwise, wrap the text value in quotes
        return f'{key}: "{val}"'

    valid_json_str = re.sub(r'("[\w]+")\s*:\s*([^,\n}]+)', quote_values, json_like)
    #print(f'valid_json_str : {valid_json_str}')
    # 3. Safely parse into a native Python dictionary
    return json.loads(valid_json_str)

def filter_func(keep_list, data_list) -> dict:

    filtered_list = [
        {key: obj[key] for key in keep_list if key in obj} 
        for obj in data_list['quotes']
    ]

    stock_dict = {}
    
    for stock in filtered_list:
        ticker = stock["symbol"]
        stock_dict[ticker] = stock
        
    filtered_json = (json.dumps(stock_dict, indent=4))
    #updated_filtered_json=parse_malformed_string(filtered_json)
    return filtered_json

@mcp.tool()
async def get_most_active_stocks(ctx: Context = CurrentContext()) -> dict:
    """
    Description: Retrieves the most actively traded stocks by using the EquityQuery method from 
    Yfinance library.

    Input: No input parameter

    Output: dictionary with the key value pair for list of actively traded stocks. The key output 
    parameters are 

                    "longName"
                    "symbol"
                    "forwardPE"
                    "fiftyDayAverage"
                    "twoHundredDayAverage",
                    "fullExchangeName"
                    "regularMarketChangePercent"
                    "regularMarketPrice"

    """
    await ctx.info(f"Get most active stocks")
    await ctx.debug(f"get active stock list")
    #Most Active Stocks
    
    q = EquityQuery('and', [
    EquityQuery('eq', ['region', 'us']),
    EquityQuery('gte', ['intradaymarketcap', 2000000000]),
    EquityQuery('gt', ['dayvolume', 5000000])
    ])

    response = yf.screen(q, sortField = 'dayvolume', sortAsc = False,count=10)
    response_json=(json.dumps(response, indent=4))

    data_list=json.loads(response_json)

    keep_fields = {"longName", "symbol","forwardPE","fiftyDayAverage", "twoHundredDayAverage",
                "fullExchangeName","regularMarketChangePercent","regularMarketPrice"}

    active_stocks_n=filter_func(keep_fields, data_list)
    active_stocks=active_stocks_n.rstrip('\n')
    #print(f'active_stocks  :  {active_stocks}', file=sys.stderr)
    active_stocks_j= json.loads(active_stocks)
    #print(f'active_stocks_j  :  {active_stocks_j}', file=sys.stderr)
    await ctx.report_progress(progress=1, total=1)
    await ctx.warning(f"No Errors")
    return active_stocks_j


@mcp.tool()
async def get_growth_stocks(ctx: Context = CurrentContext()) -> dict:
    """
    Description: Retrieves the growth  stocks by using the EquityQuery method from Yfinance library.

    Input: No input parameter

    Output: dictionary with the key value pair for list of growth stocks. The key output 
    parameters are 

                    "longName"
                    "symbol"
                    "forwardPE"
                    "fiftyDayAverage"
                    "twoHundredDayAverage",
                    "fullExchangeName"
                    "regularMarketChangePercent"
                    "regularMarketPrice"
    
    """
    await ctx.info(f"Get growth stocks ")
    await ctx.debug(f"get active stock list")
    q = EquityQuery('and', [
    EquityQuery('gte', ['quarterlyrevenuegrowth.quarterly', 25]),
    EquityQuery('gt', ['epsgrowth.lasttwelvemonths', 25]),
    EquityQuery('eq', ['sector', 'Technology']),
    EquityQuery('is-in', ['exchange', 'NMS', 'NYQ'])
    ])

    response = yf.screen(q, sortField = 'eodvolume', sortAsc = False,count=10)
    response_json=(json.dumps(response, indent=4))
    data_list=json.loads(response_json)

    keep_fields = {"longName", "symbol","forwardPE","fiftyDayAverage", "twoHundredDayAverage",
                "fullExchangeName","regularMarketChangePercent","regularMarketPrice"}


    growth_stocks_n=filter_func(keep_fields, data_list)
    growth_stocks=growth_stocks_n.rstrip('\n')
    growth_stocks_j= json.loads(growth_stocks)                                         
    #print(f'growth_stocks  :  {growth_stocks_j}', file=sys.stderr)
    await ctx.warning(f"No Errors")
    await ctx.report_progress(progress=1, total=1)
    return growth_stocks_j
    

@mcp.tool()
async def get_short_sqeeze(ctx: Context = CurrentContext()) -> dict:
    """
    Description: Retrieves the short squeeze stocks by using the EquityQuery method from Yfinance library.

    Input: No input parameter

    Output: dictionary with the key value pair for list of short queeze stocks. The key output 
    parameters are 

                "longName"
                "symbol"
                "short_interest.value"
                "short_percentage_of_float.value"
                "pctheldinsider"
                "fullExchangeName"
                "regularMarketChangePercent"
                "regularMarketPrice"


    """
    await ctx.info(f"Get most short squeeze stocks ")
    await ctx.debug(f"get active stock list")

    q = EquityQuery('and', [
       EquityQuery('gt', ['short_interest.value', 60]),
       EquityQuery('eq', ['region', 'us']),
       EquityQuery('gt', ['short_percentage_of_float.value', 20]),
       EquityQuery('gt', ['pctheldinsider', 50])
    ])
    response = yf.screen(q, sortField = 'short_interest.value', sortAsc = False,count=10)
    response_json=(json.dumps(response, indent=4))
    data_list=json.loads(response_json)

    keep_fields = {"longName", "symbol","short_interest.value","short_percentage_of_float.value", "pctheldinsider",
                "fullExchangeName","regularMarketChangePercent","regularMarketPrice"}

    short_stocks_n=filter_func(keep_fields, data_list)
    short_stocks=short_stocks_n.rstrip('\n')
    short_stocks_j= json.loads(short_stocks)                                         
    #print(f'short_stocks  :  {short_stocks_j}', file=sys.stderr)
    await ctx.warning(f"No Errors")
    await ctx.report_progress(progress=1, total=1)
    return short_stocks_j


@mcp.tool()
async def get_ticker_info(ticker: str, ctx: Context = CurrentContext())   -> Stockinfo:
    """
    Description: Retrieves the ticker details for the requested ticker by using the EquityQuery method 
    from Yfinance library.
    
        Input: ticker Name : String
    
        Output: dictionary with the key value pair for below listed keys. 
                "longName" 
                "symbol"
                "averageAnalystRating"
                "currentPrice"
                "targetHighPrice"
                "targetLowPrice"
                "regularMarketPrice"
                "industry"
                        
        NOTE: if the ticker is not found, then call the tool get_ticker_list to provide alternate ticker list
    """
    #**Get Ticker Information**
    await ctx.info(f"Get ticker info ")
    await ctx.debug(f"get ticker info {ticker}")

    try:
        tick = yf.Ticker(ticker)
        if not tick.info:
            return {"sybmol" : "0000", "longName" : "NOT FOUND"}
        else:
            data=json.dumps(tick.info, indent=4)
            data_list=json.loads(data)
            keep_fields = {"longName", "symbol", "currentPrice","targetHighPrice","targetLowPrice",
                        "averageAnalystRating","regularMarketPrice","industry"}


            filtered_list="{"
            for obj in data_list:
                if obj in keep_fields:
                    filtered_list = filtered_list  + f'{obj} : {data_list[obj]}, \n' 

            filtered_list = filtered_list[0:-3]  + "}"
            updated_filtered_json=parse_malformed_string(filtered_list)
            print(f'filtered_list  :     {updated_filtered_json}, file=sys.stderr')
            await ctx.warning(f"No Errors")
            await ctx.report_progress(progress=1, total=1)
            return updated_filtered_json
    except:
        await ctx.warning(f"Exception")
        return {"sybmol" : "0000", "longname" : "NOT FOUND"}

@mcp.tool()
async def get_ticker_list(ticker: str, ctx: Context = CurrentContext())    -> list:

    """
    Description: Retrieves the ticker values for the provided ticker or ticker description by using 
    the EquityQuery method from Yfinance library. This function is called when the actual ticker value 
    is not correct or not known. 
    
        Input: ticker Name : String
    
        Output: dictionary with the key value pair for below listed keys. 
                "symbol"
                "shortname"
                            
    """
    await ctx.info(f"Get Ticker List : {ticker} ")
    await ctx.debug(f"get Ticker list  : {ticker} ")
    
    found=False
    while not found:
        try:
            #print('BEFORE', file=sys.stderr)
            #print(f'ticker  : {ticker}', file=sys.stderr)
            data=yf.Search(query=ticker,max_results=10)
            #print(f'ticker  : {ticker}', file=sys.stderr)
            #print('AFTER', file=sys.stderr)
            if not data.quotes:
                ticker=ticker[0:-1]
                found=False
            else:
                found=True
                await ctx.report_progress(progress=1, total=1)
                await ctx.debug(f"Get Ticker List : {ticker} : get stock list - No Error")
                return fix_list(data.quotes)              
        except RequestException as e:
                return {"sybmol" : "0000", "shortname" : "NOT FOUND"}
                await ctx.debug(f"Get Ticker List : {ticker} : get stock list - Error")
                found=True
        except ValueError as e:
                found=True
                await ctx.report_progress(progress=1, total=1)
                await ctx.warning(f"Value Error")
                await ctx.debug(f"Get Ticker List : {ticker} : get stock list - Value Error")
                return fix_list(data.quotes)              
        except Exception as e:
                found=True
                await ctx.report_progress(progress=1, total=1)
                await ctx.warning(f"Execption")
                await ctx.debug(f"Get Ticker List : {ticker} : get stock list - Exception")
                return fix_list(data.quotes)              
        

if __name__ == "__main__":
    print("Starting HTTP MCP Server on http://127.0.0.1:8000")
    mcp.run(transport="http", host="127.0.0.1", port=8000)