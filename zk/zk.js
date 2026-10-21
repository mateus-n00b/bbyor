// Poseidon commitments and Groth16 proofs for the `response` circuit.
// Used by the Hardhat tests and, through `serve`, by the Python node.
const path = require("path");
const readline = require("readline");
const snarkjs = require("snarkjs");
const { buildPoseidon } = require("circomlibjs");

const BUILD = process.env.ZK_BUILD_DIR || path.join(__dirname, "..", "circuits", "build");
const WASM = path.join(BUILD, "response_js", "response.wasm");
const ZKEY = path.join(BUILD, "response.zkey");

let poseidon;

async function commit(result, nonce) {
  poseidon ??= await buildPoseidon();
  const h = poseidon([BigInt(result), BigInt(nonce)]);
  return poseidon.F.toObject(h).toString();
}

// Returns the proof already laid out as Groth16Verifier.verifyProof arguments
async function prove({ result, nonce, commitment, verifier }) {
  const input = {
    result: BigInt(result).toString(),
    nonce: BigInt(nonce).toString(),
    commitment: BigInt(commitment).toString(),
    verifier: BigInt(verifier).toString(),
  };
  const { proof, publicSignals } = await snarkjs.groth16.fullProve(input, WASM, ZKEY);
  return {
    a: [proof.pi_a[0], proof.pi_a[1]],
    // G2 coordinates are swapped for the EVM precompile
    b: [
      [proof.pi_b[0][1], proof.pi_b[0][0]],
      [proof.pi_b[1][1], proof.pi_b[1][0]],
    ],
    c: [proof.pi_c[0], proof.pi_c[1]],
    publicSignals,
  };
}

// JSON-lines server: {"id", "op": "commit"|"prove", "args": {...}} -> {"id", "ok", "value"|"error"}
async function serve() {
  const rl = readline.createInterface({ input: process.stdin });
  for await (const line of rl) {
    if (!line.trim()) continue;
    let id = null;
    try {
      const req = JSON.parse(line);
      id = req.id;
      const value =
        req.op === "commit" ? await commit(req.args.result, req.args.nonce)
        : req.op === "prove" ? await prove(req.args)
        : (() => { throw new Error(`unknown op ${req.op}`); })();
      process.stdout.write(JSON.stringify({ id, ok: true, value }) + "\n");
    } catch (err) {
      process.stdout.write(JSON.stringify({ id, ok: false, error: String(err.message || err) }) + "\n");
    }
  }
  process.exit(0);
}

module.exports = { commit, prove };

if (require.main === module && process.argv[2] === "serve") {
  serve();
}
