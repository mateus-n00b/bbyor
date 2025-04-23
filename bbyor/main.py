import json
from fastapi import Request, FastAPI
from .config.provision import  provision
import requests as rq
from bbyor import utils
from contextlib import asynccontextmanager
from .daemons.contract_poller import start_daemon
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    provision()  # executa no startup
    asyncio.create_task(start_daemon()) # run in bg
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/topic/basicmessages/")
async def basicmessages(request: Request):
    body = await request.json()
    content = json.dumps(body["content"])    
    return content

@app.post("/topic/connections/")
async def connections(request: Request):
    body = await request.json()
    content = json.dumps(body)    
    print(content)

#NOTE: this must be made in basicmessage :D
# @app.post("/topic/challenge/")
# async def challenge(request: Request):
#     return {}

from .api.routers import basicmessages

app.include_router(basicmessages.router)
app.include_router(connections.router)