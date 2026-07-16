# drop_extension.py
import json
from fastapi import Request
from litellm.proxy.proxy_server import ProxyConfig

proxy_config = ProxyConfig()

async def clear_all_output_config_middleware(request: Request, call_next):
    # Intercept all incoming POST requests (captures both chat/completions and v1/messages)
    if request.method == "POST":
        try:
            body = await request.body()
            if body:
                data = json.loads(body)
                
                # Check for output_config at the top level or nested inside extra_body
                if "output_config" in data:
                    del data["output_config"]
                if "extra_body" in data and isinstance(data["extra_body"], dict):
                    data["extra_body"].pop("output_config", None)
                
                new_body = json.dumps(data).encode("utf-8")
                
                async def receive():
                    return {"type": "http.request", "body": new_body, "more_body": False}
                request._receive = receive
        except Exception:
            pass 

    response = await call_next(request)
    return response

def initialize_plugin():
    from litellm.proxy.proxy_server import app
    app.middleware("http")(clear_all_output_config_middleware)

initialize_plugin()
