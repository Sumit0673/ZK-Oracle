
#![no_main]
#![no_std]

extern crate alloc;

use risc0_zkvm::guest::env;
use sha2::{Digest, Sha256};

use zk_oracle_core::{OracleReport, OracleCommitment};

risc0_zkvm::guest::entry!(main);

fn main() {
    let report: OracleReport = env::read();

    assert!(report.price_usd > 0.0, "Price must be positive");
    assert!(report.timestamp > 0, "Timestamp must be set");
    assert!(!report.asset.is_empty(), "Asset name must not be empty");
    assert!(!report.source.is_empty(), "Source must not be empty");

    assert!(
        report.moving_average > 0.0,
        "Moving average must be positive"
    );

    let mut hasher = Sha256::new();
    hasher.update(report.asset.as_bytes());
    hasher.update(&report.price_usd.to_le_bytes());
    hasher.update(&report.moving_average.to_le_bytes());
    hasher.update(report.source.as_bytes());
    hasher.update(&report.timestamp.to_le_bytes());
    hasher.update(report.analysis.as_bytes());
    let data_hash: [u8; 32] = hasher.finalize().into();

    let commitment = OracleCommitment {
        data_hash,
        price_usd: report.price_usd,
        moving_average: report.moving_average,
        asset: report.asset,
        timestamp: report.timestamp,
    };

    env::commit(&commitment);
}
