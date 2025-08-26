from ..contracts.client import contract_client
import json
from ..config.settings import settings
import time
from datetime import datetime

def run():
    with open("/tmp/data.csv", "w+") as fp:
        try:
            data = {}
            with open(settings.GENESIS_FHE) as f:
                peers = json.load(f)   
                for peer in peers:
                    data[peer] = [0]                 
                start = datetime.now()            
                while True:    
                    time.sleep(1)
                    now = (datetime.now()-start).total_seconds()
                    changed = False
                    last_did = None
                    for did in peers:
                        # print(f"collecting did: {did}")
                        _data = contract_client.get_latest_value()
                        if _data:
                            last_did, _round = _data
                            rep = float(contract_client.get_reputation(did))/1000
                            rep = rep if rep <= 1.0 else 1.0 
                            if not data.get(last_did) and last_did:
                                last_rep = float(contract_client.get_reputation(last_did))/1000
                                data[last_did] = [last_rep]
                                peers.append(last_did)
                            # Did it change?
                            if rep != data[did][-1]:
                                # print(f"{now},{did},{rep}")
                                changed = True
                                data[did].append(rep)
                    if changed:
                        print(f"Last chosen: {last_did} at round {_round}")                    
                        for did in peers:
                            print(f"{now},{did},{data[did][-1]}")
                            fp.write(f"{now},{did},{data[did][-1]}\n")
                        print()
                    time.sleep(1)
        except KeyboardInterrupt:
            fp.close()
            json.dump(data, open("/tmp/data.json", "w"), indent=2)

if __name__ == '__main__':
    run()
