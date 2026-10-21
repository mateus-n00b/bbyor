"""Full rounds on a Hardhat node with the real verifier and real proofs.

DIDComm is replaced by an in-memory network; everything else is production code.
Run with: uv run pytest -m integration
"""
import asyncio
import json
import os
import random
import signal
import socket
import subprocess
from pathlib import Path

import pytest
from eth_account import Account

from bbyor.behaviour import Honest, OnOff
from bbyor.chain import Chain
from bbyor.config import Attestation
from bbyor.crypto.schemes import PlainScheme
from bbyor.metrics import Metrics
from bbyor.node import Node
from bbyor.zk import ZkProver

ROOT = Path(__file__).resolve().parents[2]
# Default Hardhat accounts 1..4 (account 0 deploys)
Account.enable_unaudited_hdwallet_features()
HARDHAT_MNEMONIC = "test test test test test test test test test test test junk"
KEYS = [
    Account.from_mnemonic(HARDHAT_MNEMONIC, account_path=f"m/44'/60'/0'/0/{i}").key.hex()
    for i in range(1, 5)
]

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not (ROOT / "circuits/build/response.zkey").exists(), reason="run npm run build:circuits"),
]


class Network:
    """Delivers basic messages between in-process nodes, like a full mesh of DIDComm connections."""

    def __init__(self):
        self.nodes: dict[str, Node] = {}

    def agent(self, did: str) -> "NetAgent":
        return NetAgent(self, did)


class NetAgent:
    def __init__(self, net: Network, did: str):
        self.net, self.did = net, did

    async def active_connections(self):
        return {d: f"{self.did}>{d}" for d in self.net.nodes if d != self.did}

    async def connection(self, conn_id):
        return {"their_public_did": conn_id.split(">")[1]}

    async def connect(self, did):
        return f"{self.did}>{did}"

    async def send(self, conn_id, message):
        target = self.net.nodes[conn_id.split(">")[1]]
        target._spawn(target.on_message(f"{target.did}>{self.did}", message))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def deployment(tmp_path_factory):
    out = tmp_path_factory.mktemp("chain")
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    # Own process group: terminating npx alone would leave the hardhat child running
    hh = subprocess.Popen(["npx", "hardhat", "node", "--port", str(port)], cwd=ROOT, start_new_session=True,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        peers = [{"account": Account.from_key(k).address, "did": f"did:sov:node{i}"} for i, k in enumerate(KEYS)]
        (out / "peers.json").write_text(json.dumps(peers))
        env = dict(os.environ, PROVIDER_URL=url, PEERS_FILE=str(out / "peers.json"),
                   DEPLOYMENT_FILE=str(out / "deployment.json"), MIN_INTERVAL="8", MAX_INTERVAL="8")
        for _ in range(30):
            if subprocess.run(["npx", "hardhat", "run", "scripts/deploy.js", "--network", "localhost"],
                              cwd=ROOT, env=env, capture_output=True).returncode == 0:
                break
        else:
            pytest.fail("deploy failed")
        yield url, out / "deployment.json", peers
    finally:
        os.killpg(hh.pid, signal.SIGTERM)
        hh.wait()


async def run_rounds(deployment, behaviours, n_rounds):
    url, dep_file, peers = deployment
    net = Network()
    nodes = []
    for i, (key, peer) in enumerate(zip(KEYS, peers)):
        node = Node(
            did=peer["did"], private_key=key, chain=Chain(url, dep_file, key), agent=net.agent(peer["did"]),
            zk=ZkProver(ROOT / "zk/zk.js"), scheme=PlainScheme(), attestation=Attestation.ZK, behaviour=behaviours.get(i, Honest()),
            metrics=Metrics(None, peer["did"]), keeper=(i == 0), poll_interval=0.3, rng=random.Random(i),
        )
        net.nodes[peer["did"]] = node
        nodes.append(node)

    chain = nodes[0].chain
    start = await chain.current_round()
    tasks = [asyncio.create_task(n.run()) for n in nodes]
    try:
        async with asyncio.timeout(20 * n_rounds):
            # Round start+n is opened only after round start+n-1 is finalized
            while await chain.current_round() <= start + n_rounds:
                await asyncio.sleep(0.5)
    finally:
        for n in nodes:
            n.stop()
        await asyncio.gather(*tasks)
        for n in nodes:
            await n.drain()
            await n.zk.close()

    finished = [await chain.get_round(r) for r in range(start + 1, start + n_rounds + 1)]
    return chain, nodes, finished


async def test_honest_rounds_reach_full_quorum(deployment):
    chain, _, rounds = await run_rounds(deployment, {}, n_rounds=2)
    for r in rounds:
        assert r.finalized and r.commitment != 0
        assert (r.responses, r.eligible) == (3, 3)
        assert await chain.reputation(r.server) >= 370


async def test_withholding_server_is_penalized(deployment):
    # Every node withholds, so the server of the round gets the x0.5 penalty
    url, dep_file, peers = deployment
    reader = Chain(url, dep_file, KEYS[0])
    before = {p["account"]: await reader.reputation(p["account"]) for p in peers}

    chain, _, (r,) = await run_rounds(deployment, {i: OnOff(threshold=0) for i in range(4)}, n_rounds=1)

    assert r.finalized and r.commitment == 0 and r.responses == 0
    assert await chain.reputation(r.server) == before[r.server] // 2
