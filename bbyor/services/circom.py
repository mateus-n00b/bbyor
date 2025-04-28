import subprocess
from ..utils.logging import get_logger
from ..utils.encoder import string_to_integer
from ..config.settings import settings
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

# Etapas

commands = [
    # 1. Calcular witness
    "cd {} && snarkjs wtns calculate circuit.wasm input.json witness.wtns",

    # 2. Power of Tau (fase 1)
    # "snarkjs powersoftau new bn128 12 pot12_0000.ptau -v",
    # "snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau --name='First contribution' -v",

    # # 3. Preparar para fase 2
    # "snarkjs powersoftau prepare phase2 pot12_0001.ptau pot12_final.ptau -v",

    # # 4. Setup groth16
    # "snarkjs groth16 setup circuit.r1cs pot12_final.ptau circuit2_0000.zkey",

    # # 5. Contribuição na fase 2
    # "snarkjs zkey contribute circuit2_0000.zkey circuit2_0001.zkey --name='1st Contributor Name' -v",

    # # 6. Exportar chave de verificação
    # "snarkjs zkey export verificationkey circuit2_0001.zkey verification_key.json",

    # 7. Provar
    "cd {} && snarkjs groth16 prove circuit2_0001.zkey witness.wtns proof.json public.json",

    # 8. verificar 
    "cd {} && snarkjs groth16 verify verification_key.json public.json proof.json",

    # 8. Gerar chamada Solidity/verificação
    "cd {} && snarkjs generatecall"
]

def run(role='verifier') -> str:
    # Executa os comandos
    output = None
    dirs = {
        "verifier": "gen_hash",
        "prover": "checkHash"
    }
    dir = dirs[role]
    for cmd in commands:
        output = run_cmd(cmd.format(dir))
        if not output:
            break  # Para se algum comando falhar
    return output

def create_prover_input(nonce, hash_result, recv_result) -> str:
    try:
        _input = {
            "hash_result": str(string_to_integer(hash_result)),    
            "nonce": str(nonce),
            "result": str(recv_result),
            "in_did": str(string_to_integer(settings.PUBLIC_DID))
        }
        fp = open("./checkHash/input.json", "w")
        json.dump(_input, fp)   
        fp.close() 
        proof = run("prover")    

        return proof
    except Exception as err:
        logger.error(err)
        return None  
    
def create_verifier_input(nonce, hash_result) -> str:
    try:
        _input ={
        "result": str(string_to_integer(hash_result)),    
        "nonce": str(nonce)
        }
        fp = open("./gen_hash/input.json", "w")
        json.dump(_input, fp)    
        fp.close()  

        # Run 
        run()   
        public = json.load(open("./gen_hash/public.json"))        
        return public[0]
    except Exception as err:
        logger.error(err)
        return None  
    