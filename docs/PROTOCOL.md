# BBYOR — Especificação do protocolo (v2)

## Objetivo

Medir, de forma verificável on-chain, se um peer **servidor** presta o serviço
que se espera dele numa rodada: publicar um desafio e entregá-lo aos demais
peers. A reputação do servidor sobe quando a maioria qualificada dos peers
consegue provar que recebeu e processou o desafio, e cai caso contrário.

## Participantes

| Papel | Quem | O que faz |
|---|---|---|
| Owner | quem fez o deploy | admite peers (`registerPeer(account, did)`) |
| Servidor | peer sorteado na rodada | publica `commitment` e envia o desafio via DIDComm |
| Verificador | todos os outros peers admitidos | calcula a resposta e envia uma prova ZK |
| Keeper | qualquer conta | chama `advance()` para finalizar e abrir rodadas |

Cada peer tem uma conta Ethereum própria. O contrato mapeia `account ↔ DID`
de forma única, e toda ação de peer usa `msg.sender`.

## Rodada

```
advance()                      ── RoundStarted(round, server, did, nonce, deadline)
  servidor: x ← aleatório
            payload, result ← scheme.challenge(x, nonce)
            commitment ← Poseidon(result, nonce)
            commit(round, commitment)       ── ChallengeCommitted
            DIDComm → verificadores: {round, payload}
  verificador: result ← scheme.respond(payload, nonce)
               prova π de: Poseidon(result, nonce) == commitment
               submitProof(round, π)        ── ProofAccepted(round, verifier)
deadline passa
advance()                      ── RoundFinalized(round, server, responses, eligible, rep)
                               ── RoundStarted(round+1, ...)
```

- `nonce` é gerado pelo contrato em `advance()` e já é reduzido ao campo BN254.
- `eligible` = número de peers admitidos − 1, congelado no início da rodada.
- `result` é um elemento de campo: `int(SHA-256(bytes)[:31])`.

### Circuito `response`

```
private: result
public:  nonce, commitment, verifier
Poseidon(result, nonce) === commitment
verifier * verifier  (restrição que amarra o sinal público)
```

O contrato monta os sinais públicos com `rounds[r].nonce`,
`rounds[r].commitment` e `uint160(msg.sender)`. A prova só vale **naquela**
rodada e **para aquela** conta, então não dá para reenviar a prova de outra
rodada nem a de outro verificador.

### Regra de reputação (escala 0–1000, inicial 350)

| Condição | Atualização |
|---|---|
| servidor não publicou `commitment`, ou `responses == 0` | `rep ← rep × 0.50` |
| `3·responses < 2·eligible` | `rep ← rep × 0.80` |
| caso contrário | `rep ← min(1000, rep + 20·responses/eligible)` |

## Esquemas de desafio (`scheme`)

| Nome | `challenge(x, nonce)` | `respond(payload, nonce)` |
|---|---|---|
| `fhe` | `ct ← Enc_pk(x)`; payload = `ct`; result = H(`ct ⊞ nonce`) | result = H(`ct ⊞ nonce`) |
| `plain` | payload = `x`; result = H(`x + nonce`) | result = H(`x + nonce`) |

Os dois esquemas usam o mesmo fluxo on-chain. Assim, a comparação de custo
isola o que muda de fato: o custo da parte FHE.

### Atestação baseline (`attestation = signature`)

Para reproduzir o baseline original, o verificador assina `result` com a sua
conta e devolve a assinatura ao servidor por DIDComm, sem tocar a cadeia. Esse
modo serve só para métricas e não altera reputação.

## Modelo de ameaça

Cobre:
- **Replay de prova** entre rodadas ou entre verificadores: os sinais públicos
  são amarrados à rodada e a `msg.sender`.
- **Voto forjado** em nome de outro DID: o DID vem do registro, não de um
  parâmetro.
- **Voto duplicado**: no máximo uma prova por verificador por rodada.
- **Servidor que só finge**: sem `commitment` não há como provar; sem envio do
  payload os verificadores não conseguem calcular `result`.
- **Inflar o denominador**: `eligible` vem do registro do owner, não de
  chamadas abertas.

Não cobre (limitações conhecidas):
- **Conluio**: um verificador que recebeu o payload pode repassar `result` a
  outro peer admitido, que então prova sem ter falado com o servidor.
- **Aleatoriedade**: `prevrandao`/`blockhash` são manipuláveis pelo produtor de
  blocos. Basta para a rede local; para produção, use commit-reveal ou VRF
  (a função `_random` é `virtual`).
- **Privacidade do `x`**: no esquema `fhe` o servidor cifra com a própria
  chave. FHE aqui mede custo computacional e não protege nada dos
  verificadores.
- **Trusted setup**: o setup de fase 2 é feito localmente por um único
  contribuidor (só para desenvolvimento).
