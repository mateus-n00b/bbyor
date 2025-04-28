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
from ..utils.encoder import hex_to_int
from Crypto.Hash import MD5
from ..services.circom import create_verifier_input, create_prover_input

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
    
    # generates poseidon hash for the prover
    h_poseidon = create_verifier_input(nonce=nonce, hash_result=hash)
    os.environ["LAST_HASH"] = h_poseidon # gambiarra

    a = serialize(a)
    # Encode a as hex
    msg = {"type": "challenge" ,"a": a.hex(), "b": nonce, "c": h_poseidon}
    for conn in connection_ids:
        logger.info(f"Sending it to conn: {conn} - Expected hash: {hash}")
        send_message(conn, msg)

def handle_challenge(body, msg):
    a = bytes.fromhex(msg["a"])
    b = int(msg["b"])
    c_line = msg["c"]
    # Deserialize to FHE
    logger.info(f"Received challenge nonce {b}. Proccessing...")
    a = deserialize(a)
    c = evalAdd(a,b)
    c = serialize(c)
    
    h = MD5.new()
    h.update(c)    
    hash = h.hexdigest()

    # Create proof
    proof = create_prover_input(b, hash, c_line)
    s_fixed = "[" + proof.strip() + "]"

    # Now parse it
    proof = json.loads(s_fixed)

    conn_id = body["connection_id"] # send it back 
    logger.info(f"Sending ADD result hash {hash} to {conn_id} with proof: {proof}")        
    body = {"type": "fhe_result", "proof": proof}
    send_message(conn_id, body)

def handle_result(body, msg):
    conn_id = body["connection_id"]
    _hash = os.getenv("LAST_HASH")    
    proof = msg["proof"]
    proof_fixed = hex_to_int(proof)

    logger.info(f"Received result from {conn_id} -> {proof_fixed} == {_hash}")
    verified = contract_client.verify(proof_fixed)
    if  verified:
        logger.info("SUCCESS!!!!")