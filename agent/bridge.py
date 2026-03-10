import json
import subprocess
import tempfile
from pathlib import Path
from analyzer import OracleReport


PROVER_BINARY = Path(__file__).parent.parent / "circuits" / "target" / "release" / "zk-oracle-host"


def generate_proof(report: OracleReport) -> dict:

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, prefix="oracle_"
    ) as f:
        f.write(report.model_dump_json())
        input_path = f.name

    print(f"📝 Wrote oracle data to: {input_path}")

    output_dir = Path(__file__).parent.parent / "circuits" / "output"
    output_dir.mkdir(exist_ok=True)

    try:
        result = subprocess.run(
            [str(PROVER_BINARY), "--input", input_path],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(output_dir.parent),
        )

        if result.returncode != 0:
            print(f"❌ Prover failed: {result.stderr}")
            return {"success": False, "error": result.stderr}

        print(f"✅ Prover output: {result.stdout}")

        return {
            "success": True,
            "proof_path": str(output_dir / "proof.bin"),
            "journal_path": str(output_dir / "journal.bin"),
            "stdout": result.stdout,
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Prover binary not found at {PROVER_BINARY}. "
                     f"Run 'cd circuits && cargo build --release' first.",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Prover timed out (>300 seconds)",
        }


if __name__ == "__main__":
    mock = OracleReport(
        asset="bitcoin",
        price_usd=67000.0,
        moving_average=65000.0,
        source="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin",
        timestamp=1700000000,
        analysis="Bitcoin is trading at $67,000, above its 7-day MA of $65,000",
    )
    print("🔐 Testing ZK proof generation...")
    result = generate_proof(mock)
    print(json.dumps(result, indent=2))
