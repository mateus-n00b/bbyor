from ..contracts.client import contract_client
import json
from ..config.settings import settings
import time
def run():
    try:
        data = {}
        with open(settings.GENESIS_FHE) as f:
            peers = json.load(f)   
            for peer in peers:
                data[peer] = [0]                 
            while True:    
                for did in peers:
                    # print(f"collecting did: {did}")
                    rep = float(contract_client.get_reputation(did))/1000
                    rep = rep if rep <= 1.0 else 1.0 
                    if rep != data[did][-1]:
                        print(did, rep)
                        data[did].append(rep)
                time.sleep(3)
    except KeyboardInterrupt:
        json.dump(data, open("/tmp/data.json", "w"), indent=2)

if __name__ == '__main__':
    run()