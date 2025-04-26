import subprocess
from ..utils.logging import get_logger

logger = get_logger()
def run_cmd(cmd, input_text=None):
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
        logger.info("✅ Success")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.info("❌ Error occurred:")
        logger.info(e.stderr or e.stdout)
        return False
    return True

# Etapas

commands = [
    # 1. Calcular witness
    "snarkjs wtns calculate circuit.wasm input.json witness.wtns",

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
    "snarkjs groth16 prove circuit2_0001.zkey witness.wtns proof.json public.json",

    # 8. Gerar chamada Solidity/verificação
    "snarkjs generatecall"
]

# Executa os comandos
for cmd in commands:
    if not run_cmd(cmd):
        break  # Para se algum comando falhar
