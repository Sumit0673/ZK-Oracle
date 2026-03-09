// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ZKOracle} from "./ZKOracle.sol";

/// @title OracleConsumer — Example contract that reads from ZKOracle
/// @notice Demonstrates how other dApps would consume verified oracle data
/// @dev This is a learning example showing the oracle consumer pattern

contract OracleConsumer {
    /// @notice Reference to the ZK Oracle contract
    ZKOracle public oracle;

    /// @notice Price threshold for alerts (scaled by 1e8)
    uint256 public priceThreshold;

    /// @notice Emitted when a price check detects the price is above threshold
    event PriceAlert(string asset, uint256 price, uint256 threshold);

    constructor(address _oracle, uint256 _threshold) {
        oracle = ZKOracle(_oracle);
        priceThreshold = _threshold;
    }

    /// @notice Check if an asset's verified price is above the threshold
    /// @param asset The asset name to check
    /// @return isAbove True if price exceeds threshold
    /// @return currentPrice The current verified price
    function checkPrice(string calldata asset)
        external
        view
        returns (bool isAbove, uint256 currentPrice)
    {
        (uint256 price, ) = oracle.getLatestPrice(asset);
        isAbove = price > priceThreshold;
        currentPrice = price;
    }

    /// @notice Get a full verified report for an asset from the oracle
    /// @param asset The asset name
    /// @return The full OracleData from the ZK Oracle
    function getVerifiedReport(string calldata asset)
        external
        view
        returns (ZKOracle.OracleData memory)
    {
        return oracle.getLatestData(asset);
    }

    /// @notice Update the price threshold
    function setThreshold(uint256 _threshold) external {
        priceThreshold = _threshold;
    }
}
