# daemons/contract_poller.py
import asyncio
import logging
from ..utils.logging import get_logger
from ..utils.randomizer import chance_30_percent
from signal import SIGINT, SIGTERM
from ..contracts.client import contract_client
from ..config.settings import settings
from ..services.challenge import propose_challenge
from ..services.connections import establish_connection, get_connections
from datetime import datetime

class ContractPoller:
    def __init__(self, interval_sec: int = 2):
        self.interval = interval_sec
        self._shutdown = False
        self.logger = get_logger()
        self.lastChosenPeer = None
        self.elapsed_time = datetime.now()

    async def run(self):
        """Main daemon loop"""
        self.logger.info("Starting contract poller daemon")
        while not self._shutdown:
            try:
                did, interval = contract_client.get_peer()                
                self.interval = int(interval) # update interval
                self.logger.info(f"Latest contract value: {did}")
                await self._process_value(did)  # Custom logic
            except Exception as e:
                # NOTE: uncomment this to reveal details about the revert reason
                # self.logger.error(f"Polling failed: {e} > Trying again", exc_info=True)
                did = contract_client.get_latest_value()
                # self.interval = int(contract_client.get_latest_interval())-1           
                self.interval = 1     
                self.logger.info(f"Latest DID: {did} at {self.interval}")
                await self._process_value(did)
            
            # Update server reputation (ignore output)
            contract_client.update_server_rep()
            
            await asyncio.sleep(self.interval)

    async def _process_value(self, did):
        """Override this with your business logic"""
        if did == settings.PUBLIC_DID:
            if settings.NODE_BEHAVIOUR == 1: 
                # Fail 30% of the time
                if chance_30_percent(12):
                    propose_challenge()   
            elif settings.NODE_BEHAVIOUR == 2:
                # Wait till the higher reputation to perform the attack
                if float(contract_client.get_reputation())/1000 < 0.6:
                    propose_challenge()
            else:
                propose_challenge()
        else:
            # Do I know this DID? If not, connect 
            # NOTE: implement some kind of flag to this (AUTO_CONNECT = True)
            # Problem: acapy doesnt prevent redudant connections
            my_connections = get_connections()["results"]
            if did not in str(my_connections):
                if establish_connection(did):
                    self.logger.info("Registering neighbor...")
                    contract_client.register_neighbor(did)

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