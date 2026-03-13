#![no_std]
extern crate alloc;
use alloc::string::String;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OracleReport {
    pub asset: String,
    pub price_usd: f64,
    pub moving_average: f64,
    pub source: String,
    pub timestamp: u64,
    pub analysis: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OracleCommitment {
    pub data_hash: [u8; 32],
    pub price_usd: f64,
    pub moving_average: f64,
    pub asset: String,
    pub timestamp: u64,
}
