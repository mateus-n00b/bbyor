from ..contracts.client import contract_client
from ..config.settings import settings
import time
import json
from datetime import datetime
from pathlib import Path


def run():
    data = {}

    Path("/tmp").mkdir(parents=True, exist_ok=True)

    try:
        with open(settings.GENESIS_FHE) as f:
            peers = json.load(f)

        for peer in peers:
            data[peer] = [0]

        start = datetime.now()

        with open("/tmp/data.csv", "w+") as fp, open("/tmp/receipt.txt", "w+") as recp:
            last_round = None
            while True:
                time.sleep(1)
                now = (datetime.now() - start).total_seconds()
                changed = False
                last_did = None
                _round = None

                result = contract_client.get_latest_value()
                if result:
                    last_did, _round = result

                for did in peers:
                    if not result:
                        continue

                    if last_round != _round:
                        receipt = contract_client.get_round_receipt(_round)
                        recp.write(json.dumps(receipt) + "\n")
                        recp.flush()
                        last_round = _round

                    rep = float(contract_client.get_reputation(did)) / 1000
                    rep = min(rep, 1.0)

                    if last_did and last_did not in data:
                        last_rep = float(contract_client.get_reputation(last_did)) / 1000
                        max_size = max(len(arr) for arr in data.values())
                        fill_data_array = [0.35] * max_size
                        data[last_did] = fill_data_array + [last_rep]
                        peers.append(last_did)

                    if rep != data[did][-1]:
                        changed = True
                        data[did].append(rep)

                if changed and last_did and _round is not None:
                    print(f"Last chosen: {last_did} at round {_round}")
                    for did in peers:
                        print(f"{now},{did},{data[did][-1]}")
                        fp.write(f"{now},{did},{data[did][-1]}\n")
                    fp.flush()
                    print()

    except KeyboardInterrupt:
        with open("/tmp/data.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Finalizado com Ctrl+C. Dados salvos em /tmp/data.json")


if __name__ == '__main__':
    run()
