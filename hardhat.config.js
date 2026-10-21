require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.27",
    settings: { optimizer: { enabled: true, runs: 200 } },
  },
  paths: {
    sources: "./contracts/src",
    tests: "./contracts/test",
  },
  networks: {
    localhost: {
      url: process.env.PROVIDER_URL || "http://127.0.0.1:8545",
    },
  },
};
