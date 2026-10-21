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
    // Blocks on a timer as well, so block.timestamp advances while the network is idle
    hardhat: {
      mining: { auto: true, interval: Number(process.env.BLOCK_INTERVAL_MS || 1000) },
      // Account 0 deploys and node i uses account i + 1 (sim/generate.py)
      accounts: { count: Number(process.env.HARDHAT_ACCOUNTS || 64) },
    },
    localhost: {
      url: process.env.PROVIDER_URL || "http://127.0.0.1:8545",
    },
  },
};
