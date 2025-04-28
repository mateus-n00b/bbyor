# BBYOR
Ongoing project


**Project Structure**

```
bbyor/                     # Root package
├── __init__.py            # Package initialization
├── main.py                # FastAPI app entrypoint (minimal, just app setup)
│
├── config/                # Configuration management
│   ├── __init__.py
│   ├── settings.py        # Pydantic settings (env vars, defaults)
│   └── provision.py       # Provisioning logic (moved from Config class)
│
├── api/                   # FastAPI route handlers
│   ├── __init__.py
│   ├── routers/           # Modular routers
│   │   ├── basicmessages.py
│   │   ├── connections.py
│   │   └── challenge.py   # Future implementation
│   └── dependencies.py    # Shared dependencies (e.g., auth, DB)
│
├── contracts/             # Smart contract interactions
│   ├── __init__.py
│   ├── client.py          # Web3.py client setup
│   └── random.py          # `getRandom()` and related logic
│
├── services/              # Business logic
│   ├── __init__.py
│   ├── connections.py     # Connection management (e.g., `missing_conn`)
│   └── fhe.py             # FHE key flow (future)
│
├── utils/                 # Shared utilities
│   ├── __init__.py
│   ├── http.py            # HTTP client wrappers
│   └── logging.py         # Custom logging setup
│
├── models/                # Pydantic models/DTOs
│   ├── __init__.py
│   ├── schemas.py         # Request/response schemas
│   └── events.py          # Webhook event models
│
├── tests/                 # Tests
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── conftest.py        # Fixtures
│
└── scripts/               # Helper scripts (e.g., provisioning)
    └── bootstrap.py       # First-time setup
```

Aca-py cmd

```
aca-py start --inbound-transport http 0.0.0.0 8154  --outbound-transport ws --outbound-transport http --log-level debug --endpoint http://localhost:8154 --label JOSE --seed 315b7328bfdb532ca0dee81517f49a24 --genesis-url http://localhost:9000/genesis --ledger-pool-name localindypool --wallet-key 123456 --wallet-name josewallet --wallet-type askar-anoncreds --admin 0.0.0.0 8255 --admin-insecure-mode --public-invites --auto-accept-invites --auto-accept-requests --auto-ping-connection --auto-respond-messages --auto-respond-credential-offer --auto-respond-presentation-request --auto-store-credential --auto-respond-presentation-proposal --auto-respond-credential-request --auto-respond-credential-proposal --debug-connections --debug-credentials --debug-presentations --auto-provision --requests-through-public-did --webhook-url http://localhost:8002 --admin-client-max-request-size 10 --max-message-size 3097152

aca-py start --inbound-transport http 0.0.0.0 8155  --outbound-transport ws --outbound-transport http --log-level debug --endpoint http://localhost:8155 --label BANCO2 --seed 02fcd69da34927bc93bae7229e73ea81 --genesis-url http://localhost:9000/genesis --ledger-pool-name localindypool --wallet-key 123456 --wallet-name bancoumwallet6 --wallet-type askar-anoncreds --admin 0.0.0.0 8254 --admin-insecure-mode --public-invites --auto-accept-invites --auto-accept-requests --auto-ping-connection --auto-respond-messages --auto-respond-credential-offer --auto-respond-presentation-request --auto-store-credential --auto-respond-presentation-proposal --auto-respond-credential-request --auto-respond-credential-proposal --debug-connections --debug-credentials --debug-presentations --auto-provision --requests-through-public-did --admin-client-max-request-size 10 --webhook-url http://localhost:8001 --max-message-size 3097152 

```


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