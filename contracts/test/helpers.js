const { ethers } = require("hardhat");

const MIN_INTERVAL = 30;
const MAX_INTERVAL = 40;
const ZERO_PROOF = [[0, 0], [[0, 0], [0, 0]], [0, 0]];

async function deploy({ real = false, nPeers = 4 } = {}) {
  const signers = await ethers.getSigners();
  const [owner, ...rest] = signers;
  const verifier = await ethers.deployContract(real ? "Groth16Verifier" : "MockVerifier");
  const rep = await ethers.deployContract("Reputation", [
    await verifier.getAddress(),
    MIN_INTERVAL,
    MAX_INTERVAL,
  ]);
  const peers = rest.slice(0, nPeers);
  for (const [i, p] of peers.entries()) {
    await rep.registerPeer(p.address, `did:sov:peer${i}`);
  }
  return { owner, peers, outsider: rest[nPeers], verifier, rep };
}

// Starts a round and returns its number, data and the signers split by role
async function startRound(rep, peers) {
  await rep.advance();
  const id = await rep.currentRound();
  const round = await rep.rounds(id);
  const server = peers.find((p) => p.address === round.server);
  const verifiers = peers.filter((p) => p !== server);
  return { id, round, server, verifiers };
}

module.exports = { MIN_INTERVAL, MAX_INTERVAL, ZERO_PROOF, deploy, startRound };
