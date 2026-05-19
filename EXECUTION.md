# BBYOR — Guia de Execução

## Visão Geral do Fluxo

```
[Von Network (Indy Ledger)]
         ↓
[Registrar DIDs + Gerar docker-compose]
         ↓
[Deploy do Smart Contract (Hardhat)]
         ↓
[Build da imagem Docker]
         ↓
[Subir ACA-Py Agents + Nós BBYOR]
         ↓
[Coleta de dados (opcional)]
```

## Pré-requisitos

| Ferramenta | Versão testada | Instalação |
|---|---|---|
| Docker + Docker Compose | 24+ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Node.js + npm | 22.x | Incluso na imagem Docker |
| Python | 3.10+ | Necessário apenas para scripts locais |
| Hardhat | — | `npm install` na raiz |

> **Nota**: OpenFHE e snarkjs são instalados automaticamente pelo `Dockerfile.api`. Não é necessário instalá-los no host.

---

## Passo 1 — Iniciar o Ledger Indy (Von Network)

O Von Network provê o ledger Hyperledger Indy local necessário para os agentes ACA-Py.

```bash
git clone https://github.com/bcgov/von-network.git
cd von-network
./manage build
./manage start --logs
```

Aguarde até o painel estar disponível em `http://localhost:9000`.

---

## Passo 2 — Registrar DIDs e Gerar o `docker-compose.yml`

O script `generate_docker_compose.py` registra os DIDs no ledger e gera o arquivo de orquestração completo.

```bash
cd /caminho/para/bbyor

# Instalar dependências locais para rodar o script
pip install requests pycryptodome

# Executar o gerador (requer Von Network ativo)
python -m bbyor.scripts.generate_docker_compose
```

O arquivo gerado é salvo em `/tmp/docker-compose.yml`. Copie-o para a raiz do projeto:

```bash
cp /tmp/docker-compose.yml ./docker-compose.yml
```

O script também imprime os seeds e DIDs gerados. Atualize o arquivo `bbyor/contracts/genesis_openfhe.json` com os DIDs na ordem em que foram gerados:

```json
[
    "DID_DO_NO_0",
    "DID_DO_NO_1",
    "DID_DO_NO_2",
    "DID_DO_NO_3"
]
```

> Para controlar o número de nós, edite `N_NODES` no topo do script. O comportamento dos nós (`NODE_BEHAVIOUR`) é definido no template — por padrão os primeiros dois são honestos (0), e os demais são atacantes (1 e 2). Ajuste conforme necessário.

---

## Passo 3 — Deploy do Smart Contract

```bash
# Instalar dependências do Hardhat
npm install

# Iniciar o nó Ethereum local (em outro terminal)
npx hardhat node

# Em outro terminal: compilar e fazer deploy
npx hardhat clean
npx hardhat compile
npx hardhat ignition deploy ignition/modules/Lock.js --network localhost
```

O endereço do contrato será exibido no terminal. Guarde-o para o próximo passo.

```
Deployed Addresses
BBYOR#BBYOR - 0x5FbDB2315678afecb367f032d93F642f64180aa3
```

---

## Passo 4 — Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
# IP da máquina host (visível pelos containers)
export HOST_IP=$(hostname -I | awk '{print $1}')

# Endereço do contrato deployado no passo anterior
export CONTRACT_ADDR=0x5FbDB2315678afecb367f032d93F642f64180aa3
```

Ou exporte diretamente no shell:

```bash
export HOST_IP=$(hostname -I | awk '{print $1}')
export CONTRACT_ADDR=<endereço_do_deploy>
```

---

## Passo 5 — Build da Imagem Docker

```bash
docker build -f docker/Dockerfile.api -t bbyor .
```

> O build demora alguns minutos na primeira vez pois compila o OpenFHE do zero.

---

## Passo 6 — Subir os Agentes e Nós

```bash
docker-compose up -d
```

Isso inicializa, para cada nó:
- Um agente **ACA-Py** (identidade DID, transporte de mensagens)
- Um **nó BBYOR** (FastAPI + poller do contrato + FHE + ZK)

Verificar os logs:

```bash
# Logs de todos os serviços
docker-compose logs -f

