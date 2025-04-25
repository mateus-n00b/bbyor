from typing import List
from .fhe import evalAdd, encrypt, deserialize, serialize 
from ..contracts.client import contract_client
from ..config.settings import settings
# Adicionar tag bbyor para que o agente saiba quem esta usando o servico 
# diferenciar dos futuros nos convencionais (e.g metadata)
from .connections import send_message, get_connections
import random
from ..utils.logging import get_logger
from Crypto.Hash import MD5

logger = get_logger()

def _random():
    a = random.randint(settings.LOWER_BOUND, settings.UPPER_BOUND)
    return a

def compute_challenge(a:int, nonce: int):
    c = evalAdd(a, nonce)
    return c
    
def get_nonce():
    nonce = contract_client.get_nonce()
    return int(nonce)

def propose_challenge():
    results = get_connections()["results"]
    connection_ids = [conn["connection_id"] for conn in results["connection_id"] if conn["state"] == "active" ]
    a = encrypt(_random())
    a = serialize(a)
    nonce = get_nonce()
    c = evalAdd(a, nonce)
    msg = {"type": "challenge" ,"a": str(a), "b": nonce}
    for conn in connection_ids:
        send_message(msg)

def handle_challenge(msg):
    a = msg["a"]
    b = msg["b"]
    # Deserialize to FHE
    a = deserialize(a)
    c = evalAdd(a,b)
    logger.info("Sending ADD result")
