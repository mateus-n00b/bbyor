  circom --wasm --r1cs &&\
  snarkjs wtns calculate circuit.wasm input.json witness.wtns && \
  snarkjs powersoftau new bn128 12 pot12_0000.ptau -v && \
  snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau &&\
  snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau <<< ASKASaSKAKSDAKDKAKDKAD &&\
  snarkjs powersoftau new bn128 12 pot12_0000.ptau -v &&\
  snarkjs powersoftau contribute pot12_0000.ptau pot12_0001.ptau --name="First contribution" -v <<<  "ASKASaSKAKSDAKDKAKDKADaeuhudadaks"
  snarkjs powersoftau prepare phase2 pot12_0001.ptau pot12_final.ptau -v &&\
  snarkjs groth16 setup circuit.r1cs pot12_final.ptau circuit2_0000.zkey &&\
  snarkjs zkey contribute circuit2_0000.zkey circuit2_0001.zkey --name="1st Contributor Name" -v <<< "ASKASaSKAKSDAKDKAKDKADaeuhudadakasasas" &&\
  snarkjs zkey export verificationkey circuit2_0001.zkey verification_key.json  &&\
  snarkjs zkey export solidityverifier circuit2_0001.zkey verifier.sol
