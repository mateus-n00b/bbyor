# daemons/contract_poller.py
import asyncio
import logging
from ..utils.logging import get_logger
from ..utils.randomizer import chance_30_percent
from signal import SIGINT, SIGTERM
from ..contracts.client import contract_client
from ..config.settings import settings
from ..services.challenge import propose_challenge, request_challenge
from ..services.baseline import propose_baseline_challenge
from ..services.connections import establish_connection, get_connections
from datetime import datetime

class ContractPoller:
    def __init__(self, interval_sec: int = 5):
        self.interval = interval_sec
        self._shutdown = False
        self.logger = get_logger()
        self.last_round = 0
        self.last_finalized_round = 0
        self.elapsed_time = datetime.now()
        self.counter = 0
        self.node_turn = False

    async def run(self):
        """Main daemon loop"""
        self.logger.info("Starting contract poller daemon")
        while not self._shutdown:
            try:
                did, interval, _round = contract_client.get_peer()
                self.interval = 2
                if _round != self.last_round:
                    self.logger.info(f"Latest contract value: {did}")
                    self.last_round = _round
                    await self._process_value(did)
                                    
            except Exception as e:
                self.logger.error(f"Polling failed: {e} > Trying again", exc_info=True)

                data = contract_client.get_latest_value()
                if data:
                    did, _round = data
                    if _round != self.last_round:
                        self.interval = 1  # fallback
                        self.logger.info(f"Latest DID: {did} at {self.interval} - at round {_round}")
                        self.last_round = _round
                        await self._process_value(did)
                        
                else:
                    self.logger.error("No fallback value available from contract")
            
            # Finalize round once interval expires (retries silently until contract allows it)
            # if self.last_round > self.last_finalized_round:
            contract_client.update_server_rep(int(self.last_round))
                    # self.last_finalized_round = self.last_round
            
            await asyncio.sleep(self.interval)

    def _propose(self, _round: int):
        if settings.BASELINE_MODE:
            propose_baseline_challenge(_round=_round)
        else:
            propose_challenge(_round=_round)

    async def _process_value(self, did):
        """Override this with your business logic"""
        if did == settings.PUBLIC_DID:
            if settings.NODE_BEHAVIOUR == 1 and not self.node_turn:
                self.node_turn = True

                # Fail 30% of the time
                if not chance_30_percent(settings.SEED + self.counter):
                    self.logger.info("Good boy... For now")
                    self._propose(_round=self.last_round)

                self.counter += 1
            elif settings.NODE_BEHAVIOUR == 2:
                # Wait till higher reputation to perform the attack
                if float(contract_client.get_reputation()) / 1000 < 0.6:
                    self.logger.info("Good boy... For now")
                    self._propose(_round=self.last_round)
            else:
                self._propose(_round=self.last_round)
        else:
            # reset node_turn
            self.node_turn = False
            # Do I know this DID? If not, connect 
            # NOTE: implement some kind of flag to this (AUTO_CONNECT = True)
            # Problem: acapy doesnt prevent redudant connections
            # NOTE: if there is no connections active -> fail 
            # BUG: Sometimes the did does not exists and condition fails 
            my_connections = get_connections()["results"] 
            if did not in str(my_connections):
                conn_id = establish_connection(did)
                if conn_id:
                    self.logger.info("Registering neighbor...")
                    contract_client.register_neighbor(did)
                    conn_data = None
                    while not (conn_data and conn_data.get("rfc23_state") == "completed"):
                        conn_data = get_connections(conn_id)
                        await asyncio.sleep(1)
                    request_challenge(conn_id)

    def shutdown(self):
        """Graceful shutdown"""
        self._shutdown = True
        self.logger.info("Shutting down poller")

async def start_daemon():
    poller = ContractPoller(interval_sec=settings.POLL_INTERVAL or 5)
    
    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, poller.shutdown)
    
    await poller.run()