# Logs de um nó específico
docker-compose logs -f node0
docker-compose logs -f node1
```

Os nós estão prontos quando a linha abaixo aparecer nos logs:

```
INFO  - Starting contract poller daemon
```

### Portas expostas por padrão (4 nós)

| Serviço | Porta | Descrição |
|---|---|---|
| node0 | 8001 | Webhook / API BBYOR |
| node1 | 8002 | Webhook / API BBYOR |
| node2 | 8003 | Webhook / API BBYOR |
| node3 | 8004 | Webhook / API BBYOR |
| agent0 | 8150 / 8250 | Endpoint / Admin ACA-Py |
| agent1 | 8151 / 8251 | Endpoint / Admin ACA-Py |
| agent2 | 8152 / 8252 | Endpoint / Admin ACA-Py |
| agent3 | 8153 / 8253 | Endpoint / Admin ACA-Py |

---

## Passo 7 — Coleta de Dados (Simulação)

Com o ambiente rodando, inicie a coleta de métricas de reputação:

```bash
CONTRACT_ADDR=<endereço> \
CONTRACT_ABI_PATH=bbyor/contracts/artifacts/abi.json \
GENESIS_FHE=bbyor/contracts/genesis_openfhe.json \
python -m bbyor.services.collect_data
```

Os dados são gravados em tempo real em `/tmp/data.csv` no formato:

```
<tempo_segundos>,<DID>,<reputação>
12.3,18q1r8BkyTQLMKC7XxPuG,0.35
25.1,AQjRaYC89jBJL4e7SEYwaP,0.41
```

Encerre com `Ctrl+C`. Um snapshot JSON também é salvo em `/tmp/data.json`.

---

## Comportamentos dos Nós

Configurado via variável `NODE_BEHAVIOUR` em cada serviço no `docker-compose.yml`:

| Valor | Comportamento |
|---|---|
| `0` | Honesto — sempre propõe o desafio quando selecionado |
| `1` | Falho — falha em propor o desafio 30% das vezes |
| `2` | Atacante estratégico — age honestamente até atingir reputação 0.6, depois para de propor |

---

## Resetar o Ambiente

```bash
# Parar e remover containers + volumes
docker-compose down -v

# Rebuildar e subir novamente
docker-compose up -d --build
```

Para resetar apenas o estado do ledger, reinicie o Von Network:

```bash
cd von-network
./manage stop
./manage start
```

Após reiniciar o ledger, repita a partir do **Passo 2** (os DIDs precisam ser re-registrados).

---

## Estrutura Relevante do Projeto

```
bbyor/
├── bbyor/
│   ├── api/routers/         # Webhooks FastAPI (mensagens ACA-Py)
│   ├── config/
│   │   ├── settings.py      # Configurações via variáveis de ambiente
│   │   └── provision.py     # Inicialização: chaves FHE + conexões
│   ├── contracts/
│   │   ├── client.py        # Interface Web3 com o contrato
│   │   └── genesis_openfhe.json  # DIDs dos nós participantes
│   ├── daemons/
│   │   └── contract_poller.py    # Loop principal: polling + desafio + reputação
│   ├── services/
│   │   ├── challenge.py     # Lógica do protocolo de desafio FHE
│   │   ├── circom.py        # Geração e verificação de provas ZK
│   │   └── fhe.py           # Operações homomórficas (OpenFHE/BFV)
│   └── scripts/
│       └── generate_docker_compose.py  # Gerador de ambiente
├── circuits/
│   ├── checkHash/           # Circuito do provador (verifica hash FHE)
│   └── gen_hash/            # Circuito do challenger (gera hash de referência)
├── contracts/
│   └── bbyor.sol            # Contrato principal (reputação + ZK on-chain)
├── docker/
│   └── Dockerfile.api       # Imagem com OpenFHE + snarkjs + FastAPI
└── docker-compose.yml       # Gerado pelo script do Passo 2
```
