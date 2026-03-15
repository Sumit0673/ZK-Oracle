import json
import yaml
from pathlib import Path
from web3 import Web3
from hexbytes import HexBytes

config_path = Path("integration/config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

w3 = Web3(Web3.HTTPProvider(config["ethereum"]["rpc_url"]))
account = config["ethereum"]["submitter_address"]

abi_path = Path("contracts/out/ZKOracle.sol/ZKOracle.json")
with open(abi_path) as f:
    contract_abi = json.load(f)["abi"]

contract = w3.eth.contract(
    address=config["ethereum"]["oracle_address"],
    abi=contract_abi,
)

# Dummy info
asset = "bitcoin"
price_scaled = 6500000000000
ma_scaled = 6500000000000
timestamp = 1773445367
data_hash = w3.keccak(text="dummy_data_hash")
proof_bytes = b"\xde\xad\xbe\xef"

try:
    print("Estimating gas to see if it reverts...")
    gas_estimate = contract.functions.submitData(
        asset, price_scaled, ma_scaled, timestamp, data_hash, proof_bytes
    ).estimate_gas({"from": account})
    print(f"Gas Estimate: {gas_estimate}")

    print("Building transaction...")
    latest_block = w3.eth.get_block('latest')
    base_fee = latest_block.get('baseFeePerGas', w3.to_wei(1, 'gwei'))
    max_priority_fee = w3.to_wei(2, 'gwei')
    max_fee_per_gas = base_fee * 2 + max_priority_fee

    tx_params = {
        "from": account,
        "nonce": w3.eth.get_transaction_count(account),
        "gas": 500_000,
        "maxFeePerGas": max_fee_per_gas,
        "maxPriorityFeePerGas": max_priority_fee,
        "chainId": w3.eth.chain_id,
    }
    tx = contract.functions.submitData(
        asset, price_scaled, ma_scaled, timestamp, data_hash, proof_bytes
    ).build_transaction(tx_params)
    
    print("Signing transaction...")
    signed = w3.eth.account.sign_transaction(tx, private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
    
    print("Sending raw transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Sent tx hash: {tx_hash.hex()}")
    
    print("Waiting for receipt...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f"Receipt: {receipt['status']}")
except Exception as e:
    print(f"Error: {e}")
