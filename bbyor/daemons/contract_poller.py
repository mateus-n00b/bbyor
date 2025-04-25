# daemons/contract_poller.py
import asyncio
import logging
from ..utils.logging import get_logger
from signal import SIGINT, SIGTERM
from ..contracts.client import contract_client
from ..config.settings import settings

class ContractPoller:
    def __init__(self, interval_sec: int = 30):
        self.interval = interval_sec
        self._shutdown = False
        self.logger = get_logger()

    async def run(self):
        """Main daemon loop"""
        self.logger.info("Starting contract poller daemon")
        while not self._shutdown:
            try:
                did, interval = contract_client.get_peer()
                self.interval = int(interval)+1 # update interval
                self.logger.info(f"Latest contract value: {did}")
                await self._process_value(did)  # Custom logic
            except Exception as e:
                self.logger.error(f"Polling failed: {e}", exc_info=True)
            await asyncio.sleep(self.interval)

    async def _process_value(self, value):
        """Override this with your business logic"""

        pass

    def shutdown(self):
        """Graceful shutdown"""
        self._shutdown = True
        self.logger.info("Shutting down poller")

async def start_daemon():
    poller = ContractPoller(interval_sec=settings.POLL_INTERVAL or 15)
    
    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, poller.shutdown)
    
    await poller.run()