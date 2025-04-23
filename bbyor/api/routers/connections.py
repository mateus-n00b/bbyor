from fastapi import APIRouter, Request
from ...utils.logging import get_logger

router = APIRouter(tags=["connections"])
logger = get_logger()

@app.post("/topic/connections/")
async def connections(request: Request):
    body = await request.json()
    print(body)
    return {"status": "processed"}
