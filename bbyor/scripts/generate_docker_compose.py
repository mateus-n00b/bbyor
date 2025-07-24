import random 
import requests as rq
from Crypto.Hash import MD5
N_NODES = 20
# Register dids
# body 
body = {"role":"ENDORSER","alias":None,"did":None,"seed":""}
# Von Network url
url = "http://localhost:9000/register"
# set seed
random.seed(12)
seeds = [
    MD5.MD5Hash(str(random.random()).encode()).hexdigest() for _ in range(N_NODES)
]
# seeds[0] = "02fcd69da34927bc93bae7229e73ea81"
# seeds[1] = "315b7328bfdb532ca0dee81517f49a24"
# seeds[2] = "60b725f10c9c85c70d97880dfe8191b3"
# seeds[3] = "3b5d5c3712955042212316173ccf37be"

dids = []
for i in range(N_NODES):
    body["seed"] = seeds[i]
    result = rq.post(url=url, json=body).json()
    dids.append(result["did"])

print(dids)

docker_compose_file = '''
version: '3'

services:
{0}
       
{1}

networks:
  bbyor:

volumes:
{2}
'''

template_agent = '''
  agent{3}: 
    image: ghcr.io/openwallet-foundation/acapy-agent:py3.12-nightly
    command: >-
      start --inbound-transport http 0.0.0.0 {0} --outbound-transport http --log-level error
      --endpoint http://${{HOST_IP}}:{0} --label AGENT{3} --seed {1}
      --genesis-url http://${{HOST_IP}}:9000/genesis
      --ledger-pool-name localindypool --wallet-key 123456
      --wallet-name bancoumwallet6 --wallet-type askar-anoncreds
      --admin 0.0.0.0 {2}
      --admin-insecure-mode
      --wallet-type askar-anoncreds --storage-type postgres_storage
      --wallet-storage-type postgres_storage
      --wallet-storage-config \\"{{\\"url\\":\\"postgres:5432\\",\\"wallet_scheme\\":\\"agent{3}wallet\\"}}\\"
      --wallet-storage-creds \\"{{\\"account\\":\\"postgres\\",\\"password\\":\\"mysecretpassword\\",\\"admin_account\\":\\"postgres\\",\\"admin_password\\":\\"mysecretpassword\\"}}\\"
      --public-invites --auto-accept-invites --auto-accept-requests --auto-ping-connection
      --auto-respond-messages --auto-respond-credential-offer --auto-respond-presentation-request
      --auto-store-credential --auto-respond-presentation-proposal --auto-respond-credential-request
      --auto-respond-credential-proposal --debug-connections --debug-credentials --debug-presentations
      --auto-provision --requests-through-public-did --admin-client-max-request-size 10
      --webhook-url http://${{HOST_IP}}:{4} --max-message-size 3097152
    ports:
      - {0}:{0}
      - {2}:{2}
    networks:
      - bbyor
    volumes:
      - agent{3}-data:/home/aries/.acapy_agent
'''


template_node = '''
  node{1}:
    image: bbyor
    user: 1000:1000
    command: fastapi dev main.py --host 0.0.0.0
    environment:
      - ACAPY_URL=http://${{HOST_IP}}:{0}
      - PUBLIC_DID={5}
      - LOG_LEVEL=DEBUG
      - DEFAULT_DIR=/home/bbyor/.config/bbyor
      - PROVIDER_URL=http://${{HOST_IP}}:8545
      - GENESIS_FHE=./contracts/genesis_openfhe.json
      - CONTRACT_ADDR=${{CONTRACT_ADDR}}
      - PRIVATE_KEY={4}
      - NODE_BEHAVIOUR={2}
    networks:
      - bbyor
    ports:
      - {3}:8000
    volumes:
      - node{1}-data:/home/bbyor/.config/bbyor
    depends_on:
      - agent{1}
'''

initial_admin_port = 8257
initial_endpoint_port = 8158
initial_api_port = 8004
initial_agent_number = 0

# list of usable private keys
private_keys = [
 "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
"0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
"0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
"0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
"0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
"0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba",
"0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e",
"0x4bbbf85ce3377467afe5d46f804f221813b2bb87f24d81f60f1fcdbf7cbf4356",
"0xdbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97",
"0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6",
"0xf214f2b2cd398c806f84e317254e0f0b801d0643303237d97a22a48e01628897",
"0x701b615bbdfb9de65240bc28bd21bbc0d996645a3dd57e7b12bc2bdf6f192c82",
"0xa267530f49f8280200edf313ee7af6b827f2a8bce2897751d06a843f644967b1",
"0x47c99abed3324a2707c28affff1267e45918ec8c3f20b8aa892e8b065d2942dd",
"0xc526ee95bf44d8fc405a158bb884d9d1238d99f0612e9f33d006bb0789009aaa",
"0x8166f546bab6da521a8369cab06c5d2b9e46670292d85c875ee9ec20e84ffb61",
"0xea6c44ac03bff858b476bba40716402b03e41b8e97e276d1baec7c37d42484a0",
"0x689af8efa8c651a91ad287602527f3af2fe9f6501a7ac4b061667b5a93e037fd",
"0xde9be858da4a475276426320d5e9262ecfc3ba460bfac56360bfa6c4c28b4ee0",
"0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e"
]

# list of strings
nodes = str()
agents = str()
volumes = str()

for i in range(0,N_NODES):
    nodes += template_node.format(initial_admin_port+i, i+initial_agent_number,0,
                                initial_api_port+i, private_keys[i+initial_agent_number], dids[i-1])
    
    agents += template_agent.format(initial_endpoint_port+i, seeds[i-1], initial_admin_port+i,
                                i+initial_agent_number, initial_api_port+i)
    volumes += f"  agent{initial_agent_number+i}-data:\n"

fp = open("/tmp/docker-compose.yml", "w")
content = docker_compose_file.format(agents, nodes, volumes)
fp.write(content)
fp.close()
