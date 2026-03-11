#![no_std]
extern crate alloc;
use alloc::string::String;
use serde::{Deserialize, Serialize};

/// The oracle data structure that the AI agent produces
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OracleReport {
    /// Asset name (e.g., "bitcoin")
    pub asset: String,
    /// Current price in USD
    pub price_usd: f64,
    /// Simple moving average (computed by the agent)
    pub moving_average: f64,
    /// Data source URL
    pub source: String,
    /// UNIX timestamp of when the data was fetched
    pub timestamp: u64,
    /// AI agent's analysis summary
    pub analysis: String,
}

/// The public output committed to the proof's journal
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OracleCommitment {
    /// Hash of the full oracle report (proves data integrity)
    pub data_hash: [u8; 32],
    /// The verified price (this becomes publicly available)
    pub price_usd: f64,
    /// The verified moving average
    pub moving_average: f64,
    /// Asset name
    pub asset: String,
    /// Timestamp
    pub timestamp: u64,
}
