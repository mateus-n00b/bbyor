from typing import List
from .fhe import evalAdd, encrypt, deserialize, serialize 
from ..contracts.client import contract_client
from ..config.settings import settings
# Adicionar tag bbyor para que o agente saiba quem esta usando o servico 
# diferenciar dos futuros nos convencionais (e.g metadata)
from .connections import send_message, get_connections
import random

def _random():
    a = random.randint(settings.LOWER_BOUND, settings.UPPER_BOUND)
    return a

def compute_challenge(a:int, nonce: int):
    c = evalAdd(a, nonce)
    return c
    
def get_nonce():
    nonce = contract_client.get_nonce()
    return int(nonce)

def propose_challenge(connection_ids: List[str]):
    a = encrypt(_random())
    a = serialize(a)
    nonce = get_nonce()
    c = evalAdd(a, nonce)
    msg = {"type": "challenge" ,"a": str(a), "b": nonce}
    for conn in connection_ids:
        send_message(msg)

def send_result(a, b):
    pass