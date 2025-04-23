import os
# Config vars
class Config:
    url = os.getenv("ACAPY_URL")
    connections_url = "/connections"
    did_exchange_endpoint = "/didexchange/create-request?their_public_did="