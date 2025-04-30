# contracts/client.py
import json
from web3 import Web3
from ..config.settings import settings


class ContractClient:
    def __init__(self):
        try:
            self.w3 = Web3(Web3.HTTPProvider(settings.PROVIDER_URL))
            with open(settings.CONTRACT_ABI_PATH) as f:
                abi = json.load(f)

            self.contract = self.w3.eth.contract(
                address=settings.CONTRACT_ADDR,
                abi=abi
            )
            self.did = settings.PUBLIC_DID

        except Exception as e:
            print(f"[ERROR] Contract initialization failed: {e}")
            raise

    def get_latest_value(self):
        """Read the latest chosen peer."""
        try:
            return self.contract.functions.getLastChosenPeer().call()
        except Exception as e:
            print(f"[ERROR] Failed to get latest value: {e}")
            return None

    def get_latest_interval(self):
        try:
            interval = self.contract.functions.getRemainingTime().call()
            return interval
        except Exception as e:
            print(f"[ERROR] Failed to get latest interval: {e}")
            return None

    def signtx(self, tx):
        try:
            return self.w3.eth.account.sign_transaction(tx, private_key=settings.PRIVATE_KEY)
        except Exception as e:
            print(f"[ERROR] Transaction signing failed: {e}")
            raise

    def send_tx(self, signed_tx):
        try:
            return self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        except Exception as e:
            print(f"[ERROR] Sending transaction failed: {e}")
            raise

    def get_receipt(self, tx_hash):
        try:
            return self.w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            print(f"[ERROR] Waiting for receipt failed: {e}")
            raise

    def get_nonce(self, a: int):
        try:
            account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)
            nonce = self.w3.eth.get_transaction_count(account.address)

            tx = self.contract.functions.getNonce().build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': self.w3.to_wei('10', 'gwei')
            })

            signed_tx = self.signtx(tx)
            tx_hash = self.send_tx(signed_tx)
            receipt = self.get_receipt(tx_hash)

            logs = self.contract.events.NonceCreated().process_receipt(receipt)
            if logs:
                nonce = logs[0]['args']['nonce']
                did = logs[0]['args']['did']
                print(f"Selected nonce: {nonce} for DID {did}")
            else:
                print("No NonceCreated event found")
            return nonce

        except Exception as e:
            print(f"[ERROR] Failed to get nonce: {e}")
            return None

    def verify(self, proof: list):
        try:
            return self.contract.functions.verifyProof(
                proof[0], proof[1], proof[2], proof[3]
            ).call()
        except Exception as e:
            print(f"[ERROR] Proof verification failed: {e}")
            return False

    def register_neighbor(self, neighbor_did: str):
        try:
            account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)
            nonce = self.w3.eth.get_transaction_count(account.address)

            print("Registering neighbor...")
            tx = self.contract.functions.registerNeighbor(self.did, neighbor_did).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': self.w3.to_wei('10', 'gwei')
            })

            signed_tx = self.signtx(tx)
            tx_hash = self.send_tx(signed_tx)
            self.get_receipt(tx_hash)

        except Exception as e:
            print(f"[ERROR] Failed to register neighbor: {e}")

    def register_result(self, proof: list):
        try:
            account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)
            nonce = self.w3.eth.get_transaction_count(account.address)

            tx = self.contract.functions.registerResult(
                self.did, proof[0], proof[1], proof[2], proof[3]
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': self.w3.to_wei('10', 'gwei')
            })

            signed_tx = self.signtx(tx)
            tx_hash = self.send_tx(signed_tx)
            receipt = self.get_receipt(tx_hash)

            logs = self.contract.events.VerifiedProof().process_receipt(receipt)
            if logs:
                selected_peer = logs[0]['args']['did']
                verified = logs[0]['args']['verified']
                print(f"Verified result: {selected_peer}, return {verified}")
                return verified
            else:
                print("No VerifiedProof event found")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to register result: {e}")
            return False
        
    def update_server_rep(self):
        try:
            account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)
            nonce = self.w3.eth.get_transaction_count(account.address)

            tx = self.contract.functions.updateServerRep().build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': self.w3.to_wei('10', 'gwei')
            })

            signed_tx = self.signtx(tx)
            tx_hash = self.send_tx(signed_tx)
            receipt = self.get_receipt(tx_hash)    
        except Exception as e:
            # print(f"[ERROR] Failed to get peer: {e}")
            pass
    
    def get_reputation(self, did: str = None):
        did = did if did else settings.PUBLIC_DID
        return self.contract.functions.getReputation(did).call()

    def get_peer(self):
        try:
            account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)
            nonce = self.w3.eth.get_transaction_count(account.address)

            tx = self.contract.functions.getRandomPeer().build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': self.w3.to_wei('10', 'gwei')
            })

            signed_tx = self.signtx(tx)
            tx_hash = self.send_tx(signed_tx)
            receipt = self.get_receipt(tx_hash)

            logs = self.contract.events.PeerSelected().process_receipt(receipt)
            if logs:
                selected_peer = logs[0]['args']['peer']
                interval = logs[0]['args']['interval']
                print(f"Selected peer: {selected_peer} at time {interval}")
                return selected_peer, interval
            else:
                print("No PeerSelected event found")
                return None, None

        except Exception as e:
            print(f"[ERROR] Failed to get peer: {e}")
            return None, None


# Singleton instance
contract_client = ContractClient()
