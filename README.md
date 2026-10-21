# BBYOR — verifiable peer reputation with FHE challenges and ZK attestations

![OpenFHE](https://img.shields.io/badge/Cryptography-OpenFHE-ff69b4)
![snarkjs](https://img.shields.io/badge/ZK--Proofs-snarkjs-blue)
![ACA-PY](https://img.shields.io/badge/Agent-ACA--PY-8A2BE2)

Each round, the `Reputation` contract picks a random peer as **server**. The
server commits on-chain to `Poseidon(result, nonce)` and sends an FHE
challenge to the other peers over DIDComm. Each peer derives `result` and
submits a Groth16 proof bound to the round and to its own account. When the
round ends, the server's reputation is updated from the response quorum.

The protocol, the reputation rule and the threat model are in
[docs/PROTOCOL.md](docs/PROTOCOL.md). How to run an experiment is in
[EXECUTION.md](EXECUTION.md).

## Layout

```
contracts/src/       Reputation.sol, ReputationMath.sol (+ generated Groth16Verifier)
contracts/test/      Hardhat tests (mock verifier + real proofs)
circuits/            response.circom and build.sh (setup, verifier export)
zk/zk.js             Poseidon commitments and proofs; JSON-lines server for the node
node/                Python node (FastAPI webhooks, protocol, chain/agent/zk clients)
sim/                 scenario files and the docker-compose generator
experiments/         metric collection and plots
docker/              node and chain images
```

## Development

```bash
npm install
npm run build:circuits          # circom + snarkjs; downloads the PSE ptau once
npm test                        # contract tests

cd node
uv sync
uv run pytest -m "not integration"
uv run pytest -m integration    # full rounds on Hardhat with real proofs
```

Integration tests run every component except ACA-Py and OpenFHE: DIDComm
is replaced by an in-memory network and the `plain` scheme stands in for
`fhe`. OpenFHE is only built in `docker/Dockerfile.node`.

## License

GPL-3.0
