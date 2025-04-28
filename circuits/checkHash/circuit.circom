include "../circomlib/circuits/poseidon.circom";
// include "https://github.com/0xPARC/circom-secp256k1/blob/master/circuits/bigint.circom";

template Verify () {
    // hash md5 do nonce
    signal private input hash_result; 
    signal input nonce;
    // md5 do resultado
    signal input result;
    signal output c;    
    
    // var unused = 4;
    // c <== a * b;
    // assert(a > 2);
    
    component hash = Poseidon(2);
    hash.inputs[0] <== hash_result;
    hash.inputs[1] <== nonce;

    // component hash2 = Poseidon(1);
    // hash2.inputs[0] <== result;
   
    c <== hash.out;
    hash.out === result;
}

component main = Verify();