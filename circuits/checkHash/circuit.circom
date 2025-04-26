include "../circomlib/circuits/poseidon.circom";
// include "https://github.com/0xPARC/circom-secp256k1/blob/master/circuits/bigint.circom";

template Verify () {
    // hash md5 do nonce
    signal input nonce;
    // md5 do resultado
    signal input result;
    signal input c;
    
    // var unused = 4;
    // c <== a * b;
    // assert(a > 2);
    
    component hash = Poseidon(2);
    hash.inputs[0] <== result;
    hash.inputs[1] <== nonce;

    c === hash.out;

    // log("hash", hash.out);
}

component main = Verify();