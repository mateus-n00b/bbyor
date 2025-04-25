import json
import os
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
    nonce = contract_client.get_nonce(1)
    return int(nonce)

def propose_challenge():
    results = get_connections()["results"]
    connection_ids = [conn["connection_id"] for conn in results if conn["rfc23_state"] == "completed" 
                      and "their_public_did" in conn and conn["their_public_did"] != settings.PUBLIC_DID]
    a = encrypt(_random())
    nonce = get_nonce()
    logger.info(f"Creating challenge with nonce {nonce}...")
    c = evalAdd(a, nonce)
    # get hash of serialized c
    c = serialize(c)
    h = MD5.new()
    h.update(c)    
    hash = h.hexdigest() 
    os.environ["LAST_HASH"] = hash # gambiarra
    a = serialize(a)
    msg = {"type": "challenge" ,"a": a.hex(), "b": nonce}
    for conn in connection_ids:
        logger.info(f"Sending it to conn: {conn} - Expected hash: {hash}")
        send_message(conn, msg)

# HINT: registrar resposta do basicmessage 
# na blockchain como garantia de que o receptor recebeu o desafio
# e vice-versa
# TODO: gerar prova ZKP
def handle_challenge(body, msg):
    a = bytes.fromhex(msg["a"])
    b = int(msg["b"])
    # Deserialize to FHE
    logger.info(f"Received challenge nonce {b}. Proccessing...")
    a = deserialize(a)
    c = evalAdd(a,b)
    c = serialize(c)
    h = MD5.new()
    h.update(c)    
    hash = h.hexdigest()
    conn_id = body["connection_id"] # send it back 
    logger.info(f"Sending ADD result hash {hash} to {conn_id}")        
    body = {"type": "fhe_result", "hash": str(hash)}
    send_message(conn_id, body)

def handle_result(body, msg):
    conn_id = body["connection_id"]
    _hash = os.getenv("LAST_HASH")
    logger.info(f"Received result from {conn_id} -> {msg['hash']} == {_hash}")
    if  _hash == msg["hash"]:
        logger.info("SUCCESS!!!!")