# BlockSimPy

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

A discrete event simulator for blockchain networks that models mining competition, block propagation, difficulty adjustment, and economic incentives. The simulator enables controlled experimentation with blockchain protocols without operating live cryptocurrency nodes. Configurations for Bitcoin, Bitcoin Cash, Litecoin, and Dogecoin are provided.


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

## Testing

Validate the simulator works correctly:

```bash
python tests/test_validation.py
```

This runs simulations for Bitcoin, Litecoin, Dogecoin, and Bitcoin Cash, validating that metrics match expected values.

## Documentation

[Architecture](docs/ARCHITECTURE.md)

[Configuration guide](config/CONFIGURATION_GUIDE.md)


## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.