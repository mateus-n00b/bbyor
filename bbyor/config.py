import os
from .services.fhe import genKey,serializeKeyToFile
# Config vars
HOME = os.getenv("HOME")
DEFAULT_DIR=f"{HOME}/.config/bbyor"
class Config:
    url = os.getenv("ACAPY_URL")
    connections_url = "/connections"
    did_exchange_endpoint = "/didexchange/create-request?their_public_did="
    # blockchain config
    provider_url = os.getenv("PROVIDER_URL")
    contract_addr = os.getenv("CONTRACT_ADDR")
    contract_abi = open("./contracts/artifacts/abi.json")

    @classmethod
    def provision(cls):
        if not os.path.exists(DEFAULT_DIR):
            os.mkdir(f"{HOME}/.config")
            os.mkdir(f"{HOME}/.config/bbyor")
            # Gen FHE keys
            keypair = genKey()
            serializeKeyToFile("pk.bin", keypair.publicKey)
            serializeKeyToFile("sk.bin", keypair.secretKey)
            # Save Keys
        return keypair