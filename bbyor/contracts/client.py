# contracts/client.py
from web3 import Web3
from ..config.settings import settings
import json

class ContractClient:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.PROVIDER_URL))
        with open(settings.CONTRACT_ABI_PATH) as f:
            abi = json.load(f)
        self.contract = self.w3.eth.contract(
            address=settings.CONTRACT_ADDR,
            abi=abi
        )

    def get_latest_value(self):
        """Example: Read a 'getValue()' function from the contract"""
        return self.contract.functions.getLastChosenPeer().call()
    
    def get_latest_interval(self):
         return self.contract.functions.lastRandomInterval().call()

    def signtx(self, tx):
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=settings.PRIVATE_KEY)
        return signed_tx
    
    def send_tx(self, signed_tx):
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            return tx_hash
    
    def get_receipt(self, tx_hash):
         receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
         return receipt
    
    def get_peer(self):
        account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)
        nonce = self.w3.eth.get_transaction_count(account.address)
        tx = self.contract.functions.getRandomPeer().build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': self.w3.to_wei('10', 'gwei')
        })
        signed_tx = self.signtx(tx)
        hash = self.send_tx(signed_tx)
        receipt = self.get_receipt(hash)
        logs = self.contract.events.PeerSelected().process_receipt(receipt)
        if logs:
            selected_peer = logs[0]['args']['peer']
            interval = logs[0]['args']['interval']
            print(f"Selected peer: {selected_peer} at time {interval}")
        else:
            print("No PeerSelected event found")
        return selected_peer, interval

        
# Singleton instance
contract_client = ContractClient()