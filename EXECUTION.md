# BBYOR — Guia de Execução

## Visão geral

```
[Von Network (ledger Indy)]
          ↓
[build dos circuitos + imagens]
          ↓
[sim/generate.py: registra DIDs, atribui contas, gera compose]
          ↓
[docker compose up: chain → deploy → agents + nodes]
          ↓
[coleta de reputação e métricas]
```

Diferenças em relação à versão anterior:

- Não é preciso copiar endereço de contrato nem DIDs à mão. O serviço `deploy`
  grava `sim/out/deployment.json`, que os nós leem, e os peers vêm do
  registro on-chain (o `genesis_openfhe.json` deixou de existir).
- Cada nó tem a sua própria conta Ethereum (derivada do mnemônico do Hardhat).
- Os agentes se comunicam pela rede do compose; não existe mais `HOST_IP`.

## Pré-requisitos

| Ferramenta | Versão testada |
|---|---|
| Docker + Compose (v1.29+ ou plugin v2) | 29 / 1.29.2 |
| Node.js + npm | 20.x |
| circom | 2.2.x |
| Python + [uv](https://docs.astral.sh/uv/) | 3.12 |

OpenFHE só é compilado dentro da imagem do nó.

---

## Passo 1 — Von Network

```bash
git clone https://github.com/bcgov/von-network.git
cd von-network
./manage build
./manage start --logs
```

Aguarde o painel em `http://localhost:9000`.

## Passo 2 — Circuitos e imagens

```bash
npm install
npm run build:circuits     # gera circuits/build/ e contracts/src/generated/Groth16Verifier.sol

docker build -f docker/Dockerfile.chain -t bbyor-chain:dev .
docker build -f docker/Dockerfile.node  -t bbyor-node:dev .   # demora: compila OpenFHE
```

> Rode `build:circuits` **antes** das duas imagens: a chave de prova
> (`response.zkey`) do nó precisa corresponder ao verificador do contrato.
> Se refizer o setup, reconstrua as duas imagens.

## Passo 3 — Cenário

Edite ou copie `sim/scenarios/default.toml`:

```toml
scheme = "fhe"          # fhe | plain
attestation = "zk"      # zk | signature (baseline)
min_interval = 30
max_interval = 40

[[nodes]]
count = 2
behaviour = "honest"

[[nodes]]
count = 1
behaviour = "intermittent"
fail_probability = 0.3

[[nodes]]
count = 1
behaviour = "on_off"
attack_threshold = 600
```

Gere o ambiente (o von-network precisa estar no ar):

```bash
cd node && uv sync && cd ..
uv run --project node python sim/generate.py sim/scenarios/default.toml
```

Saída em `sim/out/`: `peers.json`, `docker-compose.yml` e `.env`.

## Passo 4 — Subir

```bash
cd sim/out
docker compose up -d        # ou docker-compose up -d
docker compose logs -f node0
```

Ordem de inicialização: `chain` → `deploy` (registra os peers e grava
`deployment.json`) → `agentN` + `nodeN`. O `node0` é o keeper: ele chama
`advance()` sempre que uma rodada pode ser fechada.

Estado de um nó:

```bash
curl localhost:8100/status    # node0; nodeN em api_port_base + N
```

| Serviço | Porta no host |
|---|---|
| chain (Hardhat) | 8545 |
| nodeN | `api_port_base` + N (padrão 8100) |

## Passo 5 — Coleta

Reputação por rodada (CSV):

```bash
uv run --project node python experiments/collect_reputation.py --out reputation.csv
```

Métricas de latência dos nós (JSONL) e gráficos:

```bash
experiments/collect_metrics.sh out/fhe_zk
python3 experiments/plot_metrics.py out/fhe_zk/metrics_all.jsonl fhe.png
```

Para comparar com o baseline, gere um cenário com `scheme = "plain"` e
`attestation = "signature"`, repita a coleta e rode:

```bash
python3 experiments/plot_metrics.py out/fhe_zk/metrics_all.jsonl \
    --baseline out/baseline/metrics_all.jsonl comparison.png
```

(`plot_metrics.py` precisa de numpy, scipy e matplotlib.)

## Comportamentos

| `behaviour` | Efeito quando o nó é sorteado servidor |
|---|---|
| `honest` | sempre publica o commitment e envia o desafio |
| `intermittent` | deixa de servir com probabilidade `fail_probability` (determinístico por `seed` e rodada) |
| `on_off` | serve enquanto a reputação estiver abaixo de `attack_threshold` (0–1000) e depois para |

## Resetar

```bash
cd sim/out && docker compose down -v
```

Se o ledger for reiniciado, rode o Passo 3 de novo para re-registrar os DIDs.
