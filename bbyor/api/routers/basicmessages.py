from fastapi import APIRouter, Request
from ...utils.logging import get_logger
import json

router = APIRouter(tags=["basicmessages"])
logger = get_logger()

@router.post("/topic/basicmessages/")
async def handle_basic_message(request: Request):
    body = await request.json()
    logger.info(f"Received message: {body['content']}")
    body = json.dumps(body['content'])
    return {"status": "processed"}