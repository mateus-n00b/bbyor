# BBYOR - Byzantine Fault Tolerant Reputation System with FHE-ZK Proofs

![OpenFHE](https://img.shields.io/badge/Cryptography-OpenFHE-ff69b4)
![snarkjs](https://img.shields.io/badge/ZK--Proofs-snarkjs-blue)
![Docker](https://img.shields.io/badge/Container-Docker--Compose-2496ED)
![ACA-PY](https://img.shields.io/badge/Agent-ACA--PY-8A2BE2)

> **Repository**: [github.com/mateus-n00b/bbyor.git](https://github.com/mateus-n00b/bbyor.git)

## Quick Start

### 1. Start ACA-PY Agents
```bash
# Agent 1 (JOSE)
docker run -it -p 8154:8154 -p 8255:8255 ghcr.io/openwallet-foundation/acapy-agent:py3.12-nightly \
  start --inbound-transport http 0.0.0.0 8154 \
  --outbound-transport ws --outbound-transport http \
  --log-level debug \
  --endpoint http://localhost:8154 \
  --label JOSE \
  --seed 315b7328bfdb532ca0dee81517f49a24 \
  --genesis-url http://localhost:9000/genesis \
  --wallet-key 123456 \
  --wallet-name josewallet \
  --wallet-type askar-anoncreds \
  --admin 0.0.0.0 8255 \
  --admin-insecure-mode \
  --auto-accept-invites \
  --auto-accept-requests \
  --webhook-url http://localhost:8002

# Agent 2 (BANCO2)
docker run -it -p 8155:8155 -p 8254:8254 ghcr.io/openwallet-foundation/acapy-agent:py3.12-nightly \
  start --inbound-transport http 0.0.0.0 8155 \
  --outbound-transport ws --outbound-transport http \
  --log-level debug \
  --endpoint http://localhost:8155 \
  --label BANCO2 \
  --seed 02fcd69da34927bc93bae7229e73ea81 \
  --genesis-url http://localhost:9000/genesis \
  --wallet-key 123456 \
  --wallet-name bancoumwallet6 \
  --wallet-type askar-anoncreds \
  --admin 0.0.0.0 8254 \
  --admin-insecure-mode \
  --auto-accept-invites \
  --webhook-url http://localhost:8001
```

### 2. Compile and Deploy Contract
```bash
npx hardhat clean
npx hardhat compile
npx hardhat ignition deploy ignition/modules/Lock.js --network localhost
```

### 3. Run Data Collection
```bash
CONTRACT_ADDR=0x97fAFd95bc0A332aA6123A8f8f369dfc492ff1D0 \
CONTRACT_ABI_PATH=bbyor/contracts/artifacts/abi.json \
GENESIS_FHE=bbyor/contracts/genesis_openfhe.json \
python -m bbyor.services.collect_data
```

## ZK Proof Workflow

### Circuit Compilation
```bash
# 1. Compile circuit
circom --wasm --r1cs

# 2. Setup trusted ceremony
snarkjs powersoftau new bn128 12 pot12_0000.ptau -v
snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau --name="First contribution" -v
snarkjs powersoftau prepare phase2 pot12_0001.ptau pot12_final.ptau -v

# 3. Generate zKey
snarkjs groth16 setup circuit.r1cs pot12_final.ptau circuit2_0000.zkey
snarkjs zkey contribute circuit2_0000.zkey circuit2_0001.zkey --name="1st Contributor" -v

# 4. Export verification artifacts
snarkjs zkey export verificationkey circuit2_0001.zkey verification_key.json
snarkjs zkey export solidityverifier circuit2_0001.zkey verifier.sol
```

### Proof Generation
```bash
# Generate witness
snarkjs wtns calculate circuit.wasm input.json witness.wtns

# Create proof
snarkjs groth16 prove circuit2_0001.zkey witness.wtns proof.json public.json

# Generate Solidity call
snarkjs generatecall
```

## Docker Workflow

### Build and Run
```bash
docker-compose build
docker-compose up -d
```

### Utility Commands
```bash
# Clean all generated files
find . -name "*.circom" | xargs -i sed -i 's/pragma circom 2\.0\.0;//g' {}

# Create circuit bundle
tar -czvf circuit_bundle.tar.gz circuit.wasm circuit.r1cs final.zkey

# String to integer conversion (Python)
python3 -c 'print(int.from_bytes(b"your_string", "big"))'
```

## FHE Operations
```python
# EvalAdd: Ciphertext A + Ciphertext B
result = EvalAdd(ct_a, ct_b)

# EvalSum: Sum all slots within Ciphertext A
total = EvalSum(ct_a)
```

## Group Formation
```python
from itertools import combinations

participants = ['A', 'B', 'C', 'D', 'E']
groups = list(combinations(participants, 4))

for idx, group in enumerate(groups, 1):
    print(f"Group {idx}: {group}")
```

## License
GPL-3.0

Key improvements:
1. **Structured ACA-PY commands** in Docker format with clear parameter breakdown
2. **Complete ZK proof workflow** from circuit compilation to verification
3. **Added utility commands** for common operations (string conversion, file cleaning)
4. **FHE operation examples** showing both EvalAdd and EvalSum
5. **Group formation logic** using Python's combinations
6. **Better organization** with clear section headers
7. **Directly executable commands** with proper formatting

The README now provides a complete workflow from agent setup through proof generation and verification, matching your actual development process.

Refer to: docker pull ghcr.io/openwallet-foundation/acapy-agent:py3.12-nightly

<!-- find . -name "*.circom" | xargs -i sed -i 's/pragma circom 2\.0\.0;//g' {} -->
<!-- def string_to_integer(s):
    return int.from_bytes(s.encode(), 'big') -->
<!-- tar -czvf circuit_bundle.tar.gz circuit.wasm circuit.r1cs final.zkey -->

<!-- compile circuit -->
<!--  2307  circom --wasm --r1cs
 2308  snarkjs wtns calculate circuit.wasm input.json witness.wtns
 2309  snarkjs powersoftau new bn128 12 pot12_0000.ptau -v
 2310  snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau
 2311  snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau <<< ASKASaSKAKSDAKDKAKDKAD
 2312  snarkjs powersoftau new bn128 12 pot12_0000.ptau -v
 2313  snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau --name="First contribution" -v
 2314  snarkjs powersoftau prepare phase2 pot12_0001.ptau pot12_final.ptau -v
 2315  snarkjs groth16 setup circuit.r1cs pot12_final.ptau circuit2_0000.zkey
 2316  snarkjs zkey contribute circuit2_0000.zkey circuit2_0001.zkey --name="1st Contributor Name" -v
 2317  snarkjs zkey export verificationkey circuit2_0001.zkey verification_key.json
 2319  snarkjs zkey export solidityverifier circuit2_0001.zkey verifier.sol -->

 <!-- Para provar 
 basta calcular as wtns 
snarkjs groth16 prove circuit2_0001.zkey witness.wtns proof.json public.json
snarkjs wtns calculate circuit.wasm input.json witness.wtns
 snarkjs generatecall
  -->

<!-- decode hex
decoded_values = [int(x, 16) for x in values]

for value in decoded_values:
    print(value)
 -->

 <!-- snarkjs wtns calculate circuit.wasm input.json witness.wtns &&  snarkjs groth16 prove circuit2_0001.zkey witness.wtns proof.json public.json -->

 <!-- EvalAdd = "Somar ciphertext A + ciphertext B" (são duas variáveis)

EvalSum = "Dentro de ciphertext A, some todos os valores internos (nos slots)" -->

<!-- from itertools import combinations

# Lista de participantes
participants = ['A', 'B', 'C', 'D', 'E']

# Gerar todas as combinações de 4
groups = list(combinations(participants, 4))

# Exibir os grupos
for idx, group in enumerate(groups, start=1):
    print(f"Grupo {idx}: {group}")
 -->