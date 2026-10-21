import json
import random

import pytest
from eth_account import Account

from bbyor.behaviour import Honest, OnOff
from bbyor.config import Attestation
from bbyor.crypto.schemes import PlainScheme
from bbyor.messages import Challenge, RequestChallenge, parse
from bbyor.metrics import Metrics
from bbyor.node import Node

from .fakes import FakeAgent, FakeChain, FakeZk

KEYS = [Account.create() for _ in range(4)]
SERVER, V1, V2, OUTSIDER = KEYS
DIDS = {k.address: f"did:{i}" for i, k in enumerate(KEYS[:3])}


def make_node(chain, account, agent, *, attestation=Attestation.ZK, behaviour=None, tmp_path=None):
    return Node(
        did=DIDS.get(account.address, "did:outsider"),
        private_key=account.key.hex(),
        chain=chain.for_account(account.address),
        agent=agent,
        zk=FakeZk(),
        scheme=PlainScheme(),
        attestation=attestation,
        behaviour=behaviour or Honest(),
        metrics=Metrics(tmp_path / "m.jsonl" if tmp_path else None, "test"),
        rng=random.Random(1),
    )


@pytest.fixture
def chain():
    c = FakeChain(dict(DIDS))
    c.start(1, SERVER.address)
    return c


async def test_server_commits_and_sends_to_registered_peers_only(chain, tmp_path):
    agent = FakeAgent({"did:1": "c1", "did:2": "c2", "did:stranger": "cx"})
    node = make_node(chain, SERVER, agent, tmp_path=tmp_path)

    await node.on_round_started(1, SERVER.address, "did:0", 77, 0)

    assert len(chain.commits) == 1 and chain.commits[0][:2] == (SERVER.address, 1)
    assert sorted(c for c, _ in agent.sent) == ["c1", "c2"]
    ops = [json.loads(l)["operation"] for l in (tmp_path / "m.jsonl").read_text().splitlines()]
    assert ops == ["challenge_create", "zk_commit", "chain_commit"]


async def test_strategic_server_withholds(chain):
    chain.reputations[SERVER.address] = 700
    agent = FakeAgent({"did:1": "c1"})
    node = make_node(chain, SERVER, agent, behaviour=OnOff(600))

    await node.on_round_started(1, SERVER.address, "did:0", 77, 0)

    assert chain.commits == [] and agent.sent == []


async def serve(chain):
    """Runs the server side and returns the challenge content it sent."""
    agent = FakeAgent({"did:1": "c1"})
    server = make_node(chain, SERVER, agent)
    await server.on_round_started(1, SERVER.address, "did:0", 77, 0)
    return server, agent, agent.sent[0][1]


async def test_verifier_proves_once_bound_to_its_address(chain):
    _, _, content = await serve(chain)
    node = make_node(chain, V1, FakeAgent({"did:0": "s"}))

    await node.on_message("s", content)
    await node.on_message("s", content)

    assert len(chain.proofs) == 1
    submitter, round_id, proof = chain.proofs[0]
    assert (submitter, round_id) == (V1.address, 1)
    assert proof.public_signals == [77, chain.rounds[1].commitment, int(V1.address, 16)]


async def test_verifier_ignores_challenge_not_from_server(chain):
    _, _, content = await serve(chain)
    node = make_node(chain, V1, FakeAgent({"did:0": "s", "did:2": "impostor"}))

    await node.on_message("impostor", content)

    assert chain.proofs == []


async def test_verifier_ignores_other_scheme(chain):
    await serve(chain)
    node = make_node(chain, V1, FakeAgent({"did:0": "s"}))

    await node.on_message("s", Challenge(round=1, scheme="fhe", payload="00").model_dump_json())

    assert chain.proofs == []


async def test_unconnected_verifier_connects_and_requests_challenge(chain):
    agent = FakeAgent()
    node = make_node(chain, V1, agent)

    await node.on_round_started(1, SERVER.address, "did:0", 77, 0)

    assert agent.connected == ["did:0"]
    assert agent.sent == [("conn-did:0", RequestChallenge(round=1).model_dump_json())]


async def test_server_replays_challenge_on_request(chain):
    server, agent, content = await serve(chain)

    await server.on_message("late", RequestChallenge(round=1).model_dump_json())
    await server.on_message("late", RequestChallenge(round=99).model_dump_json())

    assert agent.sent[-1] == ("late", content)
    assert len(agent.sent) == 2


async def test_signature_baseline_roundtrip(chain, tmp_path):
    server_agent = FakeAgent({"did:1": "c1"})
    server = make_node(chain, SERVER, server_agent, attestation=Attestation.SIGNATURE, tmp_path=tmp_path)
    await server.on_round_started(1, SERVER.address, "did:0", 77, 0)
    assert chain.commits == []  # baseline never touches the chain

    v_agent = FakeAgent({"did:0": "s"})
    verifier = make_node(chain, V1, v_agent, attestation=Attestation.SIGNATURE)
    await verifier.on_message("s", server_agent.sent[0][1])
    assert chain.proofs == []

    reply = v_agent.sent[0][1]
    assert server._check_signature("c1", parse(reply))
