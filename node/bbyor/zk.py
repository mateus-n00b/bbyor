"""Client for zk/zk.js running as a long-lived JSON-lines server."""
import asyncio
import itertools
import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Proof:
    a: list[int]
    b: list[list[int]]
    c: list[int]
    public_signals: list[int]


class ZkError(RuntimeError):
    pass


class ZkProver:
    def __init__(self, script: Path, build_dir: Path | None = None):
        self.script = script
        self.build_dir = build_dir
        self._proc: asyncio.subprocess.Process | None = None
        self._pending: dict[int, asyncio.Future] = {}
        self._ids = itertools.count(1)
        self._reader: asyncio.Task | None = None

    async def start(self) -> None:
        env = dict(os.environ)
        if self.build_dir:
            env["ZK_BUILD_DIR"] = str(self.build_dir)
        self._proc = await asyncio.create_subprocess_exec(
            "node", str(self.script), "serve",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            env=env,
            limit=1 << 20,
        )
        self._reader = asyncio.create_task(self._read_loop())

    async def close(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.stdin.close()
            await self._proc.wait()
        if self._reader:
            await self._reader

    async def _read_loop(self) -> None:
        async for line in self._proc.stdout:
            reply = json.loads(line)
            fut = self._pending.pop(reply["id"], None)
            if fut is None or fut.done():
                continue
            if reply["ok"]:
                fut.set_result(reply["value"])
            else:
                fut.set_exception(ZkError(reply["error"]))
        for fut in self._pending.values():
            fut.set_exception(ZkError("zk server exited"))
        self._pending.clear()

    async def _call(self, op: str, **args):
        if self._proc is None:
            await self.start()
        req_id = next(self._ids)
        fut = asyncio.get_running_loop().create_future()
        self._pending[req_id] = fut
        payload = {"id": req_id, "op": op, "args": {k: str(v) for k, v in args.items()}}
        self._proc.stdin.write((json.dumps(payload) + "\n").encode())
        await self._proc.stdin.drain()
        return await fut

    async def commit(self, result: int, nonce: int) -> int:
        return int(await self._call("commit", result=result, nonce=nonce))

    async def prove(self, result: int, nonce: int, commitment: int, verifier: int) -> Proof:
        v = await self._call("prove", result=result, nonce=nonce, commitment=commitment, verifier=verifier)
        return Proof(
            a=[int(x) for x in v["a"]],
            b=[[int(x) for x in row] for row in v["b"]],
            c=[int(x) for x in v["c"]],
            public_signals=[int(x) for x in v["publicSignals"]],
        )
