"""Streams RoundFinalized events to CSV (one row per finished round).

    uv run --project node python experiments/collect_reputation.py \
        --deployment sim/out/deployment.json --out reputation.csv
"""
import argparse
import asyncio
import csv
import time
from pathlib import Path

from bbyor.chain import Chain

# Read-only: the key is never used to sign
DUMMY_KEY = "0x" + "11" * 32


async def collect(provider: str, deployment: Path, out: Path, interval: float) -> None:
    chain = Chain(provider, deployment, DUMMY_KEY)
    next_block = chain.start_block
    start = time.time()
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        # block_time is the chain's clock: unlike elapsed_s it is right even for
        # rounds that finished before the collector started
        writer.writerow(["elapsed_s", "block_time", "round", "server", "did", "responses", "eligible", "reputation"])
        while True:
            events, next_block = await chain.events_since(next_block)
            for ev in events:
                if ev.name != "RoundFinalized":
                    continue
                a = ev.args
                did = await chain.did_of(a["server"])
                block_time = (await chain.w3.eth.get_block(ev.block))["timestamp"]
                writer.writerow([round(time.time() - start, 1), block_time, a["round"], a["server"], did,
                                 a["responses"], a["eligible"], a["rep"] / 1000])
                f.flush()
                print(f"round {a['round']:4d}  {did}  {a['responses']}/{a['eligible']}  rep={a['rep'] / 1000:.3f}")
            await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", default="http://localhost:8545")
    parser.add_argument("--deployment", type=Path, default=Path("sim/out/deployment.json"))
    parser.add_argument("--out", type=Path, default=Path("reputation.csv"))
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()
    try:
        asyncio.run(collect(args.provider, args.deployment, args.out, args.interval))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
