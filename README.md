# 🔮 ZK-Verified AI Oracle: https://zk-oracle-b1r7.vercel.app/


> An on-chain oracle that uses **AI agents** to fetch & analyze off-chain data, then submits **zero-knowledge proofs** to verify the AI's computation was done correctly.

## 🏗️ Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   CoinGecko API  │────▶│  LangChain Agent │────▶│  ZK Prover       │
│   (Data Source)  │     │  (Python)        │     │  (Rust/RISC Zero)│
└──────────────────┘     └──────────────────┘     └────────┬─────────┘
                                                           │
                                                    Proof + Data
                                                           │
                                                           ▼
                                                  ┌──────────────────┐
                                                  │  ZKOracle.sol    │
                                                  │  (Solidity)      │
                                                  └────────┬─────────┘
                                                           │
                                                     Verified Data
                                                           │
                                                           ▼
                                                  ┌──────────────────┐
                                                  │  Consumer dApps  │
                                                  └──────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| AI Agent | Python + LangChain | Fetch & analyze off-chain data |
| ZK Circuits | Rust + RISC Zero | Prove computation integrity |
| Smart Contracts | Solidity + Foundry | On-chain verification & storage |
| Integration | Python + web3.py | End-to-end pipeline |

## 📁 Project Structure

```
ZK-Oracle/
├── agent/               # LangChain AI Agent (Python)
│   ├── agent.py         # Main agent with tools
│   ├── data_fetcher.py  # CoinGecko API integration
│   ├── analyzer.py      # Data analysis & OracleReport
│   └── bridge.py        # Python → Rust prover bridge
├── circuits/            # ZK Circuits (Rust / RISC Zero)
│   ├── host/            # Prover host program
│   └── methods/         # Guest program (the circuit)
├── contracts/           # Smart Contracts (Solidity / Foundry)
│   ├── src/             # Contract source code
│   ├── test/            # Foundry tests
│   └── script/          # Deployment scripts
├── integration/         # End-to-end pipeline
│   ├── orchestrator.py  # Full pipeline runner
│   └── config.yaml      # Configuration
└── Makefile             # Build & run commands
```

## 🚀 Quick Start

### Prerequisites

- **Rust** 1.72+ (`rustup`)
- **Python** 3.10+ with `venv`
- **Foundry** (`foundryup`)
- **RISC Zero** (`cargo binstall cargo-risczero`)
- **OpenAI API Key** for the LangChain agent

### Setup

```bash
# 1. Install Foundry (if not already installed)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# 2. Install RISC Zero
cargo install cargo-binstall
cargo binstall cargo-risczero
cargo risczero install

# 3. Setup all components
make setup

# 4. Copy and fill in your API keys
cp agent/.env.example agent/.env
# Edit agent/.env with your OPENAI_API_KEY
```

### Run

```bash
# Run the AI agent standalone
make agent

# Run Solidity tests
make contracts-test

# Build ZK circuits
make setup-circuits

# Run the full pipeline (dry run)
python integration/orchestrator.py --dry-run

# Run with on-chain submission
make anvil          # Terminal 1: start local Ethereum node
make contracts-deploy  # Terminal 2: deploy contracts
make run            # Terminal 3: run full pipeline
```


1. **Phase 1**: Project setup (you are here!)
2. **Phase 2**: Build the LangChain AI Agent
3. **Phase 3**: Write ZK circuits in Rust
4. **Phase 4**: Build Solidity smart contracts
5. **Phase 5**: Integrate all components
6. **Phase 6**: Testing & verification
7. **Phase 7**: Documentation

