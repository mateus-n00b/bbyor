# daemons/contract_poller.py
import asyncio
import logging
from signal import SIGINT, SIGTERM
from contracts.client import contract_client
from config.settings import settings

class ContractPoller:
    def __init__(self, interval_sec: int = 30):
        self.interval = interval_sec
        self._shutdown = False
        self.logger = logging.getLogger("ContractPoller")

    async def run(self):
        """Main daemon loop"""
        self.logger.info("Starting contract poller daemon")
        while not self._shutdown:
            try:
                value = contract_client.get_latest_value()
                self.logger.info(f"Latest contract value: {value}")
                await self._process_value(value)  # Custom logic
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


# from web3 import Web3
# # Setup Web3 connection
# w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
# contract = w3.eth.contract(address="0x9A676e781A523b5d0C0e43731313A708CB607508", abi=contract_abi)

# # Set up the transaction
# account = w3.eth.account.from_key("0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
# nonce = w3.eth.get_transaction_count(account.address)

# tx = contract.functions.setRandomPeer().build_transaction({
#     'from': account.address,
#     'nonce': nonce,
#     'gas': 200000,
#     'gasPrice': w3.to_wei('10', 'gwei')
# })

# # Sign and send
# signed_tx = w3.eth.account.sign_transaction(tx, private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
# tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

# # Wait for receipt
# receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
# print(receipt)
# # Parse event
# res = contract.functions.getRandomPeer().call()
# print(res)
# logs = contract.events.PeerSelected().process_receipt(receipt)
# if logs:
#     selected_peer = logs[0]['args']['peer']
#     timestamp = logs[0]['args']['timestamp']
#     print(f"Selected peer: {selected_peer} at time {timestamp}")
# else:
#     print("No PeerSelected event found")

