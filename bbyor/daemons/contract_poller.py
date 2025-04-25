# daemons/contract_poller.py
import asyncio
import logging
from ..utils.logging import get_logger
from signal import SIGINT, SIGTERM
from ..contracts.client import contract_client
from ..config.settings import settings
from ..services.challenge import propose_challenge

class ContractPoller:
    def __init__(self, interval_sec: int = 30):
        self.interval = interval_sec
        self._shutdown = False
        self.logger = get_logger()
        self.lastChosenPeer = None

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
                # NOTE: uncomment this to reveal details about the revert reason
                # self.logger.error(f"Polling failed: {e} > Trying again", exc_info=True)
                did = contract_client.get_latest_value()
                self.interval = int(contract_client.get_latest_interval())
                self.logger.info(f"Latest DID: {did} at {self.interval}")
                await self._process_value(did)

            await asyncio.sleep(self.interval)

    async def _process_value(self, did):
        """Override this with your business logic"""
        if did == settings.PUBLIC_DID:
            propose_challenge()           

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