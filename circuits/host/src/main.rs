
use anyhow::Result;
use clap::Parser;
use risc0_zkvm::{default_prover, ExecutorEnv};
use std::fs;

use methods::{ORACLE_GUEST_ELF, ORACLE_GUEST_ID};
use zk_oracle_core::OracleReport;

#[derive(Parser, Debug)]
#[command(author, version, about)]
struct Args {
    #[arg(short, long)]
    input: String,
}

fn main() -> Result<()> {
    let args = Args::parse();

    let oracle_data_json = fs::read_to_string(&args.input)?;
    println!("📊 Loaded oracle data from: {}", args.input);

    let oracle_report: OracleReport = serde_json::from_str(&oracle_data_json)?;

    let env = ExecutorEnv::builder()
        .write(&oracle_report)?
        .build()?;

    println!("🔐 Generating ZK proof... (this may take a moment)");

    let prover = default_prover();
    let receipt = prover.prove(env, ORACLE_GUEST_ELF)?;

    receipt.receipt.verify(ORACLE_GUEST_ID)?;
    println!("✅ Proof verified locally!");

    let journal_bytes = receipt.receipt.journal.bytes.clone();
    println!("📋 Journal (public output): {}", hex::encode(&journal_bytes));

    let proof_bytes = bincode::serialize(&receipt.receipt)?;
    println!("📦 Proof size: {} bytes", proof_bytes.len());

    fs::write("output/proof.bin", &proof_bytes)?;
    fs::write("output/journal.bin", &journal_bytes)?;
    println!("💾 Proof and journal saved to output/");

    Ok(())
}
