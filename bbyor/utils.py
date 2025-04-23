import json 

def read_genesis(path="../contract/genesis_openfhe.json"):
    genesis = open(path, 'r')
    js = json.loads(genesis.read())
    return js

def missing_conn(connections: dict):
    peers = read_genesis()
    missing = []
    for con in peers:
        if con not in str(connections):
            missing.append(con)
    return missing