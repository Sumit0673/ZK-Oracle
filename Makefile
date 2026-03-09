.PHONY: all setup agent circuits contracts integration clean help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Setup

setup: setup-agent setup-circuits setup-contracts 

setup-agent:
	cd agent && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt

setup-circuits:
	cd circuits && cargo build --release

setup-contracts:
	cd contracts && forge install

# Run 

agent:
	cd agent && . venv/bin/activate && python agent.py

prover:
	cd circuits && cargo run --release -- --input sample_data.json

contracts-test:
	cd contracts && forge test -vvv

contracts-deploy:
	cd contracts && forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast

anvil:
	anvil

# Integration 

run:
	cd agent && . venv/bin/activate && python ../integration/orchestrator.py

# Clean 

clean:
	cd circuits && cargo clean
	cd contracts && forge clean
	rm -rf agent/__pycache__ agent/.pytest_cache

# All 

all: setup contracts-test
