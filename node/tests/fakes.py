from dataclasses import replace

from bbyor.chain import Round
from bbyor.crypto.field import to_field
from bbyor.zk import Proof


class FakeChain:
    """Shared in-memory stand-in for the contract; `for_account` gives each node its view."""

    def __init__(self, peers: dict[str, str]):
        self.peers = peers  # address -> did
        self.rounds: dict[int, Round] = {}
        self.reputations = {a: 350 for a in peers}
        self.commits: list[tuple[str, int, int]] = []
        self.proofs: list[tuple[str, int, Proof]] = []
        self.address = None

    def for_account(self, address: str) -> "FakeChain":
        view = object.__new__(FakeChain)
        view.__dict__ = self.__dict__.copy()
        view.address = address
        return view

    def start(self, round_id: int, server: str, nonce: int = 77) -> Round:
        self.rounds[round_id] = Round(round_id, server, 10**10, len(self.peers) - 1, 0, False, nonce, 0)
        return self.rounds[round_id]

    async def block_number(self):
        return 1

    async def current_round(self):
        return max(self.rounds, default=0)

    async def get_round(self, round_id):
        return self.rounds[round_id]

    async def reputation(self, account=None):
        return self.reputations[account or self.address]

    async def did_of(self, account):
        return self.peers[account]

    async def peer_dids(self):
        return list(self.peers.values())

    async def commit(self, round_id, commitment):
        self.commits.append((self.address, round_id, commitment))
        self.rounds[round_id] = replace(self.rounds[round_id], commitment=commitment)

    async def submit_proof(self, round_id, proof):
        self.proofs.append((self.address, round_id, proof))


class FakeAgent:
    def __init__(self, connections: dict[str, str] | None = None):
        self.connections = dict(connections or {})  # their did -> conn id
        self.sent: list[tuple[str, str]] = []
        self.connected: list[str] = []

    async def active_connections(self):
        return dict(self.connections)

    async def connection(self, conn_id):
        did = next((d for d, c in self.connections.items() if c == conn_id), None)
        return {"connection_id": conn_id, "their_public_did": did}

    async def connect(self, did):
        conn_id = f"conn-{did}"
        self.connections[did] = conn_id
        self.connected.append(did)
        return conn_id

    async def send(self, conn_id, message):
        self.sent.append((conn_id, message))


class FakeZk:
    async def commit(self, result, nonce):
        return to_field(f"{result}:{nonce}".encode())

    async def prove(self, result, nonce, commitment, verifier):
        assert await self.commit(result, nonce) == commitment, "witness would not satisfy the circuit"
        return Proof([1, 2], [[3, 4], [5, 6]], [7, 8], [nonce, commitment, verifier])
