// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ZKOracle} from "./ZKOracle.sol";

contract OracleConsumer {
    ZKOracle public oracle;

    uint256 public priceThreshold;

    event PriceAlert(string asset, uint256 price, uint256 threshold);

    constructor(address _oracle, uint256 _threshold) {
        oracle = ZKOracle(_oracle);
        priceThreshold = _threshold;
    }

    function checkPrice(
        string calldata asset
    ) external view returns (bool isAbove, uint256 currentPrice) {
        (uint256 price, ) = oracle.getLatestPrice(asset);
        isAbove = price > priceThreshold;
        currentPrice = price;
    }

    function getVerifiedReport(
        string calldata asset
    ) external view returns (ZKOracle.OracleData memory) {
        return oracle.getLatestData(asset);
    }

    function setThreshold(uint256 _threshold) external {
        priceThreshold = _threshold;
    }
}
