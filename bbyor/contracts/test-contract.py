from web3 import Web3
import json
import time

# Conectar ao nó Ethereum (mude para seu provedor/nó local)
w3 = Web3(Web3.HTTPProvider("http://192.168.0.19:8545"))

# Configurações
private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
account = w3.eth.account.from_key(private_key)
my_address = w3.to_checksum_address(account.address)
contract_address = w3.to_checksum_address("0xD8a5a9b31c3C0232E196d518E89Fd8bF83AcAd43")

# ABI contendo apenas o necessário (evento + função)
abi = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "internalType": "string", "name": "peer", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "PeerSelected",
        "type": "event"
    },
    {
        "inputs": [],
        "name": "getRandomPeer",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Instancia o contrato
contract = w3.eth.contract(address=contract_address, abi=abi)

# Criar transação para chamar getRandomPeer()
nonce = w3.eth.get_transaction_count(my_address)
tx = contract.functions.getRandomPeer().build_transaction({
    'from': my_address,
    'nonce': nonce,
    'gas': 200000,
    'gasPrice': w3.to_wei('30', 'gwei')
})

# Assinar e enviar
signed_tx = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print(f"Transação enviada! Hash: {tx_hash.hex()}")

# Esperar a transação ser minerada
print("Aguardando confirmação da transação...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# Verificar logs de evento PeerSelected
events = contract.events.PeerSelected().process_receipt(tx_receipt)

# Exibir os eventos encontrados
for e in events:
    peer = e['args']['peer']
    timestamp = e['args']['timestamp']
    print(f"🎯 Peer selecionado: {peer}")
    print(f"🕒 Timestamp: {timestamp}")
