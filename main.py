import json
from fastapi import Request, FastAPI
from bbyor.config import Config
import requests as rq
from bbyor import utils
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    main()  # executa no startup
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/topic/basicmessages/")
async def webhook(request: Request):
    body = await request.json()
    content = json.dumps(body["content"])    
    return content

@app.post("/topic/connections/")
async def webhook(request: Request):
    body = await request.json()
    content = json.dumps(body)    
    print(content)

def main():
    # loads config
    url = Config.url
    # check if there is any connection
    response = rq.get(url+Config.connections_url)
    results = response.json()
    # if results:
    #     # find missing connections
    #     missing = utils.missing_conn(results["results"])
    #     if missing:
    #         # create function for this
    #         for did in missing:
    #             result = rq.post(url+Config.did_exchange_endpoint+did)

    