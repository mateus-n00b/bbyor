// Deploys Groth16Verifier + Reputation and admits the peers listed in PEERS_FILE.
//   PEERS_FILE=sim/out/peers.json DEPLOYMENT_FILE=sim/out/deployment.json \
//     npx hardhat run scripts/deploy.js --network localhost
const fs = require("fs");
const path = require("path");
const { ethers, artifacts } = require("hardhat");

async function main() {
  const peersFile = process.env.PEERS_FILE || "sim/out/peers.json";
  const outFile = process.env.DEPLOYMENT_FILE || "sim/out/deployment.json";
  const minInterval = Number(process.env.MIN_INTERVAL || 30);
  const maxInterval = Number(process.env.MAX_INTERVAL || 40);

  // [{ "account": "0x...", "did": "..." }, ...]
  const peers = JSON.parse(fs.readFileSync(peersFile, "utf8"));

  const verifier = await ethers.deployContract("Groth16Verifier");
  await verifier.waitForDeployment();
  const rep = await ethers.deployContract("Reputation", [await verifier.getAddress(), minInterval, maxInterval]);
  await rep.waitForDeployment();

  for (const { account, did } of peers) {
    await (await rep.registerPeer(account, did)).wait();
  }

  const { abi } = await artifacts.readArtifact("Reputation");
  const deployment = {
    address: await rep.getAddress(),
    verifier: await verifier.getAddress(),
    block: (await rep.deploymentTransaction().getTransaction()).blockNumber,
    abi,
  };
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, JSON.stringify(deployment, null, 2));
  console.log(`Reputation at ${deployment.address} with ${peers.length} peers -> ${outFile}`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
