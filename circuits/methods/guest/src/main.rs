// ZK Oracle — Guest Program (The ZK Circuit)
// =============================================
// This code runs INSIDE the zkVM. Everything here is "proved":
// - The zkVM guarantees this code executed correctly
// - Private inputs (oracle data) stay hidden
// - Only the "committed" outputs become public
//
// KEY CONCEPTS:
// - env::read()   → reads private input from the host
// - env::commit() → makes a value public in the proof's journal
// - Any Rust code you write here is automatically "proved"

#![no_main]
#![no_std]

extern crate alloc;

use alloc::string::String;
use risc0_zkvm::guest::env;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

risc0_zkvm::guest::entry!(main);

/// The oracle data structure that the AI agent produces
#[derive(Debug, Serialize, Deserialize)]
struct OracleReport {
    /// Asset name (e.g., "bitcoin")
    asset: String,
    /// Current price in USD
    price_usd: f64,
    /// Simple moving average (computed by the agent)
    moving_average: f64,
    /// Data source URL
    source: String,
    /// UNIX timestamp of when the data was fetched
    timestamp: u64,
    /// AI agent's analysis summary
    analysis: String,
}

/// The public output committed to the proof's journal
#[derive(Debug, Serialize, Deserialize)]
struct OracleCommitment {
    /// Hash of the full oracle report (proves data integrity)
    data_hash: [u8; 32],
    /// The verified price (this becomes publicly available)
    price_usd: f64,
    /// The verified moving average
    moving_average: f64,
    /// Asset name
    asset: String,
    /// Timestamp
    timestamp: u64,
}

fn main() {
    // ── Step 1: Read private input from the host ──
    let report: OracleReport = env::read();

    // ── Step 2: Validate the data ──
    // These checks run inside the zkVM, so they're "proved"
    assert!(report.price_usd > 0.0, "Price must be positive");
    assert!(report.timestamp > 0, "Timestamp must be set");
    assert!(!report.asset.is_empty(), "Asset name must not be empty");
    assert!(!report.source.is_empty(), "Source must not be empty");

    // ── Step 3: Recompute / verify the analysis ──
    // Here we verify that the moving average is reasonable
    // (In a real system, you'd recompute from raw data points)
    assert!(
        report.moving_average > 0.0,
        "Moving average must be positive"
    );

    // ── Step 4: Hash the full report for integrity ──
    // Hash the key fields for integrity
    let mut hasher = Sha256::new();
    hasher.update(report.asset.as_bytes());
    hasher.update(&report.price_usd.to_le_bytes());
    hasher.update(&report.moving_average.to_le_bytes());
    hasher.update(report.source.as_bytes());
    hasher.update(&report.timestamp.to_le_bytes());
    hasher.update(report.analysis.as_bytes());
    let data_hash: [u8; 32] = hasher.finalize().into();

    // ── Step 5: Commit public outputs to the journal ──
    // Only these values become visible in the proof
    let commitment = OracleCommitment {
        data_hash,
        price_usd: report.price_usd,
        moving_average: report.moving_average,
        asset: report.asset,
        timestamp: report.timestamp,
    };

    env::commit(&commitment);
}
