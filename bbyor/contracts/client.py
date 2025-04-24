# contracts/client.py
from web3 import Web3
from config.settings import settings
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
        return self.contract.functions.getValue().call()

# Singleton instance
contract_client = ContractClient()