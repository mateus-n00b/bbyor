import subprocess
from ..utils.logging import get_logger
from ..utils.encoder import string_to_integer
from ..config.settings import settings
from ..utils import metrics
import json

logger = get_logger()

def run_cmd(cmd, input_text=None):
    output = "OK"
    try:
        logger.info(f"\n👉 Running: {cmd}")
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            input=input_text,
            capture_output=True,
            text=True
        )
        logger.info("Success")
        if result.stdout:
            logger.info(result.stdout)
            output = result.stdout
    except subprocess.CalledProcessError as e:
        logger.info("❌ Error occurred:")
        logger.info(e.stderr or e.stdout)
        return None
    return output

# (op_name, command_template)
commands = [
    ("snarkjs_witness", "cd {} && snarkjs wtns calculate circuit.wasm input.json witness.wtns"),
    ("snarkjs_prove",   "cd {} && snarkjs groth16 prove circuit2_0001.zkey witness.wtns proof.json public.json"),
    ("snarkjs_verify",  "cd {} && snarkjs groth16 verify verification_key.json public.json proof.json"),
    ("snarkjs_call",    "cd {} && snarkjs generatecall"),
]

def run(role='verifier', _round=None) -> str:
    output = None
    dirs = {"verifier": "gen_hash", "prover": "checkHash"}
    dir = dirs[role]
    for op_name, cmd in commands:
        with metrics.record(op_name, _round=_round):
            output = run_cmd(cmd.format(dir))
        if output is None:
            break
    return output

def create_prover_input(nonce, hash_result, recv_result, _round=None) -> str:
    try:
        _input = {
            "hash_result": str(string_to_integer(hash_result)),
            "nonce": str(nonce),
            "result": str(recv_result),
            "in_did": str(string_to_integer(settings.PUBLIC_DID))
        }
        with open("./checkHash/input.json", "w") as fp:
            json.dump(_input, fp)
        proof = run("prover", _round=_round)
        return proof
    except Exception as err:
        logger.error(err)
        return None

def create_verifier_input(nonce, hash_result, _round=None) -> str:
    try:
        _input = {
            "result": str(string_to_integer(hash_result)),
            "nonce": str(nonce)
        }
        with open("./gen_hash/input.json", "w") as fp:
            json.dump(_input, fp)
        run("verifier", _round=_round)
        public = json.load(open("./gen_hash/public.json"))
        return public[0]
    except Exception as err:
        logger.error(err)
        return None
    