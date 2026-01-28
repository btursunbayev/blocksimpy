# BlockSimPy

[![CI](https://github.com/bekmukhamed/blocksimpy/actions/workflows/ci.yml/badge.svg)](https://github.com/bekmukhamed/blocksimpy/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/blocksimpy.svg)](https://pypi.org/project/blocksimpy/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

A discrete event simulator for blockchain networks that models mining competition, block propagation, difficulty adjustment, and economic incentives. Enables controlled experimentation with blockchain protocols without operating live cryptocurrency nodes.

**Supported chains:** Bitcoin, Bitcoin Cash, Litecoin, Dogecoin

**Features:**
- Proof-of-Work mining with realistic exponential timing
- Network propagation with configurable topology
- Difficulty adjustment and halving events
- Attack simulations (selfish mining, 51% double-spend, eclipse)
- Checkpoint/resume and metrics export


## Installation

```bash
pip install blocksimpy
```

## Quick Start

Run a Bitcoin simulation for 100 blocks:

```bash
blocksimpy --chain btc --blocks 100
```
or

```bash
bsim --chain btc --blocks 100
```

Run a custom blockchain:

```bash
blocksimpy --blocktime 30 --blocks 50 --miners 5
```

See all options:

```bash
blocksimpy --help
```

## Attack Simulations

Simulate known blockchain attacks for research and education:

```bash
# Selfish mining - attacker withholds blocks to gain unfair rewards
blocksimpy --chain btc --blocks 100 --attack selfish --attacker-hashrate 0.3

# 51% double-spend - attacker reverses confirmed payments
blocksimpy --chain btc --blocks 100 --attack double-spend --attacker-hashrate 0.51

# Eclipse - isolate victim nodes from honest network
blocksimpy --chain btc --blocks 100 --attack eclipse --victim-nodes 2
```

## Testing

Validate the simulator works correctly:

```bash
python tests/test_validation.py
```

This runs simulations for Bitcoin, Litecoin, Dogecoin, and Bitcoin Cash, validating that metrics match expected values.

## Documentation

[Architecture](docs/ARCHITECTURE.md)

[Configuration guide](src/blocksimpy/config/CONFIGURATION_GUIDE.md)


## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
