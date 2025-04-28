include "../circomlib/circuits/poseidon.circom";
// include "https://github.com/0xPARC/circom-secp256k1/blob/master/circuits/bigint.circom";

template Verify () {
    // hash md5 do nonce
    signal private input hash_result; 
    signal input nonce;
    // md5 do resultado
    signal input result;
    // did should be converted to int
    signal input in_did;
    signal output c;    

    component hash = Poseidon(2);
    hash.inputs[0] <== hash_result;
    hash.inputs[1] <== nonce;   
   
    c <== hash.out;
    hash.out === result;
}

component main = Verify();