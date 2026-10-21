const { expect } = require("chai");
const { time } = require("@nomicfoundation/hardhat-network-helpers");
const { MIN_INTERVAL, MAX_INTERVAL, ZERO_PROOF, deploy, startRound } = require("./helpers");

const FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617n;

describe("Reputation", function () {
  describe("registration", function () {
    it("lets only the owner admit peers", async function () {
      const { rep, outsider } = await deploy();
      await expect(rep.connect(outsider).registerPeer(outsider.address, "did:x"))
        .to.be.revertedWithCustomError(rep, "NotOwner");
    });

    it("rejects duplicate accounts and DIDs", async function () {
      const { rep, peers, outsider } = await deploy();
      await expect(rep.registerPeer(peers[0].address, "did:new"))
        .to.be.revertedWithCustomError(rep, "AlreadyRegistered");
      await expect(rep.registerPeer(outsider.address, "did:sov:peer0"))
        .to.be.revertedWithCustomError(rep, "AlreadyRegistered");
    });

    it("starts peers at the initial reputation", async function () {
      const { rep, peers } = await deploy();
      expect(await rep.reputationOf(peers[0].address)).to.equal(350);
      expect(await rep.reputationOfDid("did:sov:peer1")).to.equal(350);
    });
  });

  describe("rounds", function () {
    it("needs at least three peers", async function () {
      const { rep } = await deploy({ nPeers: 2 });
      expect(await rep.canAdvance()).to.equal(false);
      await expect(rep.advance()).to.be.revertedWithCustomError(rep, "InsufficientPeers");
    });

    it("picks a registered server, a field nonce and a bounded deadline", async function () {
      const { rep, peers } = await deploy();
      const { round, server } = await startRound(rep, peers);
      const now = BigInt(await time.latest());

      expect(server).to.not.equal(undefined);
      expect(round.nonce).to.be.lessThan(FIELD);
      expect(round.deadline).to.be.gte(now + BigInt(MIN_INTERVAL));
      expect(round.deadline).to.be.lte(now + BigInt(MAX_INTERVAL));
      expect(round.eligible).to.equal(peers.length - 1);
    });

    it("cannot advance while a round is active", async function () {
      const { rep, peers } = await deploy();
      await startRound(rep, peers);
      expect(await rep.canAdvance()).to.equal(false);
      await expect(rep.advance()).to.be.revertedWithCustomError(rep, "RoundActive");
    });

    it("finalizes the previous round when advancing after the deadline", async function () {
      const { rep, peers } = await deploy();
      const first = await startRound(rep, peers);
      await time.increaseTo(first.round.deadline + 1n);

      expect(await rep.canAdvance()).to.equal(true);
      await expect(rep.advance()).to.emit(rep, "RoundFinalized").withArgs(1, first.server.address, 0, 3, 175);
      expect((await rep.rounds(1)).finalized).to.equal(true);
      expect((await rep.rounds(2)).server).to.not.equal(first.server.address);
    });

    it("lets anyone finalize an expired round exactly once", async function () {
      const { rep, peers, outsider } = await deploy();
      const { id, round } = await startRound(rep, peers);
      await expect(rep.finalize(id)).to.be.revertedWithCustomError(rep, "RoundNotOver");
      await time.increaseTo(round.deadline + 1n);
      await rep.connect(outsider).finalize(id);
      await expect(rep.finalize(id)).to.be.revertedWithCustomError(rep, "RoundClosed");
    });
  });

  describe("commit", function () {
    it("accepts one valid commitment from the server only", async function () {
      const { rep, peers } = await deploy();
      const { id, server, verifiers } = await startRound(rep, peers);

      await expect(rep.connect(verifiers[0]).commit(id, 1)).to.be.revertedWithCustomError(rep, "NotServer");
      await expect(rep.connect(server).commit(id, 0)).to.be.revertedWithCustomError(rep, "InvalidCommitment");
      await expect(rep.connect(server).commit(id, FIELD)).to.be.revertedWithCustomError(rep, "InvalidCommitment");
      await expect(rep.connect(server).commit(id, 42)).to.emit(rep, "ChallengeCommitted").withArgs(id, 42);
      await expect(rep.connect(server).commit(id, 43)).to.be.revertedWithCustomError(rep, "AlreadyCommitted");
    });

    it("is closed after the deadline", async function () {
      const { rep, peers } = await deploy();
      const { id, round, server } = await startRound(rep, peers);
      await time.increaseTo(round.deadline + 1n);
      await expect(rep.connect(server).commit(id, 1)).to.be.revertedWithCustomError(rep, "RoundClosed");
    });
  });

  describe("submitProof", function () {
    it("enforces commitment, membership, role and one vote per verifier", async function () {
      const { rep, peers, outsider } = await deploy();
      const { id, server, verifiers } = await startRound(rep, peers);
      const v = verifiers[0];

      await expect(rep.connect(v).submitProof(id, ...ZERO_PROOF)).to.be.revertedWithCustomError(rep, "NotCommitted");
      await rep.connect(server).commit(id, 42);

      await expect(rep.connect(outsider).submitProof(id, ...ZERO_PROOF)).to.be.revertedWithCustomError(rep, "NotRegistered");
      await expect(rep.connect(server).submitProof(id, ...ZERO_PROOF)).to.be.revertedWithCustomError(rep, "ServerCannotVerify");
      await expect(rep.connect(v).submitProof(id, ...ZERO_PROOF)).to.emit(rep, "ProofAccepted").withArgs(id, v.address);
      await expect(rep.connect(v).submitProof(id, ...ZERO_PROOF)).to.be.revertedWithCustomError(rep, "AlreadyResponded");
    });

    it("reverts when the verifier rejects the proof", async function () {
      const { rep, peers, verifier } = await deploy();
      const { id, server, verifiers } = await startRound(rep, peers);
      await rep.connect(server).commit(id, 42);
      await verifier.setAccept(false);
      await expect(rep.connect(verifiers[0]).submitProof(id, ...ZERO_PROOF)).to.be.revertedWithCustomError(rep, "InvalidProof");
    });

    it("is closed after the deadline", async function () {
      const { rep, peers } = await deploy();
      const { id, round, server, verifiers } = await startRound(rep, peers);
      await rep.connect(server).commit(id, 42);
      await time.increaseTo(round.deadline + 1n);
      await expect(rep.connect(verifiers[0]).submitProof(id, ...ZERO_PROOF)).to.be.revertedWithCustomError(rep, "RoundClosed");
    });
  });

  describe("reputation rule", function () {
    // 4 peers -> 3 eligible verifiers; initial reputation 350
    const cases = [
      { responses: 3, expected: 370, label: "full quorum: +20" },
      { responses: 2, expected: 363, label: "2/3 quorum: +floor(2*20/3)" },
      { responses: 1, expected: 280, label: "below quorum: x0.8" },
      { responses: 0, expected: 175, label: "no responses: x0.5" },
    ];

    for (const { responses, expected, label } of cases) {
      it(label, async function () {
        const { rep, peers } = await deploy();
        const { id, round, server, verifiers } = await startRound(rep, peers);
        await rep.connect(server).commit(id, 42);
        for (const v of verifiers.slice(0, responses)) {
          await rep.connect(v).submitProof(id, ...ZERO_PROOF);
        }
        await time.increaseTo(round.deadline + 1n);
        await expect(rep.finalize(id))
          .to.emit(rep, "RoundFinalized")
          .withArgs(id, server.address, responses, 3, expected);
        expect(await rep.reputationOf(server.address)).to.equal(expected);
      });
    }

    it("decays a server that never commits", async function () {
      const { rep, peers } = await deploy();
      const { id, round, server } = await startRound(rep, peers);
      await time.increaseTo(round.deadline + 1n);
      await rep.finalize(id);
      expect(await rep.reputationOf(server.address)).to.equal(175);
    });

    it("caps reputation at 1000", async function () {
      const { rep, peers } = await deploy({ nPeers: 3 });
      let last = 350n;
      // A target server needs ~33 successful rounds to saturate; run until it does
      for (let i = 0; i < 200 && last < 1000n; i++) {
        const { id, round, server, verifiers } = await startRound(rep, peers);
        await rep.connect(server).commit(id, 42);
        for (const v of verifiers) await rep.connect(v).submitProof(id, ...ZERO_PROOF);
        await time.increaseTo(round.deadline + 1n);
        await rep.finalize(id);
        last = await rep.reputationOf(peers[0].address);
      }
      expect(last).to.equal(1000n);
    });
  });
});
