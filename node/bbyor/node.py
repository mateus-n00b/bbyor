"""Round protocol for one peer: serve when selected, answer everyone else's challenges."""
import asyncio
import logging
import random

from eth_account import Account
from eth_account.messages import encode_defunct
from pydantic import ValidationError

from .behaviour import ServerBehaviour
from .config import Attestation
from .crypto.schemes import ChallengeScheme
from .messages import Challenge, RequestChallenge, SignedResult, parse
from .metrics import Metrics

log = logging.getLogger("bbyor.node")


class Node:
    def __init__(
        self,
        *,
        did: str,
        private_key: str,
        chain,
        agent,
        zk,
        scheme: ChallengeScheme,
        attestation: Attestation,
        behaviour: ServerBehaviour,
        metrics: Metrics,
        keeper: bool = False,
        poll_interval: float = 1.0,
        challenge_range: tuple[int, int] = (10, 9999),
        rng: random.Random | None = None,
    ):
        self.did = did
        self._key = private_key
        self.chain = chain
        self.agent = agent
        self.zk = zk
        self.scheme = scheme
        self.attestation = attestation
        self.behaviour = behaviour
        self.metrics = metrics
        self.keeper = keeper
        self.poll_interval = poll_interval
        self.challenge_range = challenge_range
        self.rng = rng or random.SystemRandom()

        self._served: dict[int, Challenge] = {}
        self._expected: dict[int, int] = {}
        self._answered: set[int] = set()
        self._tasks: set[asyncio.Task] = set()
        self._stopped = asyncio.Event()

    @property
    def address(self) -> str:
        return self.chain.address

    # ============ Main loop ============

    async def run(self) -> None:
        next_block = await self._catch_up()
        while not self._stopped.is_set():
            try:
                events, next_block = await self.chain.events_since(next_block)
                for ev in events:
                    if ev.name == "RoundStarted":
                        self._spawn(self.on_round_started(**ev.args))
                if self.keeper and await self.chain.can_advance():
                    await self.chain.advance()
            except Exception:
                log.exception("poll failed")
            try:
                await asyncio.wait_for(self._stopped.wait(), self.poll_interval)
            except TimeoutError:
                pass

    def stop(self) -> None:
        self._stopped.set()

    async def _catch_up(self) -> int:
        """Joins the round in progress (if any) and returns the first block to poll."""
        next_block = await self.chain.block_number() + 1
        round_id = await self.chain.current_round()
        if round_id:
            r = await self.chain.get_round(round_id)
            if not r.finalized:
                did = await self.chain.did_of(r.server)
                self._spawn(self.on_round_started(round_id, r.server, did, r.nonce, r.deadline))
        return next_block

    def _spawn(self, coro) -> None:
        task = asyncio.create_task(self._guard(coro))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    @staticmethod
    async def _guard(coro) -> None:
        try:
            await coro
        except Exception:
            log.exception("handler failed")

    async def drain(self) -> None:
        """Waits for background handlers (used by tests)."""
        while self._tasks:
            await asyncio.gather(*list(self._tasks))

    # ============ Chain events ============

    async def on_round_started(self, round: int, server: str, did: str, nonce: int, deadline: int) -> None:
        if server == self.address:
            await self._serve(round, nonce)
            return

        # Make sure the server can reach us; a fresh connection asks for the challenge explicitly
        if did not in await self.agent.active_connections():
            log.info("round %s: connecting to server %s", round, did)
            conn_id = await self.agent.connect(did)
            await self.agent.send(conn_id, RequestChallenge(round=round).model_dump_json())

    async def _serve(self, round_id: int, nonce: int) -> None:
        reputation = await self.chain.reputation()
        if not self.behaviour.should_serve(round_id, reputation):
            log.info("round %s: selected as server, withholding (rep=%s)", round_id, reputation)
            return

        secret = self.rng.randint(*self.challenge_range)
        with self.metrics.record("challenge_create", round=round_id, scheme=self.scheme.name):
            # Runs on the event loop thread on purpose: OpenFHE deadlocks when first
            # used from a worker thread, and each call takes only ~10 ms
            payload, result = self.scheme.challenge(secret, nonce)

        if self.attestation == Attestation.ZK:
            with self.metrics.record("zk_commit", round=round_id):
                commitment = await self.zk.commit(result, nonce)
            with self.metrics.record("chain_commit", round=round_id):
                await self.chain.commit(round_id, commitment)

        msg = Challenge(round=round_id, scheme=self.scheme.name, payload=payload)
        self._served[round_id] = msg
        self._expected[round_id] = result

        # Verifiers only trust the connection they opened to our public DID, so
        # reply over inbound connections; non-peers may receive it but cannot prove
        conns = await self.agent.inbound_connections()
        content = msg.model_dump_json()
        for conn_id in conns:
            await self.agent.send(conn_id, content)
        log.info("round %s: challenge sent over %d connections (%d eligible peers)",
                 round_id, len(conns), (await self.chain.get_round(round_id)).eligible)

    # ============ DIDComm messages ============

    async def on_message(self, conn_id: str, content: str) -> None:
        try:
            msg = parse(content)
        except ValidationError:
            log.debug("ignoring non-BBYOR message from %s", conn_id)
            return

        match msg:
            case Challenge():
                await self._answer(conn_id, msg)
            case RequestChallenge() if msg.round in self._served:
                await self.agent.send(conn_id, self._served[msg.round].model_dump_json())
            case SignedResult():
                self._check_signature(conn_id, msg)

    async def _answer(self, conn_id: str, msg: Challenge) -> None:
        if msg.round in self._answered:
            return
        r = await self.chain.get_round(msg.round)
        if r.finalized or r.server == self.address:
            return
        sender = (await self.agent.connection(conn_id)).get("their_public_did")
        if sender != await self.chain.did_of(r.server):
            log.warning("round %s: challenge from %s, who is not the server", msg.round, sender)
            return
        if msg.scheme != self.scheme.name:
            log.warning("round %s: scheme %s, expected %s", msg.round, msg.scheme, self.scheme.name)
            return
        self._answered.add(msg.round)
        with self.metrics.record("answer_total", round=msg.round):
            await self._attest(conn_id, msg, r)

    async def _attest(self, conn_id: str, msg: Challenge, r) -> None:
        with self.metrics.record("challenge_respond", round=msg.round, scheme=self.scheme.name):
            result = self.scheme.respond(msg.payload, r.nonce)

        if self.attestation == Attestation.ZK:
            with self.metrics.record("zk_prove", round=msg.round):
                proof = await self.zk.prove(result, r.nonce, r.commitment, int(self.address, 16))
            with self.metrics.record("chain_submit_proof", round=msg.round):
                await self.chain.submit_proof(msg.round, proof)
            log.info("round %s: proof accepted", msg.round)
        else:
            with self.metrics.record("sig_sign", round=msg.round):
                signed = Account.sign_message(_signable(msg.round, result), private_key=self._key)
            reply = SignedResult(round=msg.round, result=str(result), signature=signed.signature.hex())
            await self.agent.send(conn_id, reply.model_dump_json())

    def _check_signature(self, conn_id: str, msg: SignedResult) -> bool:
        with self.metrics.record("sig_verify", round=msg.round):
            signer = Account.recover_message(_signable(msg.round, int(msg.result)), signature=bytes.fromhex(msg.signature))
            ok = self._expected.get(msg.round) == int(msg.result)
        log.info("round %s: signed result from %s (%s) %s", msg.round, conn_id, signer, "ok" if ok else "MISMATCH")
        return ok


def _signable(round_id: int, result: int):
    return encode_defunct(text=f"bbyor:{round_id}:{result}")
