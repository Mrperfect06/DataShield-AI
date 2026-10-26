/**
 * DataShield AI — Hardhat Configuration
 *
 * Configures Solidity compiler (0.8.20 with optimizer), local Hardhat network,
 * and the Polygon Amoy testnet.  Private keys and RPC URLs are loaded from
 * a .env file sitting alongside this config.
 */

require("dotenv").config();
require("@nomicfoundation/hardhat-toolbox");

// Pull deployment credentials from environment (or fall back to Hardhat defaults)
const POLYGON_AMOY_RPC = process.env.POLYGON_RPC_URL || "https://rpc-amoy.polygon.technology";
const DEPLOYER_KEY = process.env.DEPLOYER_PRIVATE_KEY ||
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"; // Hardhat account #0

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },

  networks: {
    // Local Hardhat / Anvil node
    localhost: {
      url: "http://127.0.0.1:8545",
      chainId: 31337,
    },

    // Polygon Amoy testnet
    polygon_amoy: {
      url: POLYGON_AMOY_RPC,
      chainId: 80002,
      accounts: [DEPLOYER_KEY],
      gasPrice: 30000000000, // 30 gwei — comfortable for testnet
    },
  },

  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};
