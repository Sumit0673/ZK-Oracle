import json
import sys
import yaml
from pathlib import Path
from web3 import Web3

sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))

from agent import run_oracle
from bridge import generate_proof
from analyzer import OracleReport


def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


import os

def submit_to_contract(
    w3: Web3,
    contract,
    report: OracleReport,
    proof_bytes: bytes,
    account: str,
) -> dict:

    price_scaled = int(report.price_usd * 1e8)
    ma_scaled = int(report.moving_average * 1e8)

    data_hash = w3.keccak(text=report.model_dump_json())

    # Hash the 243KB proof — full proof is saved to disk, only hash goes on-chain.
    # This drops calldata from 243KB → 32 bytes, cutting gas from ~9.7M to ~100K.
    proof_hash = w3.keccak(primitive=proof_bytes)

    private_key = os.getenv("ETH_PRIVATE_KEY")

    if private_key:
        # Manual signing for testnets/production
        nonce = w3.eth.get_transaction_count(account)
        gas_price = w3.eth.gas_price
        
        tx = contract.functions.submitData(
            report.asset,
            price_scaled,
            ma_scaled,
            report.timestamp,
            data_hash,
            proof_hash,
        ).build_transaction({
            "from": account,
            "nonce": nonce,
            "gas": 300_000,
            "gasPrice": gas_price,
            "chainId": w3.eth.chain_id
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    else:
        # Development mode (Anvil unlocked accounts)
        tx_hash = contract.functions.submitData(
            report.asset,
            price_scaled,
            ma_scaled,
            report.timestamp,
            data_hash,
            proof_hash,
        ).transact({
            "from": account,
            "gas": 300_000,
        })

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)  # Longer timeout for Sepolia
    return receipt


def run_pipeline(asset: str = "bitcoin", dry_run: bool = False):

    print("=" * 60)
    print(f"🚀 ZK Oracle Pipeline — {asset.upper()}")
    print("=" * 60)

    print("\n📡 Step 1: Running AI Agent...")
    report = run_oracle(asset)
    print(f"   ✅ Got report: {report.asset} @ ${report.price_usd:,.2f}")

    print("\n🔐 Step 2: Generating ZK Proof...")
    proof_result = generate_proof(report)

    if not proof_result["success"]:
        print(f"   ❌ Proof generation failed: {proof_result['error']}")
        print("   ℹ️  Using dummy proof for demo purposes")
        proof_bytes = b"\xde\xad\xbe\xef"
    else:
        with open(proof_result["proof_path"], "rb") as f:
            proof_bytes = f.read()
        print(f"   ✅ Proof generated ({len(proof_bytes)} bytes)")

    if dry_run:
        print("\n🏁 Dry run complete — skipping on-chain submission")
        print(f"   Report: {report.model_dump_json(indent=2)}")
        return

    print("\n⛓️  Step 3: Submitting to Smart Contract...")

    try:
        config = load_config()
        w3 = Web3(Web3.HTTPProvider(config["ethereum"]["rpc_url"]))

        if not w3.is_connected():
            print("   ❌ Cannot connect to Ethereum node")
            print("   ℹ️  Start Anvil with: anvil")
            return

        abi_path = (
            Path(__file__).parent.parent
            / "contracts" / "out" / "ZKOracle.sol" / "ZKOracle.json"
        )
        with open(abi_path) as f:
            contract_abi = json.load(f)["abi"]

        contract = w3.eth.contract(
            address=config["ethereum"]["oracle_address"],
            abi=contract_abi,
        )

        account = config["ethereum"]["submitter_address"]
        receipt = submit_to_contract(w3, contract, report, proof_bytes, account)

        print(f"   ✅ Transaction submitted!")
        print(f"   📋 Tx Hash: {receipt['transactionHash'].hex()}")
        print(f"   ⛽ Gas Used: {receipt['gasUsed']}")

    except Exception as e:
        print(f"   ❌ On-chain submission failed: {e}")
        print("   ℹ️  Make sure Anvil is running and contracts are deployed")

    print("\n" + "=" * 60)
    print("🏁 Pipeline complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ZK Oracle Pipeline")
    parser.add_argument("--asset", default="bitcoin", help="Crypto asset to process")
    parser.add_argument("--dry-run", action="store_true", help="Skip on-chain submission")
    args = parser.parse_args()

    run_pipeline(asset=args.asset, dry_run=args.dry_run)
