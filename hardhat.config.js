require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.27",
  networks: {
    local: {
      url: "http://127.0.0.1:8545",
      chainId: 1337,
      gasPrice: 1,             // ← 1 wei (quase free)
      // Força tempo real (aproximado)
      mining: {
        auto: false,
        interval: 1000 // 1 segundo entre blocos
      }
    }
  }
};
