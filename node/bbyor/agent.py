"""Minimal async client for the ACA-Py admin API."""
import asyncio
import json

import httpx


class AcapyClient:
    def __init__(self, admin_url: str, timeout: float = 10.0):
        self._http = httpx.AsyncClient(base_url=admin_url, timeout=timeout)

    async def close(self) -> None:
        await self._http.aclose()

    async def wait_ready(self, timeout: float = 120.0) -> None:
        """Blocks until the admin API answers (the agent starts after the node in compose)."""
        async with asyncio.timeout(timeout):
            while True:
                try:
                    if (await self._http.get("/status/ready")).json().get("ready"):
                        return
                except httpx.TransportError:
                    pass
                await asyncio.sleep(1)

    async def connections(self) -> list[dict]:
        r = await self._http.get("/connections")
        r.raise_for_status()
        return r.json()["results"]

    async def connection(self, conn_id: str) -> dict:
        r = await self._http.get(f"/connections/{conn_id}")
        r.raise_for_status()
        return r.json()

    async def active_connections(self) -> dict[str, str]:
        """Maps their_public_did -> connection_id for completed connections we opened.

        Only the requester side records their_public_did, and it is authenticated:
        the other side answered as the holder of that public DID.
        """
        return {
            c["their_public_did"]: c["connection_id"]
            for c in await self.connections()
            if c.get("rfc23_state") == "completed" and c.get("their_public_did")
        }

    async def inbound_connections(self) -> list[str]:
        """Completed connections other agents opened to our public DID.

        Messages sent here arrive on the peer's side of the connection it opened,
        where it can authenticate us by our public DID.
        """
        return [
            c["connection_id"]
            for c in await self.connections()
            if c.get("rfc23_state") == "completed" and c.get("their_role") == "invitee"
        ]

    async def connect(self, their_public_did: str, timeout: float = 30.0) -> str:
        """Starts a DID exchange with a public DID and waits until it completes."""
        r = await self._http.post(
            "/didexchange/create-request",
            params={"their_public_did": their_public_did, "goal": "BBYOR"},
        )
        r.raise_for_status()
        conn_id = r.json()["connection_id"]

        async with asyncio.timeout(timeout):
            while (await self.connection(conn_id)).get("rfc23_state") != "completed":
                await asyncio.sleep(0.5)
        return conn_id

    async def send(self, conn_id: str, message: str) -> None:
        r = await self._http.post(f"/connections/{conn_id}/send-message", json={"content": message})
        r.raise_for_status()
