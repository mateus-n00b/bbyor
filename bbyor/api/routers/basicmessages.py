from fastapi import APIRouter, Request
from ...utils.logging import get_logger
from ...services.messages import handle_messages

router = APIRouter(tags=["basicmessages"])
logger = get_logger()

@router.post("/topic/basicmessages/")
async def handle_basic_message(request: Request):
    body = await request.json()
    logger.info(f"Received message...")
    handle_messages(body)
    return {"status": "processed"}