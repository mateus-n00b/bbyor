pragma circom 2.1.6;

include "../../node_modules/circomlib/circuits/poseidon.circom";

// Proves knowledge of `result` such that Poseidon(result, nonce) == commitment.
// `verifier` is the submitter's address; it is bound to the proof so a proof
// cannot be resubmitted by another account.
template Response() {
    signal input result;
    signal input nonce;
    signal input commitment;
    signal input verifier;

    component h = Poseidon(2);
    h.inputs[0] <== result;
    h.inputs[1] <== nonce;
    h.out === commitment;

    // Keeps `verifier` in the constraint system (see Tornado Cash's recipient binding)
    signal verifierSquare;
    verifierSquare <== verifier * verifier;
}

component main {public [nonce, commitment, verifier]} = Response();
