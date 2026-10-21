"""FastAPI app: receives ACA-Py webhooks and runs the node loop."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from .agent import AcapyClient
from .behaviour import build_behaviour
from .chain import Chain
from .config import Attestation, Settings
from .crypto.schemes import build_scheme
from .metrics import Metrics
from .node import Node
from .zk import ZkProver

log = logging.getLogger("bbyor")


async def connect_to_peers(node: Node) -> None:
    """Opens DID exchanges with every registered peer we are not connected to yet."""
    connected = await node.agent.active_connections()
    for did in set(await node.chain.peer_dids()) - {node.did} - connected.keys():
        try:
            await node.agent.connect(did)
        except Exception as err:
            log.warning("could not connect to %s: %s", did, err)


def build_node(settings: Settings) -> Node:
    metrics = Metrics(settings.metrics_file, settings.public_did)
    zk = ZkProver(settings.zk_script, settings.zk_build_dir) if settings.attestation == Attestation.ZK else None
    return Node(
        did=settings.public_did,
        private_key=settings.private_key,
        chain=Chain(settings.provider_url, settings.deployment_file, settings.private_key),
        agent=AcapyClient(settings.acapy_url),
        zk=zk,
        scheme=build_scheme(settings.scheme.value, settings.key_dir),
        attestation=settings.attestation,
        behaviour=build_behaviour(settings),
        metrics=metrics,
        keeper=settings.keeper,
        poll_interval=settings.poll_interval,
        challenge_range=(settings.challenge_min, settings.challenge_max),
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        node = build_node(settings)
        app.state.node = node
        await connect_to_peers(node)
        loop = asyncio.create_task(node.run())
        yield
        node.stop()
        await loop
        if node.zk:
            await node.zk.close()
        await node.agent.close()

    app = FastAPI(title="BBYOR node", lifespan=lifespan)

    @app.post("/topic/basicmessages/")
    async def basic_message(request: Request):
        body = await request.json()
        app.state.node._spawn(app.state.node.on_message(body["connection_id"], body["content"]))
        return {"status": "accepted"}

    @app.post("/topic/{topic}/")
    async def other_topic(topic: str):
        return {"status": "ignored"}

    @app.get("/status")
    async def status():
        node = app.state.node
        return {
            "did": node.did,
            "address": node.address,
            "reputation": await node.chain.reputation(),
            "round": await node.chain.current_round(),
            "scheme": node.scheme.name,
            "attestation": node.attestation.value,
        }

    return app


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
