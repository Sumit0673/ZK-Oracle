import os
import json
import subprocess
import tempfile
import struct
import time
import httpx
from pathlib import Path
from analyzer import OracleReport

IMAGE_ID = "62082eb7e35787321093273cad43850139c571689f309692ae0b0b8fe10f8c3f"

PROVER_BINARY = Path(__file__).parent.parent / "circuits" / "target" / "release" / "zk-oracle-host"

def serialize_for_risczero(report: OracleReport) -> bytes:
    """
    Serializes OracleReport to RISC Zero's binary format (4-byte aligned).
    Logic based on RISC Zero's native serialization for the zkVM guest.
    """
    def pack_str(s: str) -> bytes:
        data = s.encode('utf-8')
        length = len(data)
        packed = struct.pack("<I", length) + data
        padding = (4 - (len(packed) % 4)) % 4
        return packed + (b'\x00' * padding)

    data = b""
    data += pack_str(report.asset)
    data += struct.pack("<d", report.price_usd)
    data += struct.pack("<d", report.moving_average)
    data += pack_str(report.source)
    data += struct.pack("<Q", report.timestamp)
    data += pack_str(report.analysis)
    return data

def generate_proof_bonsai(report: OracleReport) -> dict:
    """Generates a ZK proof using RISC Zero's Bonsai cloud service."""
    api_key = os.getenv("BONSAI_API_KEY")
    api_url = os.getenv("BONSAI_API_URL", "https://api.bonsai.xyz/v1/").rstrip("/")

    if not api_key:
        return {"success": False, "error": "Missing BONSAI_API_KEY"}

    try:
        headers = {"x-api-key": api_key, "Content-Type": "application/octet-stream"}
        input_data = serialize_for_risczero(report)

        print("☁️ Uploading input to Bonsai...")
        with httpx.Client() as client:
            res = client.post(f"{api_url}/inputs", content=input_data, headers=headers)
            res.raise_for_status()
            input_id = res.json()["id"]

            print(f"🔄 Creating proving session for Image {IMAGE_ID[:8]}...")
            session_payload = {"image_id": IMAGE_ID, "input_id": input_id}
            res = client.post(f"{api_url}/sessions", json=session_payload, headers=headers)
            res.raise_for_status()
            session_id = res.json()["id"]

            print(f"⏳ Waiting for ZK Proof (Session: {session_id[:8]})...")
            start_time = time.time()
            while time.time() - start_time < 600:  # 10 min timeout
                res = client.get(f"{api_url}/sessions/{session_id}", headers=headers)
                status = res.json()["status"]
                
                if status == "SUCCEEDED":
                    print("✅ ZK Proof generated successfully by Bonsai!")
                    receipt_res = client.get(f"{api_url}/sessions/{session_id}/receipt", headers=headers)
                    receipt_res.raise_for_status()
                    
                    output_dir = Path(__file__).parent.parent / "circuits" / "output"
                    output_dir.mkdir(exist_ok=True)
                    
                    # Receipts from Bonsai are stored as JSON for simplified verification/audit
                    receipt_data = receipt_res.json()
                    with open(output_dir / "receipt.json", "w") as f:
                        json.dump(receipt_data, f)
                    
                    # We create a simple reference file for the proof.bin 
                    # In a full SNARK flow, we'd extract the seal here.
                    with open(output_dir / "proof.bin", "wb") as f:
                        f.write(json.dumps(receipt_data).encode())
                    
                    return {
                        "success": True,
                        "proof_path": str(output_dir / "proof.bin"),
                        "status": "SUCCEEDED"
                    }
                elif status == "FAILED":
                    return {"success": False, "error": f"Bonsai session failed: {res.json().get('error')}"}
                
                time.sleep(5)
            
            return {"success": False, "error": "Bonsai timeout"}

    except Exception as e:
        return {"success": False, "error": f"Bonsai API Error: {str(e)}"}

def generate_proof(report: OracleReport) -> dict:
    """Orchestrates proof generation, prioritizing Bonsai then Local then Dummy."""
    
    if os.getenv("BONSAI_API_KEY"):
        result = generate_proof_bonsai(report)
        if result["success"]:
            return result
        print(f"⚠️ Bonsai failed, falling back: {result.get('error')}")

    if PROVER_BINARY.exists():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(report.model_dump_json())
            input_path = f.name

        try:
            res = subprocess.run([str(PROVER_BINARY), "--input", input_path], 
                               capture_output=True, text=True, timeout=300)
            if res.returncode == 0:
                output_dir = Path(__file__).parent.parent / "circuits" / "output"
                return {
                    "success": True, 
                    "proof_path": str(output_dir / "proof.bin"),
                    "journal_path": str(output_dir / "journal.bin")
                }
        except Exception as e:
            print(f"⚠️ Local prover failed: {e}")

    print("⚠️ Using dummy proof for demonstration.")
    output_dir = Path(__file__).parent.parent / "circuits" / "output"
    output_dir.mkdir(exist_ok=True)
    dummy_proof = b"dummy_zk_proof_" + os.urandom(16)
    with open(output_dir / "proof.bin", "wb") as f:
        f.write(dummy_proof)
    
    return {
        "success": True,
        "proof_path": str(output_dir / "proof.bin"),
        "is_dummy": True
    }
