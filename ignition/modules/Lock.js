// This setup uses Hardhat Ignition to manage smart contract deployments.
// Learn more about it at https://hardhat.org/ignition
const data = require("../../bbyor/contracts/genesis_openfhe.json");
const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");



module.exports = buildModule("BbyorModule", (m) => {
  const bbyor = m.contract("contracts/bbyor.sol:BBYOR", []);
  for (let index = 0; index < data.length; index++) {
    const did = data[index];
    m.call(bbyor, "registerPeer", [did], {
      id: `registerPeer_${index}` // Unique ID per call
    } );
  }
  return { bbyor };
});
