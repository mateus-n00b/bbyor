"""Async client for the Reputation contract."""
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from eth_account import Account
from web3 import AsyncHTTPProvider, AsyncWeb3

from .zk import Proof

EVENTS = ("RoundStarted", "ChallengeCommitted", "ProofAccepted", "RoundFinalized")


@dataclass
class Round:
    id: int
    server: str
    deadline: int
    eligible: int
    responses: int
    finalized: bool
    nonce: int
    commitment: int


@dataclass
class Event:
    name: str
    block: int
    log_index: int
    args: dict


class Chain:
    def __init__(self, provider_url: str, deployment_file: Path, private_key: str):
        deployment = json.loads(Path(deployment_file).read_text())
        self.w3 = AsyncWeb3(AsyncHTTPProvider(provider_url))
        self.contract = self.w3.eth.contract(address=deployment["address"], abi=deployment["abi"])
        self.start_block = deployment.get("block", 0)
        self.account = Account.from_key(private_key)
        self._tx_lock = asyncio.Lock()

    @property
    def address(self) -> str:
        return self.account.address

    # ---- reads ----

    async def block_number(self) -> int:
        return await self.w3.eth.block_number

    async def current_round(self) -> int:
        return await self.contract.functions.currentRound().call()

    async def get_round(self, round_id: int) -> Round:
        r = await self.contract.functions.rounds(round_id).call()
        return Round(round_id, *r)

    async def can_advance(self) -> bool:
        return await self.contract.functions.canAdvance().call()

    async def reputation(self, account: str | None = None) -> int:
        return await self.contract.functions.reputationOf(account or self.address).call()

    async def did_of(self, account: str) -> str:
        did, _rep, _registered = await self.contract.functions.peers(account).call()
        return did

    async def peer_dids(self) -> list[str]:
        n = await self.contract.functions.peerCount().call()
        accounts = [await self.contract.functions.peerList(i).call() for i in range(n)]
        return [await self.did_of(a) for a in accounts]

    async def events_since(self, from_block: int) -> tuple[list[Event], int]:
        """Returns events in [from_block, latest] in chain order, and the next block to query."""
        latest = await self.block_number()
        if from_block > latest:
            return [], from_block
        events = []
        for name in EVENTS:
            logs = await getattr(self.contract.events, name)().get_logs(from_block=from_block, to_block=latest)
            events += [Event(name, log["blockNumber"], log["logIndex"], dict(log["args"])) for log in logs]
        events.sort(key=lambda e: (e.block, e.log_index))
        return events, latest + 1

    # ---- writes ----

    async def _send(self, fn) -> dict:
        # Gas estimation inside build_transaction surfaces reverts before anything is sent
        async with self._tx_lock:
            tx = await fn.build_transaction({
                "from": self.address,
                "nonce": await self.w3.eth.get_transaction_count(self.address, "pending"),
            })
            # The estimate runs against the current block; advance() takes a different
            # (randomness-dependent) path in the block that actually includes it
            tx["gas"] = tx["gas"] * 6 // 5
            signed = self.account.sign_transaction(tx)
            tx_hash = await self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return await self.w3.eth.wait_for_transaction_receipt(tx_hash)

    async def advance(self) -> dict:
        return await self._send(self.contract.functions.advance())

    async def finalize(self, round_id: int) -> dict:
        return await self._send(self.contract.functions.finalize(round_id))

    async def commit(self, round_id: int, commitment: int) -> dict:
        return await self._send(self.contract.functions.commit(round_id, commitment))

    async def submit_proof(self, round_id: int, proof: Proof) -> dict:
        return await self._send(self.contract.functions.submitProof(round_id, proof.a, proof.b, proof.c))
