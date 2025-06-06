include "../circomlib/circuits/poseidon.circom";
// include "https://github.com/0xPARC/circom-secp256k1/blob/master/circuits/bigint.circom";

template GenHash () {
    // md5 do resultado
    signal private input result;
    signal input nonce;
    signal output c;    
    
    component hash = Poseidon(2);
    hash.inputs[0] <== result;
    hash.inputs[1] <== nonce;

    c <== hash.out;
}

component main = GenHash();