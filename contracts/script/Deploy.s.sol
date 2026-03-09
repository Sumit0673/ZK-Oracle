// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import {ZKOracle} from "../src/ZKOracle.sol";
import {OracleConsumer} from "../src/OracleConsumer.sol";

/// @notice Deploy ZKOracle and OracleConsumer to local Anvil chain
contract Deploy is Script {
    function run() external {
        vm.startBroadcast();

        // Deploy the oracle
        ZKOracle oracle = new ZKOracle();
        console.log("ZKOracle deployed to:", address(oracle));

        // Deploy a consumer with $50,000 threshold (scaled by 1e8)
        OracleConsumer consumer = new OracleConsumer(
            address(oracle),
            50_000 * 1e8
        );
        console.log("OracleConsumer deployed to:", address(consumer));

        vm.stopBroadcast();
    }
}
