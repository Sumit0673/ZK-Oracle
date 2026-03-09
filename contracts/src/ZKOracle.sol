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
    // ─── State Variables ─────────────────────────────────────────────

    /// @notice The owner of the oracle (can update config)
    address public owner;

    /// @notice Counter for total data submissions
    uint256 public submissionCount;

    /// @notice Struct representing a verified oracle data point
    struct OracleData {
        string asset;          // e.g., "bitcoin"
        uint256 priceUsd;      // Price in USD (scaled by 1e8 for precision)
        uint256 movingAverage; // Moving average (scaled by 1e8)
        uint256 timestamp;     // When the data was fetched
        bytes32 dataHash;      // Hash of the full oracle report
        address submitter;     // Who submitted this data
        uint256 blockNumber;   // Block when it was submitted
    }

    /// @notice Latest verified data for each asset
    mapping(string => OracleData) public latestData;

    /// @notice History of all submissions (by index)
    mapping(uint256 => OracleData) public submissions;

    /// @notice Trusted submitters who can push data
    mapping(address => bool) public trustedSubmitters;

    // ─── Events ──────────────────────────────────────────────────────

    /// @notice Emitted when new verified data is submitted
    event DataSubmitted(
        string indexed asset,
        uint256 priceUsd,
        uint256 movingAverage,
        uint256 timestamp,
        bytes32 dataHash,
        address indexed submitter
    );

    /// @notice Emitted when a submitter is added or removed
    event SubmitterUpdated(address indexed submitter, bool trusted);

    // ─── Modifiers ───────────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "ZKOracle: not owner");
        _;
    }

    modifier onlyTrusted() {
        require(trustedSubmitters[msg.sender], "ZKOracle: not trusted submitter");
        _;
    }

    // ─── Constructor ─────────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
        trustedSubmitters[msg.sender] = true;
    }

    // ─── Core Functions ──────────────────────────────────────────────

    /// @notice Submit verified oracle data with a ZK proof
    /// @param asset The asset name (e.g., "bitcoin")
    /// @param priceUsd The price in USD (scaled by 1e8)
    /// @param movingAverage The moving average (scaled by 1e8)
    /// @param timestamp When the data was fetched (UNIX timestamp)
    /// @param dataHash Hash of the full oracle report
    /// @param proof The ZK proof bytes (to be verified)
    function submitData(
        string calldata asset,
        uint256 priceUsd,
        uint256 movingAverage,
        uint256 timestamp,
        bytes32 dataHash,
        bytes calldata proof
    ) external onlyTrusted {
        // Validate inputs
        require(bytes(asset).length > 0, "ZKOracle: empty asset");
        require(priceUsd > 0, "ZKOracle: zero price");
        require(timestamp > 0, "ZKOracle: zero timestamp");
        require(timestamp <= block.timestamp + 300, "ZKOracle: future timestamp");

        // TODO: Add actual ZK proof verification here
        // For now, we verify that proof bytes are not empty
        // In production, this would call a RISC Zero verifier contract
        require(proof.length > 0, "ZKOracle: empty proof");

        // Store the verified data
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

        emit DataSubmitted(asset, priceUsd, movingAverage, timestamp, dataHash, msg.sender);
    }

    // ─── View Functions ──────────────────────────────────────────────

    /// @notice Get the latest verified price for an asset
    /// @param asset The asset name
    /// @return priceUsd The latest price (scaled by 1e8)
    /// @return timestamp When the data was fetched
    function getLatestPrice(string calldata asset)
        external
        view
        returns (uint256 priceUsd, uint256 timestamp)
    {
        OracleData storage data = latestData[asset];
        require(data.timestamp > 0, "ZKOracle: no data for asset");
        return (data.priceUsd, data.timestamp);
    }

    /// @notice Get the full latest data for an asset
    /// @param asset The asset name
    /// @return The full OracleData struct
    function getLatestData(string calldata asset)
        external
        view
        returns (OracleData memory)
    {
        OracleData storage data = latestData[asset];
        require(data.timestamp > 0, "ZKOracle: no data for asset");
        return data;
    }

    // ─── Admin Functions ─────────────────────────────────────────────

    /// @notice Add or remove a trusted submitter
    function setTrustedSubmitter(address submitter, bool trusted) external onlyOwner {
        trustedSubmitters[submitter] = trusted;
        emit SubmitterUpdated(submitter, trusted);
    }

    /// @notice Transfer ownership
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "ZKOracle: zero address");
        owner = newOwner;
    }
}
