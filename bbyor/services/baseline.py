import hashlib
import random
from eth_account import Account
from eth_account.messages import encode_defunct
from .connections import send_message, get_connections
from ..config.settings import settings
from ..utils.logging import get_logger
from ..utils import metrics

logger = get_logger()

_round_hashes: dict[int, str] = {}


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def propose_baseline_challenge(_round: int, connection_ids: list = None):
    if not connection_ids:
        results = get_connections()["results"]
        connection_ids = [
            conn["connection_id"] for conn in results
            if conn["rfc23_state"] == "completed"
            and "their_public_did" in conn
            and conn["their_public_did"] != settings.PUBLIC_DID
        ]

    a = random.randint(settings.LOWER_BOUND, settings.UPPER_BOUND)
    nonce = random.randint(1, 99999)
    address = Account.from_key(settings.PRIVATE_KEY).address

    _round_hashes[_round] = _sha256(f"{a + nonce}:{nonce}")

    msg = {
        "type": "baseline_challenge",
        "round": _round,
        "a": a,
        "nonce": nonce,
        "address": address,
    }
    for conn in connection_ids:
        logger.info(f"[baseline] Sending challenge to {conn}, round={_round}")
        send_message(conn, msg)


def handle_baseline_challenge(body, msg):
    a = int(msg["a"])
    nonce = int(msg["nonce"])
    _round = int(msg["round"])

    logger.info(f"[baseline] Challenge received: a={a} nonce={nonce} round={_round}")

    with metrics.record("baseline_challenge_total", _round=_round):
        with metrics.record("baseline_hash", _round=_round):
            result_hash = _sha256(f"{a + nonce}:{nonce}")

        with metrics.record("baseline_sign", _round=_round):
            signable = encode_defunct(text=result_hash)
            signed = Account.sign_message(signable, private_key=settings.PRIVATE_KEY)
            signature = signed.signature.hex()

    response = {
        "type": "baseline_result",
        "round": _round,
        "result_hash": result_hash,
        "signature": signature,
    }
    send_message(body["connection_id"], response)
    logger.info(f"[baseline] Sent result for round={_round}")


def handle_baseline_result(body, msg):
    _round = int(msg["round"])
    result_hash = msg["result_hash"]
    signature = msg["signature"]
    expected = _round_hashes.get(_round)

    with metrics.record("baseline_verify", _round=_round):
        signable = encode_defunct(text=result_hash)
        recovered = Account.recover_message(signable, signature=bytes.fromhex(signature))
        ok = result_hash == expected

    if ok:
        logger.info(f"[baseline] Round {_round} verified. Recovered addr: {recovered}")
    else:
        logger.warning(f"[baseline] Round {_round} FAILED. hash_ok={ok}")
