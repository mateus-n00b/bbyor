from ..contracts.client import contract_client
import json
from ..config.settings import settings
import time
from datetime import datetime

def run():
    fp = open("/tmp/data.csv", "w")
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
                for did in peers:
                    # print(f"collecting did: {did}")
                    rep = float(contract_client.get_reputation(did))/1000
                    rep = rep if rep <= 1.0 else 1.0 
                    # Did it change?
                    if rep != data[did][-1]:
                        # print(f"{now},{did},{rep}")
                        changed = True
                        data[did].append(rep)
                if changed:
                   for did in peers:
                       print(f"{now},{did},{data[did][-1]}")
                       fp.write(f"{now},{did},{data[did][-1]}\n")
                time.sleep(5)
    except KeyboardInterrupt:
        fp.close()
        json.dump(data, open("/tmp/data.json", "w"), indent=2)

if __name__ == '__main__':
    run()