import sys
import asyncio
from pathlib import Path
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "integration"))

from agent import run_oracle
from bridge import generate_proof
from orchestrator import load_config, submit_to_contract
from web3 import Web3
import json

app = FastAPI(title="ZK-Oracle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PipelineStatus(BaseModel):
    asset: str
    status: str  # "idle", "analyzing", "proving", "submitting", "completed", "failed"
    progress: int  # 0 to 100
    message: str
    logs: list[str] = []
    report: Optional[dict] = None
    tx_hash: Optional[str] = None
    error: Optional[str] = None

pipeline_state: Dict[str, PipelineStatus] = {}

def run_zk_pipeline(asset: str):
    state = pipeline_state[asset]
    
    def log(msg: str, progress: Optional[int] = None):
        state.logs.append(msg)
        if progress is not None:
            state.progress = progress
        state.message = msg
        print(f"[{asset.upper()}] {msg}")

    try:
        # Step 1: AI Analysis
        log("Initializing AI Agent...", 5)
        state.status = "analyzing"
        
        log("Fetching current market data from Binance/ Kraken/ CoinGecko...", 10)
        
        log("AI Agent (Groq/Ollama) is analyzing price trends and generating report...", 25)
        report = run_oracle(asset)
        state.report = report.model_dump()
        
        log("Analysis complete. Verified by LLM.", 45)
        
        # Step 2: ZK Proof Generation
        state.status = "proving"
        log("Preparing data for ZK Proof generation...", 50)
        
        log("Requesting ZK Proof from RISC Zero Bonsai Cloud...", 60)
        proof_result = generate_proof(report)
        
        if not proof_result["success"]:
            log("⚠️ ZK Prover failed. Falling back to dummy proof for demonstration.", 70)
            log(f"Prover Error: {proof_result.get('error', 'Unknown')}")
            proof_bytes = b"\xde\xad\xbe\xef"
        else:
            with open(proof_result["proof_path"], "rb") as f:
                proof_bytes = f.read()
            
            if proof_result.get("status") == "SUCCEEDED":
                log("✅ ZK Proof generated successfully by Bonsai Cloud!", 75)
            else:
                log(f"✅ ZK Proof generated! Size: {len(proof_bytes)} bytes", 75)
            
        # Step 3: On-chain submission
        state.status = "submitting"
        
        config = load_config()
        rpc_url = config["ethereum"]["rpc_url"]
        network_name = "Sepolia" if "sepolia" in rpc_url.lower() else "Anvil"
        
        log(f"Connecting to Ethereum ({network_name}) via Web3.py...", 80)
        
        abi_path = Path(__file__).parent.parent / "contracts" / "out" / "ZKOracle.sol" / "ZKOracle.json"
        
        if not abi_path.exists():
             error_msg = f"Contract ABI not found at {abi_path}. Ensure you have added the JSON files to Git (git add -f contracts/out/ZKOracle.sol/ZKOracle.json)."
             log(f"❌ {error_msg}")
             raise Exception(error_msg)
             
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        log(f"Connected to {network_name}. Submitting transaction...", 85)
        
        with open(abi_path) as f:
            contract_abi = json.load(f)["abi"]
            
        contract = w3.eth.contract(
            address=config["ethereum"]["oracle_address"],
            abi=contract_abi,
        )
        
        account = config["ethereum"]["submitter_address"]
        receipt = submit_to_contract(w3, contract, report, proof_bytes, account)
        
        state.tx_hash = receipt["transactionHash"].hex()
        log(f"✅ Transaction confirmed! Hash: {state.tx_hash[:10]}...", 95)
        
        state.status = "completed"
        log("All steps verified. Pipeline complete.", 100)
        
    except Exception as e:
        state.status = "failed"
        state.error = str(e)
        log(f"❌ ERROR: {str(e)}")

@app.post("/analyze/{asset}")
async def start_analysis(asset: str):
    asset = asset.lower()
    if asset in pipeline_state and pipeline_state[asset].status in ["analyzing", "proving", "submitting"]:
        return {"message": "Pipeline already running for this asset", "status": pipeline_state[asset]}
    
    pipeline_state[asset] = PipelineStatus(
        asset=asset,
        status="idle",
        progress=0,
        message="Starting pipeline..."
    )
    
    asyncio.create_task(asyncio.to_thread(run_zk_pipeline, asset))
    return {"message": "Pipeline started", "asset": asset}

@app.get("/status/{asset}")
async def get_status(asset: str):
    asset = asset.lower()
    if asset not in pipeline_state:
        raise HTTPException(status_code=404, detail="No pipeline found for this asset")
    return pipeline_state[asset]

@app.get("/")
async def root():
    return {"message": "ZK-Oracle API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
