"""Builds a runnable experiment from a scenario file.

    uv run --project node python sim/generate.py sim/scenarios/default.toml

Registers one DID per node on von-network, assigns each node a Hardhat
account (account 0 deploys), and writes sim/out/{peers.json,docker-compose.yml,.env}.
"""
import argparse
import hashlib
import json
import tomllib
from pathlib import Path

import httpx
from eth_account import Account

HARDHAT_MNEMONIC = "test test test test test test test test test test test junk"
OUT = Path(__file__).parent / "out"

Account.enable_unaudited_hdwallet_features()


def expand(scenario: dict) -> list[dict]:
    nodes = []
    for group in scenario["nodes"]:
        opts = {k: v for k, v in group.items() if k != "count"}
        nodes += [dict(opts) for _ in range(group.get("count", 1))]
    return nodes


def register_did(von_url: str, seed: str) -> str:
    r = httpx.post(f"{von_url}/register", json={"role": "ENDORSER", "alias": None, "did": None, "seed": seed}, timeout=30)
    r.raise_for_status()
    return r.json()["did"]


def agent_service(i: int, seed: str) -> dict:
    return {
        "image": "ghcr.io/openwallet-foundation/acapy-agent:py3.12-1.2-lts",
        "restart": "unless-stopped",
        "command": " ".join([
            "start --inbound-transport http 0.0.0.0 8020 --outbound-transport http",
            f"--endpoint http://agent{i}:8020 --label NODE{i} --seed {seed}",
            "--genesis-url http://host.docker.internal:9000/genesis --ledger-pool-name localindypool",
            f"--wallet-type askar-anoncreds --wallet-name wallet{i} --wallet-key insecure-dev-key",
            "--wallet-storage-type postgres_storage",
            """--wallet-storage-config '{"url":"postgres:5432","wallet_scheme":"DatabasePerWallet"}'""",
            """--wallet-storage-creds '{"account":"postgres","password":"postgres","admin_account":"postgres","admin_password":"postgres"}'""",
            "--admin 0.0.0.0 8031 --admin-insecure-mode --auto-provision",
            "--auto-accept-invites --auto-accept-requests --public-invites --requests-through-public-did",
            f"--webhook-url http://node{i}:8000 --max-message-size 4194304 --log-level warning",
        ]),
        "extra_hosts": ["host.docker.internal:host-gateway"],
        "depends_on": ["postgres"],
    }


def node_service(i: int, node: dict, did: str, key: str, scenario: dict) -> dict:
    env = {
        "PUBLIC_DID": did,
        "PRIVATE_KEY": key,
        "ACAPY_URL": f"http://agent{i}:8031",
        "PROVIDER_URL": "http://chain:8545",
        "SCHEME": scenario.get("scheme", "fhe"),
        "ATTESTATION": scenario.get("attestation", "zk"),
        "BEHAVIOUR": node.get("behaviour", "honest"),
        "SEED": str(scenario.get("seed", 12) + i),
        "KEEPER": "true" if i == 0 else "false",
    }
    if "fail_probability" in node:
        env["FAIL_PROBABILITY"] = str(node["fail_probability"])
    if "attack_threshold" in node:
        env["ATTACK_THRESHOLD"] = str(node["attack_threshold"])
    return {
        "image": "bbyor-node:dev",
        "restart": "unless-stopped",
        "environment": env,
        "ports": [f"{scenario.get('api_port_base', 8100) + i}:8000"],
        "volumes": ["./:/app/sim/out:ro", f"node{i}-data:/home/bbyor"],
        "depends_on": {
            "deploy": {"condition": "service_completed_successfully"},
            f"agent{i}": {"condition": "service_started"},
        },
    }


def compose(nodes, dids, keys, seeds, scenario) -> dict:
    services = {
        "postgres": {
            "image": "postgres:16",
            "environment": {"POSTGRES_PASSWORD": "postgres"},
            "volumes": ["postgres-data:/var/lib/postgresql/data"],
        },
        "chain": {"image": "bbyor-chain:dev", "ports": ["8545:8545"]},
        "deploy": {
            "image": "bbyor-chain:dev",
            "command": ["sh", "-c", "until npx hardhat run scripts/deploy.js --network localhost; do sleep 2; done"],
            "environment": {
                "PROVIDER_URL": "http://chain:8545",
                "PEERS_FILE": "/out/peers.json",
                "DEPLOYMENT_FILE": "/out/deployment.json",
                "MIN_INTERVAL": str(scenario.get("min_interval", 30)),
                "MAX_INTERVAL": str(scenario.get("max_interval", 40)),
            },
            "volumes": ["./:/out"],
            "depends_on": ["chain"],
        },
    }
    volumes = {"postgres-data": {}}
    for i, node in enumerate(nodes):
        services[f"agent{i}"] = agent_service(i, seeds[i])
        services[f"node{i}"] = node_service(i, node, dids[i], keys[i], scenario)
        volumes[f"node{i}-data"] = {}
    return {"services": services, "volumes": volumes}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenario", type=Path)
    args = parser.parse_args()

    scenario = tomllib.loads(args.scenario.read_text())
    nodes = expand(scenario)
    seed = scenario.get("seed", 12)

    # Indy seeds must be 32 characters
    seeds = [hashlib.md5(f"bbyor:{seed}:{i}".encode()).hexdigest() for i in range(len(nodes))]
    dids = [register_did(scenario.get("von_network", "http://localhost:9000"), s) for s in seeds]
    accounts = [Account.from_mnemonic(HARDHAT_MNEMONIC, account_path=f"m/44'/60'/0'/0/{i + 1}") for i in range(len(nodes))]

    OUT.mkdir(exist_ok=True)
    peers = [{"account": a.address, "did": d} for a, d in zip(accounts, dids)]
    (OUT / "peers.json").write_text(json.dumps(peers, indent=2))
    # JSON is valid YAML, so docker compose reads this file as is
    spec = compose(nodes, dids, [a.key.hex() for a in accounts], seeds, scenario)
    (OUT / "docker-compose.yml").write_text(json.dumps(spec, indent=2))
    # Read by both docker-compose v1 and `docker compose` v2
    (OUT / ".env").write_text("COMPOSE_PROJECT_NAME=bbyor\n")

    for i, (node, did) in enumerate(zip(nodes, dids)):
        print(f"node{i}  {did}  {node.get('behaviour', 'honest')}")
    print(f"\nwrote {OUT}/docker-compose.yml — run: docker compose -f {OUT}/docker-compose.yml up -d")


if __name__ == "__main__":
    main()
