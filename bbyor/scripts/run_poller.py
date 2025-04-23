# scripts/run_poller.py
import asyncio
import logging
from daemons.contract_poller import start_daemon

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    try:
        asyncio.run(start_daemon())
    except KeyboardInterrupt:
        pass