# BlockSimPy

[![PyPI version](https://img.shields.io/pypi/v/blocksimpy.svg)](https://pypi.org/project/blocksimpy/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

A discrete event simulator for blockchain networks supporting Proof-of-Work, Proof-of-Stake, and Proof-of-Space consensus mechanisms. Models mining competition, validator selection, farmer allocation, block propagation, difficulty adjustment, and economic incentives. Includes attack simulations (selfish mining, 51% attacks, eclipse attacks) for security research and education. Enables controlled experimentation with blockchain protocols without operating live cryptocurrency nodes.

## Supported Chains

| Consensus | Chains |
|-----------|--------|
| **Proof of Work** | Bitcoin, Bitcoin Cash, Litecoin, Dogecoin |
| **Proof of Stake** | Ethereum 2.0 |
| **Proof of Space** | Chia |

## Features

- **PoW consensus** with exponential mining time distribution and competitive block discovery
- **PoS consensus** with stake-weighted validator selection
- **PoSpace consensus** with space-weighted farmer selection (Chia-style)
- Network propagation with configurable topology and peer connections
- Difficulty adjustment algorithms and reward halving schedules
- Attack simulations: selfish mining, 51% double-spend, eclipse attacks
- Metrics export, checkpoint/resume, and reproducible simulations


## Installation

```bash
pip install blocksimpy
```

## Quick Start

Simulate Bitcoin for 100 blocks:

```bash
blocksimpy --chain btc --blocks 100
```

Simulate Ethereum 2.0 Proof-of-Stake:

```bash
blocksimpy --chain eth2 --blocks 100
```

Simulate Chia Proof-of-Space:

```bash
blocksimpy --chain chia --blocks 100
```

Create custom blockchain with specific parameters:

```bash
blocksimpy --blocktime 30 --blocks 50 --miners 5
```

Short alias available:

```bash
bsim --chain btc --blocks 100
```

## Attack Simulations

Selfish mining attack where adversary withholds blocks to gain unfair mining rewards:

```bash
blocksimpy --chain btc --blocks 100 --attack selfish --attacker-hashrate 0.3
```

51% double-spend attack where majority hashrate reverses confirmed transactions:

```bash
blocksimpy --chain btc --blocks 100 --attack double-spend --attacker-hashrate 0.51
```

Eclipse attack isolating victim nodes from the honest network:

```bash
blocksimpy --chain btc --blocks 100 --attack eclipse --victim-nodes 2
```

## Testing

Run validation tests that verify simulator accuracy against known blockchain metrics:

```bash
pytest tests/
```

## Documentation

[Architecture](docs/ARCHITECTURE.md)

[Configuration guide](src/blocksimpy/config/CONFIGURATION_GUIDE.md)


## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.


## Author

Maintained by [**Bekmukhamed Tursunbayev**](https://btursunbayev.github.io)  
GitHub: https://github.com/btursunbayev · PyPI: https://pypi.org/user/btursunbayev/

