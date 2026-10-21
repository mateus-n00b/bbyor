#!/usr/bin/env bash
# Compiles the response circuit, runs a local (dev-only) phase-2 setup on top
# of the public PSE Perpetual Powers of Tau, and exports the Solidity verifier.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/circuits/src"
OUT="$ROOT/circuits/build"
SNARKJS="$ROOT/node_modules/.bin/snarkjs"
PTAU="$OUT/ppot_0080_12.ptau"
PTAU_URL="https://pse-trusted-setup-ppot.s3.eu-central-1.amazonaws.com/pot28_0080/ppot_0080_12.ptau"
VERIFIER="$ROOT/contracts/src/generated/Groth16Verifier.sol"

mkdir -p "$OUT" "$(dirname "$VERIFIER")"

if [ ! -f "$PTAU" ]; then
    echo "Downloading $PTAU_URL"
    curl -fsSL -o "$PTAU" "$PTAU_URL"
fi

circom "$SRC/response.circom" --r1cs --wasm -o "$OUT"

"$SNARKJS" groth16 setup "$OUT/response.r1cs" "$PTAU" "$OUT/response_0000.zkey"
"$SNARKJS" zkey contribute "$OUT/response_0000.zkey" "$OUT/response.zkey" \
    --name="bbyor dev" -e="$(head -c 32 /dev/urandom | xxd -p -c 64)"
rm "$OUT/response_0000.zkey"

"$SNARKJS" zkey export verificationkey "$OUT/response.zkey" "$OUT/verification_key.json"
"$SNARKJS" zkey export solidityverifier "$OUT/response.zkey" "$VERIFIER"

echo "Artifacts in $OUT, verifier at $VERIFIER"
