import random 
import requests as rq
from Crypto.Hash import MD5
N_NODES = 16
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
print(seeds)
print(dids)

docker_compose_file = '''
version: '3'

services:
  postgres0:
    restart: always
    image: docker.io/postgres:latest
    environment:
      POSTGRES_PASSWORD: mysecretpassword
      POSTGRES_USER: postgres
      POSTGRES_DB: config
    ports:
      - "5430:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data  # 🔐 Data is stored here
    networks:
     - bbyor
  
  postgres1:
    restart: always
    image: docker.io/postgres:latest
    environment:
      POSTGRES_PASSWORD: mysecretpassword
      POSTGRES_USER: postgres
      POSTGRES_DB: config
    ports:
      - "5431:5432"
    volumes:
      - postgres1_data:/var/lib/postgresql/data  # 🔐 Data is stored here
    networks:
     - bbyor
{0}
       
{1}

networks:
  bbyor:

volumes:
{2}
'''

template_agent = '''
  agent{3}: 
    image: ghcr.io/openwallet-foundation/acapy-agent:py3.12-1.2-lts
    restart: always
    command: >-
      start --inbound-transport http 0.0.0.0 {0} --outbound-transport http --log-level error
      --endpoint http://${{HOST_IP}}:{0} --label AGENT{3} --seed {1}
      --genesis-url http://${{HOST_IP}}:9000/genesis
      --ledger-pool-name localindypool --wallet-key 123456
      --wallet-name agentwallet{3} --wallet-type askar-anoncreds
      --admin 0.0.0.0 {2}
      --admin-insecure-mode      
      --wallet-storage-type postgres_storage
      --wallet-storage-config \"{{\\"url\\":\\"postgres{5}:5432\\",\\"wallet_scheme\\":\\"DatabasePerWallet\\"}}\"
      --wallet-storage-creds \"{{\\"account\\":\\"postgres\\",\\"password\\":\\"mysecretpassword\\",\\"admin_account\\":\\"postgres\\",\\"admin_password\\":\\"mysecretpassword\\"}}\"
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
    depends_on:
      - postgres{5}
'''


template_node = '''
  node{1}:
    image: bbyor
    user: 1000:1000
    restart: always
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

initial_admin_port = 8250
initial_endpoint_port = 8150
initial_api_port = 8001
initial_agent_number = 0

# list of usable private keys
private_keys = [
    "0x9e72e5257645bebc6e3423696be498c6973cc23cee4aaad507d04331d51fcef6",
    "0xc9f2b0f3e426d1c1762969646514c6867a344280a426a0c19a8e1ceff165c652",
    "0x37bc62a2211c499229142f1c3f9ec7d5bc0862344e046a5ce45e85baad16754c",
    "0x8dca8c3a531975af7ff143c03521fde166beff2da7d906ab924caba7950c07aa",
    "0xdb095ce70247e93723a507c20c4ae4a6d40dcd18e8eddb97c6bef1489fa42567",
    "0x038c8d2ad550b2a18a89915a6d87be68ce91b8fc010bf743b9d85f360138ad92",
    "0x19492ac1462223783f45f285ed8beefa6ff81f00bd42a6419db02c73a878550f",
    "0x30e081c086429075ddbae2b364742494860b263653fc7194f91af221e42dea9e",
    "0x86e0c2dc23073b139d36e0b904db838578240f047a6f851fb63fcf9249f313e4",
    "0xce681576d1985fb0a19a8c32739aa311896f86021bbdeb36eca66228debb7bac",
    "0x1ad7ba2e9249b2197a1b85d2244c696b4b1cd7538b90b8b03e78c721988c8792",
    "0xda8946aeffb70eb54328973b9716bc0de1c40a5c095c6811f4aab24a23d0347a",
    "0xe864cd5684388b3e45fde298c4233f15ea8471999cb8c2981dba57d65c7d839f",
    "0xeabee7ad809d11db3e57203ead8986e81edd7d5cc5171d73a71d6fe766320e93",
    "0xe2ebfd09dd0ce9b83b030712ca9e3407c3f0f89d5aacd89cc012d1587bc5ba7a",
    "0x2305d3efbc13470290eeb6c178b16d1ce9f16e5a3bef2b649da987565a846d46",
    "0xa1b70c8562ea369c1d29df8b57005842b282b912c2497b7a25207594881836ca",
    "0x04959805c11f6f4fc4f111bfadcfe947fc61340a3486ae461e061761be64a998",
    "0x523dbf81975291516744e5a32a60c1a7eefd4b7879a046fcc5dee4d5b82604da",
    "0xc9d3a40323f0997171c29ee83d56776cd3fe89659605cf77e72cdad530f8b436"
]

# list of strings
nodes = str()
agents = str()
volumes = str()

for i in range(N_NODES):
    nodes += template_node.format(initial_admin_port+i, i+initial_agent_number,0,
                                initial_api_port+i, private_keys[i], dids[i])
    
    postgres_id = 0 if initial_agent_number+i % 2 == 0 else 1
    agents += template_agent.format(initial_endpoint_port+i, seeds[i], initial_admin_port+i,
                                i+initial_agent_number, initial_api_port+i, postgres_id)
    volumes += f"  agent{i}-data:\n"
    volumes += f"  node{i}-data:\n"
volumes += "  postgres_data:\n"
volumes += "  postgres1_data:\n"


fp = open("/tmp/docker-compose.yml", "w")
content = docker_compose_file.format(agents, nodes, volumes)
fp.write(content)
fp.close()
