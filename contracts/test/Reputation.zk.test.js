// End-to-end tests against the real Groth16 verifier (needs `npm run build:circuits`)
const { expect } = require("chai");
const { time } = require("@nomicfoundation/hardhat-network-helpers");
const { deploy, startRound } = require("./helpers");
const zk = require("../../zk/zk");

const RESULT = 123456789n;

async function proofFor(round, commitment, account, result = RESULT) {
  const p = await zk.prove({ result, nonce: round.nonce, commitment, verifier: BigInt(account.address) });
  return [p.a, p.b, p.c];
}

describe("Reputation with Groth16Verifier", function () {
  this.timeout(120_000);

  it("accepts a proof bound to the round and the sender", async function () {
    const { rep, peers } = await deploy({ real: true });
    const { id, round, server, verifiers } = await startRound(rep, peers);
    const commitment = await zk.commit(RESULT, round.nonce);
    await rep.connect(server).commit(id, commitment);

    const [v0, v1] = verifiers;
    const proof = await proofFor(round, commitment, v0);
    await expect(rep.connect(v0).submitProof(id, ...proof)).to.emit(rep, "ProofAccepted");

    // Same proof from another account: public signal `verifier` differs
    await expect(rep.connect(v1).submitProof(id, ...proof)).to.be.revertedWithCustomError(rep, "InvalidProof");
  });

  it("rejects a proof of a different preimage", async function () {
    const { rep, peers } = await deploy({ real: true });
    const { id, round, server, verifiers } = await startRound(rep, peers);
    await rep.connect(server).commit(id, await zk.commit(RESULT, round.nonce));

    // Self-consistent proof for a forged commitment
    const forged = await zk.commit(RESULT + 1n, round.nonce);
    const proof = await proofFor(round, forged, verifiers[0], RESULT + 1n);
    await expect(rep.connect(verifiers[0]).submitProof(id, ...proof)).to.be.revertedWithCustomError(rep, "InvalidProof");
  });

  it("rejects replaying a proof from a previous round", async function () {
    const { rep, peers } = await deploy({ real: true });
    const first = await startRound(rep, peers);
    const commitment = await zk.commit(RESULT, first.round.nonce);
    await rep.connect(first.server).commit(first.id, commitment);
    const v = first.verifiers[0];
    const proof = await proofFor(first.round, commitment, v);
    await rep.connect(v).submitProof(first.id, ...proof);

    await time.increaseTo(first.round.deadline + 1n);
    const second = await startRound(rep, peers);
    // Server of round 2 reuses the old commitment; nonce changed so the proof no longer verifies
    await rep.connect(second.server).commit(second.id, commitment);
    const voter = second.server === v ? first.server : v;
    await expect(rep.connect(voter).submitProof(second.id, ...proof)).to.be.revertedWithCustomError(rep, "InvalidProof");
  });
});
